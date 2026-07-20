"""Tests Phase 2C — roads KNN + build_graph sans double nearest_road + cache invalidation."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("DATA_MODE", os.environ.get("DATA_MODE", "json"))


def test_nearest_road_returns_closest_point_when_db():
    if os.environ.get("DATA_MODE", "json").lower() != "db":
        pytest.skip("requires DATA_MODE=db")
    from api.services import transport_service as ts

    road = ts.nearest_road(14.589993, -4.963924)
    if not road:
        pytest.skip("no nearest road")
    assert road.get("closest_lon") is not None
    assert road.get("closest_lat") is not None
    assert road.get("distance_m") is not None


def test_match_roads_sets_need_coords(monkeypatch):
    from api.services import shared_spatial_context as ssc
    from api.services import spatial_matching_service as sms

    ssc.clear()
    fake = {
        "id": 1,
        "nom": "RN1",
        "type_route": "nationale",
        "etat": "bon",
        "distance_m": 120.0,
        "closest_lon": 14.59,
        "closest_lat": -4.96,
    }
    monkeypatch.setattr(ssc, "get_nearest_road", lambda *a, **k: fake)
    matches = sms.match_site_to_roads({"id": 29, "site_id": 29, "longitude": 14.58, "latitude": -4.96})
    assert matches
    for m in matches:
        props = m.get("properties") or {}
        assert props.get("need_lon") == 14.59
        assert props.get("need_lat") == -4.96


def test_road_endpoint_does_not_recall_transport_when_coords_present(monkeypatch):
    from api.services import spatial_decision_graph_service as sdg
    from api.services import transport_service as ts

    calls = {"n": 0}

    def boom(*a, **k):
        calls["n"] += 1
        raise AssertionError("nearest_road must not be called")

    monkeypatch.setattr(ts, "nearest_road", boom)
    ep = sdg._road_endpoint(
        {"properties": {"need_lon": 14.1, "need_lat": -4.2}},
        14.0,
        -4.0,
    )
    assert ep == (14.1, -4.2)
    assert calls["n"] == 0


def test_build_graph_cache_invalidates_on_coords():
    from api.services import site_spatial_context_cache as scc

    k1 = scc.make_key("sdg_graph", 29, program_code="sites_40", asset_type="site", lat=-4.96, lon=14.58)
    k2 = scc.make_key("sdg_graph", 29, program_code="sites_40", asset_type="site", lat=-4.96, lon=14.58)
    k3 = scc.make_key("sdg_graph", 29, program_code="sites_40", asset_type="site", lat=-5.00, lon=14.58)
    assert k1 == k2
    assert k1 != k3


def test_build_graph_cache_includes_rules_version():
    from api.services import site_spatial_context_cache as scc

    k = scc.make_key("sdg_graph", 29, program_code="sites_40", asset_type="site", lat=-4.96, lon=14.58)
    assert "site_ctx_v2" in k
    assert scc._rules_ver() in k


def test_shared_nearest_road_reused(monkeypatch):
    from api.services import shared_spatial_context as ssc
    from api.services import transport_service as ts

    ssc.clear()
    ssc.set_cache_enabled(True)
    calls = {"n": 0}
    real = ts.nearest_road

    def spy(lon, lat, max_distance_m=50000):
        calls["n"] += 1
        return {"id": 99, "distance_m": 10.0, "closest_lon": lon, "closest_lat": lat, "nom": "X"}

    monkeypatch.setattr(ts, "nearest_road", spy)
    a = ssc.get_nearest_road(14.58, -4.96)
    b = ssc.get_nearest_road(14.58, -4.96)
    assert a and b
    assert calls["n"] == 1


def test_probe_cache_hit():
    from api.services import spatial_decision_graph_service as sdg

    sdg.clear_probe_cache()
    p1 = sdg._probe_referential_availability(14.58, -4.96)
    p2 = sdg._probe_referential_availability(14.58, -4.96)
    assert p1 is p2
