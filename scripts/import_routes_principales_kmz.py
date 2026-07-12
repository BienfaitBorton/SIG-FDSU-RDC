#!/usr/bin/env python3
"""Pipeline reproductible — Routes_principales.shp.kmz → GeoJSON traité → PostgreSQL/PostGIS.

Ne jamais servir le KMZ brut en production.
Usage:
  python scripts/import_routes_principales_kmz.py           # parse + qualité + GeoJSON
  python scripts/import_routes_principales_kmz.py --db      # + import PostGIS
  python scripts/import_routes_principales_kmz.py --db --limit 500  # échantillon
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

KML_NS = {"kml": "http://www.opengis.net/kml/2.2"}
SOURCE_FILE = "Routes_principales.shp.kmz"
RAW_KMZ = PROJECT_ROOT / "data" / "raw" / SOURCE_FILE
OUT_DIR = PROJECT_ROOT / "data" / "sectoral" / "transport"
PROCESSED_DIR = OUT_DIR / "processed"
QUALITY_DIR = OUT_DIR / "quality"
GEOJSON_PATH = PROCESSED_DIR / "routes_principales.geojson"
QUALITY_PATH = QUALITY_DIR / "routes_quality_report.json"
MANIFEST_PATH = OUT_DIR / "manifest.json"
SCHEMA_SQL = PROJECT_ROOT / "database" / "transport_schema.sql"

# Emprise approximative RDC (WGS84) — contrôle hors territoire
RDC_BBOX = (12.0, -13.5, 31.5, 5.5)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).replace("\xa0", " ").split()).strip()
    if not text or text.upper() in {"NC", "N/A", "NA", "NULL", "-"}:
        return None
    return text


def parse_date(value: str | None) -> str | None:
    text = clean_text(value)
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text[:10], fmt).date().isoformat()
        except ValueError:
            continue
    return None


def parse_position(token: str) -> tuple[float, float] | None:
    parts = [p for p in token.strip().split(",") if p != ""]
    if len(parts) < 2:
        return None
    try:
        lon, lat = float(parts[0]), float(parts[1])
        if not (math.isfinite(lon) and math.isfinite(lat)):
            return None
        return lon, lat
    except ValueError:
        return None


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


def haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lon1, lat1 = map(math.radians, a)
    lon2, lat2 = map(math.radians, b)
    dlon, dlat = lon2 - lon1, lat2 - lat1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(h))


def line_length_m(coords: list[tuple[float, float]]) -> float:
    return sum(haversine_m(coords[i], coords[i + 1]) for i in range(len(coords) - 1))


def within_rdc(coords: list[tuple[float, float]]) -> bool:
    min_lon, min_lat, max_lon, max_lat = RDC_BBOX
    for lon, lat in coords:
        if not (min_lon <= lon <= max_lon and min_lat <= lat <= max_lat):
            return False
    return True


def parse_fields(placemark: ET.Element) -> dict[str, str]:
    fields: dict[str, str] = {}
    for data in placemark.findall(".//kml:Data", KML_NS):
        name = data.get("name", "")
        value_el = data.find("kml:value", KML_NS)
        fields[name] = (value_el.text or "").strip() if value_el is not None else ""
    for simple in placemark.findall(".//kml:SimpleData", KML_NS):
        fields[simple.get("name", "")] = (simple.text or "").strip()
    return fields


def extract_kml(kmz_path: Path) -> bytes:
    with zipfile.ZipFile(kmz_path) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(".kml")]
        if not names:
            raise FileNotFoundError("Aucun KML dans le KMZ")
        return zf.read(names[0])


def parse_routes(kml_bytes: bytes, limit: int | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    root = ET.fromstring(kml_bytes)
    placemarks = root.findall(".//kml:Placemark", KML_NS)
    features: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    nature_counter: Counter[str] = Counter()

    for pm in placemarks:
        if limit is not None and len(features) >= limit:
            break
        fields = parse_fields(pm)
        source_id = clean_text(fields.get("ID"))
        nom = clean_text(fields.get("NOM"))
        nature = clean_text(fields.get("NATURE")) or "Non renseigné"
        coords: list[tuple[float, float]] = []
        for line_el in pm.findall(".//kml:LineString", KML_NS):
            coords = parse_linestring(line_el)
            if len(coords) >= 2:
                break
        if len(coords) < 2:
            rejected.append({"reason": "geometry_invalid_or_missing", "source_id": source_id, "nom": nom})
            continue
        # Déduplication par source_id
        if source_id:
            if source_id in seen_ids:
                rejected.append({"reason": "duplicate_source_id", "source_id": source_id, "nom": nom})
                continue
            seen_ids.add(source_id)
        else:
            # Fallback hash géométrie
            digest = hashlib.sha1(
                json.dumps(coords, separators=(",", ":")).encode("utf-8")
            ).hexdigest()[:16]
            source_id = f"hash-{digest}"
            if source_id in seen_ids:
                rejected.append({"reason": "duplicate_geometry_hash", "source_id": source_id})
                continue
            seen_ids.add(source_id)

        hors_rdc = not within_rdc(coords)
        length_m = round(line_length_m(coords), 2)
        nature_counter[nature] += 1
        props = {
            "source_id": source_id,
            "nom": nom,
            "type_route": nature,
            "categorie": clean_text(fields.get("CL_ADMIN")),
            "etat": clean_text(fields.get("GESTION")),
            "revetement": clean_text(fields.get("FRANCHISST")),
            "numero": clean_text(fields.get("NUMERO")),
            "cl_admin": clean_text(fields.get("CL_ADMIN")),
            "gestion": clean_text(fields.get("GESTION")),
            "sens": clean_text(fields.get("SENS")),
            "nb_voies": clean_text(fields.get("NB_VOIES")),
            "source": clean_text(fields.get("SOURCE")) or "OpenStreetMap",
            "date_maj_source": parse_date(fields.get("DATE_MAJ")),
            "longueur_m": length_m,
            "hors_rdc": hors_rdc,
            "source_file": SOURCE_FILE,
        }
        features.append(
            {
                "type": "Feature",
                "id": source_id,
                "properties": props,
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[lon, lat] for lon, lat in coords],
                },
            }
        )

    quality = {
        "_meta": {
            "generated_at": _now(),
            "source_file": SOURCE_FILE,
            "pipeline": "import_routes_principales_kmz.py",
            "crs": "EPSG:4326",
        },
        "counts": {
            "placemarks": len(placemarks),
            "accepted": len(features),
            "rejected": len(rejected),
            "without_name": sum(1 for f in features if not f["properties"].get("nom")),
            "outside_rdc_bbox": sum(1 for f in features if f["properties"].get("hors_rdc")),
            "by_nature": dict(nature_counter),
        },
        "checks": [
            {
                "code": "invalid_geometry",
                "label": "Géométries invalides / manquantes",
                "severity": "error",
                "count": sum(1 for r in rejected if r["reason"] == "geometry_invalid_or_missing"),
            },
            {
                "code": "duplicate_routes",
                "label": "Routes dupliquées (source_id)",
                "severity": "warning",
                "count": sum(1 for r in rejected if r["reason"].startswith("duplicate")),
            },
            {
                "code": "unnamed_routes",
                "label": "Routes sans nom",
                "severity": "info",
                "count": sum(1 for f in features if not f["properties"].get("nom")),
            },
            {
                "code": "outside_rdc",
                "label": "Routes hors emprise RDC (bbox)",
                "severity": "warning",
                "count": sum(1 for f in features if f["properties"].get("hors_rdc")),
            },
            {
                "code": "incoherent_segments",
                "label": "Tronçons très courts (< 5 m)",
                "severity": "info",
                "count": sum(1 for f in features if (f["properties"].get("longueur_m") or 0) < 5),
            },
        ],
        "rejected_sample": rejected[:50],
    }
    return features, quality


def write_outputs(features: list[dict[str, Any]], quality: dict[str, Any]) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)
    fc = {"type": "FeatureCollection", "features": features}
    GEOJSON_PATH.write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")
    QUALITY_PATH.write_text(json.dumps(quality, ensure_ascii=False, indent=2), encoding="utf-8")
    sha = hashlib.sha256(RAW_KMZ.read_bytes()).hexdigest() if RAW_KMZ.exists() else None

    def _rel(path: Path) -> str:
        try:
            return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
        except ValueError:
            return str(path).replace("\\", "/")

    manifest = {
        "_meta": {
            "title": "Transport — Routes principales",
            "generated_at": _now(),
            "schema_version": "1.0",
        },
        "heritage": "Routes_principales.shp.kmz (OSM / référentiel routier)",
        "sources": [
            {
                "role": "raw_kmz",
                "path": "data/raw/Routes_principales.shp.kmz",
                "sha256": sha,
                "preserved_original": True,
                "not_served_in_production": True,
            }
        ],
        "outputs": {
            "geojson": _rel(GEOJSON_PATH),
            "quality": _rel(QUALITY_PATH),
        },
        "counts": quality.get("counts"),
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def apply_schema(conn) -> None:
    sql = SCHEMA_SQL.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def import_to_database(features: list[dict[str, Any]], quality: dict[str, Any]) -> dict[str, Any]:
    import psycopg2
    from psycopg2.extras import Json, execute_values

    from app.config import DATABASE_URL

    conn = psycopg2.connect(DATABASE_URL)
    try:
        apply_schema(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO transport.import_runs (source_file, status, rows_parsed, quality_report)
                VALUES (%s, 'running', %s, %s) RETURNING id
                """,
                (SOURCE_FILE, len(features), Json(quality)),
            )
            run_id = cur.fetchone()[0]
            cur.execute("DELETE FROM transport.routes WHERE source_file = %s", (SOURCE_FILE,))

            rows = []
            for feat in features:
                p = feat["properties"]
                coords = feat["geometry"]["coordinates"]
                # WKT LineString
                wkt = "SRID=4326;LINESTRING(" + ", ".join(f"{c[0]} {c[1]}" for c in coords) + ")"
                rows.append(
                    (
                        p.get("source_id"),
                        p.get("nom"),
                        p.get("type_route"),
                        p.get("categorie"),
                        p.get("etat"),
                        p.get("revetement"),
                        p.get("numero"),
                        p.get("cl_admin"),
                        p.get("gestion"),
                        p.get("sens"),
                        p.get("nb_voies"),
                        p.get("source") or "OpenStreetMap",
                        SOURCE_FILE,
                        p.get("date_maj_source"),
                        p.get("longueur_m"),
                        wkt,
                        Json({k: v for k, v in p.items() if k not in {"source_id", "nom", "type_route"}}),
                    )
                )

            execute_values(
                cur,
                """
                INSERT INTO transport.routes (
                    source_id, nom, type_route, categorie, etat, revetement, numero,
                    cl_admin, gestion, sens, nb_voies, source, source_file, date_maj_source,
                    longueur_m, geom, properties
                ) VALUES %s
                """,
                rows,
                template="""(
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    ST_GeomFromEWKT(%s), %s
                )""",
                page_size=500,
            )
            imported = len(rows)

            # Quality checks persistence
            cur.execute("DELETE FROM transport.quality_checks")
            for check in quality.get("checks") or []:
                cur.execute(
                    """
                    INSERT INTO transport.quality_checks (check_code, check_label, severity, count_value, details)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        check["code"],
                        check["label"],
                        check["severity"],
                        check["count"],
                        Json(check),
                    ),
                )

            # Statistics
            cur.execute(
                """
                INSERT INTO transport.statistics (metric_key, metric_value, metric_label, details)
                VALUES
                    ('routes_total', %s, 'Nombre de routes', %s),
                    ('length_total_km', %s, 'Longueur totale (km)', %s)
                ON CONFLICT (metric_key) DO UPDATE SET
                    metric_value = EXCLUDED.metric_value,
                    metric_label = EXCLUDED.metric_label,
                    details = EXCLUDED.details,
                    computed_at = NOW()
                """,
                (
                    imported,
                    Json(quality.get("counts") or {}),
                    round(sum((f["properties"].get("longueur_m") or 0) for f in features) / 1000.0, 2),
                    Json({"unit": "km"}),
                ),
            )

            cur.execute(
                """
                UPDATE transport.import_runs
                SET finished_at = NOW(), status = 'success', rows_imported = %s,
                    rows_rejected = %s
                WHERE id = %s
                """,
                (imported, quality["counts"].get("rejected", 0), run_id),
            )
        conn.commit()
        return {"run_id": run_id, "imported": imported}
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Import Routes principales KMZ → PostGIS")
    parser.add_argument("--db", action="store_true", help="Importer dans PostgreSQL/PostGIS")
    parser.add_argument("--limit", type=int, default=None, help="Limiter le nombre de features")
    args = parser.parse_args()

    if not RAW_KMZ.exists():
        print(f"ERREUR: fichier source introuvable: {RAW_KMZ}", file=sys.stderr)
        return 1

    print(f"Lecture {RAW_KMZ} …")
    kml = extract_kml(RAW_KMZ)
    features, quality = parse_routes(kml, limit=args.limit)
    write_outputs(features, quality)
    print(f"GeoJSON -> {GEOJSON_PATH} ({len(features)} features)")
    print(f"Qualite -> {QUALITY_PATH}")
    for check in quality["checks"]:
        print(f"  [{check['severity']}] {check['code']}: {check['count']}")

    if args.db:
        result = import_to_database(features, quality)
        print(f"PostGIS import OK — run_id={result['run_id']} imported={result['imported']}")
    else:
        print("Mode fichier uniquement (passer --db pour PostGIS).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
