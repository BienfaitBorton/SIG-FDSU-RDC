"""Référentiel Santé v1.0 — structures sanitaires (structure sans données fictives)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from api.config import connect_db
from psycopg2.extras import Json, RealDictCursor

HOSPITAL_TYPES = ("HGR",)
HEALTH_CENTER_TYPES = ("CS", "CSR", "CLINIC")
HEALTH_POST_TYPES = ("PS", "MAT")


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
            details = {
                "hospital_types": list(HOSPITAL_TYPES),
                "health_center_types": list(HEALTH_CENTER_TYPES),
                "health_post_types": list(HEALTH_POST_TYPES),
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
    rows = list_facilities(skip=0, limit=limit)
    features = []
    for index, row in enumerate(rows, start=1):
        if not row.get("geometry"):
            continue
        features.append(
            {
                "type": "Feature",
                "id": index,
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
        "_meta": {"data_available": True, "count": len(features)},
    }


def get_panel_payload() -> dict[str, Any]:
    stats = compute_statistics()
    types = list_facility_types()
    facilities = list_facilities(limit=50)
    return {
        "_meta": {
            "title": "Référentiel Santé",
            "version": "1.0.0",
            "status": "in_progress",
        },
        "statistics": stats,
        "facility_types": types,
        "facilities": facilities,
        "facilities_count": len(facilities),
        "geojson_empty_message": "Aucune donnée santé géolocalisée disponible",
        "table_empty_message": "Les données santé seront intégrées depuis une source officielle.",
    }
