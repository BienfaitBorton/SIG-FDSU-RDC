#!/usr/bin/env python3
"""Import du référentiel Santé FDSU depuis le KMZ officiel des établissements sanitaires."""

from __future__ import annotations

import hashlib
import json
import sys
import unicodedata
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg2
from psycopg2.extras import Json, RealDictCursor, execute_values

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import DATABASE_URL

KML_NS = {"kml": "http://www.opengis.net/kml/2.2"}
DATA_SOURCE = "RDC_ESS_Santé_01042026.csv.kmz"

RAW_DIR = PROJECT_ROOT / "data" / "health" / "facilities" / "raw"
KMZ_PATH = RAW_DIR / DATA_SOURCE
KML_PATH = RAW_DIR / "doc.kml"
OUT_DIR = PROJECT_ROOT / "data" / "health" / "facilities"
GEOJSON_PATH = OUT_DIR / "health_facilities.geojson"
JSON_PATH = OUT_DIR / "health_facilities.json"

FACILITY_TYPES = [
    ("HGR", "Hôpital Général de Référence", "Hôpital de référence", "hospital", {"color": "#dc2626", "icon": "hospital"}),
    ("HOSPITAL", "Hôpital", "Hôpital", "hospital", {"color": "#b91c1c", "icon": "hospital"}),
    ("CH", "Centre Hospitalier", "Centre hospitalier", "hospital", {"color": "#ef4444", "icon": "hospital"}),
    ("CS", "Centre de Santé", "Centre de santé de proximité", "health_center", {"color": "#ea580c", "icon": "clinic"}),
    ("CSR", "Centre de Santé de Référence", "Centre de santé de référence", "health_center", {"color": "#f97316", "icon": "clinic"}),
    ("PS", "Poste de Santé", "Poste de santé communautaire", "health_post", {"color": "#eab308", "icon": "health-post"}),
    ("CM", "Centre Médical", "Centre médical", "clinic", {"color": "#a855f7", "icon": "clinic"}),
    ("CLINIC", "Clinique", "Clinique privée ou associée", "clinic", {"color": "#8b5cf6", "icon": "clinic"}),
    ("POLYCLINIC", "Polyclinique", "Polyclinique", "clinic", {"color": "#7c3aed", "icon": "clinic"}),
    ("DISP", "Dispensaire", "Dispensaire", "health_post", {"color": "#ca8a04", "icon": "health-post"}),
    ("SSC", "Site Soin Communautaire", "Site de soin communautaire", "community", {"color": "#16a34a", "icon": "community"}),
    ("BCZS", "Bureau Central de la Zone de Santé", "Bureau central de zone de santé", "admin", {"color": "#0f766e", "icon": "admin"}),
    ("MAT", "Maternité", "Structure maternelle", "maternity", {"color": "#ec4899", "icon": "maternity"}),
    ("OTHER", "Autre structure sanitaire", "Autre type de structure", "other", {"color": "#64748b", "icon": "other"}),
]

TYPE_RULES: list[tuple[str, str]] = [
    ("hopital general de reference", "HGR"),
    ("centre de sante de reference", "CSR"),
    ("bureau central de la zone de sante", "BCZS"),
    ("site soin communautaire", "SSC"),
    ("centre hopitalier", "CH"),
    ("centre hospitalier", "CH"),
    ("centre medical", "CM"),
    ("centre de sante", "CS"),
    ("poste de sante", "PS"),
    ("polyclinique", "POLYCLINIC"),
    ("polyclinque", "POLYCLINIC"),
    ("dispensaire", "DISP"),
    ("clinique", "CLINIC"),
    ("hopital", "HOSPITAL"),
]


def fold_text(value: str | None) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.lower().replace("_", " ").split())


def normalize_facility_type(esstype: str | None) -> str:
    folded = fold_text(esstype)
    if not folded:
        return "OTHER"
    for needle, code in TYPE_RULES:
        if needle in folded:
            return code
    return "OTHER"


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).replace("\xa0", " ").split()).strip()
    return text or None


def parse_float(value: str | None) -> float | None:
    text = clean_text(value)
    if text is None:
        return None
    try:
        return float(text.replace(",", "."))
    except ValueError:
        return None


def extract_simple_data(placemark: ET.Element) -> dict[str, str]:
    data: dict[str, str] = {}
    for node in placemark.findall(".//kml:SimpleData", KML_NS):
        key = node.attrib.get("name")
        if not key:
            continue
        data[key] = (node.text or "").strip()
    return data


def extract_coordinates(placemark: ET.Element, simple: dict[str, str]) -> tuple[float | None, float | None]:
    lon = parse_float(simple.get("Longitude"))
    lat = parse_float(simple.get("Latitude"))
    if lon is not None and lat is not None:
        return lon, lat

    coords_el = placemark.find(".//kml:coordinates", KML_NS)
    if coords_el is None or not coords_el.text:
        return None, None
    parts = coords_el.text.strip().split(",")
    if len(parts) < 2:
        return None, None
    try:
        return float(parts[0]), float(parts[1])
    except ValueError:
        return None, None


def build_official_code(
    zs_uid: str | None,
    as_uid: str | None,
    name: str | None,
    lon: float | None,
    lat: float | None,
    esstype: str | None,
    index: int,
) -> str:
    payload = "|".join(
        [
            zs_uid or "",
            as_uid or "",
            name or "",
            f"{lon:.8f}" if lon is not None else "",
            f"{lat:.8f}" if lat is not None else "",
            esstype or "",
            str(index),
        ]
    )
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:10]
    left = zs_uid or "NA"
    right = as_uid or "NA"
    return f"{left}_{right}_{digest}"


def extract_kml() -> Path:
    if not KMZ_PATH.exists():
        raise FileNotFoundError(f"KMZ introuvable: {KMZ_PATH}")
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(KMZ_PATH) as archive:
        names = archive.namelist()
        kml_name = next((name for name in names if name.lower().endswith(".kml")), None)
        if not kml_name:
            raise RuntimeError("Aucun fichier KML dans le KMZ.")
        kml_bytes = archive.read(kml_name)
    KML_PATH.write_bytes(kml_bytes)
    return KML_PATH


def parse_facilities(kml_path: Path) -> list[dict[str, Any]]:
    facilities: list[dict[str, Any]] = []
    context = ET.iterparse(kml_path, events=("end",))
    for _event, elem in context:
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag != "Placemark":
            continue

        simple = extract_simple_data(elem)
        name = clean_text(simple.get("essnom1"))
        if not name:
            name_el = elem.find("kml:name", KML_NS)
            name = clean_text(name_el.text if name_el is not None else None) or "Structure sans nom"

        lon, lat = extract_coordinates(elem, simple)
        esstype_original = clean_text(simple.get("esstype"))
        facility_type_code = normalize_facility_type(esstype_original)
        zs_uid = clean_text(simple.get("zs_uid"))
        as_uid = clean_text(simple.get("as_uid"))
        index = len(facilities) + 1
        official_code = build_official_code(zs_uid, as_uid, name, lon, lat, esstype_original, index)

        facility = {
            "official_code": official_code,
            "name": name,
            "facility_type_code": facility_type_code,
            "province_name": clean_text(simple.get("province")),
            "territory_name": None,
            "collectivity_name": None,
            "groupement_name": None,
            "locality_name": clean_text(simple.get("localite")),
            "longitude": lon,
            "latitude": lat,
            "data_source": DATA_SOURCE,
            "properties": {
                "iso3": clean_text(simple.get("iso3")),
                "prov_uid": clean_text(simple.get("prov_uid")),
                "antenne": clean_text(simple.get("antenne")),
                "zonesante": clean_text(simple.get("zonesante")),
                "zs_uid": zs_uid,
                "airesante": clean_text(simple.get("airesante")),
                "as_uid": as_uid,
                "esstype_original": esstype_original,
            },
        }
        facilities.append(facility)
        elem.clear()

    return facilities


def to_geojson(facilities: list[dict[str, Any]]) -> dict[str, Any]:
    features = []
    for index, item in enumerate(facilities, start=1):
        geometry = None
        if item.get("longitude") is not None and item.get("latitude") is not None:
            geometry = {
                "type": "Point",
                "coordinates": [item["longitude"], item["latitude"]],
            }
        properties = {
            "official_code": item["official_code"],
            "name": item["name"],
            "facility_type_code": item["facility_type_code"],
            "province_name": item["province_name"],
            "locality_name": item["locality_name"],
            "data_source": item["data_source"],
            **(item.get("properties") or {}),
        }
        features.append(
            {
                "type": "Feature",
                "id": index,
                "geometry": geometry,
                "properties": properties,
            }
        )
    return {
        "type": "FeatureCollection",
        "features": features,
        "_meta": {
            "count": len(features),
            "source": DATA_SOURCE,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    }


def write_outputs(facilities: list[dict[str, Any]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    geojson = to_geojson(facilities)
    GEOJSON_PATH.write_text(json.dumps(geojson, ensure_ascii=False), encoding="utf-8")
    JSON_PATH.write_text(
        json.dumps(
            {
                "_meta": geojson["_meta"],
                "facilities": facilities,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def ensure_facility_types(conn) -> None:
    with conn.cursor() as cur:
        for code, name, description, category, symbology in FACILITY_TYPES:
            cur.execute(
                """
                INSERT INTO health.health_facility_types (code, name, description, category, symbology)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (code) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    category = EXCLUDED.category,
                    symbology = EXCLUDED.symbology
                """,
                (code, name, description, category, Json(symbology)),
            )
            cur.execute(
                """
                INSERT INTO reference.reference_object_types (
                    reference_code, type_code, type_name, description, symbology
                )
                VALUES ('HEALTH', %s, %s, %s, %s)
                ON CONFLICT (reference_code, type_code) DO UPDATE SET
                    type_name = EXCLUDED.type_name,
                    description = EXCLUDED.description,
                    symbology = EXCLUDED.symbology
                """,
                (code, name, description, Json(symbology)),
            )
        cur.execute(
            """
            UPDATE reference.reference_catalog
            SET status = 'active',
                updated_at = NOW(),
                metadata = COALESCE(metadata, '{}'::jsonb) || %s::jsonb
            WHERE code = 'HEALTH'
            """,
            (Json({"data_source": DATA_SOURCE, "imported_at": datetime.now(timezone.utc).isoformat()}),),
        )
    conn.commit()


def import_to_database(facilities: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for item in facilities:
        lon = item.get("longitude")
        lat = item.get("latitude")
        rows.append(
            (
                item["official_code"],
                item["name"],
                item["facility_type_code"],
                item.get("province_name"),
                item.get("territory_name"),
                item.get("collectivity_name"),
                item.get("groupement_name"),
                item.get("locality_name"),
                item.get("data_source"),
                Json(item.get("properties") or {}),
                lon,
                lat,
                lon,
                lat,
            )
        )

    with psycopg2.connect(DATABASE_URL) as conn:
        ensure_facility_types(conn)
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM health.health_facilities WHERE data_source = %s",
                (DATA_SOURCE,),
            )
            execute_values(
                cur,
                """
                INSERT INTO health.health_facilities (
                    official_code, name, facility_type_code,
                    province_name, territory_name, collectivity_name,
                    groupement_name, locality_name, data_source, properties, geom
                )
                VALUES %s
                """,
                rows,
                template="""(
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    CASE
                        WHEN %s IS NULL OR %s IS NULL THEN NULL
                        ELSE ST_SetSRID(ST_MakePoint(%s, %s), 4326)
                    END
                )""",
                page_size=1000,
            )
        conn.commit()
        stats = compute_and_store_statistics(conn, facilities)
    return stats


def compute_quality_metrics(facilities: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(facilities)
    with_geom = sum(1 for item in facilities if item.get("longitude") is not None and item.get("latitude") is not None)
    without_geom = total - with_geom
    missing_name = sum(1 for item in facilities if not clean_text(item.get("name")) or item.get("name") == "Structure sans nom")
    missing_type = sum(1 for item in facilities if item.get("facility_type_code") == "OTHER")
    by_type = Counter(item.get("facility_type_code") or "OTHER" for item in facilities)
    by_province = Counter(item.get("province_name") or "Non renseigné" for item in facilities)

    coord_keys = [
        (
            round(item["longitude"], 5) if item.get("longitude") is not None else None,
            round(item["latitude"], 5) if item.get("latitude") is not None else None,
            fold_text(item.get("name")),
        )
        for item in facilities
        if item.get("longitude") is not None and item.get("latitude") is not None
    ]
    coord_counts = Counter(coord_keys)
    potential_duplicates = sum(count - 1 for count in coord_counts.values() if count > 1)

    if total == 0:
        quality_score = 0.0
    else:
        geom_ratio = with_geom / total
        named_ratio = (total - missing_name) / total
        typed_ratio = (total - missing_type) / total
        duplicate_penalty = min(potential_duplicates / total, 0.2)
        quality_score = round(max(0.0, (geom_ratio * 0.5 + named_ratio * 0.25 + typed_ratio * 0.25 - duplicate_penalty) * 100), 2)

    return {
        "total_facilities": total,
        "by_type": dict(sorted(by_type.items(), key=lambda item: (-item[1], item[0]))),
        "by_province": dict(sorted(by_province.items(), key=lambda item: (-item[1], item[0]))),
        "facilities_with_geometry": with_geom,
        "facilities_without_geometry": without_geom,
        "missing_names": missing_name,
        "missing_types": missing_type,
        "potential_duplicates": potential_duplicates,
        "quality_score": quality_score,
    }


def compute_and_store_statistics(conn, facilities: list[dict[str, Any]]) -> dict[str, Any]:
    quality = compute_quality_metrics(facilities)
    hospital_codes = ("HGR", "HOSPITAL", "CH")
    center_codes = ("CS", "CSR", "CM", "CLINIC", "POLYCLINIC")
    post_codes = ("PS", "DISP", "SSC")

    hospitals = sum(quality["by_type"].get(code, 0) for code in hospital_codes)
    health_centers = sum(quality["by_type"].get(code, 0) for code in center_codes)
    health_posts = sum(quality["by_type"].get(code, 0) for code in post_codes)

    details = {
        "status": "imported",
        "data_source": DATA_SOURCE,
        "by_type": quality["by_type"],
        "by_province": quality["by_province"],
        "missing_names": quality["missing_names"],
        "missing_types": quality["missing_types"],
        "potential_duplicates": quality["potential_duplicates"],
        "quality_score": quality["quality_score"],
        "hospital_types": list(hospital_codes),
        "health_center_types": list(center_codes),
        "health_post_types": list(post_codes),
        "imported_at": datetime.now(timezone.utc).isoformat(),
    }

    with conn.cursor() as cur:
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
                "national",
                "RDC",
                quality["total_facilities"],
                hospitals,
                health_centers,
                health_posts,
                quality["facilities_with_geometry"],
                quality["facilities_without_geometry"],
                0,
                0,
                Json(details),
            ),
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS health.health_quality_dashboard (
                id              BIGSERIAL PRIMARY KEY,
                scope_type      VARCHAR(64) NOT NULL DEFAULT 'national',
                scope_name      VARCHAR(255) NOT NULL DEFAULT 'RDC',
                quality_score   NUMERIC(6,2) NOT NULL DEFAULT 0,
                total_facilities INTEGER NOT NULL DEFAULT 0,
                facilities_with_geometry INTEGER NOT NULL DEFAULT 0,
                facilities_without_geometry INTEGER NOT NULL DEFAULT 0,
                missing_names   INTEGER NOT NULL DEFAULT 0,
                missing_types   INTEGER NOT NULL DEFAULT 0,
                potential_duplicates INTEGER NOT NULL DEFAULT 0,
                details         JSONB NOT NULL DEFAULT '{}'::jsonb,
                computed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
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
                "national",
                "RDC",
                quality["quality_score"],
                quality["total_facilities"],
                quality["facilities_with_geometry"],
                quality["facilities_without_geometry"],
                quality["missing_names"],
                quality["missing_types"],
                quality["potential_duplicates"],
                Json(details),
            ),
        )
    conn.commit()
    return {
        **quality,
        "hospitals": hospitals,
        "health_centers": health_centers,
        "health_posts": health_posts,
        "details": details,
    }


def persist_health_spatial_relations(limit_sites: int | None = None) -> dict[str, Any]:
    """Calcule et persiste les relations Site FDSU → structures sanitaires sans écraser le télécom."""
    from api.services import spatial_analysis_service

    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id
                FROM programs.fdsu_sites
                WHERE geom IS NOT NULL
                ORDER BY id
                """
            )
            site_ids = [int(row["id"]) for row in cur.fetchall()]
    if limit_sites is not None:
        site_ids = site_ids[:limit_sites]

    completed = 0
    for site_id in site_ids:
        result = spatial_analysis_service.persist_site_health_relations(site_id)
        if result.get("analysis_status") == "completed":
            completed += 1
    return {"sites_total": len(site_ids), "sites_completed": completed}


def main() -> None:
    print(f"Extraction KML depuis {KMZ_PATH.name}…")
    kml_path = extract_kml()
    print(f"Parsing Placemarks ({kml_path})…")
    facilities = parse_facilities(kml_path)
    print(f"Établissements lus : {len(facilities)}")
    write_outputs(facilities)
    print(f"GeoJSON écrit : {GEOJSON_PATH}")
    print(f"JSON écrit    : {JSON_PATH}")
    print("Import PostgreSQL/PostGIS…")
    stats = import_to_database(facilities)
    print("Persistance relations spatiales santé…")
    spatial = persist_health_spatial_relations()
    print(json.dumps({"import": stats, "spatial": spatial}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
