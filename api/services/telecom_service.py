"""Service PostgreSQL/PostGIS pour le référentiel télécom national."""

from __future__ import annotations

from typing import Any

from api.config import connect_db
from psycopg2.extras import RealDictCursor

LAYER_OPERATOR_MAP = {
    "telecom_vodacom": "VODACOM",
    "telecom_orange": "ORANGE",
    "telecom_fiber_mw": "FIBER_MW",
    "telecom_fiberco": "FIBERCO",
    "telecom_fttx": "FTTX",
}


def _serialize_row(row: dict[str, Any]) -> dict[str, Any]:
    payload = dict(row)
    for key in ("created_at", "updated_at"):
        value = payload.get(key)
        if value is not None and hasattr(value, "isoformat"):
            payload[key] = value.isoformat()
    if payload.get("properties") is None:
        payload["properties"] = {}
    return payload


def list_operators() -> list[dict[str, Any]]:
    query = """
        SELECT id, operator_code, operator_name, operator_type, country, status, created_at, updated_at
        FROM telecom.operators
        ORDER BY operator_code
    """
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return [_serialize_row(dict(row)) for row in cur.fetchall()]


def list_infrastructure(
    operator_code: str | None = None,
    skip: int = 0,
    limit: int = 10000,
) -> list[dict[str, Any]]:
    filters = []
    params: list[Any] = []
    if operator_code:
        filters.append("o.operator_code = %s")
        params.append(operator_code)
    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    query = f"""
        SELECT
            i.id, i.operator_id, o.operator_code, o.operator_name,
            i.infra_code, i.infra_name, i.infra_type, i.technology, i.source_file,
            i.province, i.territoire, i.status, i.latitude, i.longitude, i.properties,
            CASE WHEN i.geom IS NULL THEN NULL ELSE ST_AsGeoJSON(i.geom)::json END AS geometry
        FROM telecom.infrastructure i
        JOIN telecom.operators o ON o.id = i.operator_id
        {where_clause}
        ORDER BY i.id
        OFFSET %s LIMIT %s
    """
    params.extend([skip, limit])
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, tuple(params))
            return [_serialize_row(dict(row)) for row in cur.fetchall()]


def list_network_lines(
    operator_code: str | None = None,
    skip: int = 0,
    limit: int = 10000,
) -> list[dict[str, Any]]:
    filters = []
    params: list[Any] = []
    if operator_code:
        filters.append("o.operator_code = %s")
        params.append(operator_code)
    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    query = f"""
        SELECT
            l.id, l.operator_id, o.operator_code, o.operator_name,
            l.line_code, l.line_name, l.line_type, l.technology, l.source_file, l.properties,
            CASE WHEN l.geom IS NULL THEN NULL ELSE ST_AsGeoJSON(l.geom)::json END AS geometry
        FROM telecom.network_lines l
        JOIN telecom.operators o ON o.id = l.operator_id
        {where_clause}
        ORDER BY l.id
        OFFSET %s LIMIT %s
    """
    params.extend([skip, limit])
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, tuple(params))
            return [_serialize_row(dict(row)) for row in cur.fetchall()]


def list_coverage_polygons(
    operator_code: str | None = None,
    skip: int = 0,
    limit: int = 10000,
) -> list[dict[str, Any]]:
    filters = []
    params: list[Any] = []
    if operator_code:
        filters.append("o.operator_code = %s")
        params.append(operator_code)
    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    query = f"""
        SELECT
            p.id, p.operator_id, o.operator_code, o.operator_name,
            p.polygon_code, p.polygon_name, p.polygon_type, p.technology, p.source_file, p.properties,
            CASE WHEN p.geom IS NULL THEN NULL ELSE ST_AsGeoJSON(p.geom)::json END AS geometry
        FROM telecom.coverage_polygons p
        JOIN telecom.operators o ON o.id = p.operator_id
        {where_clause}
        ORDER BY p.id
        OFFSET %s LIMIT %s
    """
    params.extend([skip, limit])
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, tuple(params))
            return [_serialize_row(dict(row)) for row in cur.fetchall()]


def _feature_from_row(row: dict[str, Any], name_key: str, type_key: str, feature_id: int) -> dict[str, Any]:
    properties = dict(row.get("properties") or {})
    for key in (
        "operator_code",
        "operator_name",
        "source_file",
        name_key.replace("_name", "_code"),
        name_key,
        type_key,
        "technology",
        "province",
        "territoire",
        "status",
    ):
        if row.get(key) not in (None, "") and key not in properties:
            properties[key] = row.get(key)
    properties["infra_category"] = type_key.replace("_type", "")
    return {
        "type": "Feature",
        "id": feature_id,
        "geometry": row.get("geometry"),
        "properties": {key: value for key, value in properties.items() if value not in (None, "")},
    }


def layer_to_geojson(layer_key: str) -> dict[str, Any]:
    operator_code = LAYER_OPERATOR_MAP.get(layer_key)
    if not operator_code:
        return {"type": "FeatureCollection", "features": []}

    features: list[dict[str, Any]] = []
    feature_id = 1

    if layer_key in {"telecom_vodacom", "telecom_orange"}:
        for row in list_infrastructure(operator_code=operator_code, limit=100000):
            features.append(_feature_from_row(row, "infra_name", "infra_type", feature_id))
            feature_id += 1
        return {"type": "FeatureCollection", "features": features}

    for row in list_infrastructure(operator_code=operator_code, limit=100000):
        features.append(_feature_from_row(row, "infra_name", "infra_type", feature_id))
        feature_id += 1
    for row in list_network_lines(operator_code=operator_code, limit=100000):
        features.append(_feature_from_row(row, "line_name", "line_type", feature_id))
        feature_id += 1
    for row in list_coverage_polygons(operator_code=operator_code, limit=100000):
        features.append(_feature_from_row(row, "polygon_name", "polygon_type", feature_id))
        feature_id += 1
    return {"type": "FeatureCollection", "features": features}


def get_statistics() -> dict[str, Any]:
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT COUNT(*) AS count FROM telecom.operators")
            operator_count = int(cur.fetchone()["count"])
            cur.execute("SELECT COUNT(*) AS count FROM telecom.infrastructure")
            point_count = int(cur.fetchone()["count"])
            cur.execute("SELECT COUNT(*) AS count FROM telecom.network_lines")
            line_count = int(cur.fetchone()["count"])
            cur.execute("SELECT COUNT(*) AS count FROM telecom.coverage_polygons")
            polygon_count = int(cur.fetchone()["count"])

            # Agrégats séparés pour éviter le produit cartésien des LEFT JOIN multiples.
            cur.execute(
                """
                SELECT
                    o.operator_code,
                    o.operator_name,
                    COALESCE(i.infrastructure_count, 0) AS infrastructure_count,
                    COALESCE(l.network_line_count, 0) AS network_line_count,
                    COALESCE(p.coverage_polygon_count, 0) AS coverage_polygon_count
                FROM telecom.operators o
                LEFT JOIN (
                    SELECT operator_id, COUNT(*) AS infrastructure_count
                    FROM telecom.infrastructure
                    GROUP BY operator_id
                ) i ON i.operator_id = o.id
                LEFT JOIN (
                    SELECT operator_id, COUNT(*) AS network_line_count
                    FROM telecom.network_lines
                    GROUP BY operator_id
                ) l ON l.operator_id = o.id
                LEFT JOIN (
                    SELECT operator_id, COUNT(*) AS coverage_polygon_count
                    FROM telecom.coverage_polygons
                    GROUP BY operator_id
                ) p ON p.operator_id = o.id
                ORDER BY o.operator_code
                """
            )
            by_operator = [dict(row) for row in cur.fetchall()]

            cur.execute(
                """
                SELECT source_file,
                       SUM(points)::int AS points,
                       SUM(lines)::int AS lines,
                       SUM(polygons)::int AS polygons
                FROM (
                    SELECT source_file,
                           COUNT(*)::int AS points,
                           0 AS lines,
                           0 AS polygons
                    FROM telecom.infrastructure
                    GROUP BY source_file
                    UNION ALL
                    SELECT source_file,
                           0 AS points,
                           COUNT(*)::int AS lines,
                           0 AS polygons
                    FROM telecom.network_lines
                    GROUP BY source_file
                    UNION ALL
                    SELECT source_file,
                           0 AS points,
                           0 AS lines,
                           COUNT(*)::int AS polygons
                    FROM telecom.coverage_polygons
                    GROUP BY source_file
                ) s
                GROUP BY source_file
                ORDER BY source_file
                """
            )
            by_source = [dict(row) for row in cur.fetchall()]

    return {
        "operator_count": operator_count,
        "infrastructure_count": point_count,
        "network_line_count": line_count,
        "coverage_polygon_count": polygon_count,
        "total_objects": point_count + line_count + polygon_count,
        "by_operator": by_operator,
        "by_source_file": by_source,
    }


def nearest_infrastructure(
    lat: float,
    lon: float,
    *,
    radius_m: float = 25000,
    limit: int = 15,
) -> dict[str, Any]:
    """Infrastructures télécom (nœuds / sites) les plus proches — PostGIS geography SRID 4326."""
    stats = get_statistics()
    referential_count = int(stats.get("infrastructure_count") or 0)
    if referential_count <= 0:
        return {
            "data_available": False,
            "search_executed": False,
            "referential_count": 0,
            "radius_m": radius_m,
            "facilities": [],
            "nearest": None,
        }
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    i.id,
                    i.infra_code,
                    i.infra_name,
                    i.infra_type,
                    i.technology,
                    i.source_file,
                    i.province,
                    i.territoire,
                    i.latitude,
                    i.longitude,
                    o.operator_code,
                    o.operator_name,
                    ST_Distance(
                        i.geom::geography,
                        ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                    ) AS distance_m
                FROM telecom.infrastructure i
                JOIN telecom.operators o ON o.id = i.operator_id
                WHERE i.geom IS NOT NULL
                  AND ST_DWithin(
                    i.geom::geography,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                    %s
                  )
                ORDER BY i.geom::geography <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                LIMIT %s
                """,
                (lon, lat, lon, lat, radius_m, lon, lat, limit),
            )
            rows = [_serialize_row(dict(r)) for r in cur.fetchall()]
            # Si rien dans le rayon demandé, remonter le plus proche absolu (contexte hors rayon)
            nearest_absolute = None
            if not rows:
                cur.execute(
                    """
                    SELECT
                        i.id,
                        i.infra_code,
                        i.infra_name,
                        i.infra_type,
                        i.technology,
                        i.source_file,
                        i.province,
                        i.territoire,
                        i.latitude,
                        i.longitude,
                        o.operator_code,
                        o.operator_name,
                        ST_Distance(
                            i.geom::geography,
                            ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                        ) AS distance_m
                    FROM telecom.infrastructure i
                    JOIN telecom.operators o ON o.id = i.operator_id
                    WHERE i.geom IS NOT NULL
                    ORDER BY i.geom::geography <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                    LIMIT 1
                    """,
                    (lon, lat, lon, lat),
                )
                abs_row = cur.fetchone()
                nearest_absolute = _serialize_row(dict(abs_row)) if abs_row else None
    return {
        "data_available": True,
        "search_executed": True,
        "referential_count": referential_count,
        "radius_m": radius_m,
        "facilities": rows,
        "nearest": rows[0] if rows else nearest_absolute,
        "nearest_outside_radius": nearest_absolute if not rows else None,
        "object_kind": "infrastructure_node",
    }


def nearest_network_line(
    lat: float,
    lon: float,
    *,
    radius_m: float = 25000,
) -> dict[str, Any]:
    """Tronçon / ligne réseau fibre le plus proche — distinct des nœuds FTTX."""
    stats = get_statistics()
    line_count = int(stats.get("network_line_count") or 0)
    if line_count <= 0:
        return {
            "data_available": False,
            "search_executed": False,
            "referential_count": 0,
            "radius_m": radius_m,
            "nearest": None,
        }
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    l.id,
                    l.line_code,
                    l.line_name,
                    l.line_type,
                    l.technology,
                    l.source_file,
                    o.operator_code,
                    o.operator_name,
                    ST_Distance(
                        l.geom::geography,
                        ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                    ) AS distance_m,
                    ST_Y(ST_ClosestPoint(l.geom, ST_SetSRID(ST_MakePoint(%s, %s), 4326))) AS latitude,
                    ST_X(ST_ClosestPoint(l.geom, ST_SetSRID(ST_MakePoint(%s, %s), 4326))) AS longitude
                FROM telecom.network_lines l
                JOIN telecom.operators o ON o.id = l.operator_id
                WHERE l.geom IS NOT NULL
                ORDER BY l.geom::geography <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                LIMIT 1
                """,
                (lon, lat, lon, lat, lon, lat, lon, lat),
            )
            row = cur.fetchone()
            nearest = _serialize_row(dict(row)) if row else None
    within = bool(nearest and float(nearest.get("distance_m") or 0) <= float(radius_m))
    return {
        "data_available": True,
        "search_executed": True,
        "referential_count": line_count,
        "radius_m": radius_m,
        "nearest": nearest,
        "within_radius": within,
        "object_kind": "network_line",
    }


def get_nearby_sites(
    latitude: float | None = None,
    longitude: float | None = None,
    radius_meters: float | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    if latitude is None or longitude is None:
        return {
            "status": "insufficient",
            "message": "Coordonnées du site requises pour l’analyse de proximité télécom.",
            "items": [],
        }
    radius = float(radius_meters or 25000)
    payload = nearest_infrastructure(float(latitude), float(longitude), radius_m=radius, limit=limit)
    return {
        "status": "success" if payload.get("search_executed") else "unavailable",
        "message": None,
        "query": {
            "latitude": latitude,
            "longitude": longitude,
            "radius_meters": radius,
            "limit": limit,
        },
        "items": payload.get("facilities") or [],
        "nearest": payload.get("nearest"),
        "referential_count": payload.get("referential_count"),
    }


def get_panel_payload() -> dict[str, Any]:
    stats = get_statistics()
    return {
        "_meta": {
            "title": "Referentiel Telecom National",
            "mode": "db",
            "sources_integrated": len(stats.get("by_source_file") or []),
        },
        "statistics": stats,
        "operators": list_operators(),
    }
