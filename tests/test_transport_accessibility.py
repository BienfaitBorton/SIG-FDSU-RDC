"""Tests Transport & Accessibility Intelligence v1.0."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.services import transport_service as ts

CLIENT = TestClient(app)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
KMZ = PROJECT_ROOT / "data" / "raw" / "Routes_principales.shp.kmz"


def _load_pipeline():
    import importlib.util

    path = PROJECT_ROOT / "scripts" / "import_routes_principales_kmz.py"
    spec = importlib.util.spec_from_file_location("import_routes_principales_kmz", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_accessibility_formula_documented_and_transparent():
    scored = ts.compute_accessibility_score(400, "Route primaire")
    assert scored["score"] == 100  # 80 + 20
    assert "80" in scored["justification"]
    assert scored["components"]["distance_points"] == 80
    assert scored["components"]["type_points"] == 20
    assert "formula" in scored

    far = ts.compute_accessibility_score(20000, "Autre")
    assert far["score"] == 25  # 20 + 5
    missing = ts.compute_accessibility_score(None, None)
    assert missing["display"] == "Données insuffisantes"


def test_pipeline_parse_sample_and_quality(tmp_path, monkeypatch):
    pipeline = _load_pipeline()
    assert KMZ.exists()
    kml = pipeline.extract_kml(KMZ)
    features, quality = pipeline.parse_routes(kml, limit=50)
    assert len(features) >= 1
    assert all(f["geometry"]["type"] == "LineString" for f in features)
    assert all(f["geometry"]["coordinates"] for f in features)
    codes = {c["code"] for c in quality["checks"]}
    assert {"invalid_geometry", "duplicate_routes", "unnamed_routes", "outside_rdc", "incoherent_segments"} <= codes

    # Write outputs to temp dirs
    monkeypatch.setattr(pipeline, "PROCESSED_DIR", tmp_path / "processed")
    monkeypatch.setattr(pipeline, "QUALITY_DIR", tmp_path / "quality")
    monkeypatch.setattr(pipeline, "GEOJSON_PATH", tmp_path / "processed" / "routes.geojson")
    monkeypatch.setattr(pipeline, "QUALITY_PATH", tmp_path / "quality" / "q.json")
    monkeypatch.setattr(pipeline, "MANIFEST_PATH", tmp_path / "manifest.json")
    pipeline.write_outputs(features, quality)
    assert (tmp_path / "processed" / "routes.geojson").exists()
    assert (tmp_path / "quality" / "q.json").exists()
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["sources"][0]["not_served_in_production"] is True


def test_schema_sql_exists_and_has_gist():
    sql = (PROJECT_ROOT / "database" / "transport_schema.sql").read_text(encoding="utf-8")
    assert "CREATE SCHEMA IF NOT EXISTS transport" in sql
    assert "transport.routes" in sql
    assert "USING GIST (geom)" in sql
    assert "longueur_m" in sql
    assert "date_import" in sql


def test_ndf_transport_active():
    from api.services import national_data_fabric_service as ndf

    reg = ndf.get_registry("transport")
    assert reg["registry"]["status"] == "active"
    assert any("/api/transport" in a for a in reg["registry"]["apis"])
    rel = ndf.list_relations("transport")
    assert rel["_meta"]["count"] >= 3


def test_nsme_rules_include_road_relations():
    from api.services.spatial_matching_service import get_rules

    rules = get_rules()
    assert "NEAR_MAIN_ROAD" in rules["relation_types"]
    assert "WITHIN_ROAD_CORRIDOR" in rules["relation_types"]
    assert "ROAD_ACCESSIBILITY" in rules["relation_types"]
    assert "nearest_main_road" in rules["service_radii_m"]


def test_tst_accessibility_metric_catalogued():
    from api.services import territorial_summary_service as tst

    ids = {m["id"] for m in tst.list_metrics()["metrics"]}
    assert "accessibility" in ids


def test_decision_engine_routes_weight_active():
    from api.services.decision_engine_service import CRITERIA_WEIGHTS, PENDING_SECTORIAL_CRITERIA

    assert CRITERIA_WEIGHTS["routes"] > 0
    assert "routes" not in PENDING_SECTORIAL_CRITERIA


def test_api_transport_formula_and_quality():
    formula = CLIENT.get("/api/transport/formula")
    assert formula.status_code == 200
    assert formula.json()["formula"]["version"] == "1.0"

    quality = CLIENT.get("/api/transport/quality")
    assert quality.status_code == 200


def test_api_transport_db_endpoints_graceful():
    # En mode DB : 200 ou données vides ; hors DB : 503
    stats = CLIENT.get("/api/transport/statistics")
    assert stats.status_code in {200, 503}
    layer = CLIENT.get("/api/transport/layers/routes_principales")
    assert layer.status_code in {200, 503}
    nearest = CLIENT.get("/api/transport/nearest-road", params={"lon": 15.3, "lat": -4.3})
    assert nearest.status_code in {200, 503}


@pytest.mark.skipif(not KMZ.exists(), reason="KMZ source absent")
def test_no_production_reads_raw_kmz_in_service():
    # Le service ne doit pas référencer le chemin KMZ brut
    src = (PROJECT_ROOT / "api" / "services" / "transport_service.py").read_text(encoding="utf-8")
    assert "Routes_principales.shp.kmz" not in src
    assert "transport.routes" in src or "PostGIS" in src or "connect_db" in src
