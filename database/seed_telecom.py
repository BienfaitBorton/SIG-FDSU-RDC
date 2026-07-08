#!/usr/bin/env python3
"""Importe le référentiel télécom national depuis les KMZ source vers PostgreSQL/PostGIS."""

from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

import psycopg2
from psycopg2.extras import Json

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import DATABASE_URL

KML_NS = {"kml": "http://www.opengis.net/kml/2.2"}
TELECOM_DIR = PROJECT_ROOT / "data" / "sectoral" / "telecom"
RAW_DIR = TELECOM_DIR / "raw"
PROCESSED_DIR = TELECOM_DIR / "processed"
SCHEMA_SQL = PROJECT_ROOT / "database" / "telecom_schema.sql"

OPERATORS = [
    {
        "operator_code": "VODACOM",
        "operator_name": "Vodacom",
        "operator_type": "MNO",
    },
    {
        "operator_code": "ORANGE",
        "operator_name": "Orange RDC",
        "operator_type": "MNO",
    },
    {
        "operator_code": "FIBER_MW",
        "operator_name": "Fibre / Micro-ondes",
        "operator_type": "BACKBONE",
    },
    {
        "operator_code": "FIBERCO",
        "operator_name": "Fiberco",
        "operator_type": "FIBER",
    },
    {
        "operator_code": "FTTX",
        "operator_name": "FTTX",
        "operator_type": "FTTX",
    },
]

KMZ_SOURCES = [
    {
        "file": "20260623_vdc_sites_database.csv.kmz",
        "operator_code": "VODACOM",
        "default_infra_type": "radio_site",
        "default_line_type": "transmission",
        "default_polygon_type": "coverage",
        "technology": "Radio",
    },
    {
        "file": "orange_existing_infrastructures_decembre_2025.kmz",
        "operator_code": "ORANGE",
        "default_infra_type": "radio_site",
        "default_line_type": "transmission",
        "default_polygon_type": "coverage",
        "technology": "Radio",
    },
    {
        "file": "08092023_fiber_mw_footprint.kmz",
        "operator_code": "FIBER_MW",
        "default_infra_type": "node",
        "default_line_type": "fiber_mw",
        "default_polygon_type": "footprint",
        "technology": "Fiber/MW",
    },
    {
        "file": "fiberco_view.kmz",
        "operator_code": "FIBERCO",
        "default_infra_type": "node",
        "default_line_type": "fiber",
        "default_polygon_type": "coverage",
        "technology": "Fiber",
    },
    {
        "file": "fttx.kmz",
        "operator_code": "FTTX",
        "default_infra_type": "fttx_node",
        "default_line_type": "fttx",
        "default_polygon_type": "fttx_coverage",
        "technology": "FTTX",
    },
]


def parse_kml_fields(placemark: ET.Element) -> dict[str, str]:
    fields: dict[str, str] = {}
    extended = placemark.find("kml:ExtendedData", KML_NS)
    if extended is not None:
        for data in extended.findall("kml:Data", KML_NS):
            name = data.get("name", "")
            value_el = data.find("kml:value", KML_NS)
            fields[name] = (value_el.text or "").strip() if value_el is not None else ""
    for simple_data in placemark.findall(".//kml:SimpleData", KML_NS):
        fields[simple_data.get("name", "")] = (simple_data.text or "").strip()
    return fields


def pick_field(fields: dict[str, str], *candidates: str) -> str:
    normalized = {
        re.sub(r"\s+", " ", key.strip().lower()): value
        for key, value in fields.items()
    }
    for candidate in candidates:
        key = re.sub(r"\s+", " ", candidate.strip().lower())
        if key in normalized and normalized[key]:
            return normalized[key]
    for candidate in candidates:
        for key, value in fields.items():
            if candidate.lower() in key.lower() and value:
                return value
    return ""


def parse_position(text: str) -> tuple[float, float] | None:
    parts = [part for part in text.strip().split(",") if part != ""]
    if len(parts) < 2:
        return None
    try:
        lon = float(parts[0])
        lat = float(parts[1])
        return lon, lat
    except ValueError:
        return None


def parse_linear_ring(element: ET.Element) -> list[tuple[float, float]]:
    coords_el = element.find(".//kml:coordinates", KML_NS)
    if coords_el is None or not coords_el.text:
        return []
    positions = []
    for token in coords_el.text.strip().split():
        parsed = parse_position(token)
        if parsed:
            positions.append(parsed)
    return positions


def parse_linestring(element: ET.Element) -> list[tuple[float, float]]:
    line = element if element.tag.endswith("LineString") else element.find("kml:LineString", KML_NS)
    if line is None:
        return []
    coords_el = line.find("kml:coordinates", KML_NS)
    if coords_el is None or not coords_el.text:
        return []
    positions = []
    for token in re.split(r"\s+", coords_el.text.strip()):
        parsed = parse_position(token)
        if parsed:
            positions.append(parsed)
    return positions


def parse_polygon(element: ET.Element) -> list[list[tuple[float, float]]]:
    polygon = element if element.tag.endswith("Polygon") else element.find("kml:Polygon", KML_NS)
    if polygon is None:
        return []
    rings = []
    outer = polygon.find("kml:outerBoundaryIs/kml:LinearRing", KML_NS)
    if outer is not None:
        ring = parse_linear_ring(outer)
        if len(ring) >= 3:
            rings.append(ring)
    for inner in polygon.findall("kml:innerBoundaryIs/kml:LinearRing", KML_NS):
        ring = parse_linear_ring(inner)
        if len(ring) >= 3:
            rings.append(ring)
    return rings


def iter_geometries(element: ET.Element) -> list[tuple[str, Any]]:
    results: list[tuple[str, Any]] = []
    if element is None:
        return results

    tag = element.tag.split("}")[-1]
    if tag == "Point":
        coords_el = element.find("kml:coordinates", KML_NS)
        if coords_el is not None and coords_el.text:
            parsed = parse_position(coords_el.text.strip().split()[0])
            if parsed:
                results.append(("Point", parsed))
        return results

    if tag == "LineString":
        line = parse_linestring(element)
        if len(line) >= 2:
            results.append(("LineString", line))
        return results

    if tag == "LinearRing":
        ring = parse_linear_ring(element)
        if len(ring) >= 3:
            results.append(("Polygon", [ring]))
        return results

    if tag == "Polygon":
        rings = parse_polygon(element)
        if rings:
            results.append(("Polygon", rings))
        return results

    if tag == "MultiGeometry":
        for child in list(element):
            results.extend(iter_geometries(child))
        return results

    for child in list(element):
        if child.tag.endswith(("Point", "LineString", "Polygon", "LinearRing", "MultiGeometry")):
            results.extend(iter_geometries(child))
    return results


def iter_placemarks(root: ET.Element):
    for placemark in root.findall(".//kml:Placemark", KML_NS):
        yield placemark


def extract_kml(kmz_path: Path) -> str:
    with zipfile.ZipFile(kmz_path) as archive:
        kml_name = next((name for name in archive.namelist() if name.lower().endswith(".kml")), "doc.kml")
        return archive.read(kml_name).decode("utf-8", errors="replace")


def wkt_point(lon: float, lat: float) -> str:
    return f"SRID=4326;POINT({lon} {lat})"


def wkt_linestring(coords: list[tuple[float, float]]) -> str | None:
    if len(coords) < 2:
        return None
    parts = ", ".join(f"{lon} {lat}" for lon, lat in coords)
    return f"SRID=4326;LINESTRING({parts})"


def close_ring(ring: list[tuple[float, float]]) -> list[tuple[float, float]]:
    if not ring:
        return ring
    if ring[0] != ring[-1]:
        return [*ring, ring[0]]
    return ring


def wkt_polygon(rings: list[list[tuple[float, float]]]) -> str | None:
    ring_parts = []
    for ring in rings:
        closed = close_ring(ring)
        if len(closed) < 4:
            continue
        coords = ", ".join(f"{lon} {lat}" for lon, lat in closed)
        ring_parts.append(f"({coords})")
    if not ring_parts:
        return None
    return f"SRID=4326;POLYGON({', '.join(ring_parts)})"


def apply_schema(conn) -> None:
    sql = SCHEMA_SQL.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def seed_operators(conn) -> dict[str, int]:
    operator_ids: dict[str, int] = {}
    with conn.cursor() as cur:
        cur.execute("DELETE FROM telecom.coverage_polygons")
        cur.execute("DELETE FROM telecom.network_lines")
        cur.execute("DELETE FROM telecom.infrastructure")
        cur.execute("DELETE FROM telecom.operators")
        for operator in OPERATORS:
            cur.execute(
                """
                INSERT INTO telecom.operators (operator_code, operator_name, operator_type, country, status)
                VALUES (%s, %s, %s, 'RDC', 'ACTIVE')
                RETURNING id
                """,
                (operator["operator_code"], operator["operator_name"], operator["operator_type"]),
            )
            operator_ids[operator["operator_code"]] = int(cur.fetchone()[0])
    conn.commit()
    return operator_ids


def import_kmz_source(
    conn,
    source: dict[str, Any],
    operator_ids: dict[str, int],
) -> dict[str, int]:
    kmz_path = RAW_DIR / source["file"]
    if not kmz_path.is_file():
        raise FileNotFoundError(f"KMZ introuvable: {kmz_path}")

    operator_id = operator_ids[source["operator_code"]]
    kml_text = extract_kml(kmz_path)
    kml_path = RAW_DIR / f"{kmz_path.stem}.kml"
    kml_path.write_text(kml_text, encoding="utf-8")

    root = ET.fromstring(kml_text)
    counts = {"points": 0, "lines": 0, "polygons": 0}
    features: list[dict[str, Any]] = []

    with conn.cursor() as cur:
        for index, placemark in enumerate(iter_placemarks(root), start=1):
            fields = parse_kml_fields(placemark)
            name = (
                pick_field(fields, "name", "site_name", "Site_name", "Site Name", "Nom")
                or (placemark.findtext("kml:name", default="", namespaces=KML_NS) or "").strip()
                or f"Objet {index}"
            )
            province = pick_field(fields, "Province", "province", "PROVINCE")
            territoire = pick_field(fields, "Territoire", "territoire", "TERRITOIRE", "District")
            status = pick_field(fields, "Status", "status", "Statut")
            properties = {key: value for key, value in fields.items() if value not in (None, "")}
            if name and "name" not in properties:
                properties["name"] = name

            geometry_root = placemark.find("kml:Point", KML_NS)
            if geometry_root is None:
                geometry_root = placemark.find("kml:LineString", KML_NS)
            if geometry_root is None:
                geometry_root = placemark.find("kml:Polygon", KML_NS)
            if geometry_root is None:
                geometry_root = placemark.find("kml:MultiGeometry", KML_NS)

            geometries = iter_geometries(geometry_root) if geometry_root is not None else []
            if not geometries:
                continue

            for geom_index, (geom_type, geom_value) in enumerate(geometries, start=1):
                code_suffix = f"{index}-{geom_index}" if len(geometries) > 1 else str(index)
                try:
                    if geom_type == "Point":
                        lon, lat = geom_value
                        cur.execute(
                            """
                            INSERT INTO telecom.infrastructure (
                                operator_id, infra_code, infra_name, infra_type, technology, source_file,
                                province, territoire, status, latitude, longitude, geom, properties
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, ST_GeomFromEWKT(%s), %s)
                            """,
                            (
                                operator_id,
                                pick_field(fields, "site_code", "code", "Site_ID", "ID") or f"{source['operator_code']}-{code_suffix}",
                                name,
                                pick_field(fields, "infra_type", "type", "Type") or source["default_infra_type"],
                                pick_field(fields, "technology", "Technology") or source["technology"],
                                source["file"],
                                province or None,
                                territoire or None,
                                status or None,
                                lat,
                                lon,
                                wkt_point(lon, lat),
                                Json(properties),
                            ),
                        )
                        counts["points"] += 1
                        features.append(
                            {
                                "type": "Feature",
                                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                                "properties": {**properties, "source_file": source["file"], "operator_code": source["operator_code"]},
                            }
                        )
                    elif geom_type == "LineString":
                        line_wkt = wkt_linestring(geom_value)
                        if not line_wkt:
                            continue
                        cur.execute(
                            """
                            INSERT INTO telecom.network_lines (
                                operator_id, line_code, line_name, line_type, technology, source_file, geom, properties
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, ST_GeomFromEWKT(%s), %s)
                            """,
                            (
                                operator_id,
                                pick_field(fields, "line_code", "code", "ID") or f"{source['operator_code']}-L-{code_suffix}",
                                name,
                                pick_field(fields, "line_type", "type", "Type") or source["default_line_type"],
                                pick_field(fields, "technology", "Technology") or source["technology"],
                                source["file"],
                                line_wkt,
                                Json(properties),
                            ),
                        )
                        counts["lines"] += 1
                        features.append(
                            {
                                "type": "Feature",
                                "geometry": {"type": "LineString", "coordinates": [[lon, lat] for lon, lat in geom_value]},
                                "properties": {**properties, "source_file": source["file"], "operator_code": source["operator_code"]},
                            }
                        )
                    elif geom_type == "Polygon":
                        polygon_wkt = wkt_polygon(geom_value)
                        if not polygon_wkt:
                            continue
                        cur.execute(
                            """
                            INSERT INTO telecom.coverage_polygons (
                                operator_id, polygon_code, polygon_name, polygon_type, technology, source_file, geom, properties
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, ST_GeomFromEWKT(%s), %s)
                            """,
                            (
                                operator_id,
                                pick_field(fields, "polygon_code", "code", "ID") or f"{source['operator_code']}-P-{code_suffix}",
                                name,
                                pick_field(fields, "polygon_type", "type", "Type") or source["default_polygon_type"],
                                pick_field(fields, "technology", "Technology") or source["technology"],
                                source["file"],
                                polygon_wkt,
                                Json(properties),
                            ),
                        )
                        counts["polygons"] += 1
                        features.append(
                            {
                                "type": "Feature",
                                "geometry": {
                                    "type": "Polygon",
                                    "coordinates": [[[lon, lat] for lon, lat in close_ring(ring)] for ring in geom_value if len(close_ring(ring)) >= 4],
                                },
                                "properties": {**properties, "source_file": source["file"], "operator_code": source["operator_code"]},
                            }
                        )
                except Exception:
                    continue

    conn.commit()
    processed_path = PROCESSED_DIR / f"{kmz_path.stem}.geojson"
    processed_path.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return counts


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    summary: dict[str, dict[str, int]] = {}
    totals = {"points": 0, "lines": 0, "polygons": 0}

    with psycopg2.connect(DATABASE_URL) as conn:
        print("Application du schema telecom...")
        apply_schema(conn)
        print("Initialisation des operateurs...")
        operator_ids = seed_operators(conn)
        for source in KMZ_SOURCES:
            print(f"Import {source['file']} -> {source['operator_code']}...")
            counts = import_kmz_source(conn, source, operator_ids)
            summary[source["file"]] = counts
            for key, value in counts.items():
                totals[key] += value
            print(f"  points={counts['points']} lines={counts['lines']} polygons={counts['polygons']}")

    print("")
    print("=== Import referentiel telecom termine ===")
    print(f"Operateurs : {len(OPERATORS)}")
    print(f"Points     : {totals['points']}")
    print(f"Lignes     : {totals['lines']}")
    print(f"Polygones  : {totals['polygons']}")
    for file_name, counts in summary.items():
        print(f"  - {file_name}: {counts['points']} pts / {counts['lines']} lignes / {counts['polygons']} polygones")


if __name__ == "__main__":
    main()
