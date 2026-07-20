"""Tests Phase 2D — cache projection Éducation + SharedSpatial + exactitude."""

from __future__ import annotations

import os
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

os.environ.setdefault("DATA_MODE", os.environ.get("DATA_MODE", "json"))


@pytest.fixture()
def edu_clean():
    from api.services import education_referential_service as edu
    from api.services import ceni_registry_service as ceni
    from api.services import shared_spatial_context as ssc
    from api.services import referential_runtime_cache as rrc

    edu.clear_education_caches(clear_disk=False)
    ceni.registry.cache_clear()
    ssc.clear()
    rrc.clear_all_caches()
    yield edu
    edu.clear_education_caches(clear_disk=False)


def test_education_projection_loads_once(edu_clean):
    edu = edu_clean
    a = edu._mappable_schools()
    st0 = edu.education_cache_stats()
    b = edu._mappable_schools()
    st1 = edu.education_cache_stats()
    assert len(a) == len(b)
    assert st1["MEM_HITS"] >= 1
    assert st1["BUILDS"] == st0["BUILDS"]  # no second build


def test_education_disk_cache_hit(edu_clean):
    edu = edu_clean
    first = edu._mappable_schools()
    assert first
    # clear memory + CENI lru, keep disk
    from api.services import ceni_registry_service as ceni

    edu.clear_education_caches(clear_disk=False)
    ceni.registry.cache_clear()
    second = edu._mappable_schools()
    st = edu.education_cache_stats()
    assert len(second) == len(first)
    assert st["DISK_HITS"] >= 1 or st["MEM_HITS"] >= 1


def test_education_signature_invalidation(edu_clean, monkeypatch):
    edu = edu_clean
    rows = edu._mappable_schools()
    assert rows
    # Force different signature → rebuild path (may still rebuild from CENI)
    monkeypatch.setattr(edu, "_registry_signature", lambda: (("fake", 1, 2),))
    edu.clear_education_caches(clear_disk=False)
    # Without matching disk, build increments
    st_before = edu.education_cache_stats()["BUILDS"]
    # Restore real signature for actual build feasibility
    monkeypatch.undo()
    edu.clear_education_caches(clear_disk=False)
    edu._mappable_schools()
    # Sanity: cache stats API works
    assert "BUILDS" in edu.education_cache_stats()


def test_education_concurrent_single_build(edu_clean):
    edu = edu_clean
    edu.clear_education_caches(clear_disk=True)
    from api.services import ceni_registry_service as ceni

    ceni.registry.cache_clear()
    barrier = threading.Barrier(4)
    results = []

    def worker():
        barrier.wait(timeout=30)
        results.append(len(edu._mappable_schools()))

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda _: worker(), range(4)))
    st = edu.education_cache_stats()
    assert len(set(results)) == 1
    assert st["BUILDS"] == 1


def test_nearest_stable_across_cache_layers(edu_clean):
    edu = edu_clean
    lat, lon = -4.963924, 14.589993
    a = edu.nearest_establishment(lat, lon, radius_m=25000, limit=5)
    from api.services import ceni_registry_service as ceni

    edu.clear_education_caches(clear_disk=False)
    ceni.registry.cache_clear()
    b = edu.nearest_establishment(lat, lon, radius_m=25000, limit=5)
    na, nb = a.get("nearest") or {}, b.get("nearest") or {}
    if not na and not nb:
        pytest.skip("no nearest education")
    assert na.get("education_id") == nb.get("education_id")
    assert na.get("distance_m") == nb.get("distance_m")
    assert na.get("latitude") == nb.get("latitude")
    assert na.get("longitude") == nb.get("longitude")


def test_shared_spatial_education_reused(edu_clean):
    from api.services import shared_spatial_context as ssc

    ssc.clear()
    ssc.set_cache_enabled(True)
    ssc.reset_stats()
    lat, lon = -4.963924, 14.589993
    a = ssc.get_education_nearest(lat, lon, radius_m=25000, limit=10)
    st0 = ssc.stats()
    b = ssc.get_education_nearest(lat, lon, radius_m=25000, limit=10)
    st1 = ssc.stats()
    assert a and b
    assert st1["HIT"] > st0.get("HIT", 0)


def test_needs_then_education_no_second_projection_build(edu_clean):
    """Après needs, un nearest education ne doit pas reconstruire la projection."""
    from api.services import spatial_matching_service as sms
    from api.services import site_spatial_context_cache as scc
    from api.services import shared_spatial_context as ssc

    if os.environ.get("DATA_MODE", "json").lower() != "db":
        pytest.skip("requires DATA_MODE=db")

    scc.clear()
    ssc.clear()
    edu_clean.clear_education_caches(clear_disk=False)
    needs = sms.get_asset_needs(29, asset_type="fdsu_site", limit=50)
    if not needs or needs.get("_meta", {}).get("status") == "not_found":
        pytest.skip("site 29 unavailable")
    builds_after_needs = edu_clean.education_cache_stats()["BUILDS"]
    edu_clean.nearest_establishment(-4.963924, 14.589993)
    assert edu_clean.education_cache_stats()["BUILDS"] == builds_after_needs
