"""Tests Program Lifecycle Engine — six dimensions, pas de faux opérationnel."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.services import program_lifecycle_engine as ple
from api.services import territorial_impact_engine as tie
from api.services import spatial_decision_graph_service as sdg

CLIENT = TestClient(app)
DB = os.environ.get("DATA_MODE", "json").lower() == "db"

SITE_IDS = [7, 14, 16, 26, 29, 30, 34, 42]


def test_sites_40_deployment_in_progress_not_operational():
    p = ple.resolve_program_lifecycle("sites_40")
    assert p["program_status"]["code"] == "deployment_in_progress"
    assert p["program_status"]["label"] != "Opérationnel"
    assert p["data_status"]["code"] == "integrated"
    assert p["data_status"]["code"] != p["program_status"]["code"]
    assert p["progress"]["operational"] is None
    assert p["progress"]["installed"] is None


def test_sites_300_planned_not_operational():
    p = ple.resolve_program_lifecycle("sites_300")
    assert p["program_status"]["code"] == "planned"
    assert "opération" not in (p["program_status"]["label"] or "").lower()


def test_sites_20476_strategic_planning():
    p = ple.resolve_program_lifecycle("sites_20476")
    assert p["program_status"]["code"] == "strategic_planning"


def test_ccn_demo_not_production_operational():
    p = ple.resolve_program_lifecycle("ccn")
    assert p["program_status"]["code"] == "preparation"
    a = ple.resolve_asset_lifecycle(
        program_code="ccn",
        asset_id="CCN-DEMO-1",
        raw_status="operational",
        asset_type="CCN",
        data_class="demonstration",
    )
    assert a["asset_status"]["code"] != "operational"
    assert a["impact_accounting"]["counts_as_observed_coverage"] is False


def test_null_not_fake_zero_on_board():
    board = ple.build_programs_board()
    for row in board["programs"]:
        assert row["operational"] is None
        assert row["display"]["operational"] == "À consolider"


def test_sdg_maturity_label_not_physical_operational():
    assert sdg.OFFICIAL_STATUS["operational"]["label"] == "Référentiel intégré"
    assert "Opérationnel" != sdg.OFFICIAL_STATUS["operational"]["label"]


def test_classify_deployment_no_keyword_realized():
    meta = tie.classify_deployment_status("à qualifier", program_code="sites_40")
    assert meta.get("counts_as_observed_coverage") is False
    assert meta["mode"] != "real" or meta.get("badge") != "Réalisé"


def test_legacy_actif_does_not_force_operational_asset():
    life = ple.resolve_asset_lifecycle(program_code="sites_40", raw_status="actif", asset_id=29)
    assert life["asset_status"]["code"] != "operational"
    assert life["impact_accounting"]["counts_as_observed_coverage"] is False


@pytest.mark.skipif(not DB, reason="Site profiles require DB")
@pytest.mark.parametrize("site_id", SITE_IDS)
def test_site_profiles_no_fake_operational(site_id):
    profile = tie.build_site_impact_profile(site_id, program_code="sites_40")
    if not profile:
        pytest.skip(f"site {site_id} unresolved")
    badges = profile.get("ui_badges") or {}
    assert "Opérationnel" not in (badges.get("asset") or "")
    # population vs localities not mixed in nature_label
    nature = (profile.get("impact") or {}).get("nature_label") or ""
    assert "nouvelles localités (" not in nature.lower()


def test_api_programs_board():
    r = CLIENT.get("/api/program-lifecycle/programs")
    assert r.status_code == 200
    body = r.json()
    codes = {p["program_code"] for p in body["programs"]}
    assert {"sites_40", "sites_300", "sites_20476", "ccn"} <= codes
    s40 = next(p for p in body["programs"] if p["program_code"] == "sites_40")
    assert s40["status_code"] == "deployment_in_progress"


def test_population_locality_wording_guard():
    """Guard against mixed population/locality phrasing in UI sentences."""
    bad = "+25500 nouvelles localités (12)"
    assert "bénéficiaires" not in bad  # documents anti-pattern
    good = "+25 500 bénéficiaires projetés dans 12 localités après mise en service"
    assert "bénéficiaires" in good and "localités" in good
