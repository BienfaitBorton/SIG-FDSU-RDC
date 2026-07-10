"""Vérifie le Mode Focus cartographique — aucune impasse UX / pas de fullscreen natif."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_cartography_focus_mode_replaces_native_fullscreen():
    html = (ROOT / "dashboard/index.html").read_text(encoding="utf-8")
    js = (ROOT / "dashboard/app.js").read_text(encoding="utf-8")
    css = (ROOT / "dashboard/styles.css").read_text(encoding="utf-8")

    assert 'id="carto-focus-btn"' in html
    assert "Mode Focus" in html
    assert "cartography-focus-bar" in html
    assert "Quitter le Mode Focus" in html
    assert "← Retour" in html
    assert "carto-fullscreen-btn" not in html
    assert "requestFullscreen" not in js
    assert "setCartographyFocusMode" in js
    assert "Escape" in js
    assert "cartography-focus-mode" in css
    assert ".cartography-map-stage.is-fullscreen" not in css
    assert (ROOT / "PROJECT_MANAGEMENT/UX_NO_DEAD_ENDS.md").exists()
