"""Spatial Intelligence Engine — analyses PostGIS génériques FDSU."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from api.config import connect_db
from psycopg2.extras import Json, RealDictCursor

SOURCE_TYPE_FDSU_SITE = "fdsu_site"
TARGET_INFRASTRUCTURE = "telecom_infrastructure"
TARGET_NETWORK_LINE = "telecom_network_line"
TARGET_OPERATOR = "telecom_operator"
TARGET_PROVINCE = "admin_province"
TARGET_TERRITOIRE = "admin_territoire"

REL_NEAREST_INFRASTRUCTURE = "nearest_infrastructure"
REL_NEAREST_FIBER = "nearest_fiber"
REL_NEAREST_OPERATOR = "nearest_operator"
REL_NEARBY_OPERATOR = "nearby_operator"
REL_ADMIN_PROVINCE = "administrative_province"
REL_ADMIN_TERRITOIRE = "administrative_territoire"

FIBER_OPERATOR_CODES = ("FIBER_MW", "FIBERCO", "FTTX")
DEFAULT_NEARBY_RADIUS_M = 10_000.0


def _serialize_row(row: dict[str, Any]) -> dict[str, Any]:
    payload = dict(row)
    for key in ("analysis_date", "created_at", "updated_at"):
        value = payload.get(key)
        if value is not None and hasattr(value, "isoformat"):
            payload[key] = value.isoformat()
    if payload.get("distance_m") is not None:
        payload["distance_m"] = float(payload["distance_m"])
    return payload


def _format_distance(distance_m: float | None) -> str | None:
    if distance_m is None:
        return None
    if distance_m >= 1000:
        return f"{distance_m / 1000:.2f} km"
    return f"{distance_m:.0f} m"


def get_fdsu_site(site_id: int) -> dict[str, Any] | None:
    query = """
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
            p.program_name,
            CASE WHEN s.geom IS NULL THEN NULL ELSE ST_AsGeoJSON(s.geom)::json END AS geometry
        FROM programs.fdsu_sites s
        JOIN programs.fdsu_programs p ON p.id = s.program_id
        WHERE s.id = %s
        LIMIT 1
    """
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (site_id,))
            row = cur.fetchone()
            return _serialize_row(dict(row)) if row else None


def list_program_sites(program_code: str) -> list[dict[str, Any]]:
    query = """
        SELECT s.id, s.site_name, s.site_code, p.program_code, p.program_name
        FROM programs.fdsu_sites s
        JOIN programs.fdsu_programs p ON p.id = s.program_id
        WHERE p.program_code = %s
        ORDER BY s.id
    """
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (program_code,))
            return [dict(row) for row in cur.fetchall()]


def clear_site_relations(site_id: int) -> None:
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM analysis.spatial_relations
                WHERE source_type = %s AND source_id = %s
                """,
                (SOURCE_TYPE_FDSU_SITE, site_id),
            )
        conn.commit()


def save_relation(
    source_id: int,
    target_type: str,
    target_id: int,
    relation_type: str,
    distance_m: float | None,
    properties: dict[str, Any],
) -> None:
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO analysis.spatial_relations (
                    source_type, source_id, target_type, target_id,
                    relation_type, distance_m, analysis_date, properties
                )
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s)
                ON CONFLICT (source_type, source_id, target_type, target_id, relation_type)
                DO UPDATE SET
                    distance_m = EXCLUDED.distance_m,
                    analysis_date = EXCLUDED.analysis_date,
                    properties = EXCLUDED.properties
                """,
                (
                    SOURCE_TYPE_FDSU_SITE,
                    source_id,
                    target_type,
                    target_id,
                    relation_type,
                    distance_m,
                    Json(properties),
                ),
            )
        conn.commit()


def compute_nearest_infrastructure(site_id: int) -> dict[str, Any] | None:
    query = """
        SELECT
            i.id,
            i.infra_name,
            i.infra_type,
            i.technology,
            o.id AS operator_id,
            o.operator_code,
            o.operator_name,
            ST_Distance(s.geom::geography, i.geom::geography) AS distance_m
        FROM programs.fdsu_sites s
        JOIN telecom.infrastructure i ON i.geom IS NOT NULL
        JOIN telecom.operators o ON o.id = i.operator_id
        WHERE s.id = %s AND s.geom IS NOT NULL
        ORDER BY s.geom::geography <-> i.geom::geography
        LIMIT 1
    """
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (site_id,))
            row = cur.fetchone()
            return _serialize_row(dict(row)) if row else None


def compute_nearest_fiber(site_id: int) -> dict[str, Any] | None:
    query = """
        SELECT
            l.id,
            l.line_name,
            l.line_type,
            l.technology,
            o.id AS operator_id,
            o.operator_code,
            o.operator_name,
            ST_Distance(s.geom::geography, l.geom::geography) AS distance_m
        FROM programs.fdsu_sites s
        JOIN telecom.network_lines l ON l.geom IS NOT NULL
        JOIN telecom.operators o ON o.id = l.operator_id
        WHERE s.id = %s
          AND s.geom IS NOT NULL
          AND (
            o.operator_code = ANY(%s)
            OR l.line_type ILIKE '%%fiber%%'
            OR l.technology ILIKE '%%fiber%%'
          )
        ORDER BY s.geom::geography <-> l.geom::geography
        LIMIT 1
    """
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (site_id, list(FIBER_OPERATOR_CODES)))
            row = cur.fetchone()
            return _serialize_row(dict(row)) if row else None


def compute_nearby_operators(site_id: int, radius_m: float = DEFAULT_NEARBY_RADIUS_M) -> list[dict[str, Any]]:
    query = """
        SELECT
            o.id AS operator_id,
            o.operator_code,
            o.operator_name,
            MIN(ST_Distance(s.geom::geography, i.geom::geography)) AS distance_m,
            COUNT(i.id) AS infrastructure_count
        FROM programs.fdsu_sites s
        JOIN telecom.infrastructure i ON i.geom IS NOT NULL
        JOIN telecom.operators o ON o.id = i.operator_id
        WHERE s.id = %s
          AND s.geom IS NOT NULL
          AND ST_DWithin(s.geom::geography, i.geom::geography, %s)
        GROUP BY o.id, o.operator_code, o.operator_name
        ORDER BY distance_m
    """
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (site_id, radius_m))
            return [_serialize_row(dict(row)) for row in cur.fetchall()]


def compute_administrative_context(site_id: int) -> dict[str, Any]:
    context: dict[str, Any] = {
        "province_id": None,
        "province_name": None,
        "territoire_id": None,
        "territoire_name": None,
        "source": "attribute",
    }
    site = get_fdsu_site(site_id)
    if not site:
        return context

    province_query = """
        SELECT p.id, p.nom
        FROM programs.fdsu_sites s
        JOIN provinces p ON p.geom IS NOT NULL
        WHERE s.id = %s
          AND s.geom IS NOT NULL
          AND (ST_Contains(p.geom, s.geom) OR ST_Intersects(p.geom, s.geom))
        ORDER BY ST_Area(p.geom::geography) ASC
        LIMIT 1
    """
    territoire_query = """
        SELECT t.id, t.nom
        FROM programs.fdsu_sites s
        JOIN territoires t ON t.geom IS NOT NULL
        WHERE s.id = %s
          AND s.geom IS NOT NULL
          AND (ST_Contains(t.geom, s.geom) OR ST_Intersects(t.geom, s.geom))
        ORDER BY ST_Area(t.geom::geography) ASC
        LIMIT 1
    """
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(province_query, (site_id,))
            province = cur.fetchone()
            if province:
                context["province_id"] = int(province["id"])
                context["province_name"] = province["nom"]
                context["source"] = "postgis"

            cur.execute(territoire_query, (site_id,))
            territoire = cur.fetchone()
            if territoire:
                context["territoire_id"] = int(territoire["id"])
                context["territoire_name"] = territoire["nom"]
                context["source"] = "postgis"

    if not context["province_name"] and site.get("province"):
        context["province_name"] = site["province"]
    if not context["territoire_name"] and site.get("territoire"):
        context["territoire_name"] = site["territoire"]
    return context


def analyze_site(site_id: int, persist: bool = True) -> dict[str, Any]:
    site = get_fdsu_site(site_id)
    if not site:
        return {
            "site_id": site_id,
            "analysis_status": "not_found",
            "message": "Site FDSU introuvable.",
        }
    if not site.get("geometry"):
        return {
            "site_id": site_id,
            "site": site.get("site_name"),
            "programme": site.get("program_name"),
            "analysis_status": "skipped",
            "message": "Géométrie absente pour ce site.",
        }

    if persist:
        clear_site_relations(site_id)

    nearest_infra = compute_nearest_infrastructure(site_id)
    nearest_fiber = compute_nearest_fiber(site_id)
    nearby_operators = compute_nearby_operators(site_id)
    admin_context = compute_administrative_context(site_id)

    if persist and nearest_infra:
        save_relation(
            site_id,
            TARGET_INFRASTRUCTURE,
            int(nearest_infra["id"]),
            REL_NEAREST_INFRASTRUCTURE,
            float(nearest_infra["distance_m"]),
            {
                "infra_name": nearest_infra.get("infra_name"),
                "operator_code": nearest_infra.get("operator_code"),
                "operator_name": nearest_infra.get("operator_name"),
            },
        )
    if persist and nearest_fiber:
        save_relation(
            site_id,
            TARGET_NETWORK_LINE,
            int(nearest_fiber["id"]),
            REL_NEAREST_FIBER,
            float(nearest_fiber["distance_m"]),
            {
                "line_name": nearest_fiber.get("line_name"),
                "operator_code": nearest_fiber.get("operator_code"),
                "operator_name": nearest_fiber.get("operator_name"),
            },
        )
    if persist and nearest_infra:
        save_relation(
            site_id,
            TARGET_OPERATOR,
            int(nearest_infra["operator_id"]),
            REL_NEAREST_OPERATOR,
            float(nearest_infra["distance_m"]),
            {
                "operator_code": nearest_infra.get("operator_code"),
                "operator_name": nearest_infra.get("operator_name"),
            },
        )
    if persist:
        for operator in nearby_operators:
            save_relation(
                site_id,
                TARGET_OPERATOR,
                int(operator["operator_id"]),
                REL_NEARBY_OPERATOR,
                float(operator["distance_m"]),
                {
                    "operator_code": operator.get("operator_code"),
                    "operator_name": operator.get("operator_name"),
                    "infrastructure_count": operator.get("infrastructure_count"),
                },
            )
        if admin_context.get("province_id"):
            save_relation(
                site_id,
                TARGET_PROVINCE,
                int(admin_context["province_id"]),
                REL_ADMIN_PROVINCE,
                None,
                {"province_name": admin_context.get("province_name"), "source": admin_context.get("source")},
            )
        if admin_context.get("territoire_id"):
            save_relation(
                site_id,
                TARGET_TERRITOIRE,
                int(admin_context["territoire_id"]),
                REL_ADMIN_TERRITOIRE,
                None,
                {"territoire_name": admin_context.get("territoire_name"), "source": admin_context.get("source")},
            )

    nearest_operator_name = None
    if nearest_infra:
        nearest_operator_name = nearest_infra.get("operator_name") or nearest_infra.get("operator_code")
    elif nearby_operators:
        nearest_operator_name = nearby_operators[0].get("operator_name") or nearby_operators[0].get("operator_code")

    return {
        "site_id": site_id,
        "site": site.get("site_name"),
        "site_code": site.get("site_code"),
        "programme": site.get("program_name"),
        "program_code": site.get("program_code"),
        "nearest_operator": nearest_operator_name,
        "distance_to_operator": _format_distance(
            float(nearest_infra["distance_m"]) if nearest_infra else None
        ),
        "distance_to_operator_m": float(nearest_infra["distance_m"]) if nearest_infra else None,
        "nearest_infrastructure": nearest_infra.get("infra_name") if nearest_infra else None,
        "nearest_fiber": nearest_fiber.get("line_name") if nearest_fiber else None,
        "distance_to_fiber": _format_distance(
            float(nearest_fiber["distance_m"]) if nearest_fiber else None
        ),
        "distance_to_fiber_m": float(nearest_fiber["distance_m"]) if nearest_fiber else None,
        "nearby_operators": [
            {
                "operator_code": item.get("operator_code"),
                "operator_name": item.get("operator_name"),
                "distance_m": float(item["distance_m"]),
                "distance": _format_distance(float(item["distance_m"])),
                "infrastructure_count": int(item.get("infrastructure_count") or 0),
            }
            for item in nearby_operators
        ],
        "province": admin_context.get("province_name") or site.get("province"),
        "territoire": admin_context.get("territoire_name") or site.get("territoire"),
        "administrative_source": admin_context.get("source"),
        "analysis_status": "completed",
        "analysis_date": datetime.now(timezone.utc).isoformat(),
    }


def analyze_program(program_code: str, persist: bool = True) -> dict[str, Any]:
    sites = list_program_sites(program_code)
    results = [analyze_site(int(site["id"]), persist=persist) for site in sites]
    completed = sum(1 for item in results if item.get("analysis_status") == "completed")
    return {
        "program_code": program_code,
        "program_name": sites[0]["program_name"] if sites else program_code,
        "site_count": len(sites),
        "sites_analyzed": completed,
        "analysis_status": "completed" if sites else "empty",
        "sites": results,
    }


def analyze_programs(program_codes: list[str], persist: bool = True) -> dict[str, Any]:
    summaries = [analyze_program(code, persist=persist) for code in program_codes]
    return {
        "programs": summaries,
        "program_count": len(summaries),
        "sites_analyzed": sum(item.get("sites_analyzed", 0) for item in summaries),
    }


def get_nearby_analysis(
    latitude: float,
    longitude: float,
    radius_m: float = DEFAULT_NEARBY_RADIUS_M,
    limit: int = 100,
) -> dict[str, Any]:
    query = """
        WITH origin AS (
            SELECT ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography AS geom
        )
        SELECT
            'telecom_infrastructure' AS object_type,
            i.id,
            i.infra_name AS name,
            o.operator_name,
            ST_Distance(origin.geom, i.geom::geography) AS distance_m
        FROM origin
        JOIN telecom.infrastructure i ON i.geom IS NOT NULL
        JOIN telecom.operators o ON o.id = i.operator_id
        WHERE ST_DWithin(origin.geom, i.geom::geography, %s)
        ORDER BY distance_m
        LIMIT %s
    """
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (longitude, latitude, radius_m, limit))
            infrastructure = [_serialize_row(dict(row)) for row in cur.fetchall()]

    fdsu_query = """
        WITH origin AS (
            SELECT ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography AS geom
        )
        SELECT
            s.id,
            s.site_name,
            p.program_name,
            ST_Distance(origin.geom, s.geom::geography) AS distance_m
        FROM origin
        JOIN programs.fdsu_sites s ON s.geom IS NOT NULL
        JOIN programs.fdsu_programs p ON p.id = s.program_id
        WHERE ST_DWithin(origin.geom, s.geom::geography, %s)
        ORDER BY distance_m
        LIMIT %s
    """
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(fdsu_query, (longitude, latitude, radius_m, limit))
            fdsu_sites = [_serialize_row(dict(row)) for row in cur.fetchall()]

    return {
        "latitude": latitude,
        "longitude": longitude,
        "radius_m": radius_m,
        "infrastructure": infrastructure,
        "fdsu_sites": fdsu_sites,
    }


def get_statistics() -> dict[str, Any]:
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT COUNT(*) AS count FROM programs.fdsu_sites")
            total_sites = int(cur.fetchone()["count"])

            cur.execute("SELECT COUNT(*) AS count FROM telecom.infrastructure")
            infrastructure_count = int(cur.fetchone()["count"])

            cur.execute("SELECT COUNT(*) AS count FROM analysis.spatial_relations")
            relation_count = int(cur.fetchone()["count"])

            cur.execute(
                """
                SELECT COUNT(DISTINCT source_id) AS count
                FROM analysis.spatial_relations
                WHERE source_type = %s
                """,
                (SOURCE_TYPE_FDSU_SITE,),
            )
            sites_analyzed = int(cur.fetchone()["count"])

            cur.execute(
                """
                SELECT MAX(analysis_date) AS last_analysis
                FROM analysis.spatial_relations
                """
            )
            last_analysis = cur.fetchone()["last_analysis"]

            cur.execute(
                """
                SELECT relation_type, COUNT(*) AS count
                FROM analysis.spatial_relations
                GROUP BY relation_type
                ORDER BY count DESC
                """
            )
            by_relation_type = [dict(row) for row in cur.fetchall()]

    last_analysis_iso = None
    if last_analysis is not None and hasattr(last_analysis, "isoformat"):
        last_analysis_iso = last_analysis.isoformat()

    return {
        "sites_total": total_sites,
        "sites_analyzed": sites_analyzed,
        "infrastructure_analyzed": infrastructure_count,
        "relations_computed": relation_count,
        "last_analysis": last_analysis_iso,
        "by_relation_type": by_relation_type,
    }


def get_panel_payload() -> dict[str, Any]:
    stats = get_statistics()
    return {
        "_meta": {
            "title": "Analyse spatiale",
            "engine": "Spatial Intelligence Engine",
        },
        "statistics": stats,
    }


def spatial_relations_geojson(limit: int = 5000) -> dict[str, Any]:
    """Architecture cartographique — lignes site → infrastructure la plus proche."""
    query = """
        SELECT
            r.id,
            r.relation_type,
            r.distance_m,
            r.properties,
            ST_AsGeoJSON(s.geom)::json AS source_geom,
            ST_AsGeoJSON(i.geom)::json AS target_geom
        FROM analysis.spatial_relations r
        JOIN programs.fdsu_sites s ON r.source_type = 'fdsu_site' AND s.id = r.source_id
        LEFT JOIN telecom.infrastructure i
            ON r.target_type = 'telecom_infrastructure' AND i.id = r.target_id
        WHERE r.relation_type IN ('nearest_infrastructure', 'nearest_fiber')
          AND s.geom IS NOT NULL
          AND i.geom IS NOT NULL
        ORDER BY r.analysis_date DESC
        LIMIT %s
    """
    features: list[dict[str, Any]] = []
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (limit,))
            rows = cur.fetchall()

    for index, row in enumerate(rows, start=1):
        source_geom = row.get("source_geom")
        target_geom = row.get("target_geom")
        if not source_geom or not target_geom:
            continue
        source_coords = source_geom.get("coordinates")
        target_coords = target_geom.get("coordinates")
        if not source_coords or not target_coords:
            continue
        features.append(
            {
                "type": "Feature",
                "id": index,
                "geometry": {
                    "type": "LineString",
                    "coordinates": [source_coords, target_coords],
                },
                "properties": {
                    "relation_type": row.get("relation_type"),
                    "distance_m": float(row["distance_m"]) if row.get("distance_m") is not None else None,
                    **(row.get("properties") or {}),
                },
            }
        )

    return {
        "type": "FeatureCollection",
        "features": features,
        "_meta": {
            "layer": "spatial_relations",
            "architecture": "prepared",
            "description": "Lignes site FDSU vers infrastructure la plus proche",
        },
    }
