#!/usr/bin/env python3
"""Extract Sites FDSU 300 from KMZ to GeoJSON and flat JSON."""

from __future__ import annotations

import json
import re
import shutil
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

KML_NS = {"kml": "http://www.opengis.net/kml/2.2"}
ROOT = Path(__file__).resolve().parent.parent
PROGRAM_DIR = ROOT / "data" / "programs" / "sites_300"
KMZ_PATH = PROGRAM_DIR / "raw" / "300_sites_new.csv.kmz"
KML_PATH = PROGRAM_DIR / "raw" / "doc.kml"
GEOJSON_PATH = PROGRAM_DIR / "sites_300.geojson"
JSON_PATH = PROGRAM_DIR / "sites_300.json"
MATRICE_SOURCE = ROOT / "data" / "strategic" / "matrice_priorisation_300_sites.xlsx"
MATRICE_DEST = PROGRAM_DIR / "matrice_priorisation_300_sites.xlsx"

PROVINCE_NORMALIZATION = {
    "Kongo-Central": "Kongo Central",
    "Kasai-Central": "Kasai Central",
    "Tanganyka": "Tanganyika",
}

ZONE_FIELD_CANDIDATES = (
    "FDSU_Zone_régionale",
    "FDSU_Zone_regionale",
    "FDSU Zone régionale",
    "FDSU Zone regionale",
)


def normalize_province(value: str) -> str:
    text = (value or "").strip()
    return PROVINCE_NORMALIZATION.get(text, text)


def parse_extended_data(placemark: ET.Element) -> dict[str, str]:
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
        re.sub(r"\s+", " ", key.replace("�", "é").strip().lower()): value
        for key, value in fields.items()
    }
    for candidate in candidates:
        key = re.sub(r"\s+", " ", candidate.replace("�", "é").strip().lower())
        if key in normalized and normalized[key]:
            return normalized[key]
    for candidate in candidates:
        for key, value in fields.items():
            if candidate.lower() in key.lower() and value:
                return value
    return ""


def extract_kml() -> str:
    with zipfile.ZipFile(KMZ_PATH) as archive:
        kml_bytes = archive.read("doc.kml")
    KML_PATH.write_bytes(kml_bytes)
    return kml_bytes.decode("utf-8")


def parse_placemarks(kml_text: str) -> list[dict]:
    root = ET.fromstring(kml_text)
    sites: list[dict] = []

    for placemark in root.findall(".//kml:Placemark", KML_NS):
        coords_el = placemark.find(".//kml:coordinates", KML_NS)
        if coords_el is None or not coords_el.text:
            continue

        parts = coords_el.text.strip().split(",")
        if len(parts) < 2:
            continue

        lon = float(parts[0])
        lat = float(parts[1])
        fields = parse_extended_data(placemark)
        name = pick_field(fields, "Site_name", "Village_name") or (
            placemark.findtext("kml:name", default="", namespaces=KML_NS) or ""
        ).strip()

        site = {
            "name": name,
            "province": normalize_province(pick_field(fields, "Province")),
            "territoire": pick_field(fields, "Territoire"),
            "zone": pick_field(fields, *ZONE_FIELD_CANDIDATES),
            "latitude": lat,
            "longitude": lon,
            "programme": "Sites 300",
            "status": "Planifié",
            "priority_status": "À calculer",
            "fdsu_score": None,
            "source": "KMZ 300 Sites",
        }
        sites.append(site)

    return sites


def to_geojson(sites: list[dict]) -> dict:
    features = []
    for index, site in enumerate(sites, start=1):
        features.append(
            {
                "type": "Feature",
                "id": index,
                "geometry": {
                    "type": "Point",
                    "coordinates": [site["longitude"], site["latitude"]],
                },
                "properties": dict(site),
            }
        )
    return {"type": "FeatureCollection", "features": features}


def copy_matrice() -> None:
    if MATRICE_SOURCE.exists():
        shutil.copy2(MATRICE_SOURCE, MATRICE_DEST)


def main() -> None:
    PROGRAM_DIR.mkdir(parents=True, exist_ok=True)
    (PROGRAM_DIR / "raw").mkdir(parents=True, exist_ok=True)
    if not KMZ_PATH.exists():
        raise SystemExit(f"KMZ introuvable: {KMZ_PATH}")

    copy_matrice()
    kml_text = extract_kml()
    sites = parse_placemarks(kml_text)
    if len(sites) != 300:
        raise SystemExit(f"Expected 300 sites, got {len(sites)}")

    geojson = to_geojson(sites)
    GEOJSON_PATH.write_text(json.dumps(geojson, ensure_ascii=False, indent=2), encoding="utf-8")
    JSON_PATH.write_text(
        json.dumps(
            {
                "_meta": {
                    "program": "Sites 300",
                    "program_status": "PLANIFIE",
                    "source_kmz": "data/programs/sites_300/raw/300_sites_new.csv.kmz",
                    "source_matrix": "data/programs/sites_300/matrice_priorisation_300_sites.xlsx",
                    "count": len(sites),
                    "deployment_status": "NON_DEMARRE",
                    "scoring_status": "A_CALCULER",
                },
                "sites": sites,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    zones: dict[str, int] = {}
    for site in sites:
        zones[site["zone"]] = zones.get(site["zone"], 0) + 1

    print(f"Imported {len(sites)} sites")
    print("Zones:", zones)


if __name__ == "__main__":
    main()
