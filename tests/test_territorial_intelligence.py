"""Tests Territorial Intelligence Explorer v1."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app
from api.services import territorial_intelligence_service as tis

CLIENT = TestClient(app)


def test_list_territories_includes_dungu():
    payload = tis.list_territories(q="Dungu", limit=20)
    assert payload["_meta"]["count"] >= 1
    dungu = payload["territories"][0]
    assert dungu["territory_id"] == "TERRITOIRE-05-002"
    assert dungu["territory_name"] == "DUNGU"
    assert dungu["fdsu_zone"] == "ND"
    assert dungu["is_demo_focus"] is True


def test_dungu_profile_no_invented_values():
    profile = tis.build_territorial_profile("TERRITOIRE-05-002")
    assert profile is not None
    p = profile["profile"]
    assert p["territory_name"] == "DUNGU"
    assert p["population"]["status"] in {
        "partial",
        "confirmed",
        "operational",
        "unavailable",
        "not_sourced",
        "estimated",
        "integration_pending",
    }
    # Superficie PostGIS branchée (Data First) — valeur réelle, pas inventée
    assert p["area_km2"]["status"] in {"operational", "partial", "confirmed"}
    assert p["area_km2"]["value"] is not None and float(p["area_km2"]["value"]) > 0
    assert p["localities_count"]["value"] is not None and int(p["localities_count"]["value"]) > 0
    assert p["groupements_count"]["value"] is not None and int(p["groupements_count"]["value"]) > 0
    assert profile["sections"]["programs"]["sites_20476"]["value"] >= 1
    health = profile["sections"]["public_services"]["etablissements_sante"]
    assert health["value"] is not None and int(health["value"]) >= 0
    assert health["status"] in {"operational", "partial", "confirmed"}


def test_api_territories_profile_map_recs_explain():
    listed = CLIENT.get("/api/territorial-intelligence/territories?q=Dungu")
    assert listed.status_code == 200
    tid = listed.json()["territories"][0]["territory_id"]

    profile = CLIENT.get(f"/api/territorial-intelligence/territories/{tid}")
    assert profile.status_code == 200
    body = profile.json()
    assert body["profile"]["territory_id"] == tid
    assert "synthesis" in body["sections"]
    assert "priority" in body["sections"]

    mapped = CLIENT.get(f"/api/territorial-intelligence/territories/{tid}/map")
    assert mapped.status_code == 200
    assert mapped.json()["geojson"]["type"] == "FeatureCollection"

    indicators = CLIENT.get(f"/api/territorial-intelligence/territories/{tid}/indicators")
    assert indicators.status_code == 200
    assert "data_gaps" in indicators.json()

    recs = CLIENT.get(f"/api/territorial-intelligence/territories/{tid}/recommendations")
    assert recs.status_code == 200
    recommendations = recs.json()["recommendations"]
    assert len(recommendations) >= 1
    for rec in recommendations:
        assert rec.get("why")
        assert rec.get("confidence_level")

    explain = CLIENT.get(f"/api/territorial-intelligence/territories/{tid}/explain")
    assert explain.status_code == 200
    assert explain.json()["doctrine"]["id"] == "DOCTRINE_SITES_FDSU"
    assert explain.json()["assumptions"]


def test_generic_not_hardcoded_only_for_dungu():
    # Another territory must resolve without Dungu-specific branching
    listed = CLIENT.get("/api/territorial-intelligence/territories?limit=5")
    assert listed.status_code == 200
    others = [t for t in listed.json()["territories"] if t["territory_name"] != "DUNGU"]
    if not others:
        return
    other = others[0]
    profile = CLIENT.get(f"/api/territorial-intelligence/territories/{other['territory_id']}")
    assert profile.status_code == 200
    assert profile.json()["profile"]["territory_id"] == other["territory_id"]
    assert profile.json()["profile"]["is_demo_focus"] is False


def test_missing_data_explicitly_flagged():
    profile = tis.build_territorial_profile("Dungu")
    economy = profile["sections"]["economy"]
    assert economy["agriculture"]["status"] in {"not_sourced", "integration_pending"}
    assert economy["agriculture"]["value"] is None


def test_composed_profile_blocks_independent():
    from api.services import territorial_profile_service as tps

    composed = tps.build_composed_profile("TERRITOIRE-05-002")
    assert composed is not None
    assert composed["administrative"]["groupements"]["value"] >= 1
    assert composed["administrative"]["localites"]["value"] >= 1
    assert composed["health"]["total"]["value"] >= 0
    assert composed["geography"]["area_km2"]["value"] is not None
    assert composed["telecom"]["infrastructures"]["value"] is not None
    assert composed["transport"]["routes"]["value"] is not None
    assert "education" in composed["section_status"]
