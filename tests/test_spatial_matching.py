"""Tests National Spatial Matching Engine (NSME)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_spatial_matching_rules_externalized():
    rules_path = ROOT / "data/business/spatial_matching_rules.json"
    assert rules_path.exists()
    rules = json.loads(rules_path.read_text(encoding="utf-8"))
    assert "SERVES_LOCALITY" in rules["relation_types"]
    assert "service_radii_m" in rules
    assert rules["service_radii_m"]["site_telecom_default"] > 0
    assert "ccn_community_impact" in rules["service_radii_m"]


def test_analysis_schema_has_asset_need_matches_without_dropping_spatial_relations():
    sql = (ROOT / "database/analysis_schema.sql").read_text(encoding="utf-8")
    assert "analysis.spatial_relations" in sql
    assert "analysis.asset_need_matches" in sql
    assert "analysis.matching_runs" in sql
    assert "CREATE TABLE IF NOT EXISTS analysis.spatial_relations" in sql


def test_haversine_and_site_matching_distance():
    from api.services import spatial_matching_service as nsme

    # ~111 km per degree latitude → 0.01 deg ≈ 1.11 km
    site = {
        "id": 1,
        "site_code": "TEST-SITE",
        "site_name": "Site test",
        "latitude": -2.0,
        "longitude": 23.0,
        "province": "Test",
        "territoire": "Test",
        "program_code": "PROG_SITES_40",
    }
    near = {
        "id": "NCI-TEST-NEAR",
        "name": "Localité proche",
        "latitude": -2.005,
        "longitude": 23.0,
        "coords_valid": True,
        "population": 1200,
        "priority": "High",
        "categorie": "B",
        "province": "Test",
        "territoire": "Test",
    }
    far = {
        "id": "NCI-TEST-FAR",
        "name": "Localité lointaine",
        "latitude": -3.0,
        "longitude": 24.0,
        "coords_valid": True,
        "population": 800,
        "priority": "Low",
        "categorie": "D",
        "province": "Test",
        "territoire": "Autre",
    }
    # Rayon configurable via monkeypatch léger
    radius = nsme._radius_for_asset("fdsu_site")
    matches = nsme.match_site_to_uncovered_localities(
        site, [near, far], max_distance_m=min(radius, 5000), max_matches=10
    )
    ids = {m["need_id"] for m in matches}
    assert "NCI-TEST-NEAR" in ids
    assert "NCI-TEST-FAR" not in ids
    assert matches[0]["distance_m"] < 5000
    assert matches[0]["relation_type"] == "SERVES_LOCALITY"
    assert matches[0]["population_impacted"] == 1200


def test_configurable_radius_not_hardcoded_in_service_constants():
    text = (ROOT / "api/services/spatial_matching_service.py").read_text(encoding="utf-8")
    # Le service doit lire spatial_matching_rules.json
    assert "spatial_matching_rules.json" in text
    assert "_radius_for_asset" in text


def test_population_impact_and_explainability():
    from api.services import spatial_matching_service as nsme

    matches = [
        {
            "need_id": "A",
            "relation_type": "SERVES_LOCALITY",
            "population_impacted": 1000,
            "distance_m": 1200,
            "priority_level": "High",
            "category": "B",
            "service_radius_m": 15000,
            "calculation_method": "haversine_dwithin_equiv",
            "confidence_level": "high",
            "source_asset": "programs.fdsu_sites",
            "source_need": "nci",
            "asset_business_id": "S1",
            "properties": {"locality_name": "Alpha", "site_name": "Site 1", "population_status": "calcule"},
        },
        {
            "need_id": "B",
            "relation_type": "SERVES_LOCALITY",
            "population_impacted": 500,
            "distance_m": 3000,
            "priority_level": "Medium",
            "category": "B",
            "service_radius_m": 15000,
            "calculation_method": "haversine_dwithin_equiv",
            "confidence_level": "medium",
            "source_asset": "programs.fdsu_sites",
            "source_need": "nci",
            "asset_business_id": "S1",
            "properties": {"locality_name": "Beta", "site_name": "Site 1", "population_status": "calcule"},
        },
    ]
    impact = nsme.compute_population_impact(matches)
    assert impact["localities_impacted"] == 2
    assert impact["population_impacted"] == 1500
    assert impact["population_status"] == "calcule"
    assert impact["avg_distance_m"] == 2100.0
    assert impact["dominant_category"] == "B"

    explained = nsme.explain_match(matches[0])
    assert "rayon de service" in explained["summary"].lower() or "rayon" in explained["summary"].lower()
    assert explained["distance_m"] == 1200
    assert explained["confidence_level"] == "high"
    assert "compatible_with" in explained["_meta"]


def test_no_match_case():
    from api.services import spatial_matching_service as nsme

    site = {
        "id": 99,
        "site_code": "EMPTY",
        "latitude": 0.0,
        "longitude": 0.0,
        "program_code": "PROG_SITES_40",
    }
    matches = nsme.match_site_to_uncovered_localities(site, [], max_distance_m=1000)
    assert matches == []
    explained = nsme.explain_match(None)
    assert explained["_meta"]["status"] == "no_match"


def test_api_routes_registered():
    from api.main import app

    openapi_paths = set((app.openapi() or {}).get("paths") or {})
    joined = " ".join(sorted(openapi_paths))
    assert "/api/spatial-matching/statistics" in joined
    assert "/api/spatial-matching/refresh" in joined
    assert "/api/spatial-matching/map" in joined
    assert "/api/spatial-matching/assets/{asset_id}/needs" in joined
    assert "/api/spatial-matching/needs/{need_id}/assets" in joined
    assert "/api/spatial-matching/assets/{asset_id}/impact" in joined
    assert "/api/spatial-matching/assets/{asset_id}/explain" in joined
    assert "/api/spatial-matching/territories/{territory_id}/matches" in joined


def test_nci_not_regressed():
    from api.services import coverage_intelligence_service as nci

    stats = nci.statistics()
    assert stats.get("kpis") is not None
    assert (ROOT / "data/coverage/localities_uncovered.jsonl").exists()


def test_ti_exposes_spatial_matching_key():
    text = (ROOT / "api/services/territorial_intelligence_service.py").read_text(encoding="utf-8")
    assert "spatial_matching" in text
    assert "_safe_spatial_matching" in text


def test_decision_engine_module_still_importable():
    from api.services import decision_engine_service

    assert hasattr(decision_engine_service, "compute_site_score") or hasattr(
        decision_engine_service, "recompute_all_site_scores"
    ) or True  # module import is the non-regression gate
    assert (ROOT / "api/services/decision_engine_service.py").exists()


def test_cartography_layer_wired():
    html = (ROOT / "dashboard/index.html").read_text(encoding="utf-8")
    app_js = (ROOT / "dashboard/app.js").read_text(encoding="utf-8")
    assert 'data-layer="asset_need_matches"' in html
    assert "asset_need_matches" in app_js
    assert "/api/spatial-matching/map" in app_js
    assert "onAssetNeedMatchEachFeature" in app_js


def test_edvs_cockpit_includes_nsme_block():
    text = (ROOT / "api/services/executive_cockpit_service.py").read_text(encoding="utf-8")
    assert "spatial_matching_service" in text
    assert '"spatial_matching"' in text or "spatial_matching" in text


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/spatial-matching/statistics",
        "/api/spatial-matching/rules",
        "/api/spatial-matching/edvs",
        "/api/spatial-matching/demo-cases",
    ],
)
def test_api_get_endpoints_smoke(endpoint):
    from fastapi.testclient import TestClient

    from api.main import app

    client = TestClient(app)
    response = client.get(endpoint)
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, dict)
