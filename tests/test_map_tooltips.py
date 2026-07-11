"""Tests du composant partagé d'infobulles cartographiques."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_map_tooltips_module_present_and_loaded():
    tip = (ROOT / "dashboard/modules/shared/map-tooltips.js").read_text(encoding="utf-8")
    html = (ROOT / "dashboard/index.html").read_text(encoding="utf-8")
    assert "Survol = comprendre rapidement" in tip
    assert "bindHoverTooltip" in tip
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


def test_focus_mode_not_regressed():
    html = (ROOT / "dashboard/index.html").read_text(encoding="utf-8")
    js = (ROOT / "dashboard/app.js").read_text(encoding="utf-8")
    css = (ROOT / "dashboard/styles.css").read_text(encoding="utf-8")
    assert "Mode Focus" in html
    assert "setCartographyFocusMode" in js
    assert "cartography-focus-mode" in css
