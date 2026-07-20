"""Tests SharedSpatialContext + progressive decision case."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("DATA_MODE", os.environ.get("DATA_MODE", "json"))


@pytest.fixture()
def spatial_ctx():
    from api.services import shared_spatial_context as ssc
    from api.services import site_spatial_context_cache as scc

    ssc.clear()
    ssc.reset_stats()
    ssc.set_cache_enabled(True)
    scc.clear()
    scc.reset_stats()
    yield ssc
    ssc.clear()
    scc.clear()


def test_shared_spatial_cache_hit(spatial_ctx):
    calls = {"n": 0}

    def builder():
        calls["n"] += 1
        return {"ok": True}

    key = spatial_ctx.make_geo_key("unit", -4.3, 15.3, radius_m=1000)
    a = spatial_ctx.get_or_build(key, builder)
    b = spatial_ctx.get_or_build(key, builder)
    assert a == b
    assert calls["n"] == 1
    assert spatial_ctx.stats()["HIT"] >= 1


def test_decision_core_faster_than_full_or_skips_evidence(spatial_ctx):
    from api.services import explainable_decision_service as eds
    from api.services import site_spatial_context_cache as scc

    scc.clear()
    core = eds.get_decision_case("29", asset_type="site", program_code="sites_40", include_spatial_evidence=False)
    if core is None:
        pytest.skip("Site 29 unavailable")
    assert core.get("spatial_evidence_status") == "deferred"
    assert (core.get("telecom_context") or {}).get("deferred") is True
    assert core.get("asset", {}).get("name")
    assert core.get("score", {}).get("global") is not None

    full = eds.build_site_case("29", program_code="sites_40", include_spatial_evidence=True)
    assert full is not None
    assert full.get("spatial_evidence_status") == "ready"
    # Métier inchangé sur identité / score
    assert full["asset"]["site_id"] == core["asset"]["site_id"]
    assert full["score"]["global"] == core["score"]["global"]


def test_attach_spatial_evidence_enriches(spatial_ctx):
    from api.services import explainable_decision_service as eds

    core = eds.get_decision_case("29", asset_type="site", program_code="sites_40", include_spatial_evidence=False)
    if core is None:
        pytest.skip("Site 29 unavailable")
    enriched = eds.attach_spatial_evidence(dict(core))
    assert enriched.get("spatial_evidence_status") == "ready"
    assert "telecom_context" in enriched
    assert enriched["telecom_context"].get("deferred") is not True


def test_api_core_and_evidence_endpoints():
    from fastapi.testclient import TestClient

    from api.main import app

    client = TestClient(app)
    core = client.get("/api/decision/case/29?asset_type=site&program_code=sites_40&include_spatial_evidence=false")
    if core.status_code == 404:
        pytest.skip("Site 29 unavailable via API")
    assert core.status_code == 200
    body = core.json()
    assert body.get("spatial_evidence_status") == "deferred"
    name = body["asset"].get("site_name") or body["asset"].get("name")
    assert name and str(name) != "29"

    ev = client.get("/api/decision/case/29/spatial-evidence?asset_type=site&program_code=sites_40")
    assert ev.status_code == 200
    evb = ev.json()
    assert evb.get("spatial_evidence_status") == "ready"


def test_referential_counts_stable():
    from api.services.nire import groupement_controlled_integration as gci
    from api.services.nire import locality_controlled_integration as lci

    assert lci.national_locality_count(include_enrichment=True) == 47130
    grp = gci.national_groupement_counts(include_enrichment=True)
    assert int(grp.get("total_count") or 0) == 2642
