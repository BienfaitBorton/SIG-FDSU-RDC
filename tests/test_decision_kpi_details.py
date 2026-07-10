"""Tests Decision Detail Workspace — boutons Voir le détail."""

from __future__ import annotations

from pathlib import Path

import pytest

CATALOG = Path(__file__).resolve().parents[1] / "data" / "business" / "decision_kpi_details.json"


@pytest.fixture(scope="module")
def detail_svc():
    from api.services import decision_kpi_detail_service as svc

    return svc


REQUIRED_KPIS = [
    "sites_fdsu",
    "sites_priority",
    "sites_critical",
    "sites_high",
    "referentials_active",
    "referentials_planned",
]


def test_catalog_exists_and_covers_required_kpis(detail_svc):
    assert CATALOG.exists()
    catalog = detail_svc.load_catalog()
    kpis = catalog.get("kpis") or {}
    for code in REQUIRED_KPIS:
        assert code in kpis
        assert kpis[code].get("route_slug")
        assert kpis[code].get("actions")


def test_aliases_resolve(detail_svc):
    assert detail_svc.resolve_kpi_code("sites-total") == "sites_fdsu"
    assert detail_svc.resolve_kpi_code("sites-prioritaires") == "sites_priority"
    assert detail_svc.resolve_kpi_code("sites-critiques") == "sites_critical"
    assert detail_svc.resolve_kpi_code("referentiels-actifs") == "referentials_active"
    assert detail_svc.resolve_kpi_code("referentiels-planifies") == "referentials_planned"


@pytest.mark.parametrize("kpi_code", REQUIRED_KPIS)
def test_build_detail_for_required_kpis(detail_svc, kpi_code):
    payload = detail_svc.build_detail(kpi_code, limit=20, offset=0)
    assert payload is not None
    assert payload["header"]["kpi_code"] == kpi_code
    assert payload["header"]["title"]
    assert payload["header"]["definition"]
    assert payload["header"]["source"]
    assert "confidence" in payload["header"]
    assert "items" in payload
    assert "explain" in payload
    assert payload["explain"].get("why")
    assert payload["_meta"]["back_route"] == "#decision-view"


def test_sites_priority_filters_critical_and_high(detail_svc):
    payload = detail_svc.build_detail("sites_priority", limit=50)
    rows = payload["items"]["rows"]
    for row in rows:
        assert row.get("priority_level") in {"critical", "high"}


def test_sites_critical_only_critical(detail_svc):
    payload = detail_svc.build_detail("sites_critical", limit=50)
    for row in payload["items"]["rows"]:
        assert row.get("priority_level") == "critical"


def test_map_charts_items_explain_export(detail_svc):
    geo = detail_svc.build_map("sites_fdsu")
    assert geo["type"] == "FeatureCollection"

    charts = detail_svc.build_charts("sites_priority")
    assert "charts" in charts

    items = detail_svc.build_items("sites_high", limit=10)
    assert items["total"] >= 0
    assert len(items["rows"]) <= 10

    explained = detail_svc.build_explain("sites_critical")
    assert explained.get("why")
    assert "doctrine" in explained

    exported = detail_svc.build_export("referentials_active", format="csv")
    assert exported["format"] == "csv"
    assert "content" in exported


def test_api_routes_registered():
    from api.routes import decision_engine

    paths = {getattr(r, "path", None) for r in decision_engine.router.routes}
    assert "/details/{kpi_code}" in paths
    assert "/details/{kpi_code}/map" in paths
    assert "/details/{kpi_code}/charts" in paths
    assert "/details/{kpi_code}/items" in paths
    assert "/details/{kpi_code}/explain" in paths
    assert "/details/{kpi_code}/export" in paths


def test_frontend_assets_exist():
    root = Path(__file__).resolve().parents[1]
    assert (root / "dashboard/modules/decision-center/decision-detail.js").exists()
    assert (root / "dashboard/modules/decision-center/decision-detail.css").exists()
    html = (root / "dashboard/index.html").read_text(encoding="utf-8")
    assert 'data-module="decision_detail"' in html
    assert "decision-detail.js" in html
    assert 'data-kpi-detail="sites_fdsu"' in html
    assert "Voir le détail" in html
    js = (root / "dashboard/modules/decision-center/decision-center.js").read_text(encoding="utf-8")
    assert "openDecisionDetail" in js
    app_js = (root / "dashboard/app.js").read_text(encoding="utf-8")
    assert "decision_detail" in app_js
    assert "decision-detail" in app_js


def test_kpi_cards_hide_sql_in_executive_html():
    html = (Path(__file__).resolve().parents[1] / "dashboard/index.html").read_text(encoding="utf-8")
    section_start = html.index('id="decision-center-kpi-grid"')
    section_end = html.index('id="decision-center-kpi-secondary"')
    primary = html[section_start:section_end]
    assert "COUNT(*)" not in primary
    assert "priority_level = critical" not in primary
    assert "kpi-meta-exec" in primary
