"""Tests — /explain réutilise get_asset_needs (pas de rematch direct)."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor

import pytest

os.environ.setdefault("DATA_MODE", os.environ.get("DATA_MODE", "json"))


def _match(need_id: str, *, distance_m: float = 1200.0) -> dict:
    return {
        "need_id": need_id,
        "relation_type": "SERVES_LOCALITY",
        "population_impacted": 1000,
        "distance_m": distance_m,
        "service_radius_m": 15000,
        "priority_level": "High",
        "category": "B",
        "calculation_method": "haversine_dwithin_equiv",
        "confidence_level": "high",
        "source_asset": "programs.fdsu_sites",
        "source_need": "nci",
        "asset_business_id": "S30",
        "ndci_before": 0.4,
        "properties": {
            "locality_name": f"Loc-{need_id}",
            "site_name": "Site 30",
            "population_status": "calcule",
        },
    }


@pytest.fixture()
def sms(monkeypatch):
    from api.services import spatial_matching_service as mod
    from api.services import site_spatial_context_cache as scc

    scc.clear()
    calls = {"get_asset_needs": 0, "match_asset_to_needs": 0}
    payload = {
        "_meta": {"engine": "test", "source": "stub"},
        "asset_id": 30,
        "asset_type": "fdsu_site",
        "match_count": 2,
        "matches": [_match("NCI-A", distance_m=1200.0), _match("NCI-B", distance_m=3000.0)],
        "impact": {
            "population_impacted": 2000,
            "localities_impacted": 2,
            "population_status": "calcule",
        },
        "asset": {"site_id": 30, "site_name": "Site 30"},
    }

    real_get = mod.get_asset_needs
    real_match = mod.match_asset_to_needs

    def tracking_get(asset_id, **filters):
        calls["get_asset_needs"] += 1
        # Délègue au cache réel si on veut tester single-flight ; ici stub contrôlé
        # mais on passe par get_asset_needs du module (patché après wrapping).
        return dict(payload)

    def tracking_match(*args, **kwargs):
        calls["match_asset_to_needs"] += 1
        return real_match(*args, **kwargs)

    monkeypatch.setattr(mod, "get_asset_needs", tracking_get)
    monkeypatch.setattr(mod, "match_asset_to_needs", tracking_match)
    return mod, calls, payload


def test_explain_asset_id_uses_get_asset_needs_not_direct_rematch(sms):
    mod, calls, payload = sms
    explained = mod.explain_match(asset_id=30)

    assert calls["get_asset_needs"] == 1
    assert calls["match_asset_to_needs"] == 0
    assert explained["distance_m"] == 1200.0
    assert explained["match"]["need_id"] == "NCI-A"
    assert explained["impact"] == payload["impact"]
    assert "rayon" in explained["summary"].lower() or "service" in explained["summary"].lower()


def test_explain_forwards_program_code_to_get_asset_needs(sms):
    mod, calls, _payload = sms
    captured = {}

    def tracking_get(asset_id, **filters):
        calls["get_asset_needs"] += 1
        captured["filters"] = dict(filters)
        return {
            "_meta": {"engine": "test"},
            "matches": [_match("NCI-A")],
            "impact": {"population_impacted": 1000},
        }

    mod.get_asset_needs = tracking_get
    explained = mod.explain_match(asset_id=30, program_code="sites_40")
    assert calls["get_asset_needs"] == 1
    assert calls["match_asset_to_needs"] == 0
    assert captured["filters"].get("program_code") == "sites_40"
    assert captured["filters"].get("asset_type") == "fdsu_site"
    assert explained["match"]["need_id"] == "NCI-A"


def test_explain_need_id_filter_preserved(sms):
    mod, calls, _payload = sms
    explained = mod.explain_match(asset_id=30, need_id="NCI-B")

    assert calls["get_asset_needs"] == 1
    assert calls["match_asset_to_needs"] == 0
    assert explained["match"]["need_id"] == "NCI-B"
    assert explained["distance_m"] == 3000.0


def test_explain_match_dict_path_unchanged(sms):
    mod, calls, _payload = sms
    row = _match("DIRECT", distance_m=500.0)
    explained = mod.explain_match(row)

    assert calls["get_asset_needs"] == 0
    assert calls["match_asset_to_needs"] == 0
    assert explained["distance_m"] == 500.0
    assert explained["match"]["need_id"] == "DIRECT"
    assert explained["confidence_level"] == "high"


def test_concurrent_needs_and_explain_share_get_asset_needs_path(monkeypatch):
    """Simule /needs + /explain : explain ne passe jamais par match_asset_to_needs direct."""
    from api.services import spatial_matching_service as mod
    from api.services import site_spatial_context_cache as scc

    scc.clear()
    builds = {"n": 0}
    rematch_direct = {"n": 0}

    stub = {
        "_meta": {"engine": "test"},
        "asset_id": 30,
        "matches": [_match("NCI-A")],
        "impact": {"population_impacted": 1000, "localities_impacted": 1},
        "match_count": 1,
    }

    def slow_build(asset_id, **filters):
        builds["n"] += 1
        return dict(stub)

    real_match = mod.match_asset_to_needs

    def boom_match(*args, **kwargs):
        rematch_direct["n"] += 1
        raise AssertionError("match_asset_to_needs ne doit pas être appelé directement par explain")

    # get_asset_needs réel avec builder stubbé via _get_asset_needs_uncached
    monkeypatch.setattr(mod, "_get_asset_needs_uncached", slow_build)
    monkeypatch.setattr(mod, "match_asset_to_needs", boom_match)

    def call_needs():
        return mod.get_asset_needs(30, asset_type="fdsu_site")

    def call_explain():
        return mod.explain_match(asset_id=30)

    with ThreadPoolExecutor(max_workers=2) as pool:
        f1 = pool.submit(call_needs)
        f2 = pool.submit(call_explain)
        needs_payload = f1.result(timeout=5)
        explained = f2.result(timeout=5)

    assert rematch_direct["n"] == 0
    assert builds["n"] == 1  # single-flight : un seul build
    assert needs_payload["matches"][0]["need_id"] == "NCI-A"
    assert explained["match"]["need_id"] == "NCI-A"
    assert explained["distance_m"] == 1200.0
