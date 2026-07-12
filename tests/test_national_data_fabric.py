"""Tests National Data Fabric (NDF)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.services import national_data_fabric_service as ndf

CLIENT = TestClient(app)
PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def isolated_extensions(tmp_path, monkeypatch):
    path = tmp_path / "registries_extensions.json"
    path.write_text(
        json.dumps(
            {
                "_meta": {"title": "test extensions", "version": "ndf-1.0.0"},
                "registries": [],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(ndf, "EXTENSIONS_PATH", path)
    return path


def test_ndf_catalog_files_exist():
    assert (PROJECT_ROOT / "data/ndf/registries.json").exists()
    assert (PROJECT_ROOT / "data/ndf/relations.json").exists()
    assert (PROJECT_ROOT / "data/ndf/registries_extensions.json").exists()


def test_list_registries_includes_active_and_planned():
    payload = ndf.list_registries()
    ids = {r["id"] for r in payload["registries"]}
    assert {
        "administrative",
        "telecom",
        "health",
        "fdsu_sites",
        "ccn",
        "prioritization",
        "territorial_summary",
        "knowledge_hub",
        "population",
        "spatial_matching",
        "transport",
        "energy",
        "education",
        "economy",
        "hydrography",
        "environment",
        "agriculture",
    }.issubset(ids)
    assert payload["_meta"]["count"] >= 17


def test_get_registry_metadata_shape():
    detail = ndf.get_registry("population")
    assert detail is not None
    reg = detail["registry"]
    for field in (
        "id",
        "name",
        "category",
        "description",
        "owner",
        "official_source",
        "update_frequency",
        "version",
        "confidence_level",
        "geographic_coverage",
        "geometry_type",
        "crs",
        "apis",
        "metrics_exposed",
        "aggregation_rules",
    ):
        assert field in reg
    assert isinstance(detail["relations"], list)
    assert isinstance(reg["quality"], list)
    assert len(reg["quality"]) == 5


def test_register_registry_extension(isolated_extensions):
    result = ndf.register_registry(
        {
            "id": "test_transport_demo",
            "name": "Transport Demo NDF",
            "category": "transport",
            "description": "Enregistrement test — sans données inventées",
            "owner": "Tests NDF",
            "official_source": "fixture://test",
            "update_frequency": "n/a",
            "version": "0.1",
            "confidence_level": "unknown",
            "geographic_coverage": "test",
            "geometry_type": "LineString",
            "crs": "EPSG:4326",
            "apis": [],
            "metrics_exposed": [],
        }
    )
    assert result["registry"]["id"] == "test_transport_demo"
    assert any(r["id"] == "test_transport_demo" for r in ndf.list_registries()["registries"])

    with pytest.raises(ValueError, match="catalogue cœur"):
        ndf.register_registry(
            {
                "id": "telecom",
                "name": "Dup",
                "category": "connectivity",
                "description": "x",
                "owner": "x",
                "official_source": "x",
                "update_frequency": "x",
                "version": "0",
                "confidence_level": "unknown",
                "geographic_coverage": "x",
                "geometry_type": "Point",
                "crs": "EPSG:4326",
            }
        )


def test_relations_coherence():
    payload = ndf.list_relations()
    assert payload["_meta"]["count"] > 0
    assert payload["_meta"]["coherence_issues"] == 0
    for rel in payload["relations"]:
        assert rel["endpoints_known"] is True
        assert rel["from"] and rel["to"] and rel["type"]


def test_quality_indicators_population_nci():
    q = ndf.compute_quality("population")
    dims = {i["dimension"] for i in q["indicators"]}
    assert dims == {"completeness", "freshness", "coherence", "geometry", "precision"}
    # Au moins une dimension mesurée depuis quality_report réel
    assert q["summary"]["measured"] >= 1
    assert all("display" in i for i in q["indicators"])


def test_quality_planned_is_insufficient():
    q = ndf.compute_quality("energy")
    assert q["summary"]["measured"] == 0
    assert all(i["display"] == "Données insuffisantes" for i in q["indicators"])


def test_transport_registry_active():
    detail = ndf.get_registry("transport")
    assert detail is not None
    assert detail["registry"]["status"] == "active"
    assert "/api/transport" in (detail["registry"].get("apis") or [])


def test_consumers_compatibility_engines():
    payload = ndf.consumers_compatibility()
    ids = {c["consumer_id"] for c in payload["consumers"]}
    assert {"territorial_summary", "decision_engine", "knowledge_hub", "spatial_matching"} <= ids
    assert all(c["compatible"] for c in payload["consumers"])


def test_api_endpoints():
    assert CLIENT.get("/api/national-data-fabric/manifest").status_code == 200
    inv = CLIENT.get("/api/national-data-fabric/registries")
    assert inv.status_code == 200
    assert inv.json()["_meta"]["count"] >= 17

    meta = CLIENT.get("/api/national-data-fabric/registries/health")
    assert meta.status_code == 200
    assert meta.json()["registry"]["id"] == "health"

    search = CLIENT.get("/api/national-data-fabric/search", params={"q": "CCN"})
    assert search.status_code == 200
    assert search.json()["_meta"]["count"] >= 1

    quality = CLIENT.get("/api/national-data-fabric/quality")
    assert quality.status_code == 200
    assert len(quality.json()["registries"]) >= 17

    stats = CLIENT.get("/api/national-data-fabric/statistics")
    assert stats.status_code == 200
    assert stats.json()["registries_total"] >= 17

    rel = CLIENT.get("/api/national-data-fabric/relations")
    assert rel.status_code == 200

    cons = CLIENT.get("/api/national-data-fabric/consumers")
    assert cons.status_code == 200


def test_api_register(isolated_extensions):
    # Route uses service path — monkeypatch must apply to service used by router
    body = {
        "id": "api_test_energy_slot",
        "name": "Energy Slot Test",
        "category": "energy",
        "description": "Test API register",
        "owner": "Tests",
        "official_source": "fixture",
        "update_frequency": "n/a",
        "version": "0.1",
        "confidence_level": "unknown",
        "geographic_coverage": "test",
        "geometry_type": "Point",
        "crs": "EPSG:4326",
    }
    res = CLIENT.post("/api/national-data-fabric/registries", json=body)
    assert res.status_code == 200
    assert res.json()["registry"]["id"] == "api_test_energy_slot"

    dup = CLIENT.post("/api/national-data-fabric/registries", json={**body, "id": "health"})
    assert dup.status_code == 400
