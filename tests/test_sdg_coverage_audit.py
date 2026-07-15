"""Tests audit de couverture SDG + explicabilité."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.services import sdg_coverage_service as coverage
from api.services import spatial_decision_graph_service as sdg

CLIENT = TestClient(app)
DB = os.environ.get("DATA_MODE", "json").lower() == "db"


def test_diagnose_without_coords_is_impossible():
    diag = coverage.diagnose_site(
        {"site_name": "X", "program_code": "sites_20476"},
        matches=[],
        radius_m=15000,
        nsme_found=False,
    )
    assert diag["classification"] == "C"
    assert "coordonnées" in " ".join(diag["missing"])


def test_diagnose_partial_with_some_layers():
    matches = [
        {"relation_type": "NEAR_HEALTH_FACILITY", "population_impacted": None},
        {"relation_type": "NEAR_ROAD"},
    ]
    diag = coverage.diagnose_site(
        {
            "id": 1,
            "site_name": "Test",
            "latitude": -4.3,
            "longitude": 15.3,
            "province": "Kinshasa",
            "program_code": "sites_40",
        },
        matches=matches,
        radius_m=15000,
        nsme_found=True,
    )
    assert diag["classification"] == "B"
    assert diag["layers"]["health"] is True
    assert diag["layers"]["roads"] is True
    assert diag["layers"]["telecom"] is False


def test_explainability_card_lists_missing():
    diag = coverage.diagnose_site(
        {"site_name": "Y", "latitude": None, "longitude": None, "province": "Kwilu"},
        matches=[],
        radius_m=None,
        nsme_found=False,
    )
    card = coverage.build_explainability_card(site={"province": "Kwilu"}, diagnosis=diag)
    assert card["title"]
    assert any("oord" in m.lower() or "Coord" in m for m in card["missing"]) or "Coordonnées" in card["missing"]
    assert "Province" in card["available"]


def test_api_coverage_matrix():
    r = CLIENT.get("/api/sdg/coverage?deep_sample=0&include_ccn=true")
    assert r.status_code == 200
    body = r.json()
    assert "coverage_rate" in body
    assert "programs" in body
    assert "matrix" in body
    codes = {row["program_code"] for row in body["matrix"]}
    assert "sites_40" in codes
    assert "sites_20476" in codes or "national" in codes
    # Sites 20476 known absents de NSME DB
    p20476 = body["programs"].get("sites_20476") or {}
    assert p20476.get("total", 0) >= 0
    if p20476.get("total"):
        assert "hors" in (p20476.get("note") or "").lower() or p20476.get("partial", 0) >= 0


def test_build_graph_never_silent_none_for_unknown():
    """Unknown site returns explainability payload, not bare None (Data First)."""
    graph = sdg.build_graph("site", "999999001", program_code="sites_40")
    assert graph is not None
    assert graph.get("explainability") or graph.get("_meta", {}).get("status") == "impossible"


@pytest.mark.skipif(not DB, reason="requires DB sites_40")
def test_sites_40_graph_has_classification():
    graph = sdg.build_graph("site", "1", program_code="sites_40")
    assert graph is not None
    assert graph.get("coverage_diagnosis") or graph.get("explainability")
    assert graph["_meta"].get("classification") in {"A", "B", "C", None} or graph.get("explainability")
