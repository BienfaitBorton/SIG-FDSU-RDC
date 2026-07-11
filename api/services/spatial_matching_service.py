"""National Spatial Matching Engine (NSME) — correspondance spatiale actifs ↔ besoins.

Relie sites FDSU / CCN / télécom aux localités non couvertes (NCI) et calcule
l'impact populationnel de façon explicable. Priorité PostGIS, fallback fichier signalé.
"""

from __future__ import annotations

import json
import math
import time
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

from psycopg2.extras import Json, RealDictCursor, execute_batch

from api.config import DATA_MODE, connect_db
from api.services import coverage_intelligence_service as nci

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RULES_PATH = PROJECT_ROOT / "data" / "business" / "spatial_matching_rules.json"
CCN_PATH = PROJECT_ROOT / "data" / "programs" / "ccn" / "demo_ccn.json"
ENGINE_VERSION = "nsme-1.0.0"

_CACHE: dict[str, Any] = {"stats": None, "stats_at": 0.0}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now_dt() -> datetime:
    return datetime.now(timezone.utc)


@lru_cache(maxsize=1)
def get_rules() -> dict[str, Any]:
    if not RULES_PATH.exists():
        return {"_meta": {"status": "missing"}, "service_radii_m": {}, "matching": {}}
    return json.loads(RULES_PATH.read_text(encoding="utf-8"))


def reload_rules() -> dict[str, Any]:
    get_rules.cache_clear()
    return get_rules()


def _radius_for_asset(asset_type: str, technology: str | None = None) -> float:
    rules = get_rules()
    radii = rules.get("service_radii_m") or {}
    matching = rules.get("matching") or {}
    if asset_type == "ccn":
        return float(radii.get("ccn_community_impact") or matching.get("default_max_distance_m") or 10000)
    if asset_type in {"telecom_infrastructure", "fiber"}:
        return float(radii.get("fiber_connection") or 5000)
    if asset_type == "backbone":
        return float(radii.get("backbone_connection") or 15000)
    if asset_type == "health_facility":
        return float(radii.get("health_proximity") or 5000)
    by_tech = radii.get("site_by_technology") or {}
    if technology and technology in by_tech:
        return float(by_tech[technology])
    return float(radii.get("site_telecom_default") or matching.get("default_max_distance_m") or 15000)


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def _confidence(locality: dict[str, Any], distance_m: float | None) -> str:
    has_coords = bool(locality.get("coords_valid"))
    has_pop = locality.get("population") not in (None, "", 0)
    has_prio = bool(locality.get("priority"))
    has_dist = distance_m is not None
    if has_coords and has_pop and has_prio and has_dist:
        return "high"
    if has_coords and has_dist:
        return "medium"
    if has_coords:
        return "low"
    return "partial"


def _estimate_ndci_gain(localities_count: int, population: float | None) -> dict[str, Any]:
    rules = get_rules().get("impact") or {}
    per = float(rules.get("ndci_gain_per_locality_point") or 0.15)
    cap = float(rules.get("ndci_gain_cap") or 12.0)
    raw = localities_count * per
    if population:
        raw += min(3.0, math.log10(max(population, 1)) * 0.8)
    value = round(min(cap, raw), 2)
    return {
        "value": value,
        "status": rules.get("coverage_gain_status") or "estime",
        "unit": "points NDCI",
        "note": "Gain estimé — non inventé comme mesure observée.",
    }


def ensure_schema() -> bool:
    """Applique le DDL NSME si la table n'existe pas encore."""
    if DATA_MODE != "db":
        return False
    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'analysis' AND table_name = 'asset_need_matches'
                    """
                )
                exists = cur.fetchone() is not None
            if exists:
                return True
            sql = (PROJECT_ROOT / "database" / "analysis_schema.sql").read_text(encoding="utf-8")
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
        return True
    except Exception:  # noqa: BLE001
        return False


def _table_ready() -> bool:
    if DATA_MODE != "db":
        return False
    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'analysis' AND table_name = 'asset_need_matches'
                    """
                )
                return cur.fetchone() is not None
    except Exception:  # noqa: BLE001
        return False


def list_fdsu_sites(
    *,
    program_code: str | None = None,
    province: str | None = None,
    territoire: str | None = None,
    asset_id: int | None = None,
    limit: int = 5000,
) -> list[dict[str, Any]]:
    if DATA_MODE != "db":
        return []
    clauses = ["s.latitude IS NOT NULL", "s.longitude IS NOT NULL"]
    params: list[Any] = []
    if asset_id is not None:
        clauses.append("s.id = %s")
        params.append(asset_id)
    if program_code:
        # Accepte PROG_SITES_40 ou sites_40
        clauses.append("(p.program_code = %s OR LOWER(REPLACE(p.program_code, 'PROG_', '')) = LOWER(%s))")
        params.extend([program_code, program_code.replace("PROG_", "").lower()])
    if province:
        clauses.append("LOWER(s.province) = LOWER(%s)")
        params.append(province)
    if territoire:
        clauses.append("LOWER(s.territoire) = LOWER(%s)")
        params.append(territoire)
    params.append(limit)
    query = f"""
        SELECT
            s.id,
            s.site_code,
            s.site_name,
            s.province,
            s.territoire,
            s.zone,
            s.status,
            s.latitude,
            s.longitude,
            p.program_code,
            p.program_name
        FROM programs.fdsu_sites s
        JOIN programs.fdsu_programs p ON p.id = s.program_id
        WHERE {' AND '.join(clauses)}
        ORDER BY s.id
        LIMIT %s
    """
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]


def _load_ccn_assets() -> list[dict[str, Any]]:
    if not CCN_PATH.exists():
        return []
    payload = json.loads(CCN_PATH.read_text(encoding="utf-8"))
    items = payload.get("items") or payload.get("ccn") or payload
    if not isinstance(items, list):
        return []
    out = []
    for item in items:
        lat = item.get("latitude") or item.get("lat")
        lon = item.get("longitude") or item.get("lon") or item.get("lng")
        if lat is None or lon is None:
            continue
        out.append(
            {
                "id": item.get("id"),
                "business_id": item.get("business_id") or item.get("code") or str(item.get("id")),
                "name": item.get("name"),
                "latitude": float(lat),
                "longitude": float(lon),
                "province": item.get("province"),
                "territoire": item.get("territoire"),
                "status": item.get("status"),
                "ccn_type": item.get("type") or item.get("ccn_type"),
                "population_served": item.get("population_served") or item.get("population"),
                "source": "fichier",
            }
        )
    return out


def _uncovered_localities(
    *,
    province: str | None = None,
    territoire: str | None = None,
    priority_level: str | None = None,
    category: str | None = None,
    coords_only: bool = True,
) -> list[dict[str, Any]]:
    rows = nci._load_localities("uncovered")  # noqa: SLF001 — réutilisation cache NCI
    out = []
    for row in rows:
        if coords_only and not row.get("coords_valid"):
            continue
        if province and str(row.get("province") or "").lower() != province.lower():
            continue
        if territoire and str(row.get("territoire") or "").lower() != territoire.lower():
            continue
        if priority_level and str(row.get("priority") or "").lower() != priority_level.lower():
            continue
        if category and str(row.get("categorie") or "").lower() != category.lower():
            continue
        out.append(row)
    return out


def match_site_to_uncovered_localities(
    site: dict[str, Any],
    localities: list[dict[str, Any]] | None = None,
    *,
    max_distance_m: float | None = None,
    max_matches: int | None = None,
) -> list[dict[str, Any]]:
    """Correspondance site FDSU → localités non couvertes (haversine ou préfiltrage territoire)."""
    rules = get_rules()
    matching = rules.get("matching") or {}
    radius = float(max_distance_m or _radius_for_asset("fdsu_site"))
    limit = int(max_matches or matching.get("max_matches_per_asset") or 80)
    lat = site.get("latitude")
    lon = site.get("longitude")
    if lat is None or lon is None:
        return []

    pool = localities
    if pool is None:
        # Préfiltre administratif si possible
        pool = _uncovered_localities(
            province=site.get("province"),
            territoire=site.get("territoire"),
            coords_only=True,
        )
        # Si trop peu dans le territoire, élargir à la province
        if len(pool) < 5:
            pool = _uncovered_localities(province=site.get("province"), coords_only=True)
        if len(pool) < 5:
            # Fenêtre spatiale autour du site (évite scan national 25k)
            try:
                lat0 = float(lat)
                lon0 = float(lon)
                deg = max(0.15, (radius / 111_000.0) * 1.2)
                all_locs = _uncovered_localities(coords_only=True)
                pool = [
                    loc
                    for loc in all_locs
                    if abs(float(loc["latitude"]) - lat0) <= deg
                    and abs(float(loc["longitude"]) - lon0) <= deg
                ]
            except (TypeError, ValueError, KeyError):
                pool = []

    matches: list[dict[str, Any]] = []
    for loc in pool:
        try:
            dist = _haversine_m(float(lat), float(lon), float(loc["latitude"]), float(loc["longitude"]))
        except (TypeError, ValueError, KeyError):
            continue
        if dist > radius:
            continue
        pop = loc.get("population")
        try:
            pop_f = float(pop) if pop is not None else None
        except (TypeError, ValueError):
            pop_f = None
        gain = _estimate_ndci_gain(1, pop_f)
        matches.append(
            {
                "asset_type": "fdsu_site",
                "asset_id": site.get("id"),
                "asset_business_id": site.get("site_code") or str(site.get("id")),
                "need_type": "uncovered_locality",
                "need_id": loc.get("id"),
                "relation_type": "SERVES_LOCALITY",
                "distance_m": round(dist, 1),
                "service_radius_m": radius,
                "population_impacted": pop_f,
                "localities_impacted": 1,
                "infrastructure_type": loc.get("infra_type"),
                "priority_level": loc.get("priority"),
                "category": loc.get("categorie"),
                "ndci_before": None,
                "ndci_after_estimated": gain["value"],
                "confidence_level": _confidence(loc, dist),
                "source_asset": "programs.fdsu_sites",
                "source_need": "data/coverage/localities_uncovered.jsonl",
                "calculation_method": "haversine_dwithin_equiv",
                "province": loc.get("province") or site.get("province"),
                "territoire": loc.get("territoire") or site.get("territoire"),
                "program_code": site.get("program_code"),
                "properties": {
                    "locality_name": loc.get("name"),
                    "site_name": site.get("site_name"),
                    "asset_lat": lat,
                    "asset_lon": lon,
                    "need_lat": loc.get("latitude"),
                    "need_lon": loc.get("longitude"),
                    "ndci_gain_status": gain["status"],
                    "population_status": "calcule" if pop_f is not None else "non_disponible",
                },
            }
        )

    matches.sort(key=lambda m: (m["distance_m"] is None, m["distance_m"] or 1e18))
    return matches[:limit]


def match_ccn_to_population(
    ccn: dict[str, Any],
    localities: list[dict[str, Any]] | None = None,
    *,
    max_distance_m: float | None = None,
) -> list[dict[str, Any]]:
    radius = float(max_distance_m or _radius_for_asset("ccn"))
    site_like = {
        "id": ccn.get("id"),
        "site_code": ccn.get("business_id"),
        "site_name": ccn.get("name"),
        "latitude": ccn.get("latitude"),
        "longitude": ccn.get("longitude"),
        "province": ccn.get("province"),
        "territoire": ccn.get("territoire"),
        "program_code": "ccn",
    }
    raw = match_site_to_uncovered_localities(
        site_like, localities, max_distance_m=radius
    )
    for row in raw:
        row["asset_type"] = "ccn"
        row["relation_type"] = "CONNECTS_CCN"
        row["source_asset"] = "data/programs/ccn/demo_ccn.json"
        row["calculation_method"] = "haversine_ccn_radius"
        row["properties"] = {
            **(row.get("properties") or {}),
            "fallback": "fichier",
            "ccn_type": ccn.get("ccn_type"),
        }
    return raw


def match_asset_to_public_infrastructure(asset: dict[str, Any]) -> list[dict[str, Any]]:
    """Utilise les infos NCI infra_* de localités déjà matchées ou proches."""
    matches = match_site_to_uncovered_localities(asset)
    infra_matches = []
    for m in matches:
        infra = m.get("infrastructure_type")
        if not infra:
            continue
        relation = "NEAR_HEALTH_FACILITY"
        low = str(infra).lower()
        if "école" in low or "ecole" in low or "school" in low:
            relation = "NEAR_SCHOOL"
        elif "marché" in low or "marche" in low or "market" in low:
            relation = "NEAR_MARKET"
        elif "admin" in low or "mairie" in low:
            relation = "NEAR_ADMINISTRATION"
        elif "fibre" in low or "fiber" in low:
            relation = "NEAR_FIBER"
        elif "backbone" in low:
            relation = "NEAR_BACKBONE"
        infra_matches.append(
            {
                **m,
                "relation_type": relation,
                "need_type": "essential_infrastructure",
                "need_id": f"INFRA::{m.get('need_id')}",
                "localities_impacted": 1,
                "calculation_method": "derived_from_nci_infra",
                "properties": {
                    **(m.get("properties") or {}),
                    "derived": True,
                    "infra_label": infra,
                },
            }
        )
    return infra_matches


def match_asset_to_needs(
    asset_type: str,
    asset_id: str | int,
    *,
    max_distance_km: float | None = None,
    relation_type: str | None = None,
    persist: bool = False,
) -> dict[str, Any]:
    max_m = (max_distance_km * 1000.0) if max_distance_km is not None else None
    started = time.time()
    matches: list[dict[str, Any]] = []
    mode = "db" if DATA_MODE == "db" else "fichier"
    fallback_note = None

    if asset_type in {"fdsu_site", "site", "sites"}:
        site_id = int(asset_id) if str(asset_id).isdigit() else None
        sites = list_fdsu_sites(asset_id=site_id, limit=1) if site_id else []
        if not sites and not site_id:
            # recherche par code métier
            all_sites = list_fdsu_sites(limit=5000)
            sites = [s for s in all_sites if str(s.get("site_code")) == str(asset_id)]
        if not sites:
            return {
                "_meta": {"engine": ENGINE_VERSION, "status": "not_found"},
                "asset_type": asset_type,
                "asset_id": asset_id,
                "matches": [],
            }
        asset = sites[0]
        matches = match_site_to_uncovered_localities(asset, max_distance_m=max_m)
        # WITHIN_TERRITORY synthetic if territoire known
        if asset.get("territoire"):
            for m in matches:
                if (m.get("territoire") or "").lower() == str(asset.get("territoire")).lower():
                    m.setdefault("properties", {})["within_territory"] = True
        # Candidate mission for high priority close localities
        for m in matches:
            if str(m.get("priority_level") or "").lower() in {"high", "critical"} and (m.get("distance_m") or 1e9) <= (
                max_m or _radius_for_asset("fdsu_site")
            ):
                cand = {
                    **m,
                    "relation_type": "CANDIDATE_FOR_MISSION",
                    "need_id": f"MISSION::{m.get('need_id')}",
                    "calculation_method": "priority_distance_rule",
                }
                matches.append(cand)
        impact_extra = match_asset_to_public_infrastructure(asset)
        matches.extend(impact_extra)
    elif asset_type == "ccn":
        ccns = _load_ccn_assets()
        asset = next(
            (
                c
                for c in ccns
                if str(c.get("id")) == str(asset_id) or str(c.get("business_id")) == str(asset_id)
            ),
            None,
        )
        if not asset:
            return {
                "_meta": {"engine": ENGINE_VERSION, "status": "not_found", "fallback": "fichier"},
                "asset_type": "ccn",
                "asset_id": asset_id,
                "matches": [],
            }
        matches = match_ccn_to_population(asset, max_distance_m=max_m)
        fallback_note = "CCN issu du fichier de démonstration (pas encore en PostGIS)."
        mode = "fichier"
    else:
        return {
            "_meta": {"engine": ENGINE_VERSION, "status": "unsupported_asset_type"},
            "asset_type": asset_type,
            "asset_id": asset_id,
            "matches": [],
        }

    if relation_type:
        matches = [m for m in matches if m.get("relation_type") == relation_type]

    if persist and matches and _table_ready():
        persist_matches(matches)

    impact = compute_population_impact(matches)
    return {
        "_meta": {
            "engine": ENGINE_VERSION,
            "generated_at": _now(),
            "mode": mode,
            "elapsed_ms": round((time.time() - started) * 1000, 1),
            "fallback_note": fallback_note,
            "rules_version": (get_rules().get("_meta") or {}).get("schema_version"),
        },
        "asset_type": asset_type,
        "asset_id": asset_id,
        "asset": asset if asset_type != "ccn" else asset,
        "match_count": len(matches),
        "matches": matches,
        "impact": impact,
    }


def compute_service_area(asset: dict[str, Any], asset_type: str = "fdsu_site") -> dict[str, Any]:
    radius = _radius_for_asset(asset_type)
    return {
        "center": {"latitude": asset.get("latitude"), "longitude": asset.get("longitude")},
        "service_radius_m": radius,
        "service_radius_km": round(radius / 1000.0, 2),
        "method": "configurable_buffer",
        "status": "calcule" if asset.get("latitude") is not None else "non_disponible",
        "geojson": {
            "type": "Feature",
            "properties": {"radius_m": radius, "asset_type": asset_type},
            "geometry": {
                "type": "Point",
                "coordinates": [asset.get("longitude"), asset.get("latitude")],
            },
        },
    }


def compute_population_impact(matches: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(matches)
    # Dédupliquer par need_id de base (hors préfixes relation)
    seen: set[str] = set()
    pop = 0.0
    pop_known = 0
    localities = 0
    distances: list[float] = []
    priorities: dict[str, int] = {}
    categories: dict[str, int] = {}
    infra = 0
    for m in rows:
        if m.get("relation_type") not in {"SERVES_LOCALITY", "CONNECTS_CCN", "IMPACTS_POPULATION"}:
            if m.get("relation_type", "").startswith("NEAR_"):
                infra += 1
            continue
        nid = str(m.get("need_id") or "")
        if nid in seen:
            continue
        seen.add(nid)
        localities += 1
        if m.get("distance_m") is not None:
            distances.append(float(m["distance_m"]))
        prio = str(m.get("priority_level") or "unknown")
        priorities[prio] = priorities.get(prio, 0) + 1
        cat = str(m.get("category") or "unknown")
        categories[cat] = categories.get(cat, 0) + 1
        if m.get("population_impacted") is not None:
            pop += float(m["population_impacted"])
            pop_known += 1

    dominant_priority = max(priorities.items(), key=lambda x: x[1])[0] if priorities else None
    dominant_category = max(categories.items(), key=lambda x: x[1])[0] if categories else None
    gain = _estimate_ndci_gain(localities, pop if pop_known else None)
    return {
        "population_impacted": round(pop) if pop_known else None,
        "population_status": "calcule" if pop_known else "non_disponible",
        "localities_impacted": localities,
        "essential_infrastructures": infra,
        "avg_distance_m": round(sum(distances) / len(distances), 1) if distances else None,
        "avg_distance_status": "calcule" if distances else "non_disponible",
        "dominant_priority": dominant_priority,
        "dominant_category": dominant_category,
        "priority_distribution": priorities,
        "category_distribution": categories,
        "ndci_gain_estimated": gain,
        "confidence_level": "high" if pop_known and localities else ("medium" if localities else "partial"),
    }


def compute_coverage_gain(matches: list[dict[str, Any]]) -> dict[str, Any]:
    impact = compute_population_impact(matches)
    return {
        "localities": impact["localities_impacted"],
        "population": impact["population_impacted"],
        "ndci_gain_estimated": impact["ndci_gain_estimated"],
        "status": "estime",
        "note": "Gain de couverture estimé à partir des localités NCI appariées — pas une mesure terrain.",
    }


def explain_match(match: dict[str, Any] | None = None, *, asset_id: str | int | None = None, need_id: str | None = None) -> dict[str, Any]:
    if match is None and asset_id is not None:
        payload = match_asset_to_needs("fdsu_site", asset_id)
        rows = payload.get("matches") or []
        if need_id:
            rows = [r for r in rows if str(r.get("need_id")) == str(need_id) or str(need_id) in str(r.get("need_id"))]
        match = rows[0] if rows else None
        impact = payload.get("impact")
    else:
        impact = compute_population_impact([match] if match else [])

    if not match:
        return {
            "_meta": {"engine": ENGINE_VERSION, "status": "no_match"},
            "summary": "Aucune correspondance trouvée pour cet actif / besoin.",
            "missing_data": ["match"],
            "confidence_level": "non_disponible",
        }

    missing = []
    if match.get("population_impacted") is None:
        missing.append("population")
    if match.get("priority_level") is None:
        missing.append("priorité")
    if match.get("ndci_before") is None:
        missing.append("NDCI local observé")

    props = match.get("properties") or {}
    return {
        "_meta": {
            "engine": ENGINE_VERSION,
            "compatible_with": "Decision Case File",
            "generated_at": _now(),
        },
        "question": "Pourquoi cette localité est-elle associée à cet actif ?",
        "summary": (
            f"La localité « {props.get('locality_name') or match.get('need_id')} » est associée à l'actif "
            f"« {props.get('site_name') or match.get('asset_business_id')} » car elle se trouve à "
            f"{match.get('distance_m')} m, dans le rayon de service configurable "
            f"({match.get('service_radius_m')} m), selon la règle {match.get('relation_type')}."
        ),
        "distance_m": match.get("distance_m"),
        "service_radius_m": match.get("service_radius_m"),
        "spatial_rule": match.get("relation_type"),
        "calculation_method": match.get("calculation_method"),
        "population_concerned": match.get("population_impacted"),
        "population_status": (props.get("population_status") or "non_disponible"),
        "priority_level": match.get("priority_level"),
        "category": match.get("category"),
        "sources": {
            "asset": match.get("source_asset"),
            "need": match.get("source_need"),
        },
        "missing_data": missing,
        "confidence_level": match.get("confidence_level"),
        "impact": impact,
        "match": match,
    }


def persist_matches(matches: list[dict[str, Any]]) -> int:
    if not matches:
        return 0
    ensure_schema()
    if not _table_ready():
        return 0
    sql = """
        INSERT INTO analysis.asset_need_matches (
            asset_type, asset_id, asset_business_id, need_type, need_id, relation_type,
            distance_m, service_radius_m, population_impacted, localities_impacted,
            infrastructure_type, priority_level, category, ndci_before, ndci_after_estimated,
            confidence_level, source_asset, source_need, calculation_method, calculated_at,
            province, territoire, program_code, properties, geom_link
        ) VALUES (
            %(asset_type)s, %(asset_id)s, %(asset_business_id)s, %(need_type)s, %(need_id)s, %(relation_type)s,
            %(distance_m)s, %(service_radius_m)s, %(population_impacted)s, %(localities_impacted)s,
            %(infrastructure_type)s, %(priority_level)s, %(category)s, %(ndci_before)s, %(ndci_after_estimated)s,
            %(confidence_level)s, %(source_asset)s, %(source_need)s, %(calculation_method)s, NOW(),
            %(province)s, %(territoire)s, %(program_code)s, %(properties)s,
            CASE
                WHEN %(asset_lon)s IS NOT NULL AND %(need_lon)s IS NOT NULL THEN
                    ST_SetSRID(ST_MakeLine(
                        ST_MakePoint(%(asset_lon)s, %(asset_lat)s),
                        ST_MakePoint(%(need_lon)s, %(need_lat)s)
                    ), 4326)
                ELSE NULL
            END
        )
        ON CONFLICT (asset_type, asset_business_id, need_type, need_id, relation_type)
        DO UPDATE SET
            distance_m = EXCLUDED.distance_m,
            service_radius_m = EXCLUDED.service_radius_m,
            population_impacted = EXCLUDED.population_impacted,
            localities_impacted = EXCLUDED.localities_impacted,
            infrastructure_type = EXCLUDED.infrastructure_type,
            priority_level = EXCLUDED.priority_level,
            category = EXCLUDED.category,
            ndci_after_estimated = EXCLUDED.ndci_after_estimated,
            confidence_level = EXCLUDED.confidence_level,
            calculation_method = EXCLUDED.calculation_method,
            calculated_at = NOW(),
            province = EXCLUDED.province,
            territoire = EXCLUDED.territoire,
            program_code = EXCLUDED.program_code,
            properties = EXCLUDED.properties,
            geom_link = EXCLUDED.geom_link
    """
    rows = []
    for m in matches:
        props = dict(m.get("properties") or {})
        raw_asset_id = m.get("asset_id")
        asset_id_int = None
        if raw_asset_id is not None and str(raw_asset_id).isdigit():
            asset_id_int = int(raw_asset_id)
        rows.append(
            {
                "asset_type": m.get("asset_type"),
                "asset_id": asset_id_int,
                "asset_business_id": m.get("asset_business_id") or str(raw_asset_id or ""),
                "need_type": m.get("need_type"),
                "need_id": str(m.get("need_id")),
                "relation_type": m.get("relation_type"),
                "distance_m": m.get("distance_m"),
                "service_radius_m": m.get("service_radius_m"),
                "population_impacted": m.get("population_impacted"),
                "localities_impacted": m.get("localities_impacted") or 1,
                "infrastructure_type": m.get("infrastructure_type"),
                "priority_level": m.get("priority_level"),
                "category": m.get("category"),
                "ndci_before": m.get("ndci_before"),
                "ndci_after_estimated": m.get("ndci_after_estimated"),
                "confidence_level": m.get("confidence_level") or "partial",
                "source_asset": m.get("source_asset"),
                "source_need": m.get("source_need"),
                "calculation_method": m.get("calculation_method"),
                "province": m.get("province"),
                "territoire": m.get("territoire"),
                "program_code": m.get("program_code"),
                "properties": Json(props),
                "asset_lat": props.get("asset_lat"),
                "asset_lon": props.get("asset_lon"),
                "need_lat": props.get("need_lat"),
                "need_lon": props.get("need_lon"),
            }
        )
    with connect_db() as conn:
        with conn.cursor() as cur:
            execute_batch(cur, sql, rows, page_size=200)
        conn.commit()
    _CACHE["stats"] = None
    return len(rows)


def refresh_matches(
    *,
    program_code: str | None = None,
    province: str | None = None,
    territoire: str | None = None,
    asset_id: int | None = None,
    include_ccn: bool = True,
    persist: bool = True,
    limit_assets: int | None = None,
) -> dict[str, Any]:
    """Recalcul ciblé (pas tout le pays sauf demande explicite)."""
    started = time.time()
    ensure_schema()
    rules = get_rules()
    limit = int(limit_assets or (rules.get("matching") or {}).get("batch_site_limit_default") or 500)

    sites = list_fdsu_sites(
        program_code=program_code,
        province=province,
        territoire=territoire,
        asset_id=asset_id,
        limit=limit,
    )
    # Précharge localités filtrées
    localities = _uncovered_localities(province=province, territoire=territoire, coords_only=True)
    if not localities and not territoire and not province:
        localities = _uncovered_localities(coords_only=True)

    all_matches: list[dict[str, Any]] = []
    for site in sites:
        # Préférer localités du même territoire si dispo
        local_pool = [
            loc
            for loc in localities
            if not site.get("territoire")
            or str(loc.get("territoire") or "").lower() == str(site.get("territoire") or "").lower()
            or str(loc.get("province") or "").lower() == str(site.get("province") or "").lower()
        ]
        if len(local_pool) < 3:
            local_pool = localities
        rows = match_site_to_uncovered_localities(site, local_pool)
        # IMPACTS_POPULATION agrégé
        impact = compute_population_impact(rows)
        if impact["localities_impacted"]:
            rows.append(
                {
                    "asset_type": "fdsu_site",
                    "asset_id": site.get("id"),
                    "asset_business_id": site.get("site_code") or str(site.get("id")),
                    "need_type": "population",
                    "need_id": f"POP::{site.get('site_code') or site.get('id')}",
                    "relation_type": "IMPACTS_POPULATION",
                    "distance_m": impact.get("avg_distance_m"),
                    "service_radius_m": _radius_for_asset("fdsu_site"),
                    "population_impacted": impact.get("population_impacted"),
                    "localities_impacted": impact.get("localities_impacted"),
                    "infrastructure_type": None,
                    "priority_level": impact.get("dominant_priority"),
                    "category": impact.get("dominant_category"),
                    "ndci_before": None,
                    "ndci_after_estimated": (impact.get("ndci_gain_estimated") or {}).get("value"),
                    "confidence_level": impact.get("confidence_level"),
                    "source_asset": "programs.fdsu_sites",
                    "source_need": "NCI population agrégée",
                    "calculation_method": "aggregate_serves_locality",
                    "province": site.get("province"),
                    "territoire": site.get("territoire"),
                    "program_code": site.get("program_code"),
                    "properties": {"aggregate": True, "population_status": impact.get("population_status")},
                }
            )
        all_matches.extend(rows)

    ccn_count = 0
    if include_ccn and asset_id is None:
        for ccn in _load_ccn_assets():
            if province and str(ccn.get("province") or "").lower() != province.lower():
                continue
            if territoire and str(ccn.get("territoire") or "").lower() != territoire.lower():
                continue
            all_matches.extend(match_ccn_to_population(ccn, localities))
            ccn_count += 1

    written = persist_matches(all_matches) if persist and all_matches else 0
    scope = program_code or province or territoire or (f"asset:{asset_id}" if asset_id else "national_sample")
    run = {
        "run_scope": scope,
        "status": "ok",
        "assets_processed": len(sites) + ccn_count,
        "matches_written": written,
        "mode": "db" if DATA_MODE == "db" else "fichier",
        "message": f"NSME refresh — {len(sites)} sites, {ccn_count} CCN, {written} matches",
        "details": {
            "program_code": program_code,
            "province": province,
            "territoire": territoire,
            "localities_pool": len(localities),
            "elapsed_ms": round((time.time() - started) * 1000, 1),
            "engine": ENGINE_VERSION,
        },
    }
    _log_run(run)
    _CACHE["stats"] = None
    return {
        "_meta": {"engine": ENGINE_VERSION, "generated_at": _now()},
        **run,
        "sample_impact": compute_population_impact(
            [m for m in all_matches if m.get("relation_type") == "SERVES_LOCALITY"][:500]
        ),
    }


def _log_run(run: dict[str, Any]) -> None:
    if not _table_ready():
        return
    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO analysis.matching_runs
                    (run_scope, status, finished_at, assets_processed, matches_written, mode, message, details)
                    VALUES (%s, %s, NOW(), %s, %s, %s, %s, %s)
                    """,
                    (
                        run.get("run_scope"),
                        run.get("status"),
                        run.get("assets_processed"),
                        run.get("matches_written"),
                        run.get("mode"),
                        run.get("message"),
                        Json(run.get("details") or {}),
                    ),
                )
            conn.commit()
    except Exception:  # noqa: BLE001
        return


def _query_matches(
    *,
    asset_type: str | None = None,
    asset_id: str | int | None = None,
    need_id: str | None = None,
    relation_type: str | None = None,
    program_code: str | None = None,
    province: str | None = None,
    territoire: str | None = None,
    priority_level: str | None = None,
    category: str | None = None,
    max_distance_m: float | None = None,
    limit: int = 200,
    offset: int = 0,
) -> list[dict[str, Any]]:
    if not _table_ready():
        return []
    clauses = ["1=1"]
    params: list[Any] = []
    if asset_type:
        clauses.append("asset_type = %s")
        params.append(asset_type)
    if asset_id is not None:
        if str(asset_id).isdigit():
            clauses.append("(asset_id = %s OR asset_business_id = %s)")
            params.extend([int(asset_id), str(asset_id)])
        else:
            clauses.append("asset_business_id = %s")
            params.append(str(asset_id))
    if need_id:
        clauses.append("need_id = %s")
        params.append(str(need_id))
    if relation_type:
        clauses.append("relation_type = %s")
        params.append(relation_type)
    if program_code:
        clauses.append("program_code = %s")
        params.append(program_code)
    if province:
        clauses.append("LOWER(province) = LOWER(%s)")
        params.append(province)
    if territoire:
        clauses.append("LOWER(territoire) = LOWER(%s)")
        params.append(territoire)
    if priority_level:
        clauses.append("LOWER(priority_level) = LOWER(%s)")
        params.append(priority_level)
    if category:
        clauses.append("LOWER(category) = LOWER(%s)")
        params.append(category)
    if max_distance_m is not None:
        clauses.append("distance_m <= %s")
        params.append(max_distance_m)
    params.extend([limit, offset])
    sql = f"""
        SELECT * FROM analysis.asset_need_matches
        WHERE {' AND '.join(clauses)}
        ORDER BY distance_m NULLS LAST, calculated_at DESC
        LIMIT %s OFFSET %s
    """
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = []
            for row in cur.fetchall():
                item = dict(row)
                if item.get("calculated_at") and hasattr(item["calculated_at"], "isoformat"):
                    item["calculated_at"] = item["calculated_at"].isoformat()
                rows.append(item)
            return rows


def get_asset_needs(asset_id: str | int, **filters: Any) -> dict[str, Any]:
    asset_type = filters.pop("asset_type", None) or "fdsu_site"
    max_km = filters.pop("max_distance_km", None)
    max_m = float(max_km) * 1000 if max_km is not None else None
    stored = _query_matches(asset_type=asset_type, asset_id=asset_id, max_distance_m=max_m, **{
        k: v for k, v in filters.items() if k in {
            "relation_type", "program_code", "province", "territoire", "priority_level", "category", "limit", "offset"
        }
    })
    if stored:
        impact = compute_population_impact(stored)
        return {
            "_meta": {"engine": ENGINE_VERSION, "source": "analysis.asset_need_matches", "generated_at": _now()},
            "asset_id": asset_id,
            "asset_type": asset_type,
            "match_count": len(stored),
            "matches": stored,
            "impact": impact,
        }
    # Calcul à la volée si pas encore persisté
    return match_asset_to_needs(asset_type, asset_id, max_distance_km=max_km, relation_type=filters.get("relation_type"))


def get_need_assets(need_id: str, **filters: Any) -> dict[str, Any]:
    stored = _query_matches(need_id=need_id, **{
        k: v for k, v in filters.items() if k in {
            "asset_type", "relation_type", "program_code", "province", "territoire", "priority_level", "limit", "offset"
        }
    })
    if stored:
        return {
            "_meta": {"engine": ENGINE_VERSION, "source": "analysis.asset_need_matches", "generated_at": _now()},
            "need_id": need_id,
            "match_count": len(stored),
            "matches": stored,
        }
    # Recherche inverse à la volée (échantillon sites programme 40/300)
    sites = list_fdsu_sites(limit=int((get_rules().get("matching") or {}).get("batch_site_limit_default") or 340))
    locs = [loc for loc in _uncovered_localities(coords_only=True) if str(loc.get("id")) == str(need_id)]
    if not locs:
        return {"_meta": {"engine": ENGINE_VERSION, "status": "need_not_found"}, "need_id": need_id, "matches": []}
    matches = []
    for site in sites:
        rows = match_site_to_uncovered_localities(site, locs)
        matches.extend(rows)
    return {
        "_meta": {"engine": ENGINE_VERSION, "source": "on_the_fly", "generated_at": _now()},
        "need_id": need_id,
        "match_count": len(matches),
        "matches": matches,
    }


def get_asset_impact(asset_id: str | int, **filters: Any) -> dict[str, Any]:
    payload = get_asset_needs(asset_id, **filters)
    area = None
    asset = payload.get("asset")
    if not asset and DATA_MODE == "db":
        sites = list_fdsu_sites(asset_id=int(asset_id) if str(asset_id).isdigit() else None, limit=1)
        if not sites and not str(asset_id).isdigit():
            sites = [s for s in list_fdsu_sites(limit=5000) if s.get("site_code") == str(asset_id)]
        asset = sites[0] if sites else None
    if asset:
        area = compute_service_area(asset, payload.get("asset_type") or "fdsu_site")
    return {
        "_meta": {"engine": ENGINE_VERSION, "generated_at": _now()},
        "asset_id": asset_id,
        "impact": payload.get("impact") or compute_population_impact(payload.get("matches") or []),
        "coverage_gain": compute_coverage_gain(payload.get("matches") or []),
        "service_area": area,
        "match_count": payload.get("match_count") or len(payload.get("matches") or []),
    }


def get_territory_matches(territory_id: str, **filters: Any) -> dict[str, Any]:
    """territory_id peut être un nom de territoire ou un code master."""
    territoire = filters.pop("territoire", None) or territory_id
    compute_if_empty = bool(filters.pop("compute_if_empty", True))
    # Si format TERRITOIRE-xx-yyy, résoudre via master si possible
    name = territoire
    try:
        from api.services import master_registry_service

        entities = master_registry_service.list_entities(entity_type="TERRITOIRE", limit=5000).get("entities") or []
        hit = next((e for e in entities if str(e.get("id")) == str(territory_id) or str(e.get("business_id")) == str(territory_id)), None)
        if hit:
            name = hit.get("name") or hit.get("label") or name
    except Exception:  # noqa: BLE001
        pass

    stored = _query_matches(territoire=name, limit=filters.get("limit", 500), offset=filters.get("offset", 0))
    if not stored and compute_if_empty:
        # Calcul léger à la volée (sans persister tout le territoire à chaque lecture TI)
        sites = list_fdsu_sites(territoire=name, limit=50)
        localities = _uncovered_localities(territoire=name, coords_only=True)
        live: list[dict[str, Any]] = []
        for site in sites:
            live.extend(match_site_to_uncovered_localities(site, localities or None))
        stored = live

    assets = {}
    needs = set()
    for m in stored:
        key = m.get("asset_business_id") or m.get("asset_id")
        assets[key] = m
        if m.get("relation_type") == "SERVES_LOCALITY":
            needs.add(m.get("need_id"))

    coverage = nci.get_territory_coverage(name) if hasattr(nci, "get_territory_coverage") else None
    if coverage is None:
        # fallback list aggregates
        agg = nci.get_aggregates() or {}
        territories = (agg.get("territories") or agg.get("by_territory") or [])
        if isinstance(territories, dict):
            coverage = territories.get(name)
        elif isinstance(territories, list):
            coverage = next((t for t in territories if str(t.get("territoire") or t.get("name") or "").lower() == name.lower()), None)

    impact = compute_population_impact(stored)
    pop_remaining = None
    if isinstance(coverage, dict):
        pop_remaining = coverage.get("population_uncovered") or coverage.get("population_remaining")

    unmatched_needs = None
    if isinstance(coverage, dict) and coverage.get("localities_uncovered") is not None:
        try:
            unmatched_needs = max(0, int(coverage["localities_uncovered"]) - len(needs))
        except (TypeError, ValueError):
            unmatched_needs = None

    return {
        "_meta": {"engine": ENGINE_VERSION, "generated_at": _now(), "territory_resolved": name},
        "territory_id": territory_id,
        "territoire": name,
        "assets_present": len(assets),
        "needs_matched": len(needs),
        "population_impacted_by_assets": impact.get("population_impacted"),
        "population_remaining": pop_remaining,
        "population_remaining_status": "calcule" if pop_remaining is not None else "non_disponible",
        "zones_without_matching_asset": unmatched_needs,
        "match_quality": impact.get("confidence_level"),
        "investment_opportunities": [
            {
                "type": "unmatched_needs",
                "value": unmatched_needs,
                "status": "estime" if unmatched_needs is not None else "non_disponible",
            }
        ],
        "impact": impact,
        "matches": stored,
        "coverage": coverage,
    }


def quality_report() -> dict[str, Any]:
    stats = get_statistics()
    issues = {
        "asset_without_need": stats.get("assets_without_match"),
        "need_without_asset": stats.get("needs_without_match_estimate"),
        "excessive_overlap": stats.get("needs_with_excessive_overlap"),
        "multi_asset_locality": stats.get("multi_asset_needs"),
        "aberrant_distance": stats.get("aberrant_distance_count"),
        "missing_identifier": stats.get("missing_identifier_count"),
    }
    return {
        "_meta": {"engine": ENGINE_VERSION, "generated_at": _now()},
        "checks": get_rules().get("quality_checks") or [],
        "issues": issues,
        "statistics": stats,
    }


def get_statistics() -> dict[str, Any]:
    if _CACHE.get("stats") and (time.time() - float(_CACHE.get("stats_at") or 0)) < 30:
        return _CACHE["stats"]

    base = {
        "_meta": {"engine": ENGINE_VERSION, "generated_at": _now(), "mode": DATA_MODE},
        "table_ready": _table_ready(),
        "rules_version": (get_rules().get("_meta") or {}).get("schema_version"),
        "service_radii_m": (get_rules().get("service_radii_m") or {}),
    }
    if not _table_ready():
        base.update(
            {
                "matches_total": 0,
                "note": "Table analysis.asset_need_matches absente — lancer POST /api/spatial-matching/refresh",
            }
        )
        return base

    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT COUNT(*) AS n FROM analysis.asset_need_matches")
            total = int(cur.fetchone()["n"])
            cur.execute(
                """
                SELECT relation_type, COUNT(*) AS n
                FROM analysis.asset_need_matches
                GROUP BY relation_type ORDER BY n DESC
                """
            )
            by_rel = {r["relation_type"]: int(r["n"]) for r in cur.fetchall()}
            cur.execute(
                """
                SELECT COALESCE(SUM(population_impacted),0) AS pop,
                       AVG(distance_m) AS avg_dist,
                       COUNT(DISTINCT asset_business_id) AS assets,
                       COUNT(DISTINCT need_id) FILTER (WHERE relation_type = 'SERVES_LOCALITY') AS needs
                FROM analysis.asset_need_matches
                WHERE relation_type IN ('SERVES_LOCALITY','IMPACTS_POPULATION','CONNECTS_CCN')
                """
            )
            agg = dict(cur.fetchone() or {})
            cur.execute(
                """
                SELECT asset_business_id, asset_type, program_code,
                       SUM(COALESCE(population_impacted,0)) FILTER (WHERE relation_type='SERVES_LOCALITY') AS pop,
                       COUNT(*) FILTER (WHERE relation_type='SERVES_LOCALITY') AS locs
                FROM analysis.asset_need_matches
                GROUP BY asset_business_id, asset_type, program_code
                ORDER BY pop DESC NULLS LAST
                LIMIT 10
                """
            )
            top_assets = [dict(r) for r in cur.fetchall()]
            cur.execute(
                """
                SELECT territoire, COUNT(DISTINCT need_id) AS needs,
                       COUNT(DISTINCT asset_business_id) AS assets
                FROM analysis.asset_need_matches
                WHERE territoire IS NOT NULL
                GROUP BY territoire
                ORDER BY needs DESC
                LIMIT 10
                """
            )
            top_territories = [dict(r) for r in cur.fetchall()]
            threshold = int((get_rules().get("excessive_overlap_threshold") or 8))
            aberrant = float(get_rules().get("aberrant_distance_m") or 100000)
            cur.execute(
                """
                SELECT COUNT(*) AS n FROM (
                  SELECT need_id FROM analysis.asset_need_matches
                  WHERE relation_type='SERVES_LOCALITY'
                  GROUP BY need_id HAVING COUNT(DISTINCT asset_business_id) >= %s
                ) t
                """,
                (threshold,),
            )
            excessive = int(cur.fetchone()["n"])
            cur.execute(
                """
                SELECT COUNT(*) AS n FROM (
                  SELECT need_id FROM analysis.asset_need_matches
                  WHERE relation_type='SERVES_LOCALITY'
                  GROUP BY need_id HAVING COUNT(DISTINCT asset_business_id) > 1
                ) t
                """
            )
            multi = int(cur.fetchone()["n"])
            cur.execute(
                "SELECT COUNT(*) AS n FROM analysis.asset_need_matches WHERE distance_m > %s",
                (aberrant,),
            )
            aberrant_n = int(cur.fetchone()["n"])
            cur.execute(
                """
                SELECT COUNT(*) AS n FROM analysis.asset_need_matches
                WHERE asset_business_id IS NULL OR need_id IS NULL OR need_id = ''
                """
            )
            missing_id = int(cur.fetchone()["n"])

    nci_stats = nci.statistics() if hasattr(nci, "statistics") else {}
    nci_kpis = (nci_stats or {}).get("kpis") or {}
    needs_total = nci_kpis.get("localities_uncovered")
    needs_matched = int(agg.get("needs") or 0)
    needs_without = None
    if needs_total is not None:
        try:
            needs_without = max(0, int(needs_total) - needs_matched)
        except (TypeError, ValueError):
            needs_without = None

    base.update(
        {
            "matches_total": total,
            "by_relation_type": by_rel,
            "population_impacted_sum": float(agg.get("pop") or 0),
            "avg_distance_m": float(agg["avg_dist"]) if agg.get("avg_dist") is not None else None,
            "assets_matched": int(agg.get("assets") or 0),
            "needs_matched": needs_matched,
            "needs_without_match_estimate": needs_without,
            "assets_without_match": None,
            "needs_with_excessive_overlap": excessive,
            "multi_asset_needs": multi,
            "aberrant_distance_count": aberrant_n,
            "missing_identifier_count": missing_id,
            "top_assets_by_impact": top_assets,
            "top_territories": top_territories,
            "nci_population_uncovered": nci_kpis.get("population_uncovered"),
            "nci_population_covered": nci_kpis.get("population_covered"),
        }
    )
    _CACHE["stats"] = base
    _CACHE["stats_at"] = time.time()
    return base


def map_payload(
    *,
    asset_id: str | int | None = None,
    territoire: str | None = None,
    limit: int = 500,
) -> dict[str, Any]:
    """GeoJSON : actif, localités liées, lignes, cercle d'influence (centre + radius property)."""
    if asset_id is not None:
        payload = get_asset_needs(asset_id, limit=limit)
        matches = [m for m in (payload.get("matches") or []) if m.get("relation_type") == "SERVES_LOCALITY"]
        asset = payload.get("asset")
        if not asset and str(asset_id).isdigit():
            sites = list_fdsu_sites(asset_id=int(asset_id), limit=1)
            asset = sites[0] if sites else None
    else:
        matches = _query_matches(territoire=territoire, relation_type="SERVES_LOCALITY", limit=limit)
        asset = None

    features = []
    if asset and asset.get("longitude") is not None:
        impact = compute_population_impact(matches)
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [asset["longitude"], asset["latitude"]]},
                "properties": {
                    "kind": "asset",
                    "code": asset.get("site_code"),
                    "type": "fdsu_site",
                    "programme": asset.get("program_code"),
                    "name": asset.get("site_name"),
                    "impact_total_population": impact.get("population_impacted"),
                    "localities_impacted": impact.get("localities_impacted"),
                    "service_radius_m": _radius_for_asset("fdsu_site"),
                },
            }
        )

    for m in matches:
        props = m.get("properties") or {}
        lon = props.get("need_lon")
        lat = props.get("need_lat")
        if lon is None or lat is None:
            continue
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {
                    "kind": "linked_locality",
                    "name": props.get("locality_name") or m.get("need_id"),
                    "population": m.get("population_impacted"),
                    "priority": m.get("priority_level"),
                    "distance_m": m.get("distance_m"),
                    "category": m.get("category"),
                    "relation_type": m.get("relation_type"),
                    "need_id": m.get("need_id"),
                    "asset_business_id": m.get("asset_business_id"),
                },
            }
        )
        a_lon, a_lat = props.get("asset_lon"), props.get("asset_lat")
        if a_lon is not None and a_lat is not None:
            features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[a_lon, a_lat], [lon, lat]],
                    },
                    "properties": {
                        "kind": "link",
                        "distance_m": m.get("distance_m"),
                        "relation_type": m.get("relation_type"),
                    },
                }
            )

    return {
        "type": "FeatureCollection",
        "features": features,
        "_meta": {
            "engine": ENGINE_VERSION,
            "count": len(features),
            "generated_at": _now(),
            "layer": "Correspondance Actifs ↔ Besoins",
        },
    }


def edvs_charts() -> dict[str, Any]:
    stats = get_statistics()
    top = stats.get("top_assets_by_impact") or []
    terr = stats.get("top_territories") or []
    calculated_at = stats.get("_meta", {}).get("generated_at")
    return {
        "_meta": {
            "engine": ENGINE_VERSION,
            "source": "analysis.asset_need_matches + NCI",
            "quality": "partiel" if not stats.get("table_ready") else "calcule",
            "calculated_at": calculated_at,
        },
        "population_covered_by_assets": {
            "label": "Population potentiellement impactée par actifs FDSU",
            "value": stats.get("population_impacted_sum"),
            "unit": "habitants",
            "source": "NSME × NCI",
            "quality": "estime",
            "calculated_at": calculated_at,
        },
        "population_without_matching_asset": {
            "label": "Population restante sans actif correspondant (proxy NCI)",
            "value": stats.get("nci_population_uncovered"),
            "unit": "habitants",
            "source": "NCI",
            "quality": "calcule" if stats.get("nci_population_uncovered") is not None else "non_disponible",
            "calculated_at": calculated_at,
        },
        "top_assets_by_impact": {
            "type": "bar",
            "unit": "habitants",
            "source": "NSME",
            "quality": "estime",
            "calculated_at": calculated_at,
            "items": [
                {
                    "label": r.get("asset_business_id"),
                    "value": float(r.get("pop") or 0),
                    "program": r.get("program_code"),
                }
                for r in top
            ],
        },
        "top_unmatched_territories_proxy": {
            "type": "bar",
            "unit": "besoins appariés",
            "source": "NSME",
            "quality": "calcule",
            "calculated_at": calculated_at,
            "items": [
                {"label": r.get("territoire"), "value": int(r.get("needs") or 0), "assets": int(r.get("assets") or 0)}
                for r in terr
            ],
        },
        "avg_distance_asset_need": {
            "label": "Distance moyenne actif–besoin",
            "value": stats.get("avg_distance_m"),
            "unit": "mètres",
            "source": "NSME",
            "quality": "calcule" if stats.get("avg_distance_m") is not None else "non_disponible",
            "calculated_at": calculated_at,
        },
        "by_relation_type": stats.get("by_relation_type") or {},
        "ndci_gain_potential_note": {
            "label": "Gain NDCI potentiel",
            "value": None,
            "unit": "points",
            "source": "NSME impact estimé",
            "quality": "estime",
            "note": "Disponible au niveau actif via /impact",
            "calculated_at": calculated_at,
        },
    }


def demo_cases() -> dict[str, Any]:
    """Trois cas réels à partir des données — aucun résultat fabriqué."""
    stats = get_statistics()
    top = stats.get("top_assets_by_impact") or []
    cases = []

    # Fort / faible impact depuis agrégats persistés (rapide)
    if top:
        best = top[0]
        code = best.get("asset_business_id")
        cases.append(
            {
                "id": "high_impact_site",
                "title": "Site à fort impact potentiel",
                "asset_business_id": code,
                "program_code": best.get("program_code"),
                "data_used": ["programs.fdsu_sites", "localities_uncovered.jsonl", "analysis.asset_need_matches"],
                "impact": {
                    "population_impacted": float(best.get("pop") or 0) or None,
                    "localities_impacted": int(best.get("locs") or 0) or None,
                    "population_status": "calcule" if best.get("pop") is not None else "non_disponible",
                    "source": "analysis.asset_need_matches",
                },
            }
        )
        weak = top[-1]
        if weak.get("asset_business_id") != code:
            cases.append(
                {
                    "id": "low_impact_site",
                    "title": "Site à impact plus faible (dans l'échantillon calculé)",
                    "asset_business_id": weak.get("asset_business_id"),
                    "program_code": weak.get("program_code"),
                    "data_used": ["programs.fdsu_sites", "localities_uncovered.jsonl", "analysis.asset_need_matches"],
                    "impact": {
                        "population_impacted": float(weak.get("pop") or 0) or None,
                        "localities_impacted": int(weak.get("locs") or 0) or None,
                        "population_status": "calcule" if weak.get("pop") is not None else "non_disponible",
                        "source": "analysis.asset_need_matches",
                    },
                }
            )

    terr = (stats.get("top_territories") or [None])[0]
    if terr:
        tname = terr.get("territoire")
        cases.append(
            {
                "id": "territory_unmatched_proxy",
                "title": "Territoire avec besoins (appariements / restes)",
                "territoire": tname,
                "data_used": ["NCI aggregates", "analysis.asset_need_matches"],
                "summary": {
                    "assets_present": terr.get("assets"),
                    "needs_matched": terr.get("needs"),
                    "note": "Détail restes via GET /territories/{id}/matches après refresh",
                },
            }
        )

    if len(cases) < 3:
        sites = list_fdsu_sites(program_code="PROG_SITES_40", limit=1)
        if sites:
            site = sites[0]
            # Matching restreint : localités du territoire uniquement (évite scan national)
            locs = _uncovered_localities(territoire=site.get("territoire"), coords_only=True)[:500]
            live_matches = match_site_to_uncovered_localities(site, locs)
            cases.append(
                {
                    "id": "live_sites40_example",
                    "title": "Exemple Sites 40 calculé à la volée (territoire filtré)",
                    "asset_id": site["id"],
                    "asset_business_id": site.get("site_code"),
                    "territoire": site.get("territoire"),
                    "data_used": ["programs.fdsu_sites", "localities_uncovered.jsonl"],
                    "match_count": len(live_matches),
                    "impact": compute_population_impact(live_matches),
                }
            )

    return {
        "_meta": {
            "engine": ENGINE_VERSION,
            "generated_at": _now(),
            "note": "Cas dérivés des données disponibles — aucun chiffre inventé.",
        },
        "cases": cases[:3],
    }
