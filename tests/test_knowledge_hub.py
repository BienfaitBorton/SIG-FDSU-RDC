"""Tests FDSU Knowledge Hub & National Indicators Framework."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app
from api.services import knowledge_hub_service

CLIENT = TestClient(app)
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_domains_catalog_files_exist():
    assert (PROJECT_ROOT / "data/knowledge/domains.json").exists()
    assert (PROJECT_ROOT / "data/knowledge/national_indicators.json").exists()


def test_list_knowledge_domains():
    payload = knowledge_hub_service.list_domains()
    ids = {item["id"] for item in payload["domains"]}
    assert {
        "territory",
        "connectivity",
        "public_services",
        "socio_economic",
        "fdsu_programs",
        "national_indicators",
        "decision",
        "business_doctrine",
    }.issubset(ids)
    assert payload["_meta"]["count"] >= 8


def test_get_domain_and_integrations():
    domain = knowledge_hub_service.get_domain("connectivity")
    assert domain is not None
    assert domain["domain"]["id"] == "connectivity"
    assert domain["_meta"]["computes_recommendations"] is False
    assert any(item["target"] == "telecom" for item in domain["integrations"])


def test_business_doctrine_domain_exposes_catalog():
    domain = knowledge_hub_service.get_domain("business_doctrine")
    assert domain is not None
    assert domain["domain"]["id"] == "business_doctrine"
    assert any(item["id"] == "DOCTRINE_CCN_FDSU" for item in domain["doctrine_catalog"])
    assert domain["_meta"]["active_doctrine_api"] == "/api/ccn/doctrine"


def test_indicators_structure_without_invented_values():
    payload = knowledge_hub_service.list_indicators()
    assert payload["_meta"]["values_included"] is False
    assert payload["_meta"]["count"] >= 10
    for item in payload["indicators"]:
        assert item.get("value_status") == "structure_only"
        assert item.get("id")
        assert item.get("definition")
        assert item.get("decision_usage")
        assert "value" not in item


def test_get_indicator_priority_score():
    detail = knowledge_hub_service.get_indicator("IND_FDSU_PRIORITY_SCORE")
    assert detail is not None
    assert detail["indicator"]["family"] == "priorite_fdsu"
    assert detail["_meta"]["computes_recommendations"] is False


def test_api_knowledge_endpoints():
    domains = CLIENT.get("/api/knowledge/domains")
    assert domains.status_code == 200
    assert domains.json()["_meta"]["count"] >= 8

    one = CLIENT.get("/api/knowledge/domain/territory")
    assert one.status_code == 200
    assert one.json()["domain"]["id"] == "territory"

    indicators = CLIENT.get("/api/knowledge/indicators")
    assert indicators.status_code == 200
    assert indicators.json()["_meta"]["values_included"] is False

    indicator = CLIENT.get("/api/knowledge/indicator/IND_CONN_COVERAGE_GAP")
    assert indicator.status_code == 200
    assert indicator.json()["indicator"]["id"] == "IND_CONN_COVERAGE_GAP"

    missing = CLIENT.get("/api/knowledge/domain/unknown-domain")
    assert missing.status_code == 404


def test_existing_cnct_knowledge_route_untouched():
    # Le Centre de connaissances historique reste sur /knowledge (pas /api/knowledge)
    response = CLIENT.get("/knowledge/types")
    assert response.status_code == 200


def test_hub_does_not_claim_recommendations():
    manifest = knowledge_hub_service.hub_manifest()
    assert manifest["_meta"]["computes_recommendations"] is False
    assert manifest["_meta"]["territorial_intelligence_engine"] == "v1_explorer"
