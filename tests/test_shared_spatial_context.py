"""Tests SharedSpatialContext + progressive decision case."""

from __future__ import annotations

import os
import time
from typing import Any

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


def test_shared_single_flight_same_key_five_threads(spatial_ctx):
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
        return {"token": "shared-same-key", "n": calls["n"]}

    key = spatial_ctx.make_geo_key("sf_unit", -5.8, 12.4, radius_m=25000)

    def worker():
        try:
            barrier.wait(timeout=5)
            results.append(spatial_ctx.get_or_build(key, builder))
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


def test_shared_single_flight_different_keys_parallel(spatial_ctx):
    """Deux clés distinctes : builders parallèles, pas de sérialisation globale."""
    import threading

    barrier = threading.Barrier(2)
    active = {"n": 0}
    peak = {"n": 0}
    lock = threading.Lock()
    out: dict[str, Any] = {}
    errors: list[BaseException] = []

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

    key_a = spatial_ctx.make_geo_key("sf_a", -1.0, 1.0, radius_m=1000)
    key_b = spatial_ctx.make_geo_key("sf_b", -2.0, 2.0, radius_m=1000)

    def worker(name: str, key: str, builder):
        try:
            barrier.wait(timeout=5)
            out[name] = spatial_ctx.get_or_build(key, builder)
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
    assert peak["n"] >= 2


def test_shared_single_flight_exception_clears_inflight(spatial_ctx):
    """Exception : waiters débloqués, in-flight nettoyé, retry possible."""
    import threading

    barrier = threading.Barrier(3)
    calls = {"n": 0}
    call_lock = threading.Lock()
    failures: list[BaseException] = []

    def failing_builder():
        with call_lock:
            calls["n"] += 1
        time.sleep(0.03)
        raise RuntimeError("boom-shared-single-flight")

    key = spatial_ctx.make_geo_key("sf_err", 0.1, 0.2, radius_m=500)

    def worker():
        try:
            barrier.wait(timeout=5)
            spatial_ctx.get_or_build(key, failing_builder)
        except BaseException as exc:  # noqa: BLE001
            failures.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert len(failures) == 3
    assert all("boom-shared-single-flight" in str(e) for e in failures)
    assert calls["n"] == 1
    with spatial_ctx._LOCK:  # noqa: SLF001
        assert key not in spatial_ctx._INFLIGHT

    ok = spatial_ctx.get_or_build(key, lambda: {"recovered": True})
    assert ok == {"recovered": True}


def test_shared_cache_hit_bypasses_inflight(spatial_ctx):
    """Hit cache : aucun Future in-flight créé."""
    key = spatial_ctx.make_geo_key("sf_hit", -3.0, 15.0, radius_m=1000)
    spatial_ctx.get_or_build(key, lambda: {"warm": True})
    with spatial_ctx._LOCK:  # noqa: SLF001
        assert key not in spatial_ctx._INFLIGHT

    calls = {"n": 0}

    def builder():
        calls["n"] += 1
        return {"warm": False}

    again = spatial_ctx.get_or_build(key, builder)
    assert again == {"warm": True}
    assert calls["n"] == 0
    with spatial_ctx._LOCK:  # noqa: SLF001
        assert key not in spatial_ctx._INFLIGHT
        assert len(spatial_ctx._INFLIGHT) == 0
