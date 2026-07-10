"""Tests EDVS — Executive Data Visualization System / Salle de Pilotage DG."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app
from api.services import executive_cockpit_service

CLIENT = TestClient(app)
ROOT = Path(__file__).resolve().parents[1]
EDVS_DIR = ROOT / "dashboard" / "modules" / "shared" / "executive-dashboard"


def test_edvs_frontend_files_exist():
    required = [
        "executive-colors.js",
        "executive-icons.js",
        "executive-utils.js",
        "executive-kpi.js",
        "executive-cards.js",
        "executive-charts.js",
        "executive-layout.js",
        "executive-dashboard.js",
        "executive-dashboard.css",
    ]
    for name in required:
        assert (EDVS_DIR / name).exists(), name


def test_edvs_color_charter_in_source():
    colors = (EDVS_DIR / "executive-colors.js").read_text(encoding="utf-8")
    for token in ("green", "orange", "red", "blue", "gray", "yellow"):
        assert token in colors
    assert "meaning" in colors


def test_presentation_mode_has_visible_exit():
    layout = (EDVS_DIR / "executive-layout.js").read_text(encoding="utf-8")
    assert "edvs-presentation-mode" in layout
    assert "Quitter le Mode Présentation" in layout
    assert "Escape" in layout
    css = (EDVS_DIR / "executive-dashboard.css").read_text(encoding="utf-8")
    assert "edvs-presentation-bar" in css


def test_cockpit_api_consumes_existing_sources():
    payload = executive_cockpit_service.build_cockpit_payload()
    assert payload["_meta"]["framework"] == "EDVS v1"
    assert payload["_meta"]["hardcoded_forbidden"] is True
    assert len(payload["kpis"]) >= 4
    assert "radar" in payload
    assert "waterfall" in payload
    assert all(rec.get("why") for rec in payload.get("recommendations") or [])
    # waterfall from doctrine weights
    assert len(payload["waterfall"]["steps"]) >= 1


def test_api_executive_endpoints():
    cockpit = CLIENT.get("/api/executive/cockpit")
    assert cockpit.status_code == 200
    body = cockpit.json()
    assert body["_meta"]["title"]
    assert "kpis" in body

    catalog = CLIENT.get("/api/executive/chart-catalog")
    assert catalog.status_code == 200
    assert "Executive KPI Card" in catalog.json()["components"]


def test_salle_pilotage_wired_in_dashboard():
    html = (ROOT / "dashboard/index.html").read_text(encoding="utf-8")
    assert 'data-route="salle-pilotage"' in html
    assert "executive-dashboard.js" in html
    assert "salle-pilotage-panel" in html
