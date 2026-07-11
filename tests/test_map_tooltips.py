"""Infobulles cartographiques — factory SigMapTooltips."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_map_tooltips_module_present_and_loaded():
    tip = (ROOT / "dashboard/modules/shared/map-tooltips.js").read_text(encoding="utf-8")
    html = (ROOT / "dashboard/index.html").read_text(encoding="utf-8")
    assert "Survol = comprendre rapidement" in tip
    assert "bindHoverTooltip" in tip or "function bind(" in tip
    assert "modules/shared/map-tooltips.js" in html
    for kind in (
        "site_fdsu",
        "ccn",
        "uncovered_locality",
        "territoire",
        "province",
        "health",
        "telecom",
        "fibre",
        "backbone",
        "route",
        "spatial_match",
        "mission_candidate",
    ):
        assert kind in tip


def test_ccn_and_ti_bind_shared_tooltips():
    ccn = (ROOT / "dashboard/modules/ccn/ccn.js").read_text(encoding="utf-8")
    ti = (ROOT / "dashboard/modules/territorial-intelligence/territorial-intelligence.js").read_text(
        encoding="utf-8"
    )
    detail = (ROOT / "dashboard/modules/decision-center/decision-detail.js").read_text(encoding="utf-8")
    assert "SigMapTooltips" in ccn
    assert "SigMapTooltips" in ti
    assert "SigMapTooltips" in detail
    assert "uncovered_locality" in ti


def test_cartography_uses_bind_factory():
    app_js = (ROOT / "dashboard/app.js").read_text(encoding="utf-8")
    assert "SigMapTooltips.bind" in app_js or "window.SigMapTooltips?.bind" in app_js
    assert "onAssetNeedMatchEachFeature" in app_js
    assert "renderSmartTooltip" in app_js


def test_focus_mode_not_regressed():
    html = (ROOT / "dashboard/index.html").read_text(encoding="utf-8")
    js = (ROOT / "dashboard/app.js").read_text(encoding="utf-8")
    css = (ROOT / "dashboard/styles.css").read_text(encoding="utf-8")
    assert "Mode Focus" in html
    assert "setCartographyFocusMode" in js
    assert "cartography-focus-mode" in css


def test_inventory_doc_exists_or_inline_coverage():
    # Couches critiques mentionnées dans le code
    app_js = (ROOT / "dashboard/app.js").read_text(encoding="utf-8")
    for layer in (
        "sites_40",
        "sites_300",
        "telecom_vodacom",
        "asset_need_matches",
        "spatial_relations",
        "provinces",
        "territoires",
    ):
        assert layer in app_js
