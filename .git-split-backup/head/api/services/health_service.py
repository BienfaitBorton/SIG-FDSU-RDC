"""Référentiel Santé v1.0 — structures sanitaires (structure sans données fictives)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from api.config import connect_db
from psycopg2.extras import Json, RealDictCursor

HOSPITAL_TYPES = ("HGR", "HOSPITAL", "CH")
HEALTH_CENTER_TYPES = ("CS", "CSR", "CM", "CLINIC", "POLYCLINIC")
HEALTH_POST_TYPES = ("PS", "DISP", "SSC", "MAT")


def _serialize_row(row: dict[str, Any]) -> dict[str, Any]:
    payload = dict(row)
    for key in ("created_at", "updated_at", "computed_at"):
        value = payload.get(key)
        if value is not None and hasattr(value, "isoformat"):
            payload[key] = value.isoformat()
    if payload.get("properties") is None:
        payload["properties"] = {}
    return payload


def list_facility_types() -> list[dict[str, Any]]:
    query = """
        SELECT id, code, name, description, category, symbology
        FROM health.health_facility_types
        ORDER BY code
    """
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return [_serialize_row(dict(row)) for row in cur.fetchall()]


def list_facilities(
    facility_type_code: str | None = None,
    province_name: str | None = None,
    territory_name: str | None = None,
    skip: int = 0,
    limit: int = 500,
) -> list[dict[str, Any]]:
    filters: list[str] = []
    params: list[Any] = []
    if facility_type_code:
        filters.append("f.facility_type_code = %s")
        params.append(facility_type_code.upper())
    if province_name:
        filters.append("f.province_name ILIKE %s")
        params.append(f"%{province_name}%")
    if territory_name:
        filters.append("f.territory_name ILIKE %s")
        params.append(f"%{territory_name}%")
    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    query = f"""
        SELECT
            f.id, f.official_code, f.name, f.facility_type_code,
            t.name AS facility_type_name,
            f.province_name, f.territory_name, f.collectivity_name,
            f.groupement_name, f.locality_name, f.manager_type, f.level,
            f.population_served, f.has_electricity, f.has_internet,
            f.data_source, f.observations, f.properties,
            f.created_at, f.updated_at,
            CASE WHEN f.geom IS NULL THEN NULL ELSE ST_AsGeoJSON(f.geom)::json END AS geometry,
            CASE WHEN f.geom IS NULL THEN NULL ELSE ST_Y(f.geom) END AS latitude,
            CASE WHEN f.geom IS NULL THEN NULL ELSE ST_X(f.geom) END AS longitude
        FROM health.health_facilities f
        LEFT JOIN health.health_facility_types t ON t.code = f.facility_type_code
        {where_clause}
        ORDER BY f.name
        OFFSET %s LIMIT %s
    """
    params.extend([skip, limit])
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, tuple(params))
            return [_serialize_row(dict(row)) for row in cur.fetchall()]


def get_facility(facility_id: int) -> dict[str, Any] | None:
    query = """
        SELECT
            f.id, f.official_code, f.name, f.facility_type_code,
            t.name AS facility_type_name,
            f.province_name, f.territory_name, f.collectivity_name,
            f.groupement_name, f.locality_name, f.manager_type, f.level,
            f.population_served, f.has_electricity, f.has_internet,
            f.data_source, f.observations, f.properties,
            f.created_at, f.updated_at,
            CASE WHEN f.geom IS NULL THEN NULL ELSE ST_AsGeoJSON(f.geom)::json END AS geometry,
            CASE WHEN f.geom IS NULL THEN NULL ELSE ST_Y(f.geom) END AS latitude,
            CASE WHEN f.geom IS NULL THEN NULL ELSE ST_X(f.geom) END AS longitude
        FROM health.health_facilities f
        LEFT JOIN health.health_facility_types t ON t.code = f.facility_type_code
        WHERE f.id = %s
        LIMIT 1
    """
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (facility_id,))
            row = cur.fetchone()
            return _serialize_row(dict(row)) if row else None


def search_facilities(
    q: str | None = None,
    facility_type_code: str | None = None,
    province_name: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    filters: list[str] = []
    params: list[Any] = []
    if q:
        filters.append("(f.name ILIKE %s OR f.official_code ILIKE %s OR f.locality_name ILIKE %s)")
        pattern = f"%{q}%"
        params.extend([pattern, pattern, pattern])
    if facility_type_code:
        filters.append("f.facility_type_code = %s")
        params.append(facility_type_code.upper())
    if province_name:
        filters.append("f.province_name ILIKE %s")
        params.append(f"%{province_name}%")
    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    query = f"""
        SELECT
            f.id, f.official_code, f.name, f.facility_type_code,
            t.name AS facility_type_name,
            f.province_name, f.territory_name, f.locality_name,
            CASE WHEN f.geom IS NULL THEN NULL ELSE ST_Y(f.geom) END AS latitude,
            CASE WHEN f.geom IS NULL THEN NULL ELSE ST_X(f.geom) END AS longitude
        FROM health.health_facilities f
        LEFT JOIN health.health_facility_types t ON t.code = f.facility_type_code
        {where_clause}
        ORDER BY f.name
        LIMIT %s
    """
    params.append(limit)
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, tuple(params))
            return [_serialize_row(dict(row)) for row in cur.fetchall()]


def nearest_facility(
    latitude: float,
    longitude: float,
    facility_type_code: str | None = None,
    radius_m: float = 50_000,
    limit: int = 10,
) -> dict[str, Any]:
    total_with_geom = _count_facilities_with_geometry()
    if total_with_geom == 0:
        return {
            "latitude": latitude,
            "longitude": longitude,
            "radius_m": radius_m,
            "facilities": [],
            "message": "aucune donnée santé disponible",
            "data_available": False,
        }

    filters = ["f.geom IS NOT NULL", "ST_DWithin(origin.geom, f.geom::geography, %s)"]
    params: list[Any] = [longitude, latitude, radius_m]
    if facility_type_code:
        filters.append("f.facility_type_code = %s")
        params.append(facility_type_code.upper())
    where_clause = " AND ".join(filters)
    params.append(limit)

    query = f"""
        WITH origin AS (
            SELECT ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography AS geom
        )
        SELECT
            f.id, f.official_code, f.name, f.facility_type_code,
            t.name AS facility_type_name,
            f.province_name, f.territory_name,
            ST_Distance(origin.geom, f.geom::geography) AS distance_m
        FROM origin
        JOIN health.health_facilities f ON TRUE
        LEFT JOIN health.health_facility_types t ON t.code = f.facility_type_code
        WHERE {where_clause}
        ORDER BY distance_m
        LIMIT %s
    """
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, tuple(params))
            facilities = [_serialize_row(dict(row)) for row in cur.fetchall()]

    return {
        "latitude": latitude,
        "longitude": longitude,
        "radius_m": radius_m,
        "facilities": facilities,
        "data_available": True,
        "message": None if facilities else "Aucune structure sanitaire dans le rayon",
    }


def _count_facilities_with_geometry() -> int:
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM health.health_facilities WHERE geom IS NOT NULL")
            return int(cur.fetchone()[0])


def _distribution_counts(cur) -> tuple[dict[str, int], dict[str, int]]:
    cur.execute(
        """
        SELECT COALESCE(facility_type_code, 'OTHER') AS code, COUNT(*) AS count
        FROM health.health_facilities
        GROUP BY 1
        ORDER BY count DESC, code
        """
    )
    by_type = {row["code"]: int(row["count"]) for row in cur.fetchall()}
    cur.execute(
        """
        SELECT COALESCE(NULLIF(TRIM(province_name), ''), 'Non renseigné') AS province, COUNT(*) AS count
        FROM health.health_facilities
        GROUP BY 1
        ORDER BY count DESC, province
        """
    )
    by_province = {row["province"]: int(row["count"]) for row in cur.fetchall()}
    return by_type, by_province


def _quality_metrics(cur, total: int, with_geom: int) -> dict[str, Any]:
    cur.execute(
        """
        SELECT COUNT(*) AS count
        FROM health.health_facilities
        WHERE name IS NULL OR TRIM(name) = '' OR name = 'Structure sans nom'
        """
    )
    missing_names = int(cur.fetchone()["count"])
    cur.execute(
        """
        SELECT COUNT(*) AS count
        FROM health.health_facilities
        WHERE facility_type_code IS NULL OR facility_type_code = 'OTHER'
        """
    )
    missing_types = int(cur.fetchone()["count"])
    cur.execute(
        """
        SELECT COUNT(*) AS count
        FROM (
            SELECT ROUND(ST_X(geom)::numeric, 5), ROUND(ST_Y(geom)::numeric, 5), lower(trim(name))
            FROM health.health_facilities
            WHERE geom IS NOT NULL
            GROUP BY 1, 2, 3
            HAVING COUNT(*) > 1
        ) duplicates
        """
    )
    duplicate_groups = int(cur.fetchone()["count"])
    cur.execute(
        """
        SELECT COALESCE(SUM(cnt - 1), 0) AS count
        FROM (
            SELECT COUNT(*) AS cnt
            FROM health.health_facilities
            WHERE geom IS NOT NULL
            GROUP BY ROUND(ST_X(geom)::numeric, 5), ROUND(ST_Y(geom)::numeric, 5), lower(trim(name))
            HAVING COUNT(*) > 1
        ) duplicates
        """
    )
    potential_duplicates = int(cur.fetchone()["count"])
    if total <= 0:
        quality_score = 0.0
    else:
        geom_ratio = with_geom / total
        named_ratio = (total - missing_names) / total
        typed_ratio = (total - missing_types) / total
        duplicate_penalty = min(potential_duplicates / total, 0.2)
        quality_score = round(
            max(0.0, (geom_ratio * 0.5 + named_ratio * 0.25 + typed_ratio * 0.25 - duplicate_penalty) * 100),
            2,
        )
    return {
        "missing_names": missing_names,
        "missing_types": missing_types,
        "duplicate_groups": duplicate_groups,
        "potential_duplicates": potential_duplicates,
        "quality_score": quality_score,
    }


def compute_statistics(scope_type: str = "national", scope_name: str = "RDC") -> dict[str, Any]:
    query = """
        SELECT
            COUNT(*) AS total_facilities,
            COUNT(*) FILTER (WHERE facility_type_code = ANY(%s)) AS hospitals,
            COUNT(*) FILTER (WHERE facility_type_code = ANY(%s)) AS health_centers,
            COUNT(*) FILTER (WHERE facility_type_code = ANY(%s)) AS health_posts,
            COUNT(*) FILTER (WHERE geom IS NOT NULL) AS facilities_with_geometry,
            COUNT(*) FILTER (WHERE geom IS NULL) AS facilities_without_geometry,
            COUNT(*) FILTER (WHERE has_electricity IS TRUE) AS facilities_with_electricity,
            COUNT(*) FILTER (WHERE has_internet IS TRUE) AS facilities_with_internet
        FROM health.health_facilities
    """
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                query,
                (list(HOSPITAL_TYPES), list(HEALTH_CENTER_TYPES), list(HEALTH_POST_TYPES)),
            )
            stats = dict(cur.fetchone())
            by_type, by_province = _distribution_counts(cur)
            quality = _quality_metrics(
                cur,
                int(stats["total_facilities"]),
                int(stats["facilities_with_geometry"]),
            )
            details = {
                "status": "imported" if int(stats["total_facilities"]) > 0 else "empty",
                "hospital_types": list(HOSPITAL_TYPES),
                "health_center_types": list(HEALTH_CENTER_TYPES),
                "health_post_types": list(HEALTH_POST_TYPES),
                "by_type": by_type,
                "by_province": by_province,
                "missing_names": quality["missing_names"],
                "missing_types": quality["missing_types"],
                "potential_duplicates": quality["potential_duplicates"],
                "quality_score": quality["quality_score"],
                "import_ready": True,
                "formats": ["csv", "excel", "geojson", "kmz"],
            }
            cur.execute(
                """
                INSERT INTO health.health_statistics (
                    scope_type, scope_name, total_facilities, hospitals, health_centers,
                    health_posts, facilities_with_geometry, facilities_without_geometry,
                    facilities_with_electricity, facilities_with_internet, computed_at, details
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
                """,
                (
                    scope_type,
                    scope_name,
                    int(stats["total_facilities"]),
                    int(stats["hospitals"]),
                    int(stats["health_centers"]),
                    int(stats["health_posts"]),
                    int(stats["facilities_with_geometry"]),
                    int(stats["facilities_without_geometry"]),
                    int(stats["facilities_with_electricity"]),
                    int(stats["facilities_with_internet"]),
                    Json(details),
                ),
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS health.health_quality_dashboard (
                    id BIGSERIAL PRIMARY KEY,
                    scope_type VARCHAR(64) NOT NULL DEFAULT 'national',
                    scope_name VARCHAR(255) NOT NULL DEFAULT 'RDC',
                    quality_score NUMERIC(6,2) NOT NULL DEFAULT 0,
                    total_facilities INTEGER NOT NULL DEFAULT 0,
                    facilities_with_geometry INTEGER NOT NULL DEFAULT 0,
                    facilities_without_geometry INTEGER NOT NULL DEFAULT 0,
                    missing_names INTEGER NOT NULL DEFAULT 0,
                    missing_types INTEGER NOT NULL DEFAULT 0,
                    potential_duplicates INTEGER NOT NULL DEFAULT 0,
                    details JSONB NOT NULL DEFAULT '{}'::jsonb,
                    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cur.execute(
                """
                INSERT INTO health.health_quality_dashboard (
                    scope_type, scope_name, quality_score, total_facilities,
                    facilities_with_geometry, facilities_without_geometry,
                    missing_names, missing_types, potential_duplicates, details, computed_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                """,
                (
                    scope_type,
                    scope_name,
                    quality["quality_score"],
                    int(stats["total_facilities"]),
                    int(stats["facilities_with_geometry"]),
                    int(stats["facilities_without_geometry"]),
                    quality["missing_names"],
                    quality["missing_types"],
                    quality["potential_duplicates"],
                    Json(details),
                ),
            )
        conn.commit()

    return get_statistics(scope_type=scope_type, scope_name=scope_name)


def get_statistics(scope_type: str = "national", scope_name: str = "RDC") -> dict[str, Any]:
    query = """
        SELECT
            id, scope_type, scope_name, total_facilities, hospitals, health_centers,
            health_posts, facilities_with_geometry, facilities_without_geometry,
            facilities_with_electricity, facilities_with_internet, computed_at, details
        FROM health.health_statistics
        WHERE scope_type = %s AND scope_name = %s
        ORDER BY computed_at DESC
        LIMIT 1
    """
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (scope_type, scope_name))
            row = cur.fetchone()
            if not row:
                return {
                    "scope_type": scope_type,
                    "scope_name": scope_name,
                    "total_facilities": 0,
                    "hospitals": 0,
                    "health_centers": 0,
                    "health_posts": 0,
                    "facilities_with_geometry": 0,
                    "facilities_without_geometry": 0,
                    "facilities_with_electricity": 0,
                    "facilities_with_internet": 0,
                    "computed_at": None,
                    "details": {"status": "empty"},
                    "data_available": False,
                }
            payload = _serialize_row(dict(row))
            payload["data_available"] = int(payload.get("total_facilities") or 0) > 0
            return payload


def facilities_geojson(limit: int = 5000) -> dict[str, Any]:
    total_geom = _count_facilities_with_geometry()
    if total_geom == 0:
        return {
            "type": "FeatureCollection",
            "features": [],
            "_meta": {
                "message": "Aucune donnée santé géolocalisée disponible",
                "data_available": False,
            },
        }
    query = """
        SELECT
            f.id, f.official_code, f.name, f.facility_type_code,
            t.name AS facility_type_name,
            f.province_name, f.locality_name, f.data_source, f.properties,
            ST_AsGeoJSON(f.geom)::json AS geometry
        FROM health.health_facilities f
        LEFT JOIN health.health_facility_types t ON t.code = f.facility_type_code
        WHERE f.geom IS NOT NULL
        ORDER BY f.id
        LIMIT %s
    """
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (limit,))
            rows = [_serialize_row(dict(row)) for row in cur.fetchall()]

    features = []
    for row in rows:
        features.append(
            {
                "type": "Feature",
                "id": row["id"],
                "geometry": row["geometry"],
                "properties": {
                    key: value
                    for key, value in row.items()
                    if key not in {"geometry"} and value is not None
                },
            }
        )
    return {
        "type": "FeatureCollection",
        "features": features,
        "_meta": {
            "data_available": True,
            "count": len(features),
            "total_geolocated": total_geom,
        },
    }


def get_quality_dashboard(scope_type: str = "national", scope_name: str = "RDC") -> dict[str, Any]:
    query = """
        SELECT
            id, scope_type, scope_name, quality_score, total_facilities,
            facilities_with_geometry, facilities_without_geometry,
            missing_names, missing_types, potential_duplicates, details, computed_at
        FROM health.health_quality_dashboard
        WHERE scope_type = %s AND scope_name = %s
        ORDER BY computed_at DESC
        LIMIT 1
    """
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT to_regclass('health.health_quality_dashboard') AS table_name
                """
            )
            exists = cur.fetchone()["table_name"]
            if not exists:
                return {"data_available": False, "quality_score": 0}
            cur.execute(query, (scope_type, scope_name))
            row = cur.fetchone()
            if not row:
                return {"data_available": False, "quality_score": 0}
            payload = _serialize_row(dict(row))
            payload["data_available"] = True
            if payload.get("quality_score") is not None:
                payload["quality_score"] = float(payload["quality_score"])
            return payload


def get_panel_payload() -> dict[str, Any]:
    stats = get_statistics()
    if not stats.get("data_available"):
        stats = compute_statistics()
    types = list_facility_types()
    facilities = list_facilities(limit=100)
    quality = get_quality_dashboard()
    details = stats.get("details") or {}
    data_available = bool(stats.get("data_available"))
    return {
        "_meta": {
            "title": "Référentiel Santé",
            "version": "1.0.0",
            "status": "active" if data_available else "in_progress",
            "data_available": data_available,
        },
        "statistics": stats,
        "quality": quality,
        "by_type": details.get("by_type") or {},
        "by_province": details.get("by_province") or {},
        "facility_types": types,
        "facilities": facilities,
        "facilities_count": int(stats.get("total_facilities") or 0),
        "geojson_empty_message": None if data_available else "Aucune donnée santé géolocalisée disponible",
        "table_empty_message": None if data_available else "Les données santé seront intégrées depuis une source officielle.",
    }


def get_decision_summary() -> dict[str, Any]:
    """Synthèse Santé orientée décision FDSU (valeur + explication)."""
    stats = get_statistics()
    quality = get_quality_dashboard()
    details = stats.get("details") or {}
    total = int(stats.get("total_facilities") or 0)
    with_geom = int(stats.get("facilities_with_geometry") or 0)
    hospitals = int(stats.get("hospitals") or 0)
    centers = int(stats.get("health_centers") or 0)

    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT COUNT(*) AS c
                FROM analysis.spatial_relations
                WHERE relation_type IN ('nearest_hgr', 'nearest_health_center', 'nearest_health_facility')
                """
            )
            proximity_relations = int(cur.fetchone()["c"])

    return {
        "_meta": {
            "title": "Synthèse décisionnelle — Référentiel Santé",
            "strategic_references": [
                "data/strategic/strategie_fdsu_ccn_2026_2030.docx",
            ],
        },
        "label": "Référentiel Santé",
        "value": total,
        "total_facilities": total,
        "hospitals": hospitals,
        "health_centers": centers,
        "facilities_with_geometry": with_geom,
        "quality_score": quality.get("quality_score") or details.get("quality_score"),
        "proximity_relations": proximity_relations,
        "definition": "Établissements sanitaires importés pour croiser sites FDSU et infrastructures sociales à connecter.",
        "source_table": "health.health_facilities",
        "calculation_method": "COUNT(*) + agrégats type/géométrie + relations spatiales nearest_hgr/nearest_health_center.",
        "last_updated": stats.get("computed_at"),
        "limitations": (
            None
            if total > 0
            else "Aucune donnée santé disponible."
        ),
        "recommended_action": "Voir la carte Santé",
        "by_type": details.get("by_type") or {},
        "by_province": details.get("by_province") or {},
        "available": total > 0,
    }
