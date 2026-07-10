"""Tests programme national FDSU — import 20 476 + priorisation générique."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from api.services import fdsu_site_priority_service, fdsu_sites_import_service

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = PROJECT_ROOT / "data" / "imports" / "PROGRAMME 20476 SITES.csv"
PROGRAM_DIR = PROJECT_ROOT / "data" / "programs" / "sites_20476"
JSON_PATH = PROGRAM_DIR / "sites_20476.json"
GEOJSON_PATH = PROGRAM_DIR / "sites_20476.geojson"


@pytest.fixture(scope="module")
def imported_payload():
    if not CSV_PATH.exists():
        pytest.skip(f"CSV national absent: {CSV_PATH}")
    # Réutiliser les artefacts déjà générés si valides (évite 20k reparse à chaque run)
    if JSON_PATH.exists() and GEOJSON_PATH.exists():
        payload = json.loads(JSON_PATH.read_text(encoding="utf-8"))
        if int(payload.get("_meta", {}).get("count") or 0) == 20476:
            return payload
    return fdsu_sites_import_service.import_sites_csv(
        CSV_PATH,
        program_code="sites_20476",
        write_outputs=True,
    )


def test_import_20476_count(imported_payload):
    assert imported_payload["_meta"]["count"] == 20476
    assert len(imported_payload["sites"]) == 20476


def test_import_normalized_fields(imported_payload):
    site = imported_payload["sites"][0]
    required = {
        "site_name",
        "latitude",
        "longitude",
        "province",
        "territoire",
        "zone",
        "population",
        "population_range",
        "nearest_site",
        "distance",
        "distance_level",
        "is_300_planned",
        "program_code",
    }
    assert required.issubset(site.keys())
    assert site["program_code"] == "sites_20476"


def test_geojson_valid(imported_payload):
    assert GEOJSON_PATH.exists()
    geo = json.loads(GEOJSON_PATH.read_text(encoding="utf-8"))
    assert geo["type"] == "FeatureCollection"
    assert len(geo["features"]) == 20476
    feature = geo["features"][0]
    assert feature["type"] == "Feature"
    assert feature["geometry"]["type"] == "Point"
    coords = feature["geometry"]["coordinates"]
    assert len(coords) == 2
    lon, lat = coords
    assert 12.0 <= lon <= 31.8
    assert -13.6 <= lat <= 5.6


def test_no_blocking_duplicates(imported_payload):
    stats = imported_payload.get("statistics") or {}
    assert stats.get("duplicate_rows", imported_payload["_meta"].get("duplicate_rows")) == 0


def test_planned_300_detected(imported_payload):
    planned = sum(1 for site in imported_payload["sites"] if site.get("is_300_planned"))
    assert planned > 0
    # Source CSV: Yes=272 (pas exactement 300 — fait métier)
    assert planned == 272


def test_priority_engine_national_scores():
    payload = fdsu_site_priority_service.list_priorities("sites_20476", limit=50)
    assert payload["summary"]["total"] == 20476
    assert payload["count"] == 50
    assert payload["sites"][0]["priority_score"] >= payload["sites"][-1]["priority_score"]
    site = payload["sites"][0]
    assert "criteria_details" in site
    assert "population" in site["criteria_details"]["criteria"]
    assert site["program_code"] == "sites_20476"


def test_top_priorities_and_explain():
    top = fdsu_site_priority_service.top_priorities("sites_20476", limit=5)
    assert len(top["sites"]) == 5
    site_id = top["sites"][0]["site_id"]
    explained = fdsu_site_priority_service.explain_site(site_id, program_code="sites_20476")
    assert explained is not None
    assert explained["explanation"]["criteria"]
    assert "calibration_note" in explained["explanation"]


def test_supported_programs_include_national():
    programs = fdsu_site_priority_service.list_supported_programs()
    codes = {item["program_code"] for item in programs}
    assert {"sites_40", "sites_300", "sites_20476"}.issubset(codes)
    national = next(item for item in programs if item["program_code"] == "sites_20476")
    assert national["data_available"] is True
    assert national["site_count"] == 20476


def test_program_code_aliases():
    assert fdsu_sites_import_service.normalize_program_code("PROG_SITES_20476") == "sites_20476"
    assert fdsu_sites_import_service.normalize_program_code("20476") == "sites_20476"
    assert fdsu_sites_import_service.normalize_program_code("sites_300") == "sites_300"
