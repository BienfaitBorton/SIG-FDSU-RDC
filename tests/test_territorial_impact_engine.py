"""Tests Moteur d’Impact Territorial — Data First, anti double-comptage."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.services import territorial_impact_engine as tie

CLIENT = TestClient(app)
DB = os.environ.get("DATA_MODE", "json").lower() == "db"


def test_audit_sources_matrix():
    matrix = tie.audit_population_sources()["matrix"]
    paths = {row["path"] for row in matrix}
    assert any("uncovered" in str(p) for p in paths)
    assert any("covered" in str(p) for p in paths)
    assert any("ccn" in str(p).lower() for p in paths)


def test_population_key_stable():
    a = tie.population_key(need_id="NCI-UNC-1")
    b = tie.population_key({"id": "NCI-UNC-1", "name": "X"})
    assert a == b == "nci:NCI-UNC-1"


@pytest.mark.skipif(not DB, reason="Site impact requires DB programs + NCI")
def test_site_40_impact_profile_no_invention():
    profile = tie.build_site_impact_profile(1, program_code="sites_40")
    assert profile is not None
    assert profile["asset_type"] == "FDSU_SITE"
    assert profile["deployment_date"] is None
    assert isinstance(profile["localities"], list)
    impact = profile["impact"]
    if impact.get("new_population_covered") is not None:
        assert impact["new_population_covered"] >= 0
    # detail calcul exposé
    assert profile["explainability"]["calculation_detail"]["double_counting_guard"]
    assert "NCI" in " ".join(profile["sources"]) or any("coverage" in s for s in profile["sources"])


@pytest.mark.skipif(not DB, reason="Scenario requires DB")
def test_scenario_monotone_and_no_double_count():
    payload = tie.build_deployment_scenario(
        programs=["sites_40"],
        include_ccn=True,
        limit_per_program=8,
        mode="planned",
    )
    assert payload["summary"]["monotone_cumulative"] is True
    site_deps = [d for d in payload["deployments"] if d["asset_type"] == "FDSU_SITE"]
    cumul = [d["cumulative_population_covered"] for d in site_deps]
    assert all(cumul[i] <= cumul[i + 1] for i in range(len(cumul) - 1))
    rem = [d["remaining_population_uncovered"] for d in site_deps if d.get("remaining_population_uncovered") is not None]
    assert all(r >= 0 for r in rem)
    # CCN n'augmente pas le cumul radio
    for d in payload["deployments"]:
        if d["asset_type"] == "CCN":
            assert d.get("new_population_covered") == 0
            assert d.get("nature") == "acces_services_numeriques_ccn"


@pytest.mark.skipif(not DB, reason="API live against DB")
def test_api_site_and_scenario():
    site = CLIENT.get("/api/territorial-impact/sites/1?program_code=sites_40")
    assert site.status_code == 200
    body = site.json()
    assert body["name"]
    assert "localities" in body

    scen = CLIENT.get(
        "/api/territorial-impact/scenario?programs=sites_40&limit_per_program=5&include_ccn=true"
    )
    assert scen.status_code == 200
    data = scen.json()
    assert data["charts"]["cumulative_curve"]
    assert data["charts"]["contribution_bars"] is not None
    assert data["data_quality"]["limits"]


def test_api_audit():
    res = CLIENT.get("/api/territorial-impact/audit/sources")
    assert res.status_code == 200
    assert len(res.json()["matrix"]) >= 5
