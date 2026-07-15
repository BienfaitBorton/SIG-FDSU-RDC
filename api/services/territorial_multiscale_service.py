"""Intelligence territoriale multi-échelle — contrat partagé Province → Localité.

Data First : aucune population / rattachement / taux inventé.
Agrégation démographique avec gardes anti double-comptage.
"""

from __future__ import annotations

import json
import re
from typing import Any

from psycopg2.extras import RealDictCursor

from api.config import DATA_MODE, connect_db
from api.services import cartography_symbology_registry as symbology

ENGINE_VERSION = "ti-multiscale-1.0.0"

# Cache léger des points NCI filtrés par territoire (évite de rescanner le JSONL à chaque drill-down)
_NCI_TERRITORY_CACHE: dict[str, dict[str, list[dict[str, Any]]]] = {}


def _nci_rows_for_territory(terr_name: str) -> dict[str, list[dict[str, Any]]]:
    key = _norm(terr_name)
    if key in _NCI_TERRITORY_CACHE:
        return _NCI_TERRITORY_CACHE[key]
    from api.services import coverage_intelligence_service as nci

    covered = nci.list_localities(status="covered", territoire=terr_name, limit=20000).get("localities") or []
    uncovered = nci.list_localities(status="uncovered", territoire=terr_name, limit=20000).get("localities") or []
    _NCI_TERRITORY_CACHE[key] = {"covered": covered, "uncovered": uncovered}
    return _NCI_TERRITORY_CACHE[key]

ENTITY_PREFIXES = {
    "PROVINCE": "province",
    "TERRITOIRE": "territoire",
    "COLLECTIVITE": "collectivite",
    "SECTEUR": "collectivite",
    "CHEFFERIE": "collectivite",
    "CITE": "collectivite",
    "GROUPEMENT": "groupement",
    "LOCALITE": "localite",
    "SITE": "site",
}

LEVEL_LABELS = {
    "rdc": "Pays",
    "province": "Province",
    "territoire": "Territoire",
    "collectivite": "Collectivité",
    "groupement": "Groupement",
    "localite": "Localité",
    "site": "Site",
}

TABLE_BY_LEVEL = {
    "province": "public.provinces",
    "territoire": "public.territoires",
    "collectivite": "public.collectivites",
    "groupement": "public.groupements",
    "localite": "public.localites",
}

CHILD_LEVEL = {
    "province": "territoire",
    "territoire": "collectivite",
    "collectivite": "groupement",
    "groupement": "localite",
    "localite": None,
}


def _norm(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().replace("-", " ").split())


def _field(
    value: Any,
    status: str,
    *,
    source: str | None = None,
    method: str | None = None,
    confidence: str | None = None,
    note: str | None = None,
    coverage_status: str | None = None,
    double_counting_guard: str | None = None,
) -> dict[str, Any]:
    return {
        "value": value,
        "status": status,
        "source": source,
        "method": method,
        "confidence": confidence or ("high" if status in {"operational", "confirmed"} else "medium" if status == "partial" else "low"),
        "coverage_status": coverage_status,
        "double_counting_guard": double_counting_guard,
        "note": note,
    }


def parse_entity_ref(ref: str) -> dict[str, Any]:
    """Parse PROVINCE-xx / TERRITOIRE-05-002 / COLLECTIVITE-328 / …"""
    token = str(ref or "").strip()
    if not token:
        return {"raw": "", "entity_type": None, "token": ""}
    upper = token.upper()
    for prefix, level in ENTITY_PREFIXES.items():
        if upper.startswith(prefix + "-") or upper.startswith(prefix + "_"):
            rest = token[len(prefix) + 1 :]
            return {
                "raw": token,
                "entity_type": level,
                "token": rest,
                "prefix": prefix,
                "business_id": token if level == "territoire" and prefix == "TERRITOIRE" else None,
            }
    # TERRITOIRE-05-002 déjà couvert ; ids numériques nus → non résolus ici
    if re.match(r"^TERRITOIRE-\d", token, re.I):
        return {"raw": token, "entity_type": "territoire", "token": token, "business_id": token}
    return {"raw": token, "entity_type": None, "token": token}


def resolve_entity(ref: str) -> dict[str, Any] | None:
    parsed = parse_entity_ref(ref)
    etype = parsed.get("entity_type")
    token = parsed.get("token") or parsed.get("raw")

    if etype == "territoire" or (not etype and str(ref).upper().startswith("TERRITOIRE")):
        from api.services.territorial_entity_resolver import resolve_territory

        entity = resolve_territory(parsed.get("business_id") or ref)
        if not entity:
            return None
        return {
            "type": "territoire",
            "id": entity.get("business_id") or entity.get("canonical_id") or ref,
            "db_id": entity.get("db_id"),
            "name": entity.get("name"),
            "code": entity.get("official_code"),
            "admin_type": "Territoire",
            "parent": entity.get("parent"),
            "hierarchy": entity.get("hierarchy") or {},
            "centroid": entity.get("centroid"),
            "has_geometry": entity.get("has_geometry"),
            "fdsu_zone": (entity.get("hierarchy") or {}).get("fdsu_zone")
            or (entity.get("registry") or {}).get("fdsu_zone"),
            "sources": entity.get("sources") or ["master_registry"],
            "_registry": entity.get("registry"),
        }

    if etype == "province":
        return _resolve_admin_row("province", token) or _resolve_admin_by_name("province", token)

    if etype in {"collectivite", "groupement", "localite"}:
        row = _resolve_admin_row(etype, token)
        if row:
            return row
        # Codes officiels type RDC-ND-COLL-…
        return _resolve_admin_by_code(etype, token) or _resolve_admin_by_name(etype, token)

    # Fallback : tenter territoire (comportement legacy)
    if not etype:
        from api.services.territorial_entity_resolver import resolve_territory

        entity = resolve_territory(ref)
        if entity:
            return resolve_entity(entity.get("business_id") or ref)
    return None


def _resolve_admin_row(level: str, token: str) -> dict[str, Any] | None:
    if DATA_MODE != "db" or not token:
        return None
    table = TABLE_BY_LEVEL.get(level)
    if not table:
        return None
    try:
        db_id = int(token)
    except (TypeError, ValueError):
        return None
    try:
        with connect_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    f"""
                    SELECT id, code, nom, type, parent_id,
                           geom IS NOT NULL AS has_geometry,
                           CASE WHEN geom IS NULL THEN NULL ELSE ST_Y(ST_Centroid(geom)) END AS lat,
                           CASE WHEN geom IS NULL THEN NULL ELSE ST_X(ST_Centroid(geom)) END AS lon
                    FROM {table}
                    WHERE id = %s
                    """,
                    (db_id,),
                )
                row = cur.fetchone()
        if not row:
            return None
        return _hydrate_admin(level, dict(row))
    except Exception:
        return None


def _resolve_admin_by_code(level: str, code: str) -> dict[str, Any] | None:
    if DATA_MODE != "db" or not code:
        return None
    table = TABLE_BY_LEVEL.get(level)
    try:
        with connect_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    f"""
                    SELECT id, code, nom, type, parent_id,
                           geom IS NOT NULL AS has_geometry,
                           CASE WHEN geom IS NULL THEN NULL ELSE ST_Y(ST_Centroid(geom)) END AS lat,
                           CASE WHEN geom IS NULL THEN NULL ELSE ST_X(ST_Centroid(geom)) END AS lon
                    FROM {table}
                    WHERE code ILIKE %s
                    LIMIT 1
                    """,
                    (code,),
                )
                row = cur.fetchone()
        return _hydrate_admin(level, dict(row)) if row else None
    except Exception:
        return None


def _resolve_admin_by_name(level: str, name: str) -> dict[str, Any] | None:
    if DATA_MODE != "db" or not name:
        return None
    table = TABLE_BY_LEVEL.get(level)
    try:
        with connect_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    f"""
                    SELECT id, code, nom, type, parent_id,
                           geom IS NOT NULL AS has_geometry,
                           CASE WHEN geom IS NULL THEN NULL ELSE ST_Y(ST_Centroid(geom)) END AS lat,
                           CASE WHEN geom IS NULL THEN NULL ELSE ST_X(ST_Centroid(geom)) END AS lon
                    FROM {table}
                    WHERE nom ILIKE %s OR code ILIKE %s
                    ORDER BY (nom ILIKE %s) DESC, id
                    LIMIT 5
                    """,
                    (f"%{name}%", f"%{name}%", name),
                )
                rows = [dict(r) for r in cur.fetchall()]
        if not rows:
            return None
        return _hydrate_admin(level, rows[0])
    except Exception:
        return None


def _hydrate_admin(level: str, row: dict[str, Any]) -> dict[str, Any]:
    prefix = {
        "province": "PROVINCE",
        "territoire": "TERRITOIRE",
        "collectivite": "COLLECTIVITE",
        "groupement": "GROUPEMENT",
        "localite": "LOCALITE",
    }[level]
    hierarchy = _build_hierarchy_chain(level, row["id"])
    parent = None
    if len(hierarchy) >= 2:
        p = hierarchy[-2]
        parent = {"type": p["type"], "id": p["id"], "name": p["name"], "code": p.get("code")}
    entity_id = f"{prefix}-{row['id']}"
    if level == "territoire":
        try:
            from api.services import territorial_intelligence_service as ti

            reg = ti._resolve_territory_ref(row.get("nom") or "")  # noqa: SLF001
            if reg and reg.get("territory_id"):
                entity_id = reg["territory_id"]
        except Exception:
            pass
    return {
        "type": level,
        "id": entity_id,
        "db_id": row["id"],
        "name": row.get("nom"),
        "code": row.get("code"),
        "admin_type": row.get("type") or LEVEL_LABELS.get(level),
        "parent": parent,
        "hierarchy": {h["type"]: h["name"] for h in hierarchy},
        "hierarchy_chain": hierarchy,
        "centroid": {"latitude": row.get("lat"), "longitude": row.get("lon")}
        if row.get("lat") is not None
        else None,
        "has_geometry": bool(row.get("has_geometry")),
        "sources": [TABLE_BY_LEVEL[level]],
    }


def _build_hierarchy_chain(level: str, db_id: int) -> list[dict[str, Any]]:
    """Remonte parent_id jusqu'à la province."""
    if DATA_MODE != "db":
        return []
    order = ["localite", "groupement", "collectivite", "territoire", "province"]
    try:
        idx = order.index(level)
    except ValueError:
        return []
    chain: list[dict[str, Any]] = []
    current_level = level
    current_id = db_id
    try:
        with connect_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                for _ in range(6):
                    table = TABLE_BY_LEVEL[current_level]
                    cur.execute(
                        f"SELECT id, code, nom, type, parent_id FROM {table} WHERE id = %s",
                        (current_id,),
                    )
                    row = cur.fetchone()
                    if not row:
                        break
                    prefix = {
                        "province": "PROVINCE",
                        "territoire": "TERRITOIRE",
                        "collectivite": "COLLECTIVITE",
                        "groupement": "GROUPEMENT",
                        "localite": "LOCALITE",
                    }[current_level]
                    entity_id = f"{prefix}-{row['id']}"
                    if current_level == "territoire":
                        try:
                            from api.services import territorial_intelligence_service as ti

                            reg = ti._resolve_territory_ref(row.get("nom") or "")  # noqa: SLF001
                            if reg and reg.get("territory_id"):
                                entity_id = reg["territory_id"]
                        except Exception:
                            pass
                    chain.append(
                        {
                            "type": current_level,
                            "id": entity_id,
                            "db_id": row["id"],
                            "name": row.get("nom"),
                            "code": row.get("code"),
                            "admin_type": row.get("type") or LEVEL_LABELS.get(current_level),
                        }
                    )
                    if current_level == "province" or not row.get("parent_id"):
                        break
                    # provinces.parent_id peut être zone — on s'arrête
                    parent_level = {
                        "localite": "groupement",
                        "groupement": "collectivite",
                        "collectivite": "territoire",
                        "territoire": "province",
                    }.get(current_level)
                    if not parent_level:
                        break
                    current_level = parent_level
                    current_id = int(row["parent_id"])
    except Exception:
        return list(reversed(chain)) if chain else []
    return list(reversed(chain))


def build_breadcrumb(entity: dict[str, Any]) -> list[dict[str, Any]]:
    crumbs = [{"type": "rdc", "id": "RDC", "name": "RDC", "label": "RDC"}]
    if entity.get("type") == "territoire":
        hier = entity.get("hierarchy") or {}
        province = hier.get("province") or (entity.get("parent") or {}).get("name")
        if province:
            crumbs.append(
                {
                    "type": "province",
                    "id": f"PROVINCE-{_slug(province)}",
                    "name": province,
                    "label": province,
                }
            )
        crumbs.append(
            {
                "type": "territoire",
                "id": entity.get("id"),
                "name": entity.get("name"),
                "label": entity.get("name"),
            }
        )
        return crumbs

    chain = entity.get("hierarchy_chain")
    if not chain:
        chain = _build_hierarchy_chain(entity["type"], int(entity["db_id"])) if entity.get("db_id") else []
    for node in chain:
        crumbs.append(
            {
                "type": node["type"],
                "id": node["id"],
                "name": node["name"],
                "label": node["name"],
                "admin_type": node.get("admin_type"),
            }
        )
    return crumbs


def _slug(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", str(name or "").strip()).strip("-").upper() or "X"


def list_children(entity: dict[str, Any], *, limit: int = 200) -> list[dict[str, Any]]:
    child_level = CHILD_LEVEL.get(entity.get("type") or "")
    if not child_level or DATA_MODE != "db" or not entity.get("db_id"):
        return []
    child_table = TABLE_BY_LEVEL[child_level]
    prefix = {
        "territoire": "TERRITOIRE",
        "collectivite": "COLLECTIVITE",
        "groupement": "GROUPEMENT",
        "localite": "LOCALITE",
    }[child_level]
    try:
        with connect_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if entity["type"] == "territoire" and child_level == "collectivite":
                    # Pour le territoire métier, préférer le code business si connu
                    pass
                cur.execute(
                    f"""
                    SELECT id, code, nom, type,
                           CASE WHEN geom IS NULL THEN NULL ELSE ST_Y(ST_Centroid(geom)) END AS lat,
                           CASE WHEN geom IS NULL THEN NULL ELSE ST_X(ST_Centroid(geom)) END AS lon,
                           geom IS NOT NULL AS has_geometry
                    FROM {child_table}
                    WHERE parent_id = %s
                    ORDER BY nom
                    LIMIT %s
                    """,
                    (entity["db_id"], limit),
                )
                rows = [dict(r) for r in cur.fetchall()]
        # Territoire registry id (TERRITOIRE-05-002) : enfants via db_id PostGIS
        out = []
        for r in rows:
            eid = f"{prefix}-{r['id']}"
            # Territoires enfants : tenter business_id master
            if child_level == "territoire":
                from api.services import territorial_intelligence_service as ti

                reg = ti._resolve_territory_ref(r.get("nom") or "")  # noqa: SLF001
                if reg and reg.get("territory_id"):
                    eid = reg["territory_id"]
            out.append(
                {
                    "type": child_level,
                    "id": eid,
                    "db_id": r["id"],
                    "name": r.get("nom"),
                    "code": r.get("code"),
                    "admin_type": r.get("type") or LEVEL_LABELS.get(child_level),
                    "has_geometry": bool(r.get("has_geometry")),
                    "centroid": {"latitude": r.get("lat"), "longitude": r.get("lon")}
                    if r.get("lat") is not None
                    else None,
                }
            )
        return out
    except Exception:
        return []


def _population_metric(
    *,
    value: Any,
    source: str,
    method: str,
    confidence: str,
    status: str,
    coverage_status: str | None = None,
    note: str | None = None,
    double_counting_guard: str = "exclusive_covered_uncovered_sets",
) -> dict[str, Any]:
    return _field(
        value,
        status,
        source=source,
        method=method,
        confidence=confidence,
        coverage_status=coverage_status,
        double_counting_guard=double_counting_guard,
        note=note,
    )


def build_population_coverage(entity: dict[str, Any]) -> dict[str, Any]:
    """Population + couverture sans double comptage.

    Priorité :
    1) Agrégats NCI territoire / province (ensembles couvert / non couvert exclusifs)
    2) Somme NCI des localités filtrées spatialement dans l’entité (mode spatial, partiel)
    3) Match nominal NCI sous le territoire parent (faiblesse déclarée)
    """
    etype = entity.get("type")
    name = entity.get("name")

    if etype == "territoire":
        from api.services import coverage_intelligence_service as nci

        payload = nci.get_territory_coverage(str(name))
        row = (payload or {}).get("territory") if payload else None
        if not row:
            return {
                "status": "unavailable",
                "note": "Aucun agrégat NCI pour ce territoire",
                "population": _population_metric(
                    value=None, source="nci", method="none", confidence="low", status="unavailable"
                ),
            }
        covered = row.get("population_covered")
        uncovered = row.get("population_uncovered")
        total = None
        if covered is not None and uncovered is not None:
            try:
                total = int(covered) + int(uncovered)
            except (TypeError, ValueError):
                total = None
        ratio = None
        if total and covered is not None and total > 0:
            try:
                ratio = round(100.0 * float(covered) / float(total), 1)
            except (TypeError, ValueError):
                ratio = None
        return {
            "status": "operational",
            "population": _population_metric(
                value=total,
                source="data/coverage/aggregates.json",
                method="sum_covered_plus_uncovered_exclusive",
                confidence="medium",
                status="partial",
                note="Somme contrôlée des populations NCI couvertes et non couvertes (ensembles exclusifs).",
            ),
            "population_covered": _population_metric(
                value=covered,
                source="data/coverage/aggregates.json",
                method="nci_territory_aggregate",
                confidence="medium",
                status="operational",
                coverage_status="covered",
            ),
            "population_uncovered": _population_metric(
                value=uncovered,
                source="data/coverage/aggregates.json",
                method="nci_territory_aggregate",
                confidence="medium",
                status="operational",
                coverage_status="uncovered",
            ),
            "localities_covered": _population_metric(
                value=row.get("localities_covered"),
                source="data/coverage/aggregates.json",
                method="nci_territory_aggregate",
                confidence="medium",
                status="operational",
                coverage_status="covered",
            ),
            "localities_uncovered": _population_metric(
                value=row.get("localities_uncovered"),
                source="data/coverage/aggregates.json",
                method="nci_territory_aggregate",
                confidence="medium",
                status="operational",
                coverage_status="uncovered",
            ),
            "coverage_rate_pct": _population_metric(
                value=ratio,
                source="derived",
                method="covered_over_covered_plus_uncovered",
                confidence="medium",
                status="partial" if ratio is not None else "unavailable",
                note="Taux uniquement si numérateur et dénominateur NCI compatibles.",
            ),
            "ndci": row.get("ndci"),
            "double_counting_guard": "covered_and_uncovered_are_exclusive_sets",
        }

    if etype == "province":
        from api.services import coverage_intelligence_service as nci

        agg = nci.get_aggregates() or {}
        by_p = agg.get("by_province") or {}
        row = None
        for k, v in by_p.items():
            if _norm(k) == _norm(name) or _norm((v or {}).get("province")) == _norm(name):
                row = v
                break
        if not row:
            return {"status": "unavailable", "note": "Aucun agrégat NCI provincial"}
        covered = row.get("population_covered")
        uncovered = row.get("population_uncovered")
        total = None
        if covered is not None and uncovered is not None:
            total = int(covered) + int(uncovered)
        ratio = round(100.0 * float(covered) / float(total), 1) if total and covered is not None else None
        return {
            "status": "operational",
            "population": _population_metric(
                value=total,
                source="data/coverage/aggregates.json",
                method="sum_covered_plus_uncovered_exclusive",
                confidence="medium",
                status="partial",
            ),
            "population_covered": _population_metric(
                value=covered, source="nci", method="nci_province_aggregate", confidence="medium", status="operational", coverage_status="covered"
            ),
            "population_uncovered": _population_metric(
                value=uncovered, source="nci", method="nci_province_aggregate", confidence="medium", status="operational", coverage_status="uncovered"
            ),
            "localities_covered": _population_metric(
                value=row.get("localities_covered"), source="nci", method="nci_province_aggregate", confidence="medium", status="operational", coverage_status="covered"
            ),
            "localities_uncovered": _population_metric(
                value=row.get("localities_uncovered"), source="nci", method="nci_province_aggregate", confidence="medium", status="operational", coverage_status="uncovered"
            ),
            "coverage_rate_pct": _population_metric(
                value=ratio, source="derived", method="covered_over_total", confidence="medium", status="partial" if ratio is not None else "unavailable"
            ),
            "double_counting_guard": "covered_and_uncovered_are_exclusive_sets",
        }

    # Niveaux fins : agrégation spatiale NCI dans la géométrie
    spatial = _aggregate_nci_within_geometry(entity)
    if spatial:
        return spatial

    return {
        "status": "partial",
        "note": "Population NCI non rattachée de façon fiable à cette entité — pas d’invention.",
        "population": _population_metric(
            value=None,
            source="nci+postgis",
            method="unresolved",
            confidence="low",
            status="unavailable",
            note="Rattachement démographique insuffisant (pas de FK population sur public.localites).",
        ),
    }


def _aggregate_nci_within_geometry(entity: dict[str, Any]) -> dict[str, Any] | None:
    if DATA_MODE != "db" or not entity.get("db_id"):
        return None
    level = entity.get("type")
    table = TABLE_BY_LEVEL.get(level or "")
    if not table:
        return None
    try:
        with connect_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    f"""
                    SELECT ST_AsGeoJSON(geom)::json AS geometry
                    FROM {table}
                    WHERE id = %s AND geom IS NOT NULL
                    """,
                    (entity["db_id"],),
                )
                row = cur.fetchone()
        if not row or not row.get("geometry"):
            return None
        geom = row["geometry"]
        # Filtrage spatial simple via bounding test PostGIS pour localités NCI ponctuelles
        terr_name = (entity.get("hierarchy") or {}).get("territoire")
        if not terr_name:
            return None
        # Filtrer d'abord par territoire parent (perf) — cache par territoire pour le drill-down.
        rows = _nci_rows_for_territory(str(terr_name))
        covered_rows = rows.get("covered") or []
        uncovered_rows = rows.get("uncovered") or []

        n_cov, p_cov = _batch_spatial_sum(geom, covered_rows)
        n_unc, p_unc = _batch_spatial_sum(geom, uncovered_rows)
        if n_cov == 0 and n_unc == 0:
            return None
        total = p_cov + p_unc
        ratio = round(100.0 * p_cov / total, 1) if total > 0 else None
        return {
            "status": "partial",
            "population": _population_metric(
                value=total if total > 0 else None,
                source="nci_jsonl+postgis",
                method="spatial_contains_within_entity_geom",
                confidence="low",
                status="partial",
                note="Agrégation spatiale partielle — pas un recensement officiel.",
            ),
            "population_covered": _population_metric(
                value=p_cov, source="nci_jsonl+postgis", method="spatial_contains", confidence="low", status="partial", coverage_status="covered"
            ),
            "population_uncovered": _population_metric(
                value=p_unc, source="nci_jsonl+postgis", method="spatial_contains", confidence="low", status="partial", coverage_status="uncovered"
            ),
            "localities_covered": _population_metric(
                value=n_cov, source="nci_jsonl+postgis", method="spatial_contains", confidence="low", status="partial", coverage_status="covered"
            ),
            "localities_uncovered": _population_metric(
                value=n_unc, source="nci_jsonl+postgis", method="spatial_contains", confidence="low", status="partial", coverage_status="uncovered"
            ),
            "coverage_rate_pct": _population_metric(
                value=ratio, source="derived", method="spatial_covered_over_total", confidence="low", status="partial" if ratio is not None else "unavailable",
                note="Partiel — localités NCI sans coordonnées exclues.",
            ),
            "double_counting_guard": "exclusive_datasets_plus_id_dedup",
        }
    except Exception:
        return None


def _batch_spatial_sum(geom: dict[str, Any], rows: list[dict[str, Any]]) -> tuple[int, int]:
    """Compte localités + population NCI dans une géométrie (dédupe par id)."""
    pts = []
    seen: set[str] = set()
    for r in rows:
        if r.get("duplicate"):
            continue
        lat, lon = r.get("latitude"), r.get("longitude")
        if lat is None or lon is None:
            continue
        rid = str(r.get("id") or "")
        if rid and rid in seen:
            continue
        if rid:
            seen.add(rid)
        try:
            pop = int(r.get("population") or 0)
        except (TypeError, ValueError):
            pop = 0
        pts.append((float(lon), float(lat), pop))
    if not pts:
        return 0, 0
    # LOTS pour éviter 50k roundtrips : VALUES + JOIN
    n_in = 0
    p_in = 0
    chunk = 400
    geom_json = json.dumps(geom)
    try:
        with connect_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                for i in range(0, len(pts), chunk):
                    batch = pts[i : i + chunk]
                    values = ",".join(
                        cur.mogrify("(%s,%s,%s)", (lon, lat, pop)).decode("utf-8")
                        for lon, lat, pop in batch
                    )
                    cur.execute(
                        f"""
                        WITH pts(lon, lat, pop) AS (VALUES {values}),
                        g AS (SELECT ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326) AS geom)
                        SELECT COUNT(*)::int AS n, COALESCE(SUM(pop),0)::bigint AS p
                        FROM pts, g
                        WHERE ST_Contains(g.geom, ST_SetSRID(ST_MakePoint(pts.lon, pts.lat), 4326))
                        """,
                        (geom_json,),
                    )
                    row = cur.fetchone() or {}
                    n_in += int(row.get("n") or 0)
                    p_in += int(row.get("p") or 0)
    except Exception:
        return 0, 0
    return n_in, p_in


def build_map_for_entity(entity: dict[str, Any]) -> dict[str, Any] | None:
    """Carte adaptée au niveau — réutilise TI pour territoire, sinon couches spatiales locales."""
    if entity.get("type") == "territoire":
        from api.services import territorial_intelligence_service as ti

        payload = ti.build_map_payload(entity["id"])
        if not payload:
            return None
        counts = (payload.get("_meta") or {}).get("layer_counts") or {}
        payload["legend"] = symbology.build_legend_items(counts, only_visible=True)
        payload["symbology"] = symbology.registry_payload()
        payload["entity"] = {
            "type": entity["type"],
            "id": entity["id"],
            "name": entity.get("name"),
        }
        return payload

    return _build_scoped_map(entity)


def _build_scoped_map(entity: dict[str, Any]) -> dict[str, Any] | None:
    if DATA_MODE != "db" or not entity.get("db_id"):
        return {
            "_meta": {"feature_count": 0, "layer_counts": {}, "note": "Carte multi-échelle disponible en mode DB"},
            "entity": {"type": entity.get("type"), "id": entity.get("id"), "name": entity.get("name")},
            "legend": [],
            "geojson": {"type": "FeatureCollection", "features": []},
            "symbology": symbology.registry_payload(),
        }
    features: list[dict[str, Any]] = []
    layer_counts: dict[str, int] = {}
    level = entity["type"]
    table = TABLE_BY_LEVEL[level]
    db_id = entity["db_id"]

    def _add(kind: str, geometry: Any, props: dict[str, Any]) -> None:
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

    try:
        with connect_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    f"""
                    SELECT ST_AsGeoJSON(geom)::json AS geometry, nom, code
                    FROM {table} WHERE id = %s AND geom IS NOT NULL
                    """,
                    (db_id,),
                )
                boundary = cur.fetchone()
                if boundary and boundary.get("geometry"):
                    kind = "territory_boundary" if level in {"province", "territoire"} else (
                        "collectivite" if level == "collectivite" else "groupement" if level == "groupement" else "locality"
                    )
                    if level == "localite":
                        kind = "locality"
                        _add(
                            kind,
                            {
                                "type": "Point",
                                "coordinates": [
                                    float(entity["centroid"]["longitude"]),
                                    float(entity["centroid"]["latitude"]),
                                ],
                            }
                            if entity.get("centroid")
                            else boundary["geometry"],
                            {"id": entity["id"], "name": entity.get("name"), "selected": True},
                        )
                    else:
                        bound_kind = "territory_boundary" if level in {"province", "territoire"} else "collectivite"
                        if level == "groupement":
                            bound_kind = "collectivite"
                        _add(
                            bound_kind,
                            boundary["geometry"],
                            {"id": entity["id"], "name": entity.get("name"), "selected": True},
                        )

                # Enfants points
                child_level = CHILD_LEVEL.get(level)
                if child_level:
                    child_table = TABLE_BY_LEVEL[child_level]
                    kind = {
                        "collectivite": "collectivite",
                        "groupement": "groupement",
                        "localite": "locality",
                        "territoire": "territory_boundary",
                    }.get(child_level, "locality")
                    cur.execute(
                        f"""
                        SELECT id, nom, code,
                               CASE WHEN geom IS NULL THEN NULL ELSE ST_Y(ST_Centroid(geom)) END AS lat,
                               CASE WHEN geom IS NULL THEN NULL ELSE ST_X(ST_Centroid(geom)) END AS lon,
                               CASE WHEN geom IS NOT NULL AND GeometryType(geom) IN ('POLYGON','MULTIPOLYGON')
                                    THEN ST_AsGeoJSON(geom)::json ELSE NULL END AS poly
                        FROM {child_table}
                        WHERE parent_id = %s
                        LIMIT 300
                        """,
                        (db_id,),
                    )
                    prefix = {
                        "collectivite": "COLLECTIVITE",
                        "groupement": "GROUPEMENT",
                        "localite": "LOCALITE",
                        "territoire": "TERRITOIRE",
                    }[child_level]
                    for r in cur.fetchall():
                        eid = f"{prefix}-{r['id']}"
                        if r.get("poly") and child_level == "collectivite":
                            _add("collectivite", r["poly"], {"id": eid, "name": r.get("nom"), "code": r.get("code")})
                        elif r.get("lat") is not None:
                            _add(
                                "groupement" if child_level == "groupement" else "locality",
                                {"type": "Point", "coordinates": [float(r["lon"]), float(r["lat"])]},
                                {"id": eid, "name": r.get("nom"), "code": r.get("code"), "drill_id": eid},
                            )

                # Couches métier dans l’emprise
                if level in {"collectivite", "groupement", "localite", "province"}:
                    for kind, sql in (
                        (
                            "health",
                            f"""
                            SELECT f.id, f.name, ST_Y(f.geom) AS lat, ST_X(f.geom) AS lon
                            FROM health.health_facilities f
                            JOIN {table} e ON e.id = %s
                            WHERE f.geom IS NOT NULL AND ST_Within(f.geom, e.geom)
                            LIMIT 400
                            """,
                        ),
                        (
                            "telecom",
                            f"""
                            SELECT i.id, i.infra_name AS name, i.infra_type,
                                   i.latitude AS lat, i.longitude AS lon
                            FROM telecom.infrastructure i
                            JOIN {table} e ON e.id = %s
                            WHERE i.geom IS NOT NULL AND ST_Intersects(i.geom, e.geom)
                              AND LOWER(COALESCE(i.infra_type,'')) NOT LIKE '%%fttx%%'
                              AND LOWER(COALESCE(i.infra_type,'')) NOT LIKE '%%fibre%%'
                              AND LOWER(COALESCE(i.infra_type,'')) NOT LIKE '%%fiber%%'
                            LIMIT 300
                            """,
                        ),
                        (
                            "fiber",
                            f"""
                            SELECT i.id, i.infra_name AS name, i.infra_type,
                                   i.latitude AS lat, i.longitude AS lon
                            FROM telecom.infrastructure i
                            JOIN {table} e ON e.id = %s
                            WHERE i.geom IS NOT NULL AND ST_Intersects(i.geom, e.geom)
                              AND (
                                LOWER(COALESCE(i.infra_type,'')) LIKE '%%fttx%%'
                                OR LOWER(COALESCE(i.infra_type,'')) LIKE '%%fibre%%'
                                OR LOWER(COALESCE(i.infra_type,'')) LIKE '%%fiber%%'
                              )
                            LIMIT 200
                            """,
                        ),
                    ):
                        try:
                            cur.execute(sql, (db_id,))
                            for r in cur.fetchall():
                                if r.get("lat") is None or r.get("lon") is None:
                                    continue
                                _add(
                                    kind,
                                    {"type": "Point", "coordinates": [float(r["lon"]), float(r["lat"])]},
                                    {"id": r["id"], "name": r.get("name"), "type": r.get("infra_type")},
                                )
                        except Exception:
                            pass
                    try:
                        cur.execute(
                            f"""
                            SELECT r.id, r.nom,
                                   ST_AsGeoJSON(ST_Intersection(r.geom, e.geom))::json AS geometry
                            FROM transport.routes r
                            JOIN {table} e ON e.id = %s
                            WHERE r.geom IS NOT NULL AND ST_Intersects(r.geom, e.geom)
                            LIMIT 200
                            """,
                            (db_id,),
                        )
                        for r in cur.fetchall():
                            if r.get("geometry"):
                                _add("route", r["geometry"], {"id": r["id"], "name": r.get("nom")})
                    except Exception:
                        pass
                    try:
                        cur.execute(
                            f"""
                            SELECT nl.id, nl.line_name,
                                   ST_AsGeoJSON(ST_Intersection(nl.geom, e.geom))::json AS geometry
                            FROM telecom.network_lines nl
                            JOIN {table} e ON e.id = %s
                            WHERE nl.geom IS NOT NULL AND ST_Intersects(nl.geom, e.geom)
                            LIMIT 200
                            """,
                            (db_id,),
                        )
                        for r in cur.fetchall():
                            if r.get("geometry"):
                                _add("fiber_line", r["geometry"], {"id": r["id"], "name": r.get("line_name")})
                    except Exception:
                        pass
    except Exception as exc:  # noqa: BLE001
        layer_counts["_error"] = str(exc)

    legend = symbology.build_legend_items(layer_counts, only_visible=True)
    return {
        "_meta": {
            "title": f"Carte — {entity.get('name')}",
            "feature_count": len(features),
            "layer_counts": layer_counts,
            "engine_version": ENGINE_VERSION,
            "data_first": True,
            "level": level,
        },
        "entity": {"type": entity.get("type"), "id": entity.get("id"), "name": entity.get("name")},
        "legend": legend,
        "symbology": symbology.registry_payload(),
        "geojson": {"type": "FeatureCollection", "features": features},
    }


def _infra_counts(entity: dict[str, Any]) -> dict[str, Any]:
    if entity.get("type") == "territoire":
        from api.services import territorial_intelligence_service as ti

        profile = ti.build_territorial_profile(entity["id"], light=True)
        if not profile:
            return {}
        sections = profile.get("sections") or {}
        return {
            "programs": sections.get("programs"),
            "public_services": sections.get("public_services"),
            "telecom": sections.get("telecom") or sections.get("connectivity"),
            "priority": sections.get("priority"),
            "sources": profile.get("sources"),
            "confidence": (profile.get("profile") or {}).get("confidence_level"),
        }
    # Compteurs spatiaux simples
    if DATA_MODE != "db" or not entity.get("db_id"):
        return {"note": "Compteurs multi-échelle disponibles en mode DB"}
    table = TABLE_BY_LEVEL[entity["type"]]
    db_id = entity["db_id"]
    out: dict[str, Any] = {}
    try:
        with connect_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                queries = {
                    "health": f"SELECT COUNT(*)::int AS n FROM health.health_facilities f JOIN {table} e ON e.id=%s WHERE f.geom IS NOT NULL AND ST_Within(f.geom, e.geom)",
                    "telecom": f"SELECT COUNT(*)::int AS n FROM telecom.infrastructure i JOIN {table} e ON e.id=%s WHERE i.geom IS NOT NULL AND ST_Intersects(i.geom, e.geom)",
                    "routes": f"SELECT COUNT(*)::int AS n FROM transport.routes r JOIN {table} e ON e.id=%s WHERE r.geom IS NOT NULL AND ST_Intersects(r.geom, e.geom)",
                }
                for key, sql in queries.items():
                    try:
                        cur.execute(sql, (db_id,))
                        n = (cur.fetchone() or {}).get("n")
                        out[key] = _field(n, "operational" if n is not None else "unavailable", source="postgis", method="spatial_count")
                    except Exception:
                        out[key] = _field(None, "unavailable", source="postgis", note="Couche non interrogeable")
                children = list_children(entity)
                out["children_count"] = _field(len(children), "operational", source=TABLE_BY_LEVEL.get(CHILD_LEVEL.get(entity["type"]) or "", "postgis"), method="parent_id_fk")
    except Exception as exc:  # noqa: BLE001
        out["error"] = str(exc)
    return out


def build_entity_intelligence(ref: str) -> dict[str, Any] | None:
    entity = resolve_entity(ref)
    if not entity:
        return None

    breadcrumb = build_breadcrumb(entity)
    children = list_children(entity)
    population = build_population_coverage(entity)
    # Carte (GeoJSON + légende dynamique) : GET /entities/{id}/map — non recalculée ici.
    map_summary = {
        "legend": [],
        "layer_counts": {},
        "feature_count": None,
        "endpoint": f"/api/territorial-intelligence/entities/{entity.get('id')}/map",
    }
    infra = _infra_counts(entity)

    # Profil territoire : conserver le contrat historique en enveloppe
    territory_profile = None
    if entity.get("type") == "territoire":
        from api.services import territorial_intelligence_service as ti

        territory_profile = ti.build_territorial_profile(entity["id"])

    decision_questions = {
        "where": f"{entity.get('admin_type') or entity.get('type')} — {entity.get('name')}",
        "population": population.get("population"),
        "coverage": {
            "covered": population.get("population_covered"),
            "uncovered": population.get("population_uncovered"),
            "rate": population.get("coverage_rate_pct"),
        },
        "services": infra.get("public_services") or {"health": infra.get("health")},
        "infrastructure": {
            "telecom": infra.get("telecom"),
            "routes": infra.get("routes"),
        },
        "children": children[:50],
        "priority": infra.get("priority"),
        "action": None
        if entity.get("type") not in {"territoire"}
        else ((territory_profile or {}).get("sections") or {}).get("recommendations"),
    }

    return {
        "_meta": {
            "engine": ENGINE_VERSION,
            "data_first": True,
            "entity_type": entity.get("type"),
        },
        "entity": {
            "type": entity.get("type"),
            "id": entity.get("id"),
            "name": entity.get("name"),
            "code": entity.get("code"),
            "admin_type": entity.get("admin_type"),
            "parent": entity.get("parent"),
            "hierarchy": entity.get("hierarchy"),
            "fdsu_zone": entity.get("fdsu_zone") or (entity.get("hierarchy") or {}).get("fdsu_zone"),
            "centroid": entity.get("centroid"),
            "has_geometry": entity.get("has_geometry"),
            "sources": entity.get("sources"),
        },
        "breadcrumb": breadcrumb,
        "population": population.get("population"),
        "coverage": {
            "population_covered": population.get("population_covered"),
            "population_uncovered": population.get("population_uncovered"),
            "localities_covered": population.get("localities_covered"),
            "localities_uncovered": population.get("localities_uncovered"),
            "coverage_rate_pct": population.get("coverage_rate_pct"),
            "ndci": population.get("ndci"),
            "status": population.get("status"),
            "double_counting_guard": population.get("double_counting_guard"),
            "note": population.get("note"),
        },
        "administrative": {
            "children": children,
            "children_level": CHILD_LEVEL.get(entity.get("type") or ""),
            "children_count": len(children),
        },
        "programs": infra.get("programs"),
        "telecom": infra.get("telecom"),
        "fiber": None,
        "health": (infra.get("public_services") or {}).get("etablissements_sante") if infra.get("public_services") else infra.get("health"),
        "routes": infra.get("routes"),
        "ccn": (infra.get("programs") or {}).get("ccn") if infra.get("programs") else None,
        "score": (infra.get("priority") or {}).get("score") if isinstance(infra.get("priority"), dict) else infra.get("priority"),
        "confidence": infra.get("confidence")
        or (
            (population.get("population") or {}).get("confidence")
            if isinstance(population.get("population"), dict)
            else "medium"
        ),
        "sources": list(
            dict.fromkeys(
                (entity.get("sources") or [])
                + ["cartography_symbology_registry_v1", "data/coverage"]
            )
        ),
        "children": children,
        "map": map_summary,
        # GeoJSON volontairement omis ici pour accélérer le drill-down — utiliser GET .../map
        "map_payload": None,
        "explainability": {
            "decision_questions": decision_questions,
            "limits": population.get("note")
            or "Les indicateurs sont sourcés ; les absences sont déclarées sans invention.",
        },
        # Compat UI historique
        "profile": (territory_profile or {}).get("profile")
        or {
            "territory_id": entity.get("id"),
            "territory_name": entity.get("name"),
            "province": (entity.get("hierarchy") or {}).get("province"),
            "fdsu_zone": entity.get("fdsu_zone"),
            "population": population.get("population"),
            "confidence_level": infra.get("confidence") or "medium",
            "entity_type": entity.get("type"),
            "admin_type": entity.get("admin_type"),
        },
        "sections": (territory_profile or {}).get("sections")
        or {
            "coverage": {
                "population_covered": population.get("population_covered"),
                "population_uncovered": population.get("population_uncovered"),
                "localities_covered": population.get("localities_covered"),
                "localities_uncovered": population.get("localities_uncovered"),
                "coverage_rate_pct": population.get("coverage_rate_pct"),
            },
            "administrative": {"children": children},
            "public_services": {"etablissements_sante": infra.get("health")},
            "synthesis": {
                "headline": f"{entity.get('admin_type') or entity.get('type')} — {entity.get('name')}",
                "body": "Synthèse multi-échelle Data First — indicateurs adaptés au niveau.",
            },
        },
    }
