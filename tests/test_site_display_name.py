"""Tests résolution libellé métier Sites FDSU (dont 20 476)."""

from __future__ import annotations

from api.services.site_display_name import (
    enrich_site_labels,
    is_technical_site_identifier,
    resolve_site_display_name,
)


def test_technical_identifier_detection():
    assert is_technical_site_identifier("Part2_23453_NewSite_1_580_50002")
    assert is_technical_site_identifier("Part1_23453_NewSite_15_450_750004")
    assert not is_technical_site_identifier("Yengembana-Ext_KOC")
    assert not is_technical_site_identifier("Colline Popokabaka_R228")
    assert not is_technical_site_identifier("Luberizi")


def test_20476_prefers_village_name_over_technical():
    site = {
        "site_name": "Part2_23453_NewSite_1_580_50002",
        "site_code": "SITES_20476_06300",
        "village_name": "Bondo Centre",
        "program_code": "sites_20476",
    }
    resolved = resolve_site_display_name(site)
    assert resolved["display_name"] == "Bondo Centre"
    assert resolved["technical_id"] == "Part2_23453_NewSite_1_580_50002"
    assert resolved["source_field"] == "village_name"
    assert resolved["is_technical_fallback"] is False


def test_20476_fallback_without_village_uses_infra_then_technical():
    with_infra = resolve_site_display_name(
        {
            "site_name": "Part2_23453_NewSite_1_580_50002",
            "infra_name": "Luberizi",
        }
    )
    assert with_infra["display_name"] == "Luberizi"
    assert with_infra["technical_id"] == "Part2_23453_NewSite_1_580_50002"
    assert with_infra["source_field"] == "infra_name"

    technical_only = resolve_site_display_name(
        {"site_name": "Part2_23453_NewSite_1_580_50002", "site_code": "SITES_20476_00001"}
    )
    assert technical_only["display_name"] == "Part2_23453_NewSite_1_580_50002"
    assert technical_only["is_technical_fallback"] is True
    assert technical_only["technical_id"] == "Part2_23453_NewSite_1_580_50002"


def test_sites_40_and_300_keep_business_names():
    s40 = resolve_site_display_name({"name": "Yengembana-Ext_KOC", "program_code": "sites_40"})
    assert s40["display_name"] == "Yengembana-Ext_KOC"
    assert s40["is_technical_fallback"] is False

    s300 = resolve_site_display_name({"name": "Colline Popokabaka_R228", "program_code": "sites_300"})
    assert s300["display_name"] == "Colline Popokabaka_R228"


def test_enrich_preserves_technical_id_and_sets_display_name():
    enriched = enrich_site_labels(
        {
            "site_name": "Part2_23453_NewSite_15_450_750004",
            "site_code": "SITES_20476_00001",
            "program_code": "sites_20476",
        }
    )
    assert enriched["technical_id"] == "Part2_23453_NewSite_15_450_750004"
    assert enriched["site_name"] == "Part2_23453_NewSite_15_450_750004"
    # Si NCI joint, display_name = infra_name ; sinon fallback technique
    assert enriched["display_name"]
    if enriched.get("infra_name"):
        assert enriched["display_name"] == enriched["infra_name"]
        assert enriched["display_name"] != enriched["site_name"]
