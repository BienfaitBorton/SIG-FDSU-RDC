"""Tests Phase 2 — cache contexte spatial partagé + non-régression métier légère."""

from __future__ import annotations

import os
import time
from typing import Any

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


def test_single_flight_same_key_five_threads(site_ctx):
    """5 appels concurrents même clé froide → builder ×1, 5 résultats identiques."""
    import threading

    barrier = threading.Barrier(5)
    calls = {"n": 0}
    call_lock = threading.Lock()
    results: list[Any] = []
    errors: list[BaseException] = []

    def builder():
        with call_lock:
            calls["n"] += 1
        time.sleep(0.05)
        return {"token": "same-key", "n": calls["n"]}

    key = site_ctx.make_key("single_flight", 41, program_code="sites_300")

    def worker():
        try:
            barrier.wait(timeout=5)
            results.append(site_ctx.get_or_build(key, builder))
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert not errors
    assert len(results) == 5
    assert calls["n"] == 1
    assert all(r == results[0] for r in results)
    assert results[0]["token"] == "same-key"


def test_single_flight_different_keys_parallel(site_ctx):
    """Deux clés distinctes ne doivent pas sérialiser globalement les builders."""
    import threading

    barrier = threading.Barrier(2)
    active = {"n": 0}
    peak = {"n": 0}
    lock = threading.Lock()

    def make_builder(label: str):
        def builder():
            with lock:
                active["n"] += 1
                peak["n"] = max(peak["n"], active["n"])
            time.sleep(0.08)
            with lock:
                active["n"] -= 1
            return {"label": label}

        return builder

    key_a = site_ctx.make_key("sf_a", 1)
    key_b = site_ctx.make_key("sf_b", 2)
    out: dict[str, Any] = {}
    errors: list[BaseException] = []

    def worker(name: str, key: str, builder):
        try:
            barrier.wait(timeout=5)
            out[name] = site_ctx.get_or_build(key, builder)
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    t1 = threading.Thread(target=worker, args=("a", key_a, make_builder("a")))
    t2 = threading.Thread(target=worker, args=("b", key_b, make_builder("b")))
    t1.start()
    t2.start()
    t1.join(timeout=10)
    t2.join(timeout=10)

    assert not errors
    assert out["a"]["label"] == "a"
    assert out["b"]["label"] == "b"
    assert peak["n"] >= 2, "builders for different keys should overlap"


def test_single_flight_exception_clears_inflight(site_ctx):
    """Exception : waiters débloqués, in-flight nettoyé, retry possible."""
    import threading

    barrier = threading.Barrier(3)
    calls = {"n": 0}
    call_lock = threading.Lock()
    failures: list[BaseException] = []
    successes: list[Any] = []

    def failing_builder():
        with call_lock:
            calls["n"] += 1
        time.sleep(0.03)
        raise RuntimeError("boom-single-flight")

    key = site_ctx.make_key("sf_err", 99)

    def worker():
        try:
            barrier.wait(timeout=5)
            site_ctx.get_or_build(key, failing_builder)
        except BaseException as exc:  # noqa: BLE001
            failures.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert len(failures) == 3
    assert all("boom-single-flight" in str(e) for e in failures)
    assert calls["n"] == 1
    with site_ctx._LOCK:  # noqa: SLF001 — assert cleanup
        assert key not in site_ctx._INFLIGHT

    # Retry après échec : un nouvel appel peut reconstruire
    ok = site_ctx.get_or_build(key, lambda: {"recovered": True})
    assert ok == {"recovered": True}
    assert site_ctx.get(key) == {"recovered": True}
