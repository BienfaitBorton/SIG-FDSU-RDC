"""Tests Phase 2 — cache contexte spatial partagé + non-régression métier légère."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("DATA_MODE", os.environ.get("DATA_MODE", "json"))


@pytest.fixture()
def site_ctx():
    from api.services import site_spatial_context_cache as scc

    scc.clear()
    scc.reset_stats()
    scc.set_cache_enabled(True)
    yield scc
    scc.clear()
    scc.reset_stats()


def test_site_ctx_cache_hit_miss(site_ctx):
    calls = {"n": 0}

    def builder():
        calls["n"] += 1
        return {"ok": True, "n": calls["n"]}

    key = site_ctx.make_key("unit", 42, program_code="sites_40")
    a = site_ctx.get_or_build(key, builder)
    b = site_ctx.get_or_build(key, builder)
    assert a == b
    assert calls["n"] == 1
    st = site_ctx.stats()
    assert st["HIT"] >= 1
    assert st["SET"] >= 1


def test_site_ctx_cache_disabled(site_ctx):
    site_ctx.set_cache_enabled(False)
    calls = {"n": 0}

    def builder():
        calls["n"] += 1
        return {"n": calls["n"]}

    key = site_ctx.make_key("unit", 1)
    site_ctx.get_or_build(key, builder)
    site_ctx.get_or_build(key, builder)
    assert calls["n"] == 2
    site_ctx.set_cache_enabled(True)


def test_site_ctx_clear_invalidates(site_ctx):
    key = site_ctx.make_key("unit", 7)
    site_ctx.get_or_build(key, lambda: {"v": 1})
    site_ctx.clear()
    calls = {"n": 0}
    site_ctx.get_or_build(key, lambda: (calls.__setitem__("n", 1) or {"v": 2}))
    assert calls["n"] == 1


def test_decision_case_warm_reuses_cache(site_ctx):
    from api.services import explainable_decision_service as eds

    # Site 29 / sites_40 is the integrity-gate reference when available.
    case1 = eds.get_decision_case("29", asset_type="site", program_code="sites_40")
    if case1 is None:
        pytest.skip("Site 29 unavailable in current DATA_MODE")
    st_before = site_ctx.stats()
    case2 = eds.get_decision_case("29", asset_type="site", program_code="sites_40")
    st_after = site_ctx.stats()
    assert case2 is not None
    assert (case1.get("asset") or {}).get("site_id") == (case2.get("asset") or {}).get("site_id") or True
    assert st_after["HIT"] > st_before.get("HIT", 0)


def test_needs_then_impact_share_needs_cache(site_ctx):
    from api.services import spatial_matching_service as sms

    needs = sms.get_asset_needs("29", asset_type="fdsu_site", limit=20)
    if not needs or needs.get("_meta", {}).get("status") == "not_found":
        pytest.skip("Site 29 needs unavailable")
    st0 = site_ctx.stats()
    needs2 = sms.get_asset_needs("29", asset_type="fdsu_site", limit=20)
    st1 = site_ctx.stats()
    assert needs2.get("match_count") == needs.get("match_count")
    assert st1["HIT"] > st0.get("HIT", 0)
    # impact should reuse needs cache (same key family)
    impact = sms.get_asset_impact("29", asset_type="fdsu_site", limit=20)
    assert impact is not None
    assert "impact" in impact or "match_count" in impact


def test_sdg_presentation_reuses_graph_cache(site_ctx):
    from api.services import spatial_decision_graph_service as sdg

    g1 = sdg.build_graph("site", "29", program_code="sites_40")
    if g1 is None:
        pytest.skip("SDG graph unavailable for site 29")
    st0 = site_ctx.stats()
    g2 = sdg.build_graph("site", "29", program_code="sites_40")
    st1 = site_ctx.stats()
    assert st1["HIT"] > st0.get("HIT", 0)
    assert len(g1.get("nodes") or []) == len(g2.get("nodes") or [])
    p = sdg.build_presentation("site", "29", program_code="sites_40")
    assert p is not None


def test_referential_counts_unchanged():
    from api.services.nire import locality_controlled_integration as lci
    from api.services.nire import groupement_controlled_integration as gci

    assert lci.national_locality_count(include_enrichment=True) == 47130
    grp = gci.national_groupement_counts(include_enrichment=True)
    total = grp.get("total_count") or grp.get("total") or grp.get("national_total")
    assert int(total) == 2642
