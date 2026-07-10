"""Import générique des programmes de sites FDSU (40 / 300 / 20 476 / futures vagues)."""

from __future__ import annotations

import csv
import json
import math
import re
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
IMPORTS_DIR = PROJECT_ROOT / "data" / "imports"
PROGRAMS_DIR = PROJECT_ROOT / "data" / "programs"

PROGRAM_CATALOG = {
    "sites_40": {
        "program_code": "sites_40",
        "program_code_db": "PROG_SITES_40",
        "label": "Sites 40",
        "phase": "pilot",
        "description": "Phase pilote FDSU",
    },
    "sites_300": {
        "program_code": "sites_300",
        "program_code_db": "PROG_SITES_300",
        "label": "Sites 300",
        "phase": "first_wave",
        "description": "Première vague opérationnelle",
    },
    "sites_20476": {
        "program_code": "sites_20476",
        "program_code_db": "PROG_SITES_20476",
        "label": "Sites 20 476",
        "phase": "national",
        "description": "Programme national complet FDSU (5 ans)",
        "default_csv": IMPORTS_DIR / "PROGRAMME 20476 SITES.csv",
    },
}

FIELD_ALIASES = {
    "site_name": ("site name", "site_name", "nom", "name", "site"),
    "latitude": ("latitude", "lat", "y"),
    "longitude": ("longitude", "lon", "lng", "long", "x"),
    "province": ("provinces", "province", "prov"),
    "territoire": ("territoire", "territory", "terr"),
    "zone": ("zone", "zone_fdsu"),
    "population": ("population", "pop"),
    "population_range": ("population range", "population_range", "pop_range"),
    "nearest_site": ("nearest site", "nearest_site", "site_proche"),
    "distance": ("distance", "dist", "distance_m"),
    "distance_level": ("distance level", "distance_level", "niveau_distance"),
    "is_300_planned": ("300 sites planned", "is_300_planned", "sites_300", "in_300"),
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_header(value: str) -> str:
    text = str(value or "").strip().lower()
    text = text.replace("é", "e").replace("è", "e").replace("ê", "e")
    text = re.sub(r"\s+", " ", text)
    return text


def _detect_encoding(path: Path) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            path.read_text(encoding=enc)
            return enc
        except UnicodeDecodeError:
            continue
    return "latin-1"


def _detect_delimiter(header_line: str) -> str:
    return ";" if header_line.count(";") >= header_line.count(",") else ","


def _map_headers(fieldnames: list[str] | None) -> dict[str, str | None]:
    normalized = {_normalize_header(h): h for h in (fieldnames or []) if h}
    mapping: dict[str, str | None] = {}
    for target, aliases in FIELD_ALIASES.items():
        mapping[target] = None
        for alias in aliases:
            if alias in normalized:
                mapping[target] = normalized[alias]
                break
    return mapping


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(" ", "").replace(",", ".")
    text = re.sub(r"[^0-9.\-]+", "", text)
    if not text or text in {"-", ".", "-."}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _to_int(value: Any) -> int | None:
    number = _to_float(value)
    if number is None:
        return None
    return int(round(number))


def _to_bool_300(value: Any) -> bool:
    text = str(value or "").strip().lower()
    return text in {"yes", "y", "true", "1", "oui", "o"}


def _in_rdc(lat: float | None, lon: float | None) -> bool:
    if lat is None or lon is None:
        return False
    return -13.6 <= lat <= 5.6 and 12.0 <= lon <= 31.8


def normalize_program_code(program_code: str | None) -> str:
    raw = (program_code or "").strip()
    lowered = raw.lower().replace("prog_", "")
    aliases = {
        "sites_40": "sites_40",
        "sites40": "sites_40",
        "40": "sites_40",
        "sites_300": "sites_300",
        "sites300": "sites_300",
        "300": "sites_300",
        "sites_20476": "sites_20476",
        "sites20476": "sites_20476",
        "20476": "sites_20476",
        "national": "sites_20476",
    }
    if lowered in aliases:
        return aliases[lowered]
    if raw.upper() == "PROG_SITES_40":
        return "sites_40"
    if raw.upper() == "PROG_SITES_300":
        return "sites_300"
    if raw.upper() == "PROG_SITES_20476":
        return "sites_20476"
    return lowered or "sites_20476"


def program_meta(program_code: str) -> dict[str, Any]:
    code = normalize_program_code(program_code)
    return dict(PROGRAM_CATALOG.get(code) or {
        "program_code": code,
        "program_code_db": f"PROG_{code.upper()}",
        "label": code,
        "phase": "custom",
        "description": f"Vague FDSU {code}",
    })


def program_output_dir(program_code: str) -> Path:
    code = normalize_program_code(program_code)
    path = PROGRAMS_DIR / code
    path.mkdir(parents=True, exist_ok=True)
    (path / "raw").mkdir(parents=True, exist_ok=True)
    return path


def normalize_row(raw: dict[str, Any], mapping: dict[str, str | None], program_code: str, index: int) -> dict[str, Any]:
    meta = program_meta(program_code)

    def get(field: str) -> Any:
        source = mapping.get(field)
        return raw.get(source) if source else None

    lat = _to_float(get("latitude"))
    lon = _to_float(get("longitude"))
    population = _to_int(get("population"))
    distance = _to_float(get("distance"))
    is_300 = _to_bool_300(get("is_300_planned"))
    site_name = str(get("site_name") or f"Site_{index}").strip()
    site_code = f"{meta['program_code'].upper()}_{index:05d}"

    return {
        "site_id": index,
        "site_code": site_code,
        "site_name": site_name,
        "latitude": lat,
        "longitude": lon,
        "province": (str(get("province")).strip() if get("province") not in (None, "") else None),
        "territoire": (str(get("territoire")).strip() if get("territoire") not in (None, "") else None),
        "zone": (str(get("zone")).strip() if get("zone") not in (None, "") else None),
        "population": population,
        "population_range": (str(get("population_range")).strip() if get("population_range") not in (None, "") else None),
        "nearest_site": (str(get("nearest_site")).strip() if get("nearest_site") not in (None, "") else None),
        "distance": distance,
        "distance_level": (str(get("distance_level")).strip() if get("distance_level") not in (None, "") else None),
        "is_300_planned": is_300,
        "program_code": meta["program_code"],
        "program_code_db": meta["program_code_db"],
        "programme": meta["label"],
        "phase": meta["phase"],
        "has_geometry": _in_rdc(lat, lon),
        "source": "PROGRAMME 20476 SITES.csv" if meta["program_code"] == "sites_20476" else "import_fdsu",
    }


def import_sites_csv(
    csv_path: Path | None = None,
    *,
    program_code: str = "sites_20476",
    write_outputs: bool = True,
) -> dict[str, Any]:
    meta = program_meta(program_code)
    code = meta["program_code"]
    source = Path(csv_path) if csv_path else meta.get("default_csv")
    if source is None or not Path(source).exists():
        raise FileNotFoundError(f"CSV introuvable pour {code}: {source}")
    source = Path(source)

    encoding = _detect_encoding(source)
    first_line = source.read_text(encoding=encoding).splitlines()[0]
    delimiter = _detect_delimiter(first_line)

    with source.open(encoding=encoding, newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        mapping = _map_headers(reader.fieldnames)
        required = ("site_name", "latitude", "longitude")
        missing = [field for field in required if not mapping.get(field)]
        if missing:
            raise ValueError(f"Colonnes obligatoires manquantes: {missing}")

        sites: list[dict[str, Any]] = []
        seen_keys: set[str] = set()
        duplicate_count = 0
        for index, raw in enumerate(reader, start=1):
            site = normalize_row(raw, mapping, code, index)
            key = "|".join(
                [
                    (site["site_name"] or "").lower(),
                    str(site["latitude"]),
                    str(site["longitude"]),
                    site["province"] or "",
                    site["territoire"] or "",
                ]
            )
            if key in seen_keys:
                duplicate_count += 1
                site["duplicate_flag"] = True
            else:
                seen_keys.add(key)
                site["duplicate_flag"] = False
            sites.append(site)

    by_province = Counter(site.get("province") or "Non renseignée" for site in sites)
    planned_300 = sum(1 for site in sites if site.get("is_300_planned"))
    with_geom = sum(1 for site in sites if site.get("has_geometry"))

    payload = {
        "_meta": {
            "program": meta["label"],
            "program_code": code,
            "program_code_db": meta["program_code_db"],
            "phase": meta["phase"],
            "source_csv": str(source.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "count": len(sites),
            "with_geometry": with_geom,
            "is_300_planned_count": planned_300,
            "duplicate_rows": duplicate_count,
            "imported_at": _now(),
            "schema_version": "1.0.0",
            "note": (
                "Les 40 sites = phase pilote ; les 300 = première vague ; "
                "les 20 476 = programme national. Le moteur reste extensible aux vagues futures."
            ),
        },
        "statistics": {
            "by_province": dict(sorted(by_province.items(), key=lambda item: (-item[1], item[0]))),
            "planned_300_yes": planned_300,
            "planned_300_no": len(sites) - planned_300,
            "geometry_valid": with_geom,
            "geometry_invalid": len(sites) - with_geom,
            "duplicate_rows": duplicate_count,
        },
        "sites": sites,
    }

    outputs: dict[str, str] = {}
    if write_outputs:
        out_dir = program_output_dir(code)
        raw_copy = out_dir / "raw" / source.name
        if source.resolve() != raw_copy.resolve():
            raw_copy.write_bytes(source.read_bytes())

        json_path = out_dir / f"{code}.json"
        geojson_path = out_dir / f"{code}.geojson"
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        features = []
        for site in sites:
            if not site.get("has_geometry"):
                continue
            features.append(
                {
                    "type": "Feature",
                    "id": site["site_id"],
                    "geometry": {
                        "type": "Point",
                        "coordinates": [site["longitude"], site["latitude"]],
                    },
                    "properties": {
                        key: value
                        for key, value in site.items()
                        if key not in {"latitude", "longitude"} and value not in (None, "")
                    },
                }
            )
        geojson = {
            "type": "FeatureCollection",
            "name": code,
            "features": features,
            "metadata": payload["_meta"],
        }
        geojson_path.write_text(json.dumps(geojson, ensure_ascii=False), encoding="utf-8")
        outputs = {
            "json": str(json_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "geojson": str(geojson_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "raw": str(raw_copy.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        }
        payload["_meta"]["outputs"] = outputs

        # rewrite json with outputs
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "program_code": code,
        "count": len(sites),
        "statistics": payload["statistics"],
        "outputs": outputs,
        "meta": payload["_meta"],
        "sites": sites,
    }


def load_program_sites(program_code: str) -> dict[str, Any]:
    code = normalize_program_code(program_code)
    json_path = program_output_dir(code) / f"{code}.json"
    if not json_path.exists():
        if code == "sites_20476":
            return import_sites_csv(program_code=code)
        raise FileNotFoundError(f"Données programme introuvables: {json_path}")
    return json.loads(json_path.read_text(encoding="utf-8"))


def get_postgis_schema_sql() -> str:
    example = PROJECT_ROOT / "docs" / "fdsu_sites_national_postgis.sql.example"
    if example.exists():
        return example.read_text(encoding="utf-8")
    return """
CREATE SCHEMA IF NOT EXISTS programs;
ALTER TABLE programs.fdsu_programs ADD COLUMN IF NOT EXISTS phase TEXT;
-- Les sites nationaux réutilisent programs.fdsu_sites avec program_code PROG_SITES_20476.
""".strip()
