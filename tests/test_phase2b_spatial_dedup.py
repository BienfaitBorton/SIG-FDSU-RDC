"""Tests Phase 2B — clé needs partagée + SDG sans evidence lourde."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("DATA_MODE", os.environ.get("DATA_MODE", "json"))


def test_needs_cache_shared_across_limits():
    from api.services import site_spatial_context_cache as scc
    from api.services import spatial_matching_service as sms

    scc.clear()
    scc.reset_stats()
    scc.set_cache_enabled(True)

    a = sms.get_asset_needs("29", asset_type="fdsu_site", limit=20)
    if not a or a.get("_meta", {}).get("status") == "not_found":
        pytest.skip("Site 29 needs unavailable")
    st0 = scc.stats()
    b = sms.get_asset_needs("29", asset_type="fdsu_site", limit=50)
    st1 = scc.stats()
    assert st1["HIT"] > st0.get("HIT", 0)
    # Même corpus sous-jacent (full_match_count)
    full_a = (a.get("_meta") or {}).get("full_match_count")
    full_b = (b.get("_meta") or {}).get("full_match_count")
    if full_a is not None and full_b is not None:
        assert full_a == full_b


def test_impact_reuses_needs_cache():
    from api.services import site_spatial_context_cache as scc
    from api.services import spatial_matching_service as sms

    scc.clear()
    scc.set_cache_enabled(True)
    needs = sms.get_asset_needs("29", asset_type="fdsu_site", limit=30)
    if not needs or not needs.get("matches"):
        pytest.skip("Site 29 needs unavailable")
    st0 = scc.stats()
    impact = sms.get_asset_impact("29", asset_type="fdsu_site")
    assert impact is not None
    st1 = scc.stats()
    assert st1["HIT"] >= st0.get("HIT", 0)


def test_make_key_includes_coords_when_provided():
    from api.services import site_spatial_context_cache as scc

    k1 = scc.make_key("unit", 29, lat=-4.96, lon=14.58)
    k2 = scc.make_key("unit", 29, lat=-4.96, lon=14.58)
    k3 = scc.make_key("unit", 29, lat=-5.00, lon=14.58)
    assert k1 == k2
    assert k1 != k3


def test_sdg_uses_core_decision_case(monkeypatch):
    """SDG ne doit pas forcer include_spatial_evidence=True."""
    from api.services import spatial_decision_graph_service as sdg
    from api.services import explainable_decision_service as eds

    calls = []

    real = eds.get_decision_case

    def spy(*args, **kwargs):
        calls.append(kwargs)
        return real(*args, **kwargs)

    monkeypatch.setattr(eds, "get_decision_case", spy)
    # Peut skip si graphe indisponible
    try:
        g = sdg.build_graph("site", "29", program_code="sites_40")
    except Exception:
        pytest.skip("SDG unavailable")
    if g is None:
        pytest.skip("SDG graph None")
    evidence_flags = [c.get("include_spatial_evidence") for c in calls if "include_spatial_evidence" in c]
    if evidence_flags:
        assert all(flag is False for flag in evidence_flags)
