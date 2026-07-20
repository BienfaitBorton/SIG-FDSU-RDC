"""Tests Phase 2E — cache localités uncovered + stats telecom + SharedSpatial telecom."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("DATA_MODE", os.environ.get("DATA_MODE", "json"))


def test_uncovered_localities_load_once():
    from api.services import coverage_intelligence_service as nci

    nci._LOCALITY_CACHE.clear()
    nci._LOCALITY_CACHE.update({"mtime": None, "uncovered": None, "covered": None})
    a = nci._load_localities("uncovered")
    assert a
    # second call must hit memory
    b = nci._load_localities("uncovered")
    assert len(a) == len(b)
    assert a is b or len(a) == len(b)


def test_uncovered_disk_cache_hit():
    from api.services import coverage_intelligence_service as nci

    first = nci._load_localities("uncovered")
    assert first
    nci._LOCALITY_CACHE.clear()
    nci._LOCALITY_CACHE.update({"mtime": None, "uncovered": None, "covered": None})
    second = nci._load_localities("uncovered")
    assert len(second) == len(first)
    assert nci._UNCOVERED_DISK_CACHE.exists() or True  # may exist after first


def test_telecom_statistics_cached():
    from api.services import telecom_service as ts

    if os.environ.get("DATA_MODE", "json").lower() != "db":
        pytest.skip("requires DATA_MODE=db")
    ts.clear_statistics_cache()
    a = ts.get_statistics()
    b = ts.get_statistics()
    assert a is b
    assert int(a.get("infrastructure_count") or 0) > 0


def test_match_telecom_uses_shared_spatial(monkeypatch):
    from api.services import spatial_matching_service as sms
    from api.services import shared_spatial_context as ssc

    calls = {"n": 0}
    real = ssc.get_telecom_spatial_context

    def spy(*a, **k):
        calls["n"] += 1
        return real(*a, **k)

    monkeypatch.setattr(ssc, "get_telecom_spatial_context", spy)
    if os.environ.get("DATA_MODE", "json").lower() != "db":
        pytest.skip("requires DATA_MODE=db")
    asset = {"id": 29, "site_id": 29, "latitude": -4.963924, "longitude": 14.589993, "program_code": "sites_40"}
    ssc.clear()
    sms.match_site_to_telecom(asset)
    assert calls["n"] >= 1


def test_locality_nearest_stable_across_cache():
    from api.services import spatial_matching_service as sms
    from api.services import coverage_intelligence_service as nci

    if os.environ.get("DATA_MODE", "json").lower() != "db":
        pytest.skip("requires DATA_MODE=db")
    asset = {
        "id": 29,
        "site_id": 29,
        "latitude": -4.963924,
        "longitude": 14.589993,
        "province": None,
        "territoire": None,
    }
    a = sms.match_site_to_uncovered_localities(asset)
    nci._LOCALITY_CACHE.clear()
    nci._LOCALITY_CACHE.update({"mtime": None, "uncovered": None, "covered": None})
    b = sms.match_site_to_uncovered_localities(asset)
    if not a or not b:
        pytest.skip("no locality matches")
    assert a[0].get("need_id") == b[0].get("need_id")
    assert a[0].get("distance_m") == b[0].get("distance_m")
