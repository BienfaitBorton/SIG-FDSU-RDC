"""Tests module opérationnel CCN v1 — doctrine versionnée, API, données DEMO."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app
from api.services import ccn_operational_service, decision_engine_service

CLIENT = TestClient(app)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCTRINE_PATH = PROJECT_ROOT / "data" / "business" / "doctrines" / "ccn_doctrine_v1.json"
TYPES_PATH = PROJECT_ROOT / "data" / "business" / "ccn_types.json"
DEMO_PATH = PROJECT_ROOT / "data" / "programs" / "ccn" / "demo_ccn.json"


def test_doctrine_files_versioned_and_official_weights():
    assert DOCTRINE_PATH.exists()
    assert TYPES_PATH.exists()
    doctrine = json.loads(DOCTRINE_PATH.read_text(encoding="utf-8"))
    criteria = {c["id"]: c for c in doctrine["selection_criteria"]}
    assert criteria["CRIT_CONN_EXTENSION"]["weight_percent"] == 25
    assert criteria["CRIT_INFRA_PRESENCE"]["weight_percent"] == 15
    assert criteria["CRIT_PROJECT_PRESENCE"]["weight_percent"] == 15
    assert criteria["CRIT_NEEDS_TYPOLOGY"]["weight_percent"] == 15
    assert criteria["CRIT_SERVICE_UNIVERSAL_FIRST"]["weight_percent"] == 20
    assert criteria["CRIT_LOCAL_INTEGRATOR"]["weight_percent"] == 10
    assert abs(sum(c["weight"] for c in doctrine["selection_criteria"]) - 1.0) < 1e-9
    assert len(doctrine["measurement_indicators"]) >= 9
    assert len(doctrine["opposability_rules"]) >= 4
    assert doctrine["_meta"]["hardcoded_forbidden"] is True


def test_official_ccn_types_catalog():
    types = json.loads(TYPES_PATH.read_text(encoding="utf-8"))
    codes = {t["code"] for t in types["types"]}
    assert codes == {"A", "B", "C", "D", "Z"}


def test_demo_data_marked_and_sized():
    payload = json.loads(DEMO_PATH.read_text(encoding="utf-8"))
    assert payload["_meta"]["data_class"] == "demonstration"
    assert 15 <= len(payload["ccn"]) <= 30
    provinces = {item["province"] for item in payload["ccn"]}
    assert len(provinces) >= 3
    assert all(item.get("site_fdsu_code") for item in payload["ccn"][:5])


def test_priority_score_uses_doctrine_not_hardcode():
    doctrine = ccn_operational_service.load_doctrine()
    record = {
        "criteria_scores": {
            "CRIT_CONN_EXTENSION": 100,
            "CRIT_INFRA_PRESENCE": 0,
            "CRIT_PROJECT_PRESENCE": 0,
            "CRIT_NEEDS_TYPOLOGY": 0,
            "CRIT_SERVICE_UNIVERSAL_FIRST": 0,
            "CRIT_LOCAL_INTEGRATOR": 0,
        },
        "site_fdsu_code": "FDSU_OT_10_001_10100",
    }
    scored = ccn_operational_service.compute_priority_score(record, doctrine)
    # 100 * 0.25 = 25
    assert scored["priority_score"] == 25.0
    assert scored["doctrine_id"] == "DOCTRINE_CCN_FDSU"
    assert any(r["rule_id"] == "RULE_CONNECTIVITY_SITES_FIRST" and r["applied"] for r in scored["opposability"])


def test_api_list_statistics_map_doctrine_detail():
    listed = CLIENT.get("/api/ccn")
    assert listed.status_code == 200
    body = listed.json()
    assert body["_meta"]["data_class"] == "demonstration"
    assert body["_meta"]["count"] >= 15
    assert body["ccn"][0]["asset_type"] == "CCN"
    assert body["ccn"][0]["demo"] is True

    stats = CLIENT.get("/api/ccn/statistics")
    assert stats.status_code == 200
    kpis = stats.json()["kpis"]
    assert kpis["total"] == body["_meta"]["total"]
    assert "population_desservie" in kpis
    assert "sites_fdsu_associes" in kpis

    mapped = CLIENT.get("/api/ccn/map")
    assert mapped.status_code == 200
    features = mapped.json()["geojson"]["features"]
    kinds = {f["properties"]["kind"] for f in features}
    assert "ccn" in kinds
    assert "site_fdsu" in kinds
    assert "site_ccn_link" in kinds

    doctrine = CLIENT.get("/api/ccn/doctrine")
    assert doctrine.status_code == 200
    assert doctrine.json()["_meta"]["hardcoded_forbidden"] is True
    assert len(doctrine.json()["doctrine"]["selection_criteria"]) == 6

    first_id = body["ccn"][0]["id"]
    detail = CLIENT.get(f"/api/ccn/{first_id}")
    assert detail.status_code == 200
    ccn = detail.json()["ccn"]
    assert ccn["asset_type"] == "CCN"
    assert "sections" in ccn
    for key in (
        "identification",
        "localisation",
        "connectivite",
        "equipements",
        "services",
        "exploitation",
        "maintenance",
        "population",
        "indicateurs",
        "impact",
        "historique",
    ):
        assert key in ccn["sections"]


def test_site_fdsu_not_confused_with_ccn_in_payload():
    listed = CLIENT.get("/api/ccn?limit=5").json()["ccn"]
    for item in listed:
        assert item["asset_type"] == "CCN"
        assert not str(item["business_id"]).startswith("FDSU_") or "CCN" in item["business_id"]
        if item.get("site_fdsu_code"):
            assert "CCN" not in item["site_fdsu_code"]


def test_decision_engine_ccn_extension_hooks():
    hooks = decision_engine_service.ccn_doctrine_extension_points()
    assert hooks["_meta"]["hardcoded_weights_forbidden"] is True
    assert "load_doctrine" in hooks["hooks"]
    assert hooks["criteria_count"] == 6
    assert hooks["opposability_rules_count"] >= 4


def test_knowledge_hub_business_doctrine_domain():
    response = CLIENT.get("/api/knowledge/domain/business_doctrine")
    assert response.status_code == 200
    body = response.json()
    assert body["domain"]["id"] == "business_doctrine"
    assert any(d["id"] == "DOCTRINE_CCN_FDSU" for d in body["doctrine_catalog"])
    assert any(d["status"] == "planned" for d in body["doctrine_catalog"])
