#!/usr/bin/env python3
"""Extract Sites FDSU 40 from KMZ to GeoJSON and flat JSON."""

from __future__ import annotations

import html
import json
import re
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

KML_NS = {"kml": "http://www.opengis.net/kml/2.2"}
ROOT = Path(__file__).resolve().parent.parent
KMZ_PATH = ROOT / "data" / "programs" / "sites_40" / "raw" / "Sites_FDSU_40.kmz"
KML_PATH = ROOT / "data" / "programs" / "sites_40" / "raw" / "doc.kml"
GEOJSON_PATH = ROOT / "data" / "programs" / "sites_40" / "sites_40.geojson"
JSON_PATH = ROOT / "data" / "programs" / "sites_40" / "sites_40.json"

PROVINCE_NORMALIZATION = {
    "Kongo-Central": "Kongo Central",
    "Kasai-Central": "Kasai Central",
    "Tanganyka": "Tanganyika",
}


def normalize_province(value: str) -> str:
    text = (value or "").strip()
    return PROVINCE_NORMALIZATION.get(text, text)


def parse_description(raw: str) -> dict[str, str]:
    text = html.unescape(raw or "")
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    fields: dict[str, str] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()
        if key.startswith("province"):
            fields["province"] = normalize_province(value)
        elif key.startswith("territoire"):
            fields["territoire"] = value
        elif key.startswith("zone"):
            fields["zone"] = value
    return fields


def extract_kml() -> str:
    with zipfile.ZipFile(KMZ_PATH) as archive:
        kml_bytes = archive.read("doc.kml")
    KML_PATH.write_bytes(kml_bytes)
    return kml_bytes.decode("utf-8")


def parse_placemarks(kml_text: str) -> list[dict]:
    root = ET.fromstring(kml_text)
    sites: list[dict] = []

    for placemark in root.findall(".//kml:Placemark", KML_NS):
        name_el = placemark.find("kml:name", KML_NS)
        desc_el = placemark.find("kml:description", KML_NS)
        coords_el = placemark.find(".//kml:coordinates", KML_NS)
        if coords_el is None or not coords_el.text:
            continue

        parts = coords_el.text.strip().split(",")
        if len(parts) < 2:
            continue

        lon = float(parts[0])
        lat = float(parts[1])
        meta = parse_description(desc_el.text if desc_el is not None else "")

        site = {
            "name": (name_el.text if name_el is not None else "").strip(),
            "province": meta.get("province", ""),
            "territoire": meta.get("territoire", ""),
            "zone": meta.get("zone", ""),
            "latitude": lat,
            "longitude": lon,
            "programme": "Sites 40",
            "status": "à qualifier",
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


def main() -> None:
    kml_text = extract_kml()
    sites = parse_placemarks(kml_text)
    if len(sites) != 40:
        raise SystemExit(f"Expected 40 sites, got {len(sites)}")

    geojson = to_geojson(sites)
    GEOJSON_PATH.write_text(json.dumps(geojson, ensure_ascii=False, indent=2), encoding="utf-8")
    JSON_PATH.write_text(
        json.dumps(
            {
                "_meta": {
                    "program": "Sites 40",
                    "source_kmz": "data/programs/sites_40/raw/Sites_FDSU_40.kmz",
                    "count": len(sites),
                },
                "sites": sites,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    zones: dict[str, int] = {}
    provinces: dict[str, int] = {}
    for site in sites:
        zones[site["zone"]] = zones.get(site["zone"], 0) + 1
        provinces[site["province"]] = provinces.get(site["province"], 0) + 1

    print(f"Imported {len(sites)} sites")
    print("Zones:", zones)
    print("Provinces:", len(provinces))


if __name__ == "__main__":
    main()
