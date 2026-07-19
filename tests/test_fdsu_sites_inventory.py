"""Tests inventaire Sites FDSU (#sites) + non-régression libellés 20 476."""

from __future__ import annotations

from pathlib import Path

import pytest

from api.services import fdsu_site_priority_service, fdsu_sites_inventory_service
from api.services.site_display_name import is_technical_site_identifier

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def inventory_page():
    return fdsu_sites_inventory_service.list_inventory(program_code="sites_20476", limit=20, offset=0)


def test_inventory_summary_programs_and_portfolio():
    summary = fdsu_sites_inventory_service.inventory_summary()
    counts = summary["counts"]
    assert counts["sites_40"] == 40
    assert counts["sites_300"] == 300
    assert counts["sites_20476"] == 20476
    assert counts["portfolio_340"] == 340
    assert counts["primary"] == 20476
    assert summary["_meta"]["primary_counter"]["key"] == "sites_20476"
    # Pas de programme « Sites 340 »
    labels = [p.get("label") for p in summary["programs"]]
    assert "Sites 40" in labels
    assert "Sites 300" in labels
    assert any("20 476" in str(l) for l in labels)
    assert not any("340" in str(l) for l in labels)


def test_inventory_pagination(inventory_page):
    assert inventory_page["total"] == 20476
    assert inventory_page["count"] == 20
    assert inventory_page["limit"] == 20
    assert len(inventory_page["sites"]) == 20


def test_inventory_search_by_technical_id():
    payload = fdsu_sites_inventory_service.list_inventory(
        program_code="sites_20476",
        q="Part2_23453_NewSite_1_580_50002",
        limit=10,
    )
    assert payload["total"] >= 1
    site = payload["sites"][0]
    assert site["technical_id"] or site["site_name"]
    assert "Part2_23453_NewSite_1_580_50002" in str(site.get("site_name") or site.get("technical_id"))


def test_inventory_filter_program_40():
    payload = fdsu_sites_inventory_service.list_inventory(program_code="sites_40", limit=100)
    assert payload["total"] == 40
    assert all(s["program_code"] == "sites_40" for s in payload["sites"])


def test_inventory_20476_display_name_not_technical_when_infra_available(inventory_page):
    with_infra = [s for s in inventory_page["sites"] if s.get("infra_name")]
    if not with_infra:
        pytest.skip("Aucun infra_name NCI sur la première page")
    site = with_infra[0]
    assert site["display_name"] == site["infra_name"] or site.get("village_name")
    assert is_technical_site_identifier(site["site_name"])
    assert site["technical_id"] == site["site_name"]
    assert not is_technical_site_identifier(site["display_name"])


def test_decision_top_priorities_use_display_name():
    top = fdsu_site_priority_service.top_priorities("sites_20476", limit=5)
    assert top["sites"]
    site = top["sites"][0]
    assert site.get("display_name")
    assert site.get("technical_id") or is_technical_site_identifier(site.get("site_name"))
    # Libellé principal ≠ identifiant technique lorsque enrichissement possible
    if site.get("infra_name"):
        assert site["display_name"] == site["infra_name"]
        assert site["display_name"] != site["site_name"]


def test_sites_40_300_no_regression_names():
    p40 = fdsu_sites_inventory_service.list_inventory(program_code="sites_40", limit=5)
    p300 = fdsu_sites_inventory_service.list_inventory(program_code="sites_300", limit=5)
    assert p40["sites"][0]["display_name"]
    assert not is_technical_site_identifier(p40["sites"][0]["display_name"])
    assert p300["sites"][0]["display_name"]
    assert "NewSite" not in p300["sites"][0]["display_name"]


def test_sites_module_html_no_placeholder():
    html = (PROJECT_ROOT / "dashboard" / "index.html").read_text(encoding="utf-8")
    assert "Module Sites FDSU à construire en v0.7.0" not in html
    assert 'id="sites-inventory-tbody"' in html
    assert "Inventaire des Sites FDSU" in html
    app_js = (PROJECT_ROOT / "dashboard" / "app.js").read_text(encoding="utf-8")
    assert "Module Sites FDSU à construire en v0.7.0" not in app_js
    assert "SitesInventory" in app_js


def test_get_inventory_site_detail():
    detail = fdsu_sites_inventory_service.get_inventory_site(1, program_code="sites_40")
    assert detail and detail["site"]["site_id"] == 1
    assert detail["site"]["display_name"]
