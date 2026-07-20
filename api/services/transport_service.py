"""Référentiel Transport & Accessibility Intelligence.

Source d'exploitation : transport.routes (PostGIS).
Le KMZ brut n'est jamais lu par l'API de production.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from psycopg2.extras import RealDictCursor

from api.config import connect_db

PROJECT_ROOT = Path(__file__).resolve().parents[2]
QUALITY_FILE = PROJECT_ROOT / "data" / "sectoral" / "transport" / "quality" / "routes_quality_report.json"
MANIFEST_FILE = PROJECT_ROOT / "data" / "sectoral" / "transport" / "manifest.json"
ENGINE_VERSION = "transport-accessibility-1.0.0"

# ---------------------------------------------------------------------------
# Score d'accessibilité — FORMULE DOCUMENTÉE (aucune boîte noire)
# ---------------------------------------------------------------------------
# score = clamp(0, 100, distance_component + type_component)
#
# distance_component (0–80) :
#   d <= 500 m     → 80
#   d <= 2 000 m   → 65
#   d <= 5 000 m   → 50
#   d <= 15 000 m  → 35
#   d > 15 000 m   → 20
#   pas de route   → insuffisant (pas de score)
#
# type_component (0–20) :
#   Route primaire / Voie rapide → 20
#   Route secondaire             → 12
#   Autre / Non renseigné        → 5
#
# Classes affichées :
#   >= 80 excellent | >= 60 bon | >= 40 moyen | >= 20 difficile | < 20 critique
# ---------------------------------------------------------------------------

ACCESSIBILITY_FORMULA = {
    "version": "1.0",
    "formula": "clamp(0,100, distance_component + type_component)",
    "distance_component": [
        {"max_m": 500, "points": 80},
        {"max_m": 2000, "points": 65},
        {"max_m": 5000, "points": 50},
        {"max_m": 15000, "points": 35},
        {"max_m": None, "points": 20},
    ],
    "type_component": {
        "Route primaire": 20,
        "Voie rapide": 20,
        "Route secondaire": 12,
        "default": 5,
    },
    "classes": [
        {"min": 80, "id": "excellent", "label": "Accessibilité excellente"},
        {"min": 60, "id": "good", "label": "Accessibilité bonne"},
        {"min": 40, "id": "medium", "label": "Accessibilité moyenne"},
        {"min": 20, "id": "hard", "label": "Accessibilité difficile"},
        {"min": 0, "id": "critical", "label": "Accessibilité critique"},
    ],
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _serialize(row: dict[str, Any]) -> dict[str, Any]:
    payload = dict(row)
    for key in ("created_at", "updated_at", "date_import", "date_maj_source", "computed_at", "started_at", "finished_at"):
        value = payload.get(key)
        if value is not None and hasattr(value, "isoformat"):
            payload[key] = value.isoformat()
    if payload.get("properties") is None:
        payload["properties"] = {}
    return payload


def _table_ready() -> bool:
    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'transport' AND table_name = 'routes'
                    """
                )
                return cur.fetchone() is not None
    except Exception:
        return False


def distance_component(distance_m: float) -> int:
    if distance_m <= 500:
        return 80
    if distance_m <= 2000:
        return 65
    if distance_m <= 5000:
        return 50
    if distance_m <= 15000:
        return 35
    return 20


def type_component(type_route: str | None) -> int:
    mapping = ACCESSIBILITY_FORMULA["type_component"]
    key = (type_route or "").strip()
    return int(mapping.get(key, mapping["default"]))


def accessibility_class(score: float) -> dict[str, str]:
    for item in ACCESSIBILITY_FORMULA["classes"]:
        if score >= item["min"]:
            return {"id": item["id"], "label": item["label"]}
    return {"id": "critical", "label": "Accessibilité critique"}


def compute_accessibility_score(distance_m: float | None, type_route: str | None) -> dict[str, Any]:
    if distance_m is None:
        return {
            "score": None,
            "display": "Données insuffisantes",
            "class_id": "insufficient",
            "class_label": "Données insuffisantes",
            "justification": "Aucune route principale trouvée à proximité (référentiel transport vide ou site non géoréférencé).",
            "components": {},
            "formula": ACCESSIBILITY_FORMULA,
        }
    d_pts = distance_component(float(distance_m))
    t_pts = type_component(type_route)
    score = max(0, min(100, d_pts + t_pts))
    klass = accessibility_class(score)
    return {
        "score": score,
        "display": str(score),
        "class_id": klass["id"],
        "class_label": klass["label"],
        "justification": (
            f"Distance {round(float(distance_m))} m → +{d_pts} pts ; "
            f"type « {type_route or 'Non renseigné'} » → +{t_pts} pts ; "
            f"score = {d_pts}+{t_pts} = {score}/100 ({klass['label']})."
        ),
        "components": {
            "distance_m": round(float(distance_m), 1),
            "distance_points": d_pts,
            "type_route": type_route,
            "type_points": t_pts,
        },
        "formula": ACCESSIBILITY_FORMULA,
    }


def get_manifest() -> dict[str, Any]:
    if MANIFEST_FILE.exists():
        try:
            return json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "_meta": {"version": ENGINE_VERSION, "updated_at": _now()},
        "status": "manifest_missing",
        "note": "Exécuter scripts/import_routes_principales_kmz.py",
    }


def get_quality_report() -> dict[str, Any]:
    """Rapport qualité — fichier pipeline + contrôles PostGIS si disponibles."""
    file_report: dict[str, Any] = {}
    if QUALITY_FILE.exists():
        try:
            file_report = json.loads(QUALITY_FILE.read_text(encoding="utf-8"))
        except Exception:
            file_report = {}

    db_checks: list[dict[str, Any]] = []
    db_stats: dict[str, Any] = {}
    if _table_ready():
        try:
            with connect_db() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        """
                        SELECT check_code, check_label, severity, count_value, details, computed_at
                        FROM transport.quality_checks
                        ORDER BY id
                        """
                    )
                    db_checks = [_serialize(dict(r)) for r in cur.fetchall()]
                    cur.execute(
                        """
                        SELECT
                            COUNT(*)::int AS routes_total,
                            COUNT(*) FILTER (WHERE nom IS NULL OR nom = '')::int AS unnamed,
                            COUNT(*) FILTER (WHERE NOT ST_IsValid(geom))::int AS invalid_geom,
                            ROUND(SUM(COALESCE(longueur_m, ST_Length(geom::geography)))::numeric / 1000, 2) AS length_km
                        FROM transport.routes
                        """
                    )
                    db_stats = _serialize(dict(cur.fetchone() or {}))
        except Exception as exc:
            db_stats = {"error": str(exc)}

    return {
        "_meta": {"version": ENGINE_VERSION, "updated_at": _now()},
        "pipeline_report": file_report,
        "database_checks": db_checks,
        "database_stats": db_stats,
    }


def get_statistics() -> dict[str, Any]:
    if not _table_ready():
        return {
            "_meta": {"version": ENGINE_VERSION, "status": "unavailable"},
            "routes_total": 0,
            "note": "Table transport.routes absente — lancer le pipeline --db",
        }
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    COUNT(*)::int AS routes_total,
                    COUNT(DISTINCT type_route)::int AS types_count,
                    ROUND(SUM(COALESCE(longueur_m, 0))::numeric / 1000, 2) AS length_km,
                    COUNT(*) FILTER (WHERE nom IS NULL OR nom = '')::int AS unnamed
                FROM transport.routes
                """
            )
            totals = dict(cur.fetchone() or {})
            cur.execute(
                """
                SELECT type_route, COUNT(*)::int AS count
                FROM transport.routes
                GROUP BY type_route
                ORDER BY count DESC
                """
            )
            by_type = [dict(r) for r in cur.fetchall()]
    return {
        "_meta": {"version": ENGINE_VERSION, "updated_at": _now()},
        **totals,
        "by_type": by_type,
    }


def list_routes(skip: int = 0, limit: int = 5000, type_route: str | None = None) -> list[dict[str, Any]]:
    if not _table_ready():
        return []
    filters = []
    params: list[Any] = []
    if type_route:
        filters.append("type_route = %s")
        params.append(type_route)
    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    query = f"""
        SELECT
            id, source_id, nom, type_route, categorie, etat, revetement, numero,
            source, source_file, longueur_m, date_import, date_maj_source, properties,
            CASE WHEN geom IS NULL THEN NULL ELSE ST_AsGeoJSON(geom)::json END AS geometry
        FROM transport.routes
        {where}
        ORDER BY id
        OFFSET %s LIMIT %s
    """
    params.extend([skip, limit])
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, tuple(params))
            return [_serialize(dict(r)) for r in cur.fetchall()]


def routes_layer(limit: int = 8000) -> dict[str, Any]:
    rows = list_routes(skip=0, limit=limit)
    features = []
    for row in rows:
        geom = row.get("geometry")
        if not geom:
            continue
        features.append(
            {
                "type": "Feature",
                "id": row.get("id"),
                "geometry": geom,
                "properties": {
                    "id": row.get("id"),
                    "nom": row.get("nom") or "Sans nom",
                    "type": row.get("type_route"),
                    "longueur_m": row.get("longueur_m"),
                    "longueur_km": round((row.get("longueur_m") or 0) / 1000, 2),
                    "source": row.get("source"),
                    "etat": row.get("etat") or "Non renseigné",
                    "categorie": row.get("categorie"),
                    "tooltip_kind": "transport_route",
                },
            }
        )
    return {
        "type": "FeatureCollection",
        "features": features,
        "_meta": {
            "layer": "routes_principales",
            "count": len(features),
            "source": "transport.routes",
            "version": ENGINE_VERSION,
        },
    }


def nearest_road(lon: float, lat: float, max_distance_m: float = 50000) -> dict[str, Any] | None:
    """Route principale la plus proche d'un point (KNN GiST geometry + distance geography).

    Évite ``ORDER BY geom::geography <-> …`` / ``ST_DWithin(geography)`` qui forcent
    un Seq Scan (~1,5 s). Le plan GiST ``geom <->`` reste ~ms ; la distance métrique
    et le filtre rayon restent en geography sur la seule ligne candidate.
    """
    if not _table_ready():
        return None
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                WITH nearest AS (
                    SELECT
                        r.id,
                        r.source_id,
                        r.nom,
                        r.type_route,
                        r.categorie,
                        r.etat,
                        r.source,
                        r.longueur_m,
                        ST_Distance(
                            r.geom::geography,
                            ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                        ) AS distance_m,
                        ST_X(ST_ClosestPoint(r.geom, ST_SetSRID(ST_MakePoint(%s, %s), 4326))) AS closest_lon,
                        ST_Y(ST_ClosestPoint(r.geom, ST_SetSRID(ST_MakePoint(%s, %s), 4326))) AS closest_lat
                    FROM transport.routes r
                    WHERE r.geom IS NOT NULL
                    ORDER BY r.geom <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)
                    LIMIT 1
                )
                SELECT * FROM nearest
                WHERE distance_m <= %s
                """,
                (lon, lat, lon, lat, lon, lat, lon, lat, max_distance_m),
            )
            row = cur.fetchone()
            return _serialize(dict(row)) if row else None


def site_accessibility(site_id: int | None = None, lon: float | None = None, lat: float | None = None) -> dict[str, Any]:
    """Accessibilité d'un site FDSU (par id ou coordonnées)."""
    coords: tuple[float, float] | None = None
    site_meta: dict[str, Any] = {}
    if site_id is not None:
        with connect_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, site_code, site_name, province, territoire, latitude, longitude
                    FROM programs.fdsu_sites
                    WHERE id = %s
                    """,
                    (site_id,),
                )
                site = cur.fetchone()
                if not site:
                    return {
                        "_meta": {"version": ENGINE_VERSION},
                        "status": "site_not_found",
                        "display": "Données insuffisantes",
                    }
                site_meta = _serialize(dict(site))
                if site.get("longitude") is not None and site.get("latitude") is not None:
                    coords = (float(site["longitude"]), float(site["latitude"]))
    elif lon is not None and lat is not None:
        coords = (float(lon), float(lat))

    if not coords:
        return {
            "_meta": {"version": ENGINE_VERSION, "updated_at": _now()},
            "site": site_meta,
            "nearest_road": None,
            "accessibility": compute_accessibility_score(None, None),
            "status": "insufficient",
        }

    road = nearest_road(coords[0], coords[1])
    scored = compute_accessibility_score(
        float(road["distance_m"]) if road and road.get("distance_m") is not None else None,
        (road or {}).get("type_route"),
    )
    return {
        "_meta": {"version": ENGINE_VERSION, "updated_at": _now()},
        "site": site_meta or {"longitude": coords[0], "latitude": coords[1]},
        "nearest_road": road,
        "accessibility": scored,
        "status": "ok" if scored.get("score") is not None else "insufficient",
    }


def accessibility_by_province(site_limit: int = 800) -> dict[str, dict[str, Any]]:
    """Agrégat provincial réel : moyenne des scores sites géoréférencés (échantillon borné)."""
    if not _table_ready():
        return {}
    try:
        with connect_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, province, longitude, latitude
                    FROM programs.fdsu_sites
                    WHERE longitude IS NOT NULL AND latitude IS NOT NULL
                      AND province IS NOT NULL AND TRIM(province) <> ''
                    ORDER BY id
                    LIMIT %s
                    """,
                    (site_limit,),
                )
                sites = [dict(r) for r in cur.fetchall()]
    except Exception:
        return {}

    buckets: dict[str, list[float]] = {}
    for site in sites:
        try:
            road = nearest_road(float(site["longitude"]), float(site["latitude"]))
            if not road:
                continue
            scored = compute_accessibility_score(road.get("distance_m"), road.get("type_route"))
            if scored.get("score") is None:
                continue
            key = " ".join(str(site.get("province") or "").strip().lower().split())
            buckets.setdefault(key, []).append(float(scored["score"]))
        except Exception:
            continue

    result: dict[str, dict[str, Any]] = {}
    for key, values in buckets.items():
        if not values:
            continue
        avg = round(sum(values) / len(values), 1)
        result[key] = {
            "province": key,
            "avg_score": avg,
            "sites_scored": len(values),
            "class_id": accessibility_class(avg)["id"],
        }
    return result


def get_panel_payload(site_id: int | None = None) -> dict[str, Any]:
    stats = get_statistics()
    accessibility = site_accessibility(site_id=site_id) if site_id else None
    return {
        "_meta": {"version": ENGINE_VERSION, "updated_at": _now()},
        "title": "Transport & Accessibilité",
        "statistics": stats,
        "formula": ACCESSIBILITY_FORMULA,
        "site_accessibility": accessibility,
        "actions": [
            {"id": "layer", "label": "Afficher les routes principales", "hash": "cartographie"},
        ],
    }
