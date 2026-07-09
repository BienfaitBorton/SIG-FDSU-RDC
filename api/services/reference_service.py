"""National Reference Framework — catalogue et qualité des référentiels FDSU."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from api.config import connect_db
from psycopg2.extras import Json, RealDictCursor


def _serialize_row(row: dict[str, Any]) -> dict[str, Any]:
    payload = dict(row)
    for key in ("created_at", "updated_at", "computed_at"):
        value = payload.get(key)
        if value is not None and hasattr(value, "isoformat"):
            payload[key] = value.isoformat()
    if payload.get("quality_score") is not None:
        payload["quality_score"] = float(payload["quality_score"])
    return payload


def _count_telecom_objects(cur) -> dict[str, int]:
    cur.execute("SELECT COUNT(*) AS c FROM telecom.infrastructure")
    infra = int(cur.fetchone()["c"])
    cur.execute("SELECT COUNT(*) AS c FROM telecom.infrastructure WHERE geom IS NOT NULL")
    infra_geom = int(cur.fetchone()["c"])
    return {
        "total": infra,
        "with_geometry": infra_geom,
        "without_geometry": infra - infra_geom,
        "with_admin_link": 0,
        "without_admin_link": infra,
    }


def _count_programs_objects(cur) -> dict[str, int]:
    cur.execute("SELECT COUNT(*) AS c FROM programs.fdsu_sites")
    total = int(cur.fetchone()["c"])
    cur.execute("SELECT COUNT(*) AS c FROM programs.fdsu_sites WHERE geom IS NOT NULL")
    with_geom = int(cur.fetchone()["c"])
    cur.execute(
        """
        SELECT COUNT(*) AS c FROM programs.fdsu_sites
        WHERE province IS NOT NULL AND province <> ''
        """
    )
    with_admin = int(cur.fetchone()["c"])
    return {
        "total": total,
        "with_geometry": with_geom,
        "without_geometry": total - with_geom,
        "with_admin_link": with_admin,
        "without_admin_link": total - with_admin,
    }


def _count_health_objects(cur) -> dict[str, int]:
    cur.execute("SELECT COUNT(*) AS c FROM health.health_facilities")
    total = int(cur.fetchone()["c"])
    cur.execute("SELECT COUNT(*) AS c FROM health.health_facilities WHERE geom IS NOT NULL")
    with_geom = int(cur.fetchone()["c"])
    cur.execute(
        """
        SELECT COUNT(*) AS c FROM health.health_facilities
        WHERE province_name IS NOT NULL AND province_name <> ''
        """
    )
    with_admin = int(cur.fetchone()["c"])
    return {
        "total": total,
        "with_geometry": with_geom,
        "without_geometry": total - with_geom,
        "with_admin_link": with_admin,
        "without_admin_link": total - with_admin,
    }


def _count_admin_objects(cur) -> dict[str, int]:
    counts = {"total": 0, "with_geometry": 0, "without_geometry": 0, "with_admin_link": 0, "without_admin_link": 0}
    for table in ("provinces", "territoires", "collectivites", "groupements", "villages"):
        try:
            cur.execute(f"SELECT COUNT(*) AS c FROM {table}")
            total = int(cur.fetchone()["c"])
            cur.execute(f"SELECT COUNT(*) AS c FROM {table} WHERE geom IS NOT NULL")
            with_geom = int(cur.fetchone()["c"])
            counts["total"] += total
            counts["with_geometry"] += with_geom
        except Exception:
            continue
    counts["without_geometry"] = counts["total"] - counts["with_geometry"]
    counts["with_admin_link"] = counts["total"]
    return counts


def _quality_score(counts: dict[str, int]) -> float | None:
    total = counts["total"]
    if total <= 0:
        return None
    geom_ratio = counts["with_geometry"] / total
    admin_ratio = counts["with_admin_link"] / total
    return round((geom_ratio * 0.6 + admin_ratio * 0.4) * 100, 2)


def compute_quality_indicators(reference_code: str | None = None) -> list[dict[str, Any]]:
    counters: dict[str, dict[str, int]] = {}
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT code FROM reference.reference_catalog ORDER BY code")
            codes = [row["code"] for row in cur.fetchall()]
            if reference_code:
                codes = [reference_code] if reference_code in codes else []

            for code in codes:
                if code == "TELECOM":
                    counters[code] = _count_telecom_objects(cur)
                elif code == "PROGRAMS":
                    counters[code] = _count_programs_objects(cur)
                elif code == "HEALTH":
                    counters[code] = _count_health_objects(cur)
                elif code == "ADMIN":
                    counters[code] = _count_admin_objects(cur)
                elif code == "DECISION":
                    cur.execute("SELECT COUNT(*) AS c FROM decision.fdsu_site_scores")
                    total = int(cur.fetchone()["c"])
                    counters[code] = {
                        "total": total,
                        "with_geometry": total,
                        "without_geometry": 0,
                        "with_admin_link": total,
                        "without_admin_link": 0,
                    }
                else:
                    counters[code] = {
                        "total": 0,
                        "with_geometry": 0,
                        "without_geometry": 0,
                        "with_admin_link": 0,
                        "without_admin_link": 0,
                    }

            results: list[dict[str, Any]] = []
            for code, counts in counters.items():
                score = _quality_score(counts)
                details = {"reference_code": code, "computed_by": "reference_service"}
                cur.execute(
                    """
                    INSERT INTO reference.reference_quality_indicators (
                        reference_code, total_objects, objects_with_geometry,
                        objects_without_geometry, objects_with_admin_link,
                        objects_without_admin_link, quality_score, computed_at, details
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), %s)
                    """,
                    (
                        code,
                        counts["total"],
                        counts["with_geometry"],
                        counts["without_geometry"],
                        counts["with_admin_link"],
                        counts["without_admin_link"],
                        score,
                        Json(details),
                    ),
                )
                results.append(
                    {
                        "reference_code": code,
                        "total_objects": counts["total"],
                        "objects_with_geometry": counts["with_geometry"],
                        "objects_without_geometry": counts["without_geometry"],
                        "objects_with_admin_link": counts["with_admin_link"],
                        "objects_without_admin_link": counts["without_admin_link"],
                        "quality_score": score,
                        "computed_at": datetime.now(timezone.utc).isoformat(),
                        "details": details,
                    }
                )
        conn.commit()
    return results


def list_catalog(category: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
    filters: list[str] = []
    params: list[Any] = []
    if category:
        filters.append("category = %s")
        params.append(category)
    if status:
        filters.append("status = %s")
        params.append(status)
    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    query = f"""
        SELECT id, code, name, category, description, source_name, source_type,
               update_frequency, status, created_at, updated_at, metadata
        FROM reference.reference_catalog
        {where_clause}
        ORDER BY
            CASE status
                WHEN 'active' THEN 1
                WHEN 'in_progress' THEN 2
                WHEN 'planned' THEN 3
                ELSE 4
            END,
            name
    """
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, tuple(params))
            return [_serialize_row(dict(row)) for row in cur.fetchall()]


def get_catalog_entry(code: str) -> dict[str, Any] | None:
    query = """
        SELECT id, code, name, category, description, source_name, source_type,
               update_frequency, status, created_at, updated_at, metadata
        FROM reference.reference_catalog
        WHERE code = %s
        LIMIT 1
    """
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (code.upper(),))
            row = cur.fetchone()
            return _serialize_row(dict(row)) if row else None


def list_object_types(reference_code: str) -> list[dict[str, Any]]:
    query = """
        SELECT id, reference_code, type_code, type_name, description, symbology, metadata
        FROM reference.reference_object_types
        WHERE reference_code = %s
        ORDER BY type_code
    """
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (reference_code.upper(),))
            return [_serialize_row(dict(row)) for row in cur.fetchall()]


def get_quality_indicators(reference_code: str | None = None) -> list[dict[str, Any]]:
    compute_quality_indicators(reference_code)
    filters: list[str] = []
    params: list[Any] = []
    if reference_code:
        filters.append("reference_code = %s")
        params.append(reference_code.upper())
    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    query = f"""
        SELECT DISTINCT ON (reference_code)
            id, reference_code, total_objects, objects_with_geometry,
            objects_without_geometry, objects_with_admin_link,
            objects_without_admin_link, quality_score, computed_at, details
        FROM reference.reference_quality_indicators
        {where_clause}
        ORDER BY reference_code, computed_at DESC
    """
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, tuple(params))
            return [_serialize_row(dict(row)) for row in cur.fetchall()]


def get_panel_payload() -> dict[str, Any]:
    catalog = list_catalog()
    quality = get_quality_indicators()
    quality_by_code = {item["reference_code"]: item for item in quality}
    sectorial = [item for item in catalog if item.get("category") == "sectorial" or item.get("code") == "HEALTH"]
    return {
        "_meta": {
            "title": "Référentiels sectoriels",
            "framework": "National Reference Framework",
        },
        "catalog": catalog,
        "sectorial_referentials": sectorial,
        "quality": quality_by_code,
    }
