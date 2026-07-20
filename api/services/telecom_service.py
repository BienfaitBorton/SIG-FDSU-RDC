"""Service PostgreSQL/PostGIS pour le référentiel télécom national."""

from __future__ import annotations

import threading
from typing import Any

from api.config import connect_db
from psycopg2.extras import Json, RealDictCursor

LAYER_OPERATOR_MAP = {
    "telecom_vodacom": "VODACOM",
    "telecom_orange": "ORANGE",
    "telecom_fiber_mw": "FIBER_MW",
    "telecom_fiberco": "FIBERCO",
    "telecom_fttx": "FTTX",
    # Couches FDSU / typées — résolues via catalog (voir resolve_layer_geojson)
    "telecom_airtel": "AIRTEL",
    "telecom_africell": "AFRICELL",
    "telecom_mno_planned": "FDSU_MNO_PLANNED",
    "telecom_fiber": "FIBER",
    "telecom_microwave": "MICROWAVE",
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
        "latitude",
        "longitude",
    ):
        if row.get(key) not in (None, "") and key not in properties:
            properties[key] = row.get(key)
    # Coordonnées depuis géométrie si absentes (popups / tooltips)
    geom = row.get("geometry") or {}
    coords = geom.get("coordinates") if isinstance(geom, dict) else None
    if isinstance(coords, (list, tuple)) and len(coords) >= 2:
        if properties.get("longitude") is None:
            properties["longitude"] = coords[0]
        if properties.get("latitude") is None:
            properties["latitude"] = coords[1]
    properties["infra_category"] = type_key.replace("_type", "")
    return {
        "type": "Feature",
        "id": feature_id,
        "geometry": row.get("geometry"),
        "properties": {key: value for key, value in properties.items() if value not in (None, "")},
    }


def _enrich_feature_typing(feature: dict[str, Any], geometry_kind: str) -> dict[str, Any]:
    from api.services.telecom_asset_typing import classify_telecom_asset

    props = feature.get("properties") or {}
    typed = classify_telecom_asset(props, geometry_kind=geometry_kind)
    props = {**props, **typed, "source_label": props.get("source_label") or "Référentiel télécom"}
    feature["properties"] = {k: v for k, v in props.items() if v not in (None, "")}
    return feature


def layer_to_geojson(layer_key: str) -> dict[str, Any]:
    """Couches DB historiques (Vodacom/Orange/Fiberco/FTTX/Fibre-MW combiné)."""
    operator_code = LAYER_OPERATOR_MAP.get(layer_key)
    if not operator_code or operator_code in {"AIRTEL", "AFRICELL", "FDSU_MNO_PLANNED", "FIBER", "MICROWAVE"}:
        return {"type": "FeatureCollection", "features": []}

    features: list[dict[str, Any]] = []
    feature_id = 1

    if layer_key in {"telecom_vodacom", "telecom_orange"}:
        for row in list_infrastructure(operator_code=operator_code, limit=100000):
            feat = _feature_from_row(row, "infra_name", "infra_type", feature_id)
            feat["properties"]["nire_quality_status"] = "VERIFIED"
            feat["properties"]["data_source"] = "TELECOM_DB"
            features.append(_enrich_feature_typing(feat, "point"))
            feature_id += 1
        return {"type": "FeatureCollection", "features": features, "meta": {"source_kind": "TELECOM_DB", "kpi_included": True}}

    for row in list_infrastructure(operator_code=operator_code, limit=100000):
        feat = _feature_from_row(row, "infra_name", "infra_type", feature_id)
        feat["properties"]["data_source"] = "TELECOM_DB"
        features.append(_enrich_feature_typing(feat, "point"))
        feature_id += 1
    for row in list_network_lines(operator_code=operator_code, limit=100000):
        feat = _feature_from_row(row, "line_name", "line_type", feature_id)
        feat["properties"]["data_source"] = "TELECOM_DB"
        features.append(_enrich_feature_typing(feat, "line"))
        feature_id += 1
    # Polygones de couverture exclus des couches Fiberco/FTTX/Fibre-MW combiné
    # (ne pas les présenter comme des objets fibre).
    return {
        "type": "FeatureCollection",
        "features": features,
        "meta": {
            "source_kind": "TELECOM_DB",
            "operator_code": operator_code,
            "kpi_included": True,
            "coverage_polygons_excluded": True,
        },
    }


def _typed_backbone_geojson(*, asset_filter: str, limit: int = 50000) -> dict[str, Any]:
    """Sous-couches Fibre vs Microwave dérivées sans mutation des sources."""
    from api.services.telecom_asset_typing import classify_telecom_asset, is_microwave_asset

    features: list[dict[str, Any]] = []
    feature_id = 1

    def maybe_add(row: dict[str, Any], name_key: str, type_key: str, geometry_kind: str, ops: set[str]) -> None:
        nonlocal feature_id
        if row.get("operator_code") not in ops:
            return
        typed = classify_telecom_asset(row, geometry_kind=geometry_kind)
        is_mw = is_microwave_asset(row, geometry_kind=geometry_kind)
        # FIBER_MW footprint (1515 lines) → couche microwave ; Fiberco/FTTX → fibre
        if asset_filter == "MICROWAVE":
            if row.get("operator_code") != "FIBER_MW" and not is_mw:
                return
            if row.get("operator_code") == "FIBER_MW" or is_mw:
                pass
            else:
                return
        elif asset_filter == "FIBER":
            if row.get("operator_code") == "FIBER_MW" and not is_mw:
                # Inclure aussi les tronçons Fiber/MW non explicitement MW comme fibre backbone
                pass
            elif row.get("operator_code") in {"FIBERCO", "FTTX"}:
                pass
            elif is_mw:
                return
            else:
                return
            if row.get("operator_code") == "FIBER_MW" and asset_filter == "FIBER":
                # Éviter double comptage massif : fibre pure = Fiberco+FTTX ; FIBER_MW va à microwave
                return

        feat = _feature_from_row(row, name_key, type_key, feature_id)
        feat["properties"].update(typed)
        feat["properties"]["data_source"] = "TELECOM_DB"
        feat["properties"]["source_label"] = "Référentiel télécom"
        features.append(feat)
        feature_id += 1

    if asset_filter == "FIBER":
        ops = {"FIBERCO", "FTTX"}
    else:
        ops = {"FIBER_MW"}

    for row in list_infrastructure(limit=100000):
        maybe_add(row, "infra_name", "infra_type", "point", ops)
        if len(features) >= limit:
            break
    for row in list_network_lines(limit=100000):
        maybe_add(row, "line_name", "line_type", "line", ops)
        if len(features) >= limit:
            break
    # Couverture polygones ≠ fibre / MW — exclus des couches typées Fibre & Microwave.
    # (Les polygones restent accessibles via /coverage-polygons si besoin métier.)

    return {
        "type": "FeatureCollection",
        "features": features[:limit],
        "meta": {
            "source_kind": "TELECOM_DB_TYPED",
            "asset_filter": asset_filter,
            "returned": min(len(features), limit),
            "coverage_polygons_excluded": True,
            "kpi_included": True,
        },
    }


def resolve_layer_geojson(layer_key: str, *, limit: int = 5000) -> dict[str, Any]:
    """Résout une couche catalogue : consolidé opérateurs, DB, typée, ou FDSU MNO."""
    from api.services.telecom_layer_catalog import get_layer_definition

    definition = get_layer_definition(layer_key)
    if not definition and layer_key not in LAYER_OPERATOR_MAP:
        return {"type": "FeatureCollection", "features": [], "meta": {"error": "unknown_layer"}}

    source_kind = (definition or {}).get("source_kind") or "TELECOM_DB"

    if source_kind == "OPERATOR_SITES_CONSOLIDATED":
        from api.services.telecom_operator_sites_consolidation import (
            build_consolidated_operator_geojson,
        )

        op = (definition or {}).get("operator_code") or LAYER_OPERATOR_MAP.get(layer_key)
        return build_consolidated_operator_geojson(str(op or ""), limit=limit)

    if source_kind == "FDSU_MNO_AUDIT":
        from api.services.nire import mno_audit

        planned_only = (definition or {}).get("filter") == "PLANNED"
        operator = None if planned_only else (definition or {}).get("operator_code")
        return mno_audit.layer_geojson(
            operator,
            limit=limit,
            include_planned=True,
            planned_only=planned_only,
            ensure_loaded=True,
        )

    if source_kind == "TELECOM_DB_TYPED":
        return _typed_backbone_geojson(asset_filter=(definition or {}).get("asset_filter") or "FIBER", limit=limit)

    payload = layer_to_geojson(layer_key)
    # Plafond Soft pour couches denses (FTTX)
    feats = payload.get("features") or []
    if len(feats) > limit:
        payload = {**payload, "features": feats[:limit], "meta": {**(payload.get("meta") or {}), "capped": True, "returned": limit}}
    return payload


def ensure_operator_metadata(operator_code: str, operator_name: str, operator_type: str = "MNO") -> None:
    """Insert opérateur métadonnées sans créer d'infrastructures KPI."""
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO telecom.operators (operator_code, operator_name, operator_type, status)
                VALUES (%s, %s, %s, 'ACTIVE')
                ON CONFLICT (operator_code) DO UPDATE
                SET operator_name = EXCLUDED.operator_name,
                    operator_type = EXCLUDED.operator_type,
                    updated_at = NOW()
                """,
                (operator_code, operator_name, operator_type),
            )
        conn.commit()


def ensure_fdsu_mobile_operators() -> None:
    ensure_operator_metadata("AIRTEL", "Airtel", "MNO")
    ensure_operator_metadata("AFRICELL", "Africell", "MNO")
    ensure_operator_metadata("VODACOM", "Vodacom", "MNO")
    ensure_operator_metadata("ORANGE", "Orange RDC", "MNO")


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
        "fdsu_note": (
            "Couches FDSU MNO (Airtel/Africell/Planned) visibles avec statut NIRE ; "
            "exclues du KPI COUNT(telecom.infrastructure)."
        ),
    }


def ensure_fdsu_staging_table() -> None:
    from pathlib import Path

    sql_path = Path(__file__).resolve().parents[2] / "database" / "telecom_fdsu_mno_staging.sql"
    ddl = sql_path.read_text(encoding="utf-8")
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute(ddl)
        conn.commit()


def sync_fdsu_mno_staging_from_audit(*, max_rows: int = 20000) -> dict[str, Any]:
    """Matérialise les sites FDSU MNO hors KPI pour relations PostGIS. Pas d'enqueue NIRE."""
    from api.services.nire import mno_audit

    ensure_fdsu_staging_table()
    if not mno_audit.get_state().executed:
        mno_audit.run_mno_audit(enqueue_reviews=False)
    rows = [r for r in mno_audit.get_state().rows if r.get("geometry_valid")]
    synced = 0
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE telecom.fdsu_mno_sites")
            for r in rows[:max_rows]:
                cur.execute(
                    """
                    INSERT INTO telecom.fdsu_mno_sites (
                        row_id, operator_code, site_name, status_normalized, rat,
                        nire_classification, nire_quality_status, requires_human_review,
                        latitude, longitude, geom, source_file, source_row, source_hash, properties
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                        %s, %s, %s, %s::jsonb
                    )
                    """,
                    (
                        r["row_id"],
                        r["operator"],
                        r["site_name_original"],
                        r.get("status_normalized"),
                        r.get("rat_normalized") or r.get("rat_original"),
                        r.get("classification"),
                        mno_audit.nire_quality_status(r),
                        bool(r.get("requires_human_review")),
                        float(r["latitude"]),
                        float(r["longitude"]),
                        float(r["longitude"]),
                        float(r["latitude"]),
                        r.get("source_file"),
                        r.get("source_row"),
                        r.get("source_hash"),
                        Json(
                            {
                                "secondary_flags": r.get("secondary_flags") or [],
                                "kpi_excluded": True,
                            }
                        ),
                    ),
                )
                synced += 1
        conn.commit()
    return {
        "synced": synced,
        "kpi_untouched": True,
        "table": "telecom.fdsu_mno_sites",
        "note": "Staging hors COUNT(telecom.infrastructure)",
    }


def _nearest_mno_audit_operator(lat: float, lon: float, operator_code: str, radius_m: float) -> dict[str, Any] | None:
    """Fallback spatial Airtel/Africell via audit MNO en mémoire (si staging vide)."""
    try:
        from api.services.nire import mno_audit
        from api.services.nire.mno_audit import haversine_m

        if not mno_audit._STATE.executed:  # noqa: SLF001
            mno_audit.run_mno_audit(enqueue_reviews=False)
        best = None
        best_d = float("inf")
        for r in mno_audit._STATE.rows:  # noqa: SLF001
            if r.get("operator") != operator_code or not r.get("geometry_valid"):
                continue
            if (r.get("status_normalized") or "") == "PLANNED":
                continue
            d = haversine_m((lat, lon), (float(r["latitude"]), float(r["longitude"])))
            if d <= radius_m and d < best_d:
                best_d = d
                best = r
        if not best:
            return None
        return {
            "row_id": best.get("row_id"),
            "infra_name": best.get("site_name_original"),
            "site_name": best.get("site_name_original"),
            "operator_code": best.get("operator"),
            "operator_name": str(best.get("operator") or "").title(),
            "status_normalized": best.get("status_normalized"),
            "nire_quality_status": mno_audit.nire_quality_status(best),
            "latitude": best.get("latitude"),
            "longitude": best.get("longitude"),
            "distance_m": best_d,
            "data_source": "FDSU_MNO_AUDIT",
        }
    except Exception:
        return None


def _nearest_fdsu_operator(lat: float, lon: float, operator_code: str, radius_m: float) -> dict[str, Any] | None:
    """Nearest Airtel/Africell via staging PostGIS (préféré) puis audit mémoire.

    Important perf : ne pas relancer run_mno_audit à chaque dossier.
    SharedSpatialContext.ensure_fdsu_mno_staging_ready synchronise la table une fois
    si elle est vide ; ensuite les requêtes GiST restent < 10 ms.
    """
    try:
        from api.services import shared_spatial_context as ssc

        ssc.ensure_fdsu_mno_staging_ready(sync_if_empty=True)
    except Exception:
        ensure_fdsu_staging_table()
    try:
        with connect_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # KNN geometry (index GiST) puis distance geography — évite cast geography dans ORDER BY
                cur.execute(
                    """
                    SELECT row_id, operator_code, site_name, status_normalized, nire_quality_status,
                           latitude, longitude,
                           ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) AS distance_m
                    FROM telecom.fdsu_mno_sites
                    WHERE operator_code = %s AND geom IS NOT NULL
                    ORDER BY geom <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)
                    LIMIT 1
                    """,
                    (lon, lat, operator_code, lon, lat),
                )
                row = cur.fetchone()
                if row:
                    out = _serialize_row(dict(row))
                    dist = out.get("distance_m")
                    if dist is not None and float(dist) > float(radius_m):
                        return None
                    out["data_source"] = "FDSU_MNO_STAGING"
                    return out
    except Exception:
        pass
    return _nearest_mno_audit_operator(lat, lon, operator_code, radius_m)


def _nearest_db_operator(lat: float, lon: float, operator_code: str, radius_m: float) -> dict[str, Any] | None:
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT i.id, i.infra_name, i.infra_type, i.technology, o.operator_code, o.operator_name,
                       i.latitude, i.longitude,
                       ST_Distance(i.geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) AS distance_m
                FROM telecom.infrastructure i
                JOIN telecom.operators o ON o.id = i.operator_id
                WHERE o.operator_code = %s AND i.geom IS NOT NULL
                  AND ST_DWithin(i.geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s)
                ORDER BY i.geom::geography <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                LIMIT 1
                """,
                (lon, lat, operator_code, lon, lat, radius_m, lon, lat),
            )
            row = cur.fetchone()
            return _serialize_row(dict(row)) if row else None


def nearest_fiber_link(lat: float, lon: float, *, radius_m: float = 25000) -> dict[str, Any] | None:
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT l.id, l.line_name, l.line_type, l.technology, o.operator_code, o.operator_name,
                       ST_Distance(l.geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) AS distance_m
                FROM telecom.network_lines l
                JOIN telecom.operators o ON o.id = l.operator_id
                WHERE o.operator_code IN ('FIBERCO', 'FTTX') AND l.geom IS NOT NULL
                  AND ST_DWithin(l.geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s)
                ORDER BY l.geom::geography <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                LIMIT 1
                """,
                (lon, lat, lon, lat, radius_m, lon, lat),
            )
            row = cur.fetchone()
            return _serialize_row(dict(row)) if row else None


def nearest_microwave_link(lat: float, lon: float, *, radius_m: float = 25000) -> dict[str, Any] | None:
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT l.id, l.line_name, l.line_type, l.technology, o.operator_code, o.operator_name,
                       ST_Distance(l.geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) AS distance_m
                FROM telecom.network_lines l
                JOIN telecom.operators o ON o.id = l.operator_id
                WHERE o.operator_code = 'FIBER_MW' AND l.geom IS NOT NULL
                  AND ST_DWithin(l.geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s)
                ORDER BY l.geom::geography <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                LIMIT 1
                """,
                (lon, lat, lon, lat, radius_m, lon, lat),
            )
            row = cur.fetchone()
            return _serialize_row(dict(row)) if row else None


_SPATIAL_TLS = threading.local()


def spatial_context_around(lat: float, lon: float, *, radius_m: float = 25000) -> dict[str, Any]:
    """Relations spatiales étendues pour un site / infrastructure.

    Prépare le staging FDSU MNO une fois, puis exécute les nearest en parallèle
    sauf si déjà dans un pool (évite ThreadPool imbriqués).
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    try:
        from api.services import shared_spatial_context as ssc

        ssc.ensure_fdsu_mno_staging_ready(sync_if_empty=True)
    except Exception:
        pass

    tasks = {
        "nearest_any": lambda: nearest_infrastructure(lat, lon, radius_m=radius_m, limit=5),
        "vodacom": lambda: _nearest_db_operator(lat, lon, "VODACOM", radius_m),
        "orange": lambda: _nearest_db_operator(lat, lon, "ORANGE", radius_m),
        "airtel": lambda: _nearest_fdsu_operator(lat, lon, "AIRTEL", radius_m),
        "africell": lambda: _nearest_fdsu_operator(lat, lon, "AFRICELL", radius_m),
        "fiber": lambda: nearest_fiber_link(lat, lon, radius_m=radius_m),
        "mw": lambda: nearest_microwave_link(lat, lon, radius_m=radius_m),
    }
    results: dict[str, Any] = {}
    nested = bool(getattr(_SPATIAL_TLS, "in_pool", False))
    if nested:
        for name, fn in tasks.items():
            try:
                results[name] = fn()
            except Exception:
                results[name] = None if name != "nearest_any" else {
                    "data_available": False,
                    "search_executed": False,
                    "nearest": None,
                    "facilities": [],
                }
    else:
        _SPATIAL_TLS.in_pool = True
        try:
            with ThreadPoolExecutor(max_workers=4) as pool:
                futures = {pool.submit(fn): name for name, fn in tasks.items()}
                for fut in as_completed(futures):
                    name = futures[fut]
                    try:
                        results[name] = fut.result()
                    except Exception:
                        results[name] = None if name != "nearest_any" else {
                            "data_available": False,
                            "search_executed": False,
                            "nearest": None,
                            "facilities": [],
                        }
        finally:
            _SPATIAL_TLS.in_pool = False

    nearest_any = results.get("nearest_any") or {}
    vodacom = results.get("vodacom")
    orange = results.get("orange")
    airtel = results.get("airtel")
    africell = results.get("africell")
    fiber = results.get("fiber")
    mw = results.get("mw")

    nearby_ops = []
    for code, hit in (("VODACOM", vodacom), ("ORANGE", orange), ("AIRTEL", airtel), ("AFRICELL", africell)):
        if hit and float(hit.get("distance_m") or 1e12) <= min(radius_m, 500):
            nearby_ops.append(code)

    fiber_dist = float(fiber["distance_m"]) if fiber and fiber.get("distance_m") is not None else None
    backhaul = bool(fiber and fiber_dist is not None and fiber_dist <= 5000) or bool(
        mw and float(mw.get("distance_m") or 1e12) <= 5000
    )
    mutualization = len(nearby_ops) >= 2

    return {
        "search_executed": True,
        "radius_m": radius_m,
        "nearest_infrastructure": nearest_any.get("nearest"),
        "NEAREST_MNO_VODACOM": vodacom,
        "NEAREST_MNO_ORANGE": orange,
        "NEAREST_MNO_AIRTEL": airtel,
        "NEAREST_MNO_AFRICELL": africell,
        "NEAREST_FIBER_LINK": fiber,
        "DISTANCE_TO_FIBER_M": fiber_dist,
        "NEAREST_MICROWAVE_LINK": mw,
        "MULTI_OPERATOR_PROXIMITY": nearby_ops,
        "COLOCATION_SIGNAL": mutualization,
        "BACKHAUL_CANDIDATE": backhaul,
        "MUTUALIZATION_POTENTIAL": mutualization or backhaul,
        "kpi_national_untouched": True,
        "data_absence_vs_error": {
            "NEAREST_MNO_AIRTEL": "none" if airtel else "no_site_within_radius_or_unloaded",
            "NEAREST_MNO_AFRICELL": "none" if africell else "no_site_within_radius_or_unloaded",
            "NEAREST_FIBER_LINK": "none" if fiber else "no_link_within_radius",
            "NEAREST_MICROWAVE_LINK": "none" if mw else "no_link_within_radius",
        },
    }
