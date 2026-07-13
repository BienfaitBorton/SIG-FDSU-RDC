"""Territorial Intelligence Explorer v1 — consolidation de connaissance territoriale.

Répond à : « Que sait le FDSU d’un territoire, quels besoins numériques,
quelles interventions prioriser ? »

Ne duplique pas les sources : consolide Référentiel National, Knowledge Hub,
programmes, santé, télécom, CCN, priorisation et Explainable Decision Engine.
N’invente aucune valeur — statut explicite si indisponible.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from psycopg2.extras import RealDictCursor

from api.config import DATA_MODE, connect_db

PROJECT_ROOT = Path(__file__).resolve().parents[2]
NOMENCLATURE_PATH = PROJECT_ROOT / "data" / "reports" / "fdsu_nomenclature.json"
HIERARCHY_PATH = PROJECT_ROOT / "data" / "reports" / "territory_hierarchy" / "territoires_hierarchie_kmz.report.json"
PROGRAMS_DIR = PROJECT_ROOT / "data" / "programs"

ENGINE_VERSION = "territorial-intelligence-1.0.0"
DEMO_FOCUS_NAME = "DUNGU"  # cas de démo UI uniquement — pas de logique métier dédiée

STATUS_CONFIRMED = "confirmed"
STATUS_ESTIMATED = "estimated"
STATUS_PARTIAL = "partial"
STATUS_UNAVAILABLE = "unavailable"
STATUS_NOT_SOURCED = "not_sourced"
STATUS_DEMONSTRATION = "demonstration"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def field(
    value: Any,
    status: str,
    *,
    source: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    return {
        "value": value,
        "status": status,
        "source": source,
        "note": note,
        "available": status
        in {
            STATUS_CONFIRMED,
            STATUS_ESTIMATED,
            STATUS_PARTIAL,
            STATUS_DEMONSTRATION,
            "operational",
            "partial",
            "estimated",
            "confirmed",
            "demonstration",
        }
        and value is not None,
    }


def unavailable(note: str = "Non disponible dans les sources actuelles", source: str | None = None) -> dict[str, Any]:
    return field(None, STATUS_UNAVAILABLE, source=source, note=note)


def not_sourced(note: str = "Non sourcé", source: str | None = None) -> dict[str, Any]:
    return field(None, STATUS_NOT_SOURCED, source=source, note=note)


def _norm(text: str | None) -> str:
    return " ".join(str(text or "").strip().upper().replace("-", " ").split())


def _names_match(a: str | None, b: str | None) -> bool:
    na, nb = _norm(a), _norm(b)
    return bool(na and nb and (na == nb or na in nb or nb in na))


def _nomenclature_territories() -> list[dict[str, Any]]:
    payload = _load_json(NOMENCLATURE_PATH)
    return list(payload.get("territoires") or payload.get("territories") or [])


def _master_territories() -> list[dict[str, Any]]:
    from api.services import master_registry_service

    result = master_registry_service.list_entities(entity_type="TERRITOIRE", limit=5000)
    return list(result.get("entities") or [])


def _resolve_territory_ref(territory_id: str) -> dict[str, Any] | None:
    needle = str(territory_id or "").strip()
    if not needle:
        return None

    for entity in _master_territories():
        attrs = entity.get("attributes") or {}
        candidates = {
            str(entity.get("business_id") or ""),
            str(entity.get("uuid") or ""),
            str(entity.get("name") or ""),
            f"{attrs.get('province_code')}-{attrs.get('territoire_code')}",
            str(attrs.get("territoire_code") or ""),
        }
        if needle in candidates or _names_match(needle, entity.get("name")):
            return {
                "territory_id": entity.get("business_id"),
                "territory_name": entity.get("name"),
                "province": attrs.get("province_name"),
                "province_code": attrs.get("province_code"),
                "administrative_code": attrs.get("territoire_code"),
                "fdsu_zone": attrs.get("zone_fdsu"),
                "nb_sites_reference": attrs.get("nb_sites_reference"),
                "source": "master_registry",
                "master": entity,
            }

    for item in _nomenclature_territories():
        name = item.get("nom") or item.get("name")
        code = str(item.get("territoire_code") or item.get("code") or "")
        prov_code = str(item.get("province_code") or "")
        business_id = f"TERRITOIRE-{prov_code}-{code}" if prov_code and code else None
        if (
            needle == business_id
            or needle == code
            or needle == f"{prov_code}-{code}"
            or _names_match(needle, name)
        ):
            return {
                "territory_id": business_id or code or name,
                "territory_name": name,
                "province": item.get("province"),
                "province_code": prov_code,
                "administrative_code": code,
                "fdsu_zone": item.get("zone_fdsu"),
                "nb_sites_reference": item.get("nb_sites_reference"),
                "source": "fdsu_nomenclature",
                "nomenclature": item,
            }
    return None


def list_territories(
    *,
    province: str | None = None,
    zone: str | None = None,
    priority_level: str | None = None,
    data_quality: str | None = None,
    q: str | None = None,
    limit: int = 500,
) -> dict[str, Any]:
    items = []
    for entity in _master_territories():
        attrs = entity.get("attributes") or {}
        row = {
            "territory_id": entity.get("business_id"),
            "territory_name": entity.get("name"),
            "province": attrs.get("province_name"),
            "province_code": attrs.get("province_code"),
            "administrative_code": attrs.get("territoire_code"),
            "fdsu_zone": attrs.get("zone_fdsu"),
            "nb_sites_reference": attrs.get("nb_sites_reference"),
            "confidence_level": entity.get("confidence_level"),
            "data_quality": "partial",
            "is_demo_focus": _norm(entity.get("name")) == DEMO_FOCUS_NAME,
        }
        if province and not _names_match(province, row["province"]):
            continue
        if zone and str(row.get("fdsu_zone") or "").upper() != zone.upper():
            continue
        if q and q.lower() not in f"{row['territory_name']} {row['province']} {row['territory_id']}".lower():
            continue
        if data_quality and row["data_quality"] != data_quality:
            continue
        items.append(row)

    # priority_level filter applied after light scoring if requested
    if priority_level:
        filtered = []
        for item in items:
            profile = build_territorial_profile(item["territory_id"], light=True)
            level = ((profile or {}).get("priority") or {}).get("level", {}).get("value")
            if level == priority_level:
                filtered.append(item)
        items = filtered

    items.sort(key=lambda r: (str(r.get("province") or ""), str(r.get("territory_name") or "")))
    page = items[:limit]
    return {
        "_meta": {
            "title": "Territoires — Territorial Intelligence Explorer",
            "count": len(page),
            "total": len(items),
            "engine_version": ENGINE_VERSION,
            "demo_focus": DEMO_FOCUS_NAME,
            "note": "Liste issue du Référentiel National (TERRITOIRE). Aucune valeur inventée.",
        },
        "territories": page,
    }


def _program_sites(program_code: str, territory_name: str) -> list[dict[str, Any]]:
    path = PROGRAMS_DIR / program_code / f"{program_code}.json"
    payload = _load_json(path)
    sites = payload.get("sites") if isinstance(payload, dict) else payload
    if not isinstance(sites, list):
        return []
    return [s for s in sites if _names_match(s.get("territoire"), territory_name)]


def _hierarchy_feature(territory_name: str, province: str | None = None) -> dict[str, Any] | None:
    payload = _load_json(HIERARCHY_PATH)
    territories = payload.get("territories") or []
    for item in territories:
        attrs = (item.get("attributs") or {}).get("extended_data") or {}
        if attrs.get("TYPE") and str(attrs.get("TYPE")).lower() != "territoire":
            # some entries may not have TYPE; still match by name
            pass
        name = item.get("nom") or item.get("name")
        item_province = item.get("province")
        if _names_match(name, territory_name) and (not province or _names_match(item_province, province) or not item_province):
            return item
    return None


def _safe_health(territory_name: str, province: str | None) -> dict[str, Any]:
    try:
        from api.services import health_service

        facilities = health_service.list_facilities(
            province_name=province,
            territory_name=territory_name,
            limit=500,
        )
        if isinstance(facilities, list):
            rows = facilities
        elif isinstance(facilities, dict):
            rows = facilities.get("facilities") or facilities.get("items") or []
        else:
            rows = []
        return {
            "count": len(rows),
            "items": rows[:50],
            "status": STATUS_CONFIRMED if rows else STATUS_PARTIAL,
            "source": "/api/health",
            "note": None if rows else "Aucun établissement de santé trouvé pour ce filtre territoire/province.",
        }
    except Exception as exc:  # noqa: BLE001 — consolidation tolérante
        return {"count": 0, "items": [], "status": STATUS_UNAVAILABLE, "source": "/api/health", "note": str(exc)}


def _safe_telecom(territory_name: str, province: str | None) -> dict[str, Any]:
    try:
        from api.services import telecom_service

        objects = telecom_service.list_infrastructure(limit=20000)
        filtered = [
            o
            for o in (objects or [])
            if _names_match(o.get("territoire") or o.get("territory"), territory_name)
            or (
                province
                and _names_match(o.get("province"), province)
                and _names_match(o.get("territoire") or o.get("territory"), territory_name)
            )
        ]
        # Prefer strict territory match
        strict = [o for o in (objects or []) if _names_match(o.get("territoire"), territory_name)]
        rows = strict or filtered
        if rows:
            return {
                "count": len(rows),
                "items": rows[:50],
                "status": STATUS_PARTIAL,
                "source": "/api/telecom/infrastructure",
            }
        return {
            "count": 0,
            "items": [],
            "status": STATUS_NOT_SOURCED,
            "source": "/api/telecom/infrastructure",
            "note": "Aucune infrastructure télécom rattachée explicitement à ce territoire.",
        }
    except Exception as exc:  # noqa: BLE001
        return {"count": None, "items": [], "status": STATUS_UNAVAILABLE, "source": "/api/telecom", "note": str(exc)}


def _safe_ccn(territory_name: str, province: str | None) -> dict[str, Any]:
    try:
        from api.services import ccn_operational_service

        listed = ccn_operational_service.list_ccn(territoire=territory_name, province=province, limit=200)
        items = listed.get("ccn") or []
        # also try name-only if empty
        if not items:
            listed = ccn_operational_service.list_ccn(territoire=territory_name, limit=200)
            items = listed.get("ccn") or []
        return {
            "count": len(items),
            "items": items,
            "status": STATUS_DEMONSTRATION if items else STATUS_UNAVAILABLE,
            "source": "/api/ccn",
            "data_class": listed.get("_meta", {}).get("data_class"),
            "note": None if items else "Aucun CCN DEMO associé à ce territoire dans le jeu actuel.",
        }
    except Exception as exc:  # noqa: BLE001
        return {"count": 0, "items": [], "status": STATUS_UNAVAILABLE, "source": "/api/ccn", "note": str(exc)}


def _safe_coverage(territory_name: str) -> dict[str, Any]:
    """Référentiel National des Besoins — couverture numérique du territoire."""
    try:
        from api.services import coverage_intelligence_service as nci

        payload = nci.get_territory_coverage(territory_name)
        if not payload:
            return {
                "available": False,
                "status": STATUS_UNAVAILABLE,
                "source": "/api/coverage",
                "note": "Territoire absent du Référentiel National des Besoins",
            }
        row = payload.get("territory") or {}
        explain = payload.get("explain") or {}
        return {
            "available": True,
            "status": STATUS_CONFIRMED,
            "source": "data/coverage/aggregates.json",
            "population_covered": row.get("population_covered"),
            "population_uncovered": row.get("population_uncovered"),
            "population_remaining": row.get("population_remaining"),
            "localities_covered": row.get("localities_covered"),
            "localities_uncovered": row.get("localities_uncovered"),
            "categories": row.get("categories") or {},
            "priorities": row.get("priorities") or {},
            "avg_distance_km": row.get("avg_distance_km"),
            "ndci": (row.get("ndci") or {}).get("index"),
            "ndci_components": (row.get("ndci") or {}).get("components"),
            "data_quality_avg": row.get("data_quality_avg"),
            "explain": explain,
            "note": "Données officielles FDSU (besoins) — distinctes des actifs programmes.",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "available": False,
            "status": STATUS_UNAVAILABLE,
            "source": "/api/coverage",
            "note": str(exc),
        }


def _score_sites(sites: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from api.services import fdsu_site_priority_service

    scored = []
    for site in sites:
        try:
            scored.append(fdsu_site_priority_service.compute_national_site_score(site))
        except Exception:  # noqa: BLE001
            continue
    scored.sort(key=lambda s: (-float(s.get("priority_score") or 0), str(s.get("site_name") or "")))
    return scored


def build_territorial_profile(territory_id: str, *, light: bool = False) -> dict[str, Any] | None:
    """Profil territorial — délègue au TerritorialProfileService (Data First / source unique)."""
    from api.services import territorial_profile_service as tps

    composed = tps.build_composed_profile(territory_id, light=light)
    if not composed:
        return None

    adapted = tps.to_territorial_intelligence_profile(composed)
    profile = adapted["profile"]
    name = profile.get("territory_name")
    province = profile.get("province")
    zone = profile.get("fdsu_zone")

    # Enrichissements historiques encore consommés par map / recommendations
    sites_40 = _program_sites("sites_40", name)
    sites_300 = _program_sites("sites_300", name)
    sites_20476 = _program_sites("sites_20476", name)
    all_program_sites = sites_20476 or sites_300 or sites_40
    distances = [float(s["distance"]) for s in all_program_sites if s.get("distance") not in (None, "")]

    health_block = composed.get("health") or {}
    telecom_block = composed.get("telecom") or {}
    ccn_block = composed.get("ccn") or {}
    coverage = composed.get("coverage") or _safe_coverage(name)
    scored_sites: list[dict[str, Any]] = []
    if not light:
        scored_sites = _score_sites(all_program_sites[:200])

    health = {
        "count": (health_block.get("total") or {}).get("value") or 0,
        "items": [],
        "status": (health_block.get("total") or {}).get("status") or STATUS_UNAVAILABLE,
        "source": (health_block.get("total") or {}).get("source"),
        "note": (health_block.get("total") or {}).get("note"),
        "by_type": health_block.get("by_type") or {},
    }
    telecom = {
        "count": (telecom_block.get("infrastructures") or {}).get("value"),
        "items": [],
        "status": (telecom_block.get("infrastructures") or {}).get("status") or STATUS_NOT_SOURCED,
        "source": (telecom_block.get("infrastructures") or {}).get("source"),
        "note": (telecom_block.get("infrastructures") or {}).get("note"),
    }
    ccn = {
        "count": (ccn_block.get("count") or {}).get("value") or 0,
        "items": [],
        "status": (ccn_block.get("count") or {}).get("status") or STATUS_UNAVAILABLE,
        "source": (ccn_block.get("count") or {}).get("source"),
        "note": (ccn_block.get("count") or {}).get("note"),
        "data_class": ccn_block.get("data_class"),
    }

    population_field = profile["population"]
    area_field = profile["area_km2"]
    density_field = profile["density"]
    localities_count = profile["localities_count"]
    groupements_count = profile["groupements_count"]
    missing = list(adapted.get("data_gaps") or [])
    avg_score = (adapted["sections"]["priority"]["score"] or {}).get("value")
    top_level = (adapted["sections"]["priority"]["level"] or {}).get("value")
    confidence = profile.get("confidence_level") or "medium"
    ref = {
        "territory_id": profile.get("territory_id"),
        "territory_name": name,
        "province": province,
        "fdsu_zone": zone,
        "administrative_code": profile.get("administrative_code"),
        "province_code": profile.get("province_code"),
        "nb_sites_reference": (composed.get("entity") or {}).get("registry", {}).get("nb_sites_reference")
        if isinstance((composed.get("entity") or {}).get("registry"), dict)
        else None,
    }
    # nb_sites from registry attributes
    try:
        reg = _resolve_territory_ref(territory_id) or {}
        ref["nb_sites_reference"] = reg.get("nb_sites_reference")
        ref["administrative_code"] = reg.get("administrative_code") or ref.get("administrative_code")
    except Exception:
        pass

    if light:
        profile["priority"] = {
            "score": field(avg_score, STATUS_ESTIMATED if avg_score is not None else STATUS_UNAVAILABLE, source="agrégation scores sites"),
            "level": field(top_level, STATUS_ESTIMATED if top_level else STATUS_UNAVAILABLE, source="top site scoré"),
        }
        return profile

    hierarchy = _hierarchy_feature(name, province)

    # Sections Data First (source unique) + enrichissements historiques
    sections = dict(adapted.get("sections") or {})
    digital = dict(sections.get("digital") or {})
    digital["distance_moyenne_sites"] = field(
        round(sum(distances) / len(distances), 1) if distances else None,
        STATUS_PARTIAL if distances else STATUS_UNAVAILABLE,
        source="programmes sites.distance",
        note="Moyenne des distances renseignées sur les sites programme du territoire.",
    )
    digital["zones_peu_desservies"] = field(
        sum(
            1
            for s in all_program_sites
            if str(s.get("distance_level") or "").lower() in {"far", "éloigné", "eloigne", "high"}
        ),
        STATUS_PARTIAL if all_program_sites else STATUS_UNAVAILABLE,
        source="sites.distance_level",
    )
    sections["digital"] = digital

    accessibility = dict(sections.get("accessibility") or {})
    accessibility["aerodromes"] = field(
        any(
            "airport" in str(s.get("nearest_site") or "").lower()
            or "aerodrome" in str(s.get("site_name") or "").lower()
            for s in all_program_sites
        ),
        STATUS_PARTIAL if all_program_sites else STATUS_NOT_SOURCED,
        source="indices sites (nearest_site / site_name)",
        note="Signal faible dérivé des libellés sites — à confirmer.",
    )
    sections["accessibility"] = accessibility

    public_services = dict(sections.get("public_services") or {})
    public_services["health_sample"] = health.get("items") or []
    sections["public_services"] = public_services

    priority = dict(sections.get("priority") or {})
    priority["sites_scored"] = field(
        len(scored_sites),
        STATUS_CONFIRMED if scored_sites else STATUS_UNAVAILABLE,
        source="priorisation nationale",
    )
    priority["top_site"] = scored_sites[0] if scored_sites else None
    priority["main_factors"] = (
        ((scored_sites[0].get("criteria_details") or {}).get("top_factors") or []) if scored_sites else []
    )
    priority["missing_criteria"] = missing
    priority["confidence_level"] = confidence
    sections["priority"] = priority

    # Coverage section — conserver le détail NCI historique
    cov_status = coverage.get("status", STATUS_UNAVAILABLE) if coverage.get("available") or coverage.get("status") == "operational" else STATUS_UNAVAILABLE
    if coverage.get("status") in {"operational", "partial", "confirmed"}:
        cov_status = coverage.get("status")
    coverage_section = {
        "population_covered": coverage.get("population_covered")
        if isinstance(coverage.get("population_covered"), dict)
        else field(
            coverage.get("population_covered"),
            cov_status,
            source=coverage.get("source"),
            note=coverage.get("note"),
        ),
        "population_uncovered": coverage.get("population_uncovered")
        if isinstance(coverage.get("population_uncovered"), dict)
        else field(coverage.get("population_uncovered"), cov_status, source=coverage.get("source")),
        "localities_covered": coverage.get("localities_covered")
        if isinstance(coverage.get("localities_covered"), dict)
        else field(coverage.get("localities_covered"), cov_status, source=coverage.get("source")),
        "localities_uncovered": coverage.get("localities_uncovered")
        if isinstance(coverage.get("localities_uncovered"), dict)
        else field(coverage.get("localities_uncovered"), cov_status, source=coverage.get("source")),
        "ndci": coverage.get("ndci")
        if isinstance(coverage.get("ndci"), dict)
        else field(coverage.get("ndci"), cov_status, source="NCI"),
        "explain": coverage.get("explain") if isinstance(coverage, dict) else None,
    }
    sections["coverage"] = coverage_section
    sections["opportunities"] = _build_opportunities(scored_sites, health, ccn, sites_300)
    sections["risks"] = _build_risks(missing, confidence, distances)
    if hierarchy:
        sections.setdefault("synthesis", {})["hierarchy_surface_km2"] = field(
            ((hierarchy.get("attributs") or {}).get("extended_data") or {}).get("SURFACE"),
            STATUS_PARTIAL,
            source="territory_hierarchy KMZ",
            note="Surface attributaire KMZ (contrôle croisé PostGIS).",
        )

    from api.services import knowledge_hub_service

    kh_domain = knowledge_hub_service.get_domain("territory")
    nif = knowledge_hub_service.list_indicators(domain_id="territory")
    kh_coverage = knowledge_hub_service.get_domain("national_coverage")

    profile = {
        **profile,
        "sources": list(dict.fromkeys((profile.get("sources") or []) + (composed.get("sources") or []))),
        "confidence_level": confidence,
        "is_demo_focus": _norm(name) == DEMO_FOCUS_NAME,
        "engine_version": ENGINE_VERSION,
    }

    return {
        "_meta": {
            "title": f"Profil Territorial FDSU — {name}",
            "engine_version": ENGINE_VERSION,
            "composed_engine": (composed.get("_meta") or {}).get("engine"),
            "principle": "Data First — consolider sans inventer ; blocs indépendants",
            "generated_at": _now(),
        },
        "profile": profile,
        "sections": sections,
        "assets": {
            "sites_sample": all_program_sites[:20],
            "sites_scored_top": scored_sites[:10],
            "ccn": ccn.get("items") or [],
            "health_sample": health.get("items") or [],
        },
        "needs": {
            "coverage": coverage,
            "heritage": "Référentiel National des Besoins",
        },
        "spatial_matching": _safe_spatial_matching(
            name, profile.get("territory_id") if isinstance(profile, dict) else territory_id
        ),
        "knowledge_hub": {
            "domain": (kh_domain or {}).get("domain"),
            "national_coverage": (kh_coverage or {}).get("domain"),
            "nif_indicators": nif.get("indicators") if isinstance(nif, dict) else nif,
        },
        "data_gaps": missing,
        "composed": {
            "section_status": composed.get("section_status"),
            "sources": composed.get("sources"),
            "entity": composed.get("entity"),
        },
        "hierarchy_feature": {
            "available": hierarchy is not None,
            "name": (hierarchy or {}).get("nom"),
            "province": (hierarchy or {}).get("province"),
        },
        "explainability": _safe_explainability_bundle(territory_id),
    }


def _safe_explainability_bundle(territory_id: str) -> dict[str, Any]:
    try:
        from api.services import territorial_explainability_service as tex

        return tex.build_explainability_bundle(territory_id) or {}
    except Exception as exc:  # noqa: BLE001
        return {"_error": str(exc), "status": "error"}


def _safe_spatial_matching(territory_name: str, territory_id: str | None = None) -> dict[str, Any]:
    """Intègre le NSME sans casser le profil TI si la table n'est pas encore peuplée."""
    try:
        from api.services import spatial_matching_service as nsme

        payload = nsme.get_territory_matches(territory_id or territory_name, limit=100, compute_if_empty=False)
        return {
            "available": True,
            "engine": "nsme-1.0.0",
            "assets_present": payload.get("assets_present"),
            "needs_matched": payload.get("needs_matched"),
            "population_impacted_by_assets": payload.get("population_impacted_by_assets"),
            "population_remaining": payload.get("population_remaining"),
            "zones_without_matching_asset": payload.get("zones_without_matching_asset"),
            "match_quality": payload.get("match_quality"),
            "investment_opportunities": payload.get("investment_opportunities"),
            "impact": payload.get("impact"),
            "source": "/api/spatial-matching",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "available": False,
            "engine": "nsme-1.0.0",
            "status": "unavailable",
            "note": str(exc),
            "source": "/api/spatial-matching",
        }


def _build_opportunities(scored_sites, health, ccn, sites_300) -> dict[str, Any]:
    items = []
    if sites_300:
        items.append({"id": "wave_300", "label": "Présence dans la vague 300", "status": STATUS_CONFIRMED, "source": "sites_300"})
    if scored_sites:
        items.append({"id": "priority_sites", "label": f"{len(scored_sites)} sites scorés disponibles pour arbitrage", "status": STATUS_CONFIRMED, "source": "priorisation"})
    if health.get("count"):
        items.append({"id": "health_anchor", "label": "Ancrage services de santé documenté", "status": STATUS_CONFIRMED, "source": "/api/health"})
    if ccn.get("count"):
        items.append({"id": "ccn_demo", "label": "CCN DEMO présents", "status": STATUS_DEMONSTRATION, "source": "/api/ccn"})
    if not items:
        items.append({"id": "collect_data", "label": "Opportunité principale : compléter la connaissance territoriale", "status": STATUS_NOT_SOURCED})
    return {"items": items}


def _build_risks(missing: list[str], confidence: str, distances: list[float]) -> dict[str, Any]:
    risks = []
    if "telecom_territorial" in missing:
        risks.append({"type": "data", "label": "Télécom non ventilé par territoire", "severity": "confidence"})
    if "area_km2" in missing:
        risks.append({"type": "data", "label": "Superficie absente — densité indisponible", "severity": "analysis"})
    if "ccn" in missing:
        risks.append({"type": "program", "label": "Aucun CCN associé dans les sources actuelles", "severity": "planning"})
    if confidence == "low":
        risks.append({"type": "confidence", "label": "Faible confiance globale du profil", "severity": "flag"})
    if distances and (sum(distances) / len(distances)) > 10000:
        risks.append({"type": "access", "label": "Distance moyenne élevée aux sites de référence", "severity": "partial", "status": STATUS_PARTIAL})
    risks.append({"type": "security", "label": "Contraintes sécuritaires", "status": STATUS_NOT_SOURCED, "note": "Non sourcé pour ce territoire"})
    return {"items": risks}


def build_map_payload(territory_id: str) -> dict[str, Any] | None:
    """GeoJSON territorial Data First — toutes les couches réellement disponibles.

    Cause racine historique : seuls boundary + sites_sample (20) + health_sample=[]
    étaient exposés → carte quasi vide malgré KPI télécom/santé/routes/fibre.
    """
    from api.services.territorial_entity_resolver import resolve_territory

    entity = resolve_territory(territory_id)
    if not entity:
        return None
    db_id = entity.get("db_id")
    name = entity.get("name")
    province = entity.get("province")
    territory_code = entity.get("territory_id") or territory_id
    features: list[dict[str, Any]] = []
    layer_counts: dict[str, int] = {}

    def _add(kind: str, geometry: dict[str, Any] | None, props: dict[str, Any]) -> None:
        if not geometry:
            return
        if isinstance(geometry, str):
            try:
                geometry = json.loads(geometry)
            except Exception:
                return
        if not isinstance(geometry, dict):
            return
        features.append({"type": "Feature", "geometry": geometry, "properties": {"kind": kind, **props}})
        layer_counts[kind] = layer_counts.get(kind, 0) + 1

    # 1) Limite territoriale PostGIS (prioritaire) puis fallback KMZ hierarchy
    if DATA_MODE == "db" and db_id:
        try:
            with connect_db() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        """
                        SELECT ST_AsGeoJSON(geom)::json AS geometry
                        FROM public.territoires WHERE id = %s AND geom IS NOT NULL
                        """,
                        (db_id,),
                    )
                    row = cur.fetchone()
                    if row and row.get("geometry"):
                        _add(
                            "territory_boundary",
                            row["geometry"] if isinstance(row["geometry"], dict) else None,
                            {"name": name, "territory_id": territory_code},
                        )
        except Exception:
            pass
    if "territory_boundary" not in layer_counts:
        hierarchy = _hierarchy_feature(name, province)
        if hierarchy and hierarchy.get("geometry"):
            _add(
                "territory_boundary",
                hierarchy["geometry"],
                {"name": name, "territory_id": territory_code},
            )

    # 2) Couches métier PostGIS
    if DATA_MODE == "db" and db_id:
        try:
            with connect_db() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Santé
                    cur.execute(
                        """
                        SELECT f.id, f.name,
                               ST_Y(f.geom) AS latitude, ST_X(f.geom) AS longitude,
                               f.facility_type_code
                        FROM health.health_facilities f
                        JOIN public.territoires t ON t.id = %s
                        WHERE f.geom IS NOT NULL AND ST_Within(f.geom, t.geom)
                        LIMIT 800
                        """,
                        (db_id,),
                    )
                    for r in cur.fetchall():
                        _add(
                            "health",
                            {"type": "Point", "coordinates": [float(r["longitude"]), float(r["latitude"])]},
                            {
                                "id": r["id"],
                                "name": r.get("name"),
                                "type": r.get("facility_type_code") or "OTHER",
                            },
                        )

                    # Télécom (hors FTTX) + Fibre nœuds
                    cur.execute(
                        """
                        SELECT i.id, i.infra_name, i.infra_type, i.technology,
                               i.latitude, i.longitude, o.operator_name
                        FROM telecom.infrastructure i
                        JOIN public.territoires t ON t.id = %s
                        LEFT JOIN telecom.operators o ON o.id = i.operator_id
                        WHERE i.geom IS NOT NULL AND ST_Intersects(i.geom, t.geom)
                        LIMIT 500
                        """,
                        (db_id,),
                    )
                    for r in cur.fetchall():
                        infra_type = (r.get("infra_type") or "").lower()
                        is_fiber = any(x in infra_type for x in ("fttx", "fibre", "fiber"))
                        kind = "fiber" if is_fiber else "telecom"
                        lat, lon = r.get("latitude"), r.get("longitude")
                        if lat is None or lon is None:
                            continue
                        _add(
                            kind,
                            {"type": "Point", "coordinates": [float(lon), float(lat)]},
                            {
                                "id": r["id"],
                                "name": r.get("infra_name"),
                                "type": r.get("infra_type"),
                                "operator": r.get("operator_name"),
                                "technology": r.get("technology"),
                            },
                        )

                    # Tronçons fibre / network_lines
                    cur.execute(
                        """
                        SELECT nl.id, nl.line_name, nl.line_code, nl.line_type,
                               ST_AsGeoJSON(ST_Intersection(nl.geom, t.geom))::json AS geometry
                        FROM telecom.network_lines nl
                        JOIN public.territoires t ON t.id = %s
                        WHERE nl.geom IS NOT NULL AND ST_Intersects(nl.geom, t.geom)
                        LIMIT 300
                        """,
                        (db_id,),
                    )
                    for r in cur.fetchall():
                        geom = r.get("geometry")
                        if isinstance(geom, dict):
                            _add(
                                "fiber_line",
                                geom,
                                {
                                    "id": r["id"],
                                    "name": r.get("line_name") or r.get("line_code"),
                                    "type": r.get("line_type"),
                                },
                            )

                    # Routes
                    cur.execute(
                        """
                        SELECT r.id, r.nom, r.type_route, r.categorie, r.numero,
                               ST_AsGeoJSON(ST_Intersection(r.geom, t.geom))::json AS geometry
                        FROM transport.routes r
                        JOIN public.territoires t ON t.id = %s
                        WHERE r.geom IS NOT NULL AND ST_Intersects(r.geom, t.geom)
                        LIMIT 300
                        """,
                        (db_id,),
                    )
                    for r in cur.fetchall():
                        geom = r.get("geometry")
                        if isinstance(geom, dict):
                            _add(
                                "route",
                                geom,
                                {
                                    "id": r["id"],
                                    "name": r.get("nom") or (f"Axe {r.get('numero')}" if r.get("numero") else f"Tronçon {r['id']}"),
                                    "type": r.get("type_route") or r.get("categorie"),
                                },
                            )

                    # Groupements (centroïdes)
                    cur.execute(
                        """
                        SELECT DISTINCT g.id, g.nom, g.code,
                               ST_Y(ST_Centroid(g.geom)) AS latitude,
                               ST_X(ST_Centroid(g.geom)) AS longitude
                        FROM public.groupements g
                        JOIN public.territoires t ON t.id = %s
                        LEFT JOIN public.collectivites c ON g.parent_id = c.id AND c.parent_id = t.id
                        WHERE g.geom IS NOT NULL
                          AND (c.parent_id = t.id OR g.parent_id = t.id OR ST_Within(g.geom, t.geom))
                        LIMIT 200
                        """,
                        (db_id,),
                    )
                    for r in cur.fetchall():
                        if r.get("latitude") is None or r.get("longitude") is None:
                            continue
                        _add(
                            "groupement",
                            {"type": "Point", "coordinates": [float(r["longitude"]), float(r["latitude"])]},
                            {"id": r["id"], "name": r.get("nom"), "code": r.get("code")},
                        )

                    # Localités (points)
                    cur.execute(
                        """
                        SELECT l.id, l.nom, l.code,
                               ST_Y(l.geom) AS latitude, ST_X(l.geom) AS longitude
                        FROM public.localites l
                        JOIN public.territoires t ON t.id = %s
                        WHERE l.geom IS NOT NULL AND ST_Within(l.geom, t.geom)
                        LIMIT 500
                        """,
                        (db_id,),
                    )
                    for r in cur.fetchall():
                        if r.get("latitude") is None or r.get("longitude") is None:
                            continue
                        _add(
                            "locality",
                            {"type": "Point", "coordinates": [float(r["longitude"]), float(r["latitude"])]},
                            {"id": r["id"], "name": r.get("nom"), "code": r.get("code")},
                        )
        except Exception as exc:  # noqa: BLE001
            layer_counts["_error"] = str(exc)

    # 3) Sites FDSU + CCN (programmes / DEMO) — sans second profil complet lourd
    try:
        for program_code in ("sites_20476", "sites_300", "sites_40"):
            for site in _program_sites(program_code, name)[:250]:
                if site.get("latitude") is None or site.get("longitude") is None:
                    continue
                sid = site.get("site_id") or site.get("id") or site.get("site_code")
                _add(
                    "site_fdsu",
                    {"type": "Point", "coordinates": [float(site["longitude"]), float(site["latitude"])]},
                    {
                        "id": sid,
                        "code": site.get("site_code"),
                        "name": site.get("site_name"),
                        "program_code": program_code,
                    },
                )
    except Exception:
        pass
    try:
        from api.services import ccn_operational_service

        listed = ccn_operational_service.list_ccn(territoire=name, limit=50)
        for ccn in listed.get("ccn") or []:
            if ccn.get("latitude") is None or ccn.get("longitude") is None:
                continue
            _add(
                "ccn",
                {"type": "Point", "coordinates": [float(ccn["longitude"]), float(ccn["latitude"])]},
                {"id": ccn.get("id"), "name": ccn.get("name"), "data_class": "demonstration"},
            )
    except Exception:
        pass

    return {
        "_meta": {
            "title": f"Carte territoriale — {name}",
            "feature_count": len(features),
            "layer_counts": layer_counts,
            "engine_version": ENGINE_VERSION,
            "data_first": True,
            "note": "Couches branchées sur PostGIS lorsque disponibles — pas de second calcul inventé.",
        },
        "territory_id": territory_code,
        "legend": [
            {"kind": "territory_boundary", "label": "Limite territoriale"},
            {"kind": "site_fdsu", "label": "Sites FDSU"},
            {"kind": "ccn", "label": "CCN"},
            {"kind": "health", "label": "Santé"},
            {"kind": "telecom", "label": "Télécom"},
            {"kind": "fiber", "label": "Fibre (nœuds)"},
            {"kind": "fiber_line", "label": "Fibre (tronçons)"},
            {"kind": "route", "label": "Routes"},
            {"kind": "groupement", "label": "Groupements"},
            {"kind": "locality", "label": "Localités"},
        ],
        "geojson": {"type": "FeatureCollection", "features": features},
    }


def build_indicators(territory_id: str) -> dict[str, Any] | None:
    profile = build_territorial_profile(territory_id)
    if not profile:
        return None
    from api.services import knowledge_hub_service

    nif = knowledge_hub_service.list_indicators()
    return {
        "_meta": {
            "title": "Indicateurs territoriaux",
            "values_policy": "Pas de valeur inventée — NIF structure_only + champs profil",
        },
        "territory_id": profile["profile"]["territory_id"],
        "profile_fields": {
            "population": profile["profile"]["population"],
            "area_km2": profile["profile"]["area_km2"],
            "sites_20476": profile["sections"]["programs"]["sites_20476"],
            "health": profile["sections"]["public_services"]["etablissements_sante"],
            "priority_score": profile["sections"]["priority"]["score"],
            "coverage_ndci": (profile.get("sections") or {}).get("coverage", {}).get("ndci"),
            "population_remaining": (profile.get("sections") or {}).get("coverage", {}).get("population_uncovered"),
            "localities_uncovered": (profile.get("sections") or {}).get("coverage", {}).get("localities_uncovered"),
        },
        "nif": nif.get("indicators") or [],
        "data_gaps": profile.get("data_gaps") or [],
    }


def build_recommendations(territory_id: str) -> dict[str, Any] | None:
    profile = build_territorial_profile(territory_id)
    if not profile:
        return None

    from api.services import explainable_decision_service

    doctrine_sites = explainable_decision_service.get_doctrine_payload("DOCTRINE_SITES_FDSU")
    doctrine_ccn = explainable_decision_service.get_doctrine_payload("DOCTRINE_CCN_FDSU")
    gaps = profile.get("data_gaps") or []
    top_sites = profile["assets"]["sites_scored_top"][:3]
    recommendations = []

    for site in top_sites:
        case = None
        try:
            case = explainable_decision_service.build_site_case(str(site.get("site_id")), program_code=site.get("program_code"))
        except Exception:  # noqa: BLE001
            case = None
        recommendations.append(
            {
                "id": f"site-{site.get('site_id')}",
                "type": "site",
                "action": "Prioriser le site pour arbitrage FDSU",
                "target": {
                    "site_id": site.get("site_id"),
                    "site_code": site.get("site_code"),
                    "site_name": site.get("site_name"),
                    "score": site.get("priority_score"),
                    "level": site.get("priority_level"),
                },
                "why": (
                    f"Score site {site.get('priority_score')}/100 ({site.get('priority_level_label')}) "
                    f"selon Doctrine Sites v{(doctrine_sites or {}).get('doctrine', {}).get('_meta', {}).get('version')}."
                ),
                "doctrine": {
                    "id": "DOCTRINE_SITES_FDSU",
                    "version": (doctrine_sites or {}).get("doctrine", {}).get("_meta", {}).get("version"),
                },
                "indicators": ["population", "deficit_distance", "wave_calibration"],
                "missing_data": gaps,
                "confidence_level": profile["profile"]["confidence_level"],
                "case_ref": case.get("case_id") if case else None,
            }
        )

    if "ccn" in gaps:
        recommendations.append(
            {
                "id": "ccn-study",
                "type": "ccn",
                "action": "Étudier l’opportunité d’un CCN (pas de CCN sourcé actuellement)",
                "why": (
                    "Aucun CCN associé dans les sources actuelles. "
                    f"Doctrine CCN v{(doctrine_ccn or {}).get('doctrine', {}).get('_meta', {}).get('version')} "
                    "exige critères versionnés avant recommandation d’implantation."
                ),
                "doctrine": {
                    "id": "DOCTRINE_CCN_FDSU",
                    "version": (doctrine_ccn or {}).get("doctrine", {}).get("_meta", {}).get("version"),
                },
                "indicators": ["MEAS_SCHOOL", "MEAS_HOSPITAL", "MEAS_ADMIN", "CRIT_CONN_EXTENSION"],
                "missing_data": ["ccn", "typologie_besoins_locale"],
                "confidence_level": "low",
                "fdsu_action": "étude terrain + collecte indicateurs doctrine CCN",
            }
        )

    if "telecom_territorial" in gaps:
        recommendations.append(
            {
                "id": "telecom-collect",
                "type": "extension_reseau",
                "action": "Collecter / ventiler les données télécom au niveau territoire",
                "why": "Le référentiel télécom n’expose pas encore une ventilation fiable par territoire.",
                "doctrine": {"id": "DOCTRINE_SITES_FDSU", "rule": "RULE_DATA_CONFIDENCE"},
                "indicators": ["IND_CONN_COVERAGE_GAP"],
                "missing_data": ["telecom_territorial"],
                "confidence_level": "low",
                "fdsu_action": "collecte de données",
            }
        )

    # NCI — besoins nationaux
    cov = (profile.get("needs") or {}).get("coverage") or {}
    if cov.get("available"):
        high_pri = int((cov.get("priorities") or {}).get("High") or 0)
        remaining = int(cov.get("population_remaining") or cov.get("population_uncovered") or 0)
        ndci = cov.get("ndci")
        recommendations.insert(
            0,
            {
                "id": "nci-needs",
                "type": "coverage_needs",
                "action": "Arbitrer les besoins numériques non couverts du territoire",
                "why": (
                    f"NCI: {cov.get('localities_uncovered') or 0} localités non couvertes, "
                    f"population restante {remaining:,}, "
                    f"{high_pri} priorités High, NDCI={ndci}, "
                    f"distance moyenne {cov.get('avg_distance_km')} km. "
                    "Comparaison Actifs (sites/CCN) vs Besoins (NCI)."
                ),
                "population": remaining,
                "priority": cov.get("priorities"),
                "distance_km_avg": cov.get("avg_distance_km"),
                "infrastructure": list((cov.get("explain") or {}).get("infrastructure") or cov.get("categories") or {}),
                "category": cov.get("categories"),
                "ndci": ndci,
                "doctrine": {
                    "id": "DOCTRINE_SITES_FDSU",
                    "version": (doctrine_sites or {}).get("doctrine", {}).get("_meta", {}).get("version"),
                    "matrix": "priority_matrix.json",
                },
                "indicators": ["population", "priority", "distance", "infrastructure", "category", "ndci"],
                "confidence_level": (cov.get("explain") or {}).get("confidence_level") or profile["profile"]["confidence_level"],
                "sources": ["/api/coverage", "data/coverage/"],
            },
        )

    recommendations.append(
        {
            "id": "data-collect",
            "type": "collecte_donnees",
            "action": "Compléter superficie, écoles, administrations, énergie",
            "why": "Plusieurs domaines du portrait restent not_sourced / unavailable — la décision territoriale reste partielle.",
            "doctrine": {"id": "Knowledge Hub", "note": "NIF structure_only"},
            "indicators": list(gaps),
            "missing_data": gaps,
            "confidence_level": profile["profile"]["confidence_level"],
            "fdsu_action": "collecte de données / étude terrain",
        }
    )

    # Guarantee: every recommendation has why
    for rec in recommendations:
        if not rec.get("why"):
            rec["why"] = "Justification manquante — recommandation non affichable sans explication."
            rec["confidence_level"] = "low"

    return {
        "_meta": {
            "title": "Recommandations territoriales explicables",
            "principle": "Aucune recommandation sans justification",
            "count": len(recommendations),
            "engine_version": ENGINE_VERSION,
        },
        "territory_id": profile["profile"]["territory_id"],
        "confidence_level": profile["profile"]["confidence_level"],
        "recommendations": recommendations,
        "coverage": cov if cov.get("available") else None,
    }


def explain_territory(territory_id: str) -> dict[str, Any] | None:
    profile = build_territorial_profile(territory_id)
    recs = build_recommendations(territory_id)
    if not profile or not recs:
        return None

    from api.services import explainable_decision_service

    doctrine_sites = explainable_decision_service.get_doctrine_payload("DOCTRINE_SITES_FDSU")
    return {
        "_meta": {
            "title": "Justification territoriale",
            "principle": "Aucune recommandation sans justification",
            "engine_version": ENGINE_VERSION,
        },
        "territory": {
            "id": profile["profile"]["territory_id"],
            "name": profile["profile"]["territory_name"],
            "province": profile["profile"]["province"],
            "zone": profile["profile"]["fdsu_zone"],
        },
        "priority": profile["sections"]["priority"],
        "doctrine": {
            "id": "DOCTRINE_SITES_FDSU",
            "version": (doctrine_sites or {}).get("doctrine", {}).get("_meta", {}).get("version"),
            "title": (doctrine_sites or {}).get("doctrine", {}).get("_meta", {}).get("title"),
            "references": (doctrine_sites or {}).get("doctrine", {}).get("_meta", {}).get("source_document"),
        },
        "matrix": "data/business/priority_matrix.json",
        "indicators_mobilized": [
            "population (sites)",
            "deficit_distance",
            "wave_calibration",
            "health facilities (si DB)",
        ],
        "rules_applied": ["agrégation scores sites", "Doctrine Sites", "signalement gaps Knowledge Hub"],
        "sources": profile["profile"]["sources"],
        "assumptions": [
            "Le score territorial est une agrégation des scores sites, pas un score officiel territoire.",
            "Les champs not_sourced / unavailable ne sont pas remplacés par des valeurs inventées.",
            "Les CCN DEMO restent explicitement marqués demonstration.",
        ],
        "missing_data": profile.get("data_gaps") or [],
        "confidence_level": profile["profile"]["confidence_level"],
        "recommendations": recs["recommendations"],
    }
