"""Tests — réutilisation du premier match localités dans Needs (pas de double scan)."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("DATA_MODE", os.environ.get("DATA_MODE", "json"))


def _loc(need_id: str, *, priority: str = "medium", infra: str | None = "école primaire") -> dict:
    return {
        "asset_type": "fdsu_site",
        "asset_id": 41,
        "need_id": need_id,
        "relation_type": "SERVES_LOCALITY",
        "distance_m": 1000.0,
        "priority_level": priority,
        "infrastructure_type": infra,
        "territoire": "TestTerr",
        "province": "TestProv",
        "population_impacted": 100,
        "properties": {"locality_name": need_id},
        "calculation_method": "haversine_dwithin_equiv",
    }


@pytest.fixture()
def sms_mod(monkeypatch):
    from api.services import spatial_matching_service as sms

    calls = {"uncovered": 0, "public_kwargs": []}
    locality_payload = [
        _loc("NCI-1", priority="high", infra="école primaire"),
        _loc("NCI-2", priority="medium", infra="marché"),
    ]

    def fake_uncovered(site, localities=None, *, max_distance_m=None, max_matches=None):
        calls["uncovered"] += 1
        return [dict(row) for row in locality_payload]

    real_public = sms.match_asset_to_public_infrastructure

    def tracking_public(asset, locality_matches=None):
        calls["public_kwargs"].append(
            {
                "has_locality_matches": locality_matches is not None,
                "rels": [m.get("relation_type") for m in (locality_matches or [])],
                "need_ids": [m.get("need_id") for m in (locality_matches or [])],
            }
        )
        return real_public(asset, locality_matches=locality_matches)

    monkeypatch.setattr(sms, "match_site_to_uncovered_localities", fake_uncovered)
    monkeypatch.setattr(sms, "match_asset_to_public_infrastructure", tracking_public)
    monkeypatch.setattr(
        sms,
        "list_fdsu_sites",
        lambda **_k: [{
            "id": 41,
            "site_code": "Y1",
            "site_name": "Yoseki",
            "latitude": -5.0,
            "longitude": 12.0,
            "territoire": "TestTerr",
            "province": "TestProv",
            "program_code": "sites_300",
        }],
    )
    for name in (
        "match_site_to_roads",
        "match_site_to_health_facilities",
        "match_site_to_schools",
        "match_site_to_ceni_signal",
        "match_site_to_telecom",
        "match_site_to_neighbor_fdsu",
        "match_site_to_near_ccn",
    ):
        monkeypatch.setattr(sms, name, lambda *a, **k: [])

    yield sms, calls


def test_needs_scans_uncovered_localities_once(sms_mod):
    sms, calls = sms_mod
    out = sms.match_asset_to_needs("fdsu_site", 41)
    assert calls["uncovered"] == 1
    assert out["match_count"] >= 2


def test_public_infra_receives_precomputed_locality_matches(sms_mod):
    sms, calls = sms_mod
    sms.match_asset_to_needs("fdsu_site", 41)
    assert len(calls["public_kwargs"]) == 1
    assert calls["public_kwargs"][0]["has_locality_matches"] is True
    assert "CANDIDATE_FOR_MISSION" not in calls["public_kwargs"][0]["rels"]
    assert all(not str(nid).startswith("MISSION::") for nid in calls["public_kwargs"][0]["need_ids"])


def test_derived_infra_relations_identical(sms_mod):
    sms, _calls = sms_mod
    out = sms.match_asset_to_needs("fdsu_site", 41)
    infra = [m for m in out["matches"] if str(m.get("calculation_method") or "") == "derived_from_nci_infra"]
    rels = sorted(m["relation_type"] for m in infra)
    assert rels == ["NEAR_MARKET", "NEAR_SCHOOL"]
    assert all(m["need_id"].startswith("INFRA::") for m in infra)


def test_public_infra_without_locality_matches_rescans(monkeypatch):
    from api.services import spatial_matching_service as sms

    calls = {"n": 0}

    def fake_uncovered(site, localities=None, *, max_distance_m=None, max_matches=None):
        calls["n"] += 1
        return [_loc("NCI-X", infra="école")]

    monkeypatch.setattr(sms, "match_site_to_uncovered_localities", fake_uncovered)

    out = sms.match_asset_to_public_infrastructure({"id": 1, "latitude": -5.0, "longitude": 12.0})
    assert calls["n"] == 1
    assert len(out) == 1
    assert out[0]["relation_type"] == "NEAR_SCHOOL"

    calls["n"] = 0
    out2 = sms.match_asset_to_public_infrastructure(
        {"id": 1, "latitude": -5.0, "longitude": 12.0},
        locality_matches=[_loc("NCI-Y", infra="marché")],
    )
    assert calls["n"] == 0
    assert out2[0]["relation_type"] == "NEAR_MARKET"


def test_mission_relations_not_in_transmitted_locality_matches(sms_mod):
    sms, calls = sms_mod
    out = sms.match_asset_to_needs("fdsu_site", 41)
    assert any(m.get("relation_type") == "CANDIDATE_FOR_MISSION" for m in out["matches"])
    assert calls["public_kwargs"][0]["rels"] == ["SERVES_LOCALITY", "SERVES_LOCALITY"]
