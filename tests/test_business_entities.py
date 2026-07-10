"""Tests du vocabulaire métier Enterprise Business Model (EBM)."""

from __future__ import annotations

from pathlib import Path

from api.models import business_entities as be
from api.models.business_entities import (
    AssetStatus,
    AssetType,
    CCN_CODE_SCHEME,
    DataStatus,
    DecisionStatus,
    OFFICIAL_SITE_NOMENCLATURE_PATH,
    RelationshipType,
    SITE_FDSU_CODE_SCHEME,
)


def test_asset_types_include_core_entities():
    required = {
        AssetType.PROGRAM,
        AssetType.BATCH,
        AssetType.PROJECT,
        AssetType.SITE,
        AssetType.CCN,
        AssetType.PROVINCE,
        AssetType.TERRITOIRE,
        AssetType.LOCALITE,
        AssetType.VILLAGE,
        AssetType.MISSION,
        AssetType.SCORE,
        AssetType.RECOMMENDATION,
        AssetType.DECISION,
        AssetType.PARTNER,
        AssetType.DATA_SOURCE,
    }
    assert required.issubset(set(AssetType))


def test_standard_lifecycle_statuses():
    assert AssetStatus.PROPOSED.value == "proposed"
    assert AssetStatus.OPERATIONAL.value == "operational"
    assert AssetStatus.ARCHIVED.value == "archived"
    assert len(AssetStatus) == 10

    assert DataStatus.RAW.value == "raw"
    assert DataStatus.VALIDATED.value == "validated"
    assert len(DataStatus) == 6

    assert DecisionStatus.DRAFT.value == "draft"
    assert DecisionStatus.APPROVED.value == "approved"
    assert DecisionStatus.CLOSED.value == "closed"
    assert len(DecisionStatus) == 6


def test_site_and_ccn_are_distinct():
    assert be.is_site_fdsu(AssetType.SITE) is True
    assert be.is_ccn(AssetType.CCN) is True
    assert be.is_site_fdsu(AssetType.CCN) is False
    assert be.is_ccn(AssetType.SITE) is False
    assert be.assert_site_ccn_distinct(AssetType.SITE, AssetType.CCN) is True
    assert be.assert_site_ccn_distinct(AssetType.SITE, AssetType.SITE) is False


def test_official_site_scheme():
    assert SITE_FDSU_CODE_SCHEME.is_official is True
    assert SITE_FDSU_CODE_SCHEME.source == OFFICIAL_SITE_NOMENCLATURE_PATH
    assert OFFICIAL_SITE_NOMENCLATURE_PATH == "data/raw/FDSU Structure code Territoire zones.xlsx"
    assert Path(OFFICIAL_SITE_NOMENCLATURE_PATH).exists()
    assert SITE_FDSU_CODE_SCHEME.example.startswith("FDSU_")
    assert "CCN" not in SITE_FDSU_CODE_SCHEME.pattern


def test_ccn_scheme_is_preparatory_not_official():
    assert CCN_CODE_SCHEME.is_official is False
    assert CCN_CODE_SCHEME.pattern.startswith("FDSU_CCN_")
    assert "proposition" in (CCN_CODE_SCHEME.notes or "").lower() or "préparatoire" in (
        CCN_CODE_SCHEME.notes or ""
    ).lower()
    assert CCN_CODE_SCHEME.source is None


def test_relationship_types_cover_core_links():
    required = {
        RelationshipType.CONTAINS,
        RelationshipType.TARGETS,
        RelationshipType.FEEDS_CONNECTIVITY,
        RelationshipType.HOSTED_IN,
        RelationshipType.SCORED_BY,
        RelationshipType.PRODUCES,
        RelationshipType.CONCERNS,
    }
    assert required.issubset(set(RelationshipType))


def test_imports_do_not_break_master_registry():
    from api.services import fdsu_code_service, master_registry_service

    assert fdsu_code_service.OFFICIAL_NOMENCLATURE_SOURCE == OFFICIAL_SITE_NOMENCLATURE_PATH
    assert callable(master_registry_service.statistics)
