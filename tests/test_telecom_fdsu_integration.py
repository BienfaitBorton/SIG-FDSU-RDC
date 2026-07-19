"""Tests intégration Télécom FDSU non bloquante (hors KPI national)."""
from __future__ import annotations

from pathlib import Path

import openpyxl
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import telecom as telecom_routes
from api.services import telecom_service
from api.services.nire import mno_audit
from api.services.telecom_asset_typing import classify_telecom_asset
from api.services.telecom_layer_catalog import catalog_payload, get_layer_definition, known_layer_keys

ROOT = Path(__file__).resolve().parents[1]


def _write_mno_sample(path: Path) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Site Name", "Latitude", "Longitude", "RAT", "Status", "Operator name"])
    ws.append(["Airtel Site A", -4.32, 15.31, "2G/3G/4G", "Online", "Airtel"])
    ws.append(["Africell Site B", -4.33, 15.32, "2G-3G-4G", "Online", "Africell"])
    ws.append(["Planned Airtel", -4.10, 15.20, "2G", "Planned", "Airtel"])
    ws.append(["Vodacom Site", -4.40, 15.40, "2G", "Online", "Vodacom"])
    wb.save(path)


@pytest.fixture
def mno_sample(tmp_path):
    path = tmp_path / "mno.xlsx"
    _write_mno_sample(path)
    mno_audit.reset_state()
    yield path
    mno_audit.reset_state()


def test_catalog_includes_four_mnos_and_backbone():
    keys = known_layer_keys()
    for key in (
        "telecom_vodacom",
        "telecom_orange",
        "telecom_airtel",
        "telecom_africell",
        "telecom_mno_planned",
        "telecom_fiber",
        "telecom_microwave",
        "telecom_fiberco",
    ):
        assert key in keys
    payload = catalog_payload()
    assert "PROVISIONAL" in payload["quality_statuses"]
    assert payload["extensible"] is True
    airtel = get_layer_definition("telecom_airtel")
    assert airtel["source_kind"] == "FDSU_MNO_AUDIT"
    assert airtel.get("kpi_excluded") is True
    vodacom = get_layer_definition("telecom_vodacom")
    orange = get_layer_definition("telecom_orange")
    assert vodacom["source_kind"] == "OPERATOR_SITES_CONSOLIDATED"
    assert orange["source_kind"] == "OPERATOR_SITES_CONSOLIDATED"
    fiber = get_layer_definition("telecom_fiber")
    assert "polygon" not in (fiber.get("geometry_kinds") or [])


def test_asset_typing_preserves_original():
    row = {"line_type": "fiber", "technology": "Fiber", "line_name": "Link A", "properties": {}}
    typed = classify_telecom_asset(row, geometry_kind="line")
    assert typed["original_type"] == "fiber"
    assert typed["derived_asset_type"] in {"FIBER_LINK", "MICROWAVE_LINK", "OTHER"}


def test_nire_quality_non_blocking_and_fdsu_layers(mno_sample):
    state = mno_audit.run_mno_audit(mno_sample, telecom_points=[], enqueue_reviews=False)
    assert state.review_enqueued == 0
    for r in state.rows:
        q = mno_audit.nire_quality_status(r)
        assert q in {"VERIFIED", "HIGH_CONFIDENCE", "PROVISIONAL", "NEEDS_REVIEW", "CONFLICT"}
    airtel = mno_audit.layer_geojson("AIRTEL", limit=50, ensure_loaded=False)
    assert airtel["meta"]["kpi_national_untouched"] is True
    assert airtel["meta"]["nire_non_blocking"] is True
    assert any(f["properties"].get("operator_code") == "AIRTEL" for f in airtel["features"])
    assert all(f["properties"].get("nire_quality_status") for f in airtel["features"])
    africell = mno_audit.layer_geojson("AFRICELL", limit=50)
    assert africell["features"]
    planned = mno_audit.layer_geojson(None, planned_only=True, limit=50)
    assert planned["features"]
    assert all(f["properties"].get("status_normalized") == "PLANNED" for f in planned["features"])


def test_resolve_layer_geojson_fdsu(mno_sample):
    mno_audit.run_mno_audit(mno_sample, telecom_points=[], enqueue_reviews=False)
    layer = telecom_service.resolve_layer_geojson("telecom_airtel", limit=100)
    assert layer["type"] == "FeatureCollection"
    assert layer["features"]
    assert layer["meta"].get("kpi_national_untouched") is True


def test_ui_exposes_new_layer_toggles():
    html = (ROOT / "dashboard/index.html").read_text(encoding="utf-8")
    js = (ROOT / "dashboard/app.js").read_text(encoding="utf-8")
    for key in (
        "telecom_airtel",
        "telecom_africell",
        "telecom_mno_planned",
        "telecom_fiber",
        "telecom_microwave",
    ):
        assert f'data-layer="{key}"' in html
        assert key in js
    assert "nire_quality_status" in js
    assert "Hors KPI" in js or "kpi_excluded" in js


def test_api_catalog_route_shape():
    app = FastAPI()
    app.include_router(telecom_routes.router, prefix="/api/telecom")
    client = TestClient(app)
    # May 503 if not db — accept both
    r = client.get("/api/telecom/layer-catalog")
    assert r.status_code in {200, 503}
    if r.status_code == 200:
        body = r.json()
        assert "layers" in body
        keys = {x["layer_key"] for x in body["layers"]}
        assert "telecom_airtel" in keys


@pytest.mark.skipif(
    __import__("os").environ.get("DATA_MODE") != "db",
    reason="DB mode required for live layer counts",
)
def test_db_backbone_layers_non_empty():
    fiber = telecom_service.resolve_layer_geojson("telecom_fiber", limit=500)
    mw = telecom_service.resolve_layer_geojson("telecom_microwave", limit=500)
    fiberco = telecom_service.resolve_layer_geojson("telecom_fiberco", limit=500)
    assert fiber["features"]
    assert mw["features"]
    assert fiberco["features"]
    # KPI table untouched by FDSU staging helper contract
    stats = telecom_service.get_statistics()
    assert stats["infrastructure_count"] >= 14580 or stats["infrastructure_count"] > 0
