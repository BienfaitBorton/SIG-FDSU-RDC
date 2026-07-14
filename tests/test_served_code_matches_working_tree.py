"""Non-régression : le code servi (dashboard static) correspond au working tree courant."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "dashboard"

CRITICAL = [
    DASHBOARD / "app.js",
    DASHBOARD / "index.html",
    DASHBOARD / "styles.css",
    DASHBOARD / "modules" / "shared" / "basemap-manager" / "basemap-manager.js",
    DASHBOARD / "modules" / "shared" / "spatial-decision-graph" / "spatial-decision-graph.js",
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_critical_dashboard_files_exist_in_working_tree():
    missing = [str(p.relative_to(ROOT)) for p in CRITICAL if not p.is_file()]
    assert missing == [], f"Fichiers absents du working tree : {missing}"


def test_basemap_manager_wired_in_index_and_app():
    index_html = (DASHBOARD / "index.html").read_text(encoding="utf-8")
    app_js = (DASHBOARD / "app.js").read_text(encoding="utf-8")
    manager = (DASHBOARD / "modules" / "shared" / "basemap-manager" / "basemap-manager.js").read_text(
        encoding="utf-8"
    )
    assert "basemap-manager/basemap-manager.js" in index_html
    assert "SigBasemapManager" in manager
    assert "attachCartographyBasemap" in app_js
    assert "SigBasemapManager" in app_js


def test_served_static_matches_working_tree_hashes():
    """Si le dashboard local répond, les octets servis = fichiers du dépôt courant."""
    httpx = pytest.importorskip("httpx")
    base = "http://127.0.0.1:8000"
    try:
        probe = httpx.get(f"{base}/index.html", timeout=5.0)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Dashboard non joignable sur :8000 ({exc})")
    if probe.status_code != 200:
        pytest.skip(f"Dashboard HTTP {probe.status_code}")

    mapping = {
        "/index.html": DASHBOARD / "index.html",
        "/app.js": DASHBOARD / "app.js",
        "/styles.css": DASHBOARD / "styles.css",
        "/modules/shared/basemap-manager/basemap-manager.js": CRITICAL[3],
        "/modules/shared/spatial-decision-graph/spatial-decision-graph.js": CRITICAL[4],
    }
    mismatches = []
    for url, path in mapping.items():
        res = httpx.get(f"{base}{url}", timeout=20.0, headers={"Cache-Control": "no-cache"})
        assert res.status_code == 200, url
        served = hashlib.sha256(res.content).hexdigest()
        disk = _sha256(path)
        if served != disk:
            mismatches.append(f"{url}: served={served[:12]} disk={disk[:12]} len_s={len(res.content)} len_d={path.stat().st_size}")
    assert mismatches == [], "Code servi ≠ working tree:\n" + "\n".join(mismatches)
