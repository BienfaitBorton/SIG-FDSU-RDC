"""Tests fondations Capability CCN — modèle métier, relations, nomenclature préparatoire."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app
from api.models.business_entities import (
    CCN_ATTRIBUTE_DOMAINS,
    CCN_CODE_SCHEME,
    CCN_DECISION_EXTENSIONS,
    CCN_RELATIONSHIPS,
    AssetType,
    CcnHostType,
    RelationshipType,
    assert_site_ccn_distinct,
    build_proposed_ccn_code,
    is_ccn,
    is_site_fdsu,
    validate_proposed_ccn_code,
)
from api.services import ccn_capability_service

CLIENT = TestClient(app)


def test_site_and_ccn_remain_distinct():
    assert is_site_fdsu(AssetType.SITE)
    assert is_ccn(AssetType.CCN)
    assert assert_site_ccn_distinct("SITE", "CCN") is True
    assert assert_site_ccn_distinct("SITE", "SITE") is False


def test_ccn_attribute_domains_and_hosts():
    required = {
        "identification",
        "implantation",
        "connectivite",
        "services",
        "indicateurs",
        "partenaires",
    }
    assert required.issubset(set(CCN_ATTRIBUTE_DOMAINS))
    assert CcnHostType.SCHOOL in CcnHostType
    assert CcnHostType.HEALTH_CENTER in CcnHostType


def test_ccn_business_relationships():
    codes = {item.code for item in CCN_RELATIONSHIPS}
    assert "site_feeds_ccn" in codes
    assert "ccn_hosted_in_building" in codes
    assert "ccn_serves_population" in codes
    assert "ccn_offers_services" in codes
    assert "ccn_tracked_by_kpis" in codes
    assert "program_funds_ccn" in codes
    assert "mission_audits_ccn" in codes
    assert ccn_capability_service.required_connectivity_link() == RelationshipType.FEEDS_CONNECTIVITY.value


def test_proposed_ccn_nomenclature_ready_but_not_official():
    assert CCN_CODE_SCHEME.is_official is False
    assert ccn_capability_service.CCN_NOMENCLATURE_OFFICIALLY_ACTIVATED is False
    code = build_proposed_ccn_code(zone="ND", province_code=18, territoire_code=3, numero=1)
    assert code == "FDSU_CCN_ND_18_003_00001"
    validation = validate_proposed_ccn_code(code)
    assert validation["is_valid_format"] is True
    assert validation["is_official"] is False
    assert any("non officielle" in w.lower() for w in validation["warnings"])


def test_reject_site_code_as_ccn():
    validation = validate_proposed_ccn_code("FDSU_ND_18_003_10100")
    assert validation["is_valid_format"] is False
    assert any("Site FDSU" in err for err in validation["errors"])


def test_decision_extensions_prepared():
    codes = {item.code for item in CCN_DECISION_EXTENSIONS}
    assert "ccn.prioritization" in codes
    assert "ccn.implantation_simulation" in codes
    assert "ccn.performance_monitoring" in codes
    assert all(item.ui_ready is False for item in CCN_DECISION_EXTENSIONS)


def test_capability_api_manifest():
    response = CLIENT.get("/api/ccn/capability")
    assert response.status_code == 200
    body = response.json()
    assert body["_meta"]["crud_enabled"] is False
    assert body["_meta"]["official_nomenclature_activated"] is False
    assert body["asset_type"] == "CCN"
    assert body["distinction"]["must_remain_distinct"] is True


def test_capability_api_prepare_and_extensions():
    prepared = CLIENT.post(
        "/api/ccn/nomenclature/prepare",
        json={"zone": "ND", "province_code": "18", "territoire_code": "003", "numero": "1"},
    )
    assert prepared.status_code == 200
    assert prepared.json()["business_id"] == "FDSU_CCN_ND_18_003_00001"
    assert prepared.json()["is_official"] is False

    extensions = CLIENT.get("/api/ccn/decision-extensions")
    assert extensions.status_code == 200
    assert len(extensions.json()["extensions"]) == 3
