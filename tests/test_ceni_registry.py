from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app
from api.services import ceni_registry_service
from app.referentials.ceni_official.models import CeniCategory
from app.referentials.ceni_official.service import (
    SENTINEL_COORDINATES_STATUS,
    CeniRegistryService,
    REGISTRY_PATH,
    SOURCE_PATH,
    apply_quarantine_contract,
)

EXPECTED_SHA256 = "C3762911DF483D0B291145AF31CF612A30332039BB3D7BFD86FA894C650ABE9D"


def source_hash() -> str:
    return hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest().upper()


def test_kmz_audit_contract_and_source_integrity():
    before = source_hash()
    audit = CeniRegistryService().audit()
    after = source_hash()
    assert before == after == EXPECTED_SHA256
    assert audit["structure"]["placemarks"] == 32221
    assert audit["structure"]["geometries"] == {"Point": 32221}
    assert {field["name"] for field in audit["structure"]["schemas"][0]["fields"]} == {"Name", "Latitude", "Longitude"}
    assert audit["structure"]["descriptions"] == 0


def test_registry_keeps_every_source_record_and_unique_ids():
    registry = CeniRegistryService.load()
    assets = registry["assets"]
    assert len(assets) == 32221
    assert len({row["asset_uid"] for row in assets}) == 32221
    assert len({row["source_record_id"] for row in assets}) == 32221
    assert all(row["fingerprint"] and row["raw_properties"] for row in assets)
    assert registry["_meta"]["source_sha256"] == EXPECTED_SHA256


def test_no_ceni_fdsu_confusion_and_no_invented_scores():
    registry = CeniRegistryService.load()
    assert registry["contract"] == {
        "asset_domain": "INSTITUTIONAL",
        "institution": "CENI",
        "forbidden_asset_type": "FDSU",
        "sdg_relations_active": False,
        "ntie_scores_added": False,
    }
    assert all(row["asset_domain"] == "INSTITUTIONAL" and row["institution"] == "CENI" and row["asset_type"] != "FDSU" for row in registry["assets"])
    assert all("score" not in row for row in registry["assets"])


def test_taxonomy_and_uncertain_values_remain_unclassified():
    registry = CeniRegistryService.load()
    allowed = {category.value for category in CeniCategory}
    assert all(row["normalized_category"] in allowed for row in registry["assets"])
    assert registry["statistics"]["categories"]["UNCLASSIFIED"] > 0
    assert all(row["classification_justification"] for row in registry["assets"])


def test_duplicates_are_flagged_not_deleted():
    registry = CeniRegistryService.load()
    exact = [row for row in registry["assets"] if row["duplicate"]["status"] == "exact"]
    assert exact
    assert registry["statistics"]["total_raw"] == 32221
    assert all(row["duplicate"]["automatic_action"] == "none" for row in exact)


def test_sentinel_coordinates_are_quarantined_without_geographic_duplicates():
    ceni_registry_service.registry.cache_clear()
    registry = ceni_registry_service.registry()
    quarantined = [row for row in registry["assets"] if row["geometry_status"] == SENTINEL_COORDINATES_STATUS]
    assert len(quarantined) == 265
    assert registry["statistics"]["total_raw"] == 32221
    assert registry["statistics"]["integrated"] == 31956
    assert registry["statistics"]["quarantined"] == 265
    assert registry["statistics"]["rejected"] == 0
    assert registry["statistics"]["resolution_candidates"] == 38
    assert registry["statistics"]["quarantined_school_candidates"] == 90
    assert all(row["quarantine"]["primary_reason"] == SENTINEL_COORDINATES_STATUS for row in quarantined)
    assert all(row["quarantine"]["mappable"] is False for row in quarantined)
    assert all(row["duplicate"]["status"] not in {"exact", "same_geometry", "probable"} for row in quarantined)


def test_real_geographic_duplicates_remain_detected():
    rows = [
        {"asset_uid": "A", "name": "SITE TEST", "fingerprint": "F", "longitude": 20.0, "latitude": -4.0, "normalized_category": "OTHER"},
        {"asset_uid": "B", "name": "SITE TEST", "fingerprint": "F", "longitude": 20.0, "latitude": -4.0, "normalized_category": "OTHER"},
    ]
    apply_quarantine_contract(rows, batch_id="TEST")
    assert [row["duplicate"]["status"] for row in rows] == ["exact", "exact"]


def test_ceni_map_never_returns_sentinel_coordinates():
    payload = ceni_registry_service.map_features(limit=5000)
    assert payload["features"]
    assert all(feature["geometry"]["coordinates"] != [0.0, 0.0] for feature in payload["features"])
    assert all(feature["properties"]["quality"] in {"valid", "suspect"} for feature in payload["features"])


def test_api_routes_and_filters():
    client = TestClient(app)
    assert client.get("/api/ceni/statistics").status_code == 200
    quarantine = client.get("/api/ceni/sites", params={"limit": 300, "quality": SENTINEL_COORDINATES_STATUS}).json()
    assert quarantine["total"] == 265 and len(quarantine["sites"]) == 265
    categories = client.get("/api/ceni/categories").json()["categories"]
    assert {row["id"] for row in categories} == {category.value for category in CeniCategory}
    payload = client.get("/api/ceni/sites", params={"limit": 3, "category": "UNCLASSIFIED"}).json()
    assert payload["total"] > 0 and len(payload["sites"]) == 3
    uid = payload["sites"][0]["asset_uid"]
    detail = client.get(f"/api/ceni/sites/{uid}")
    assert detail.status_code == 200 and detail.json()["site"]["institution"] == "CENI"
    assert client.get("/api/ceni/map", params={"limit": 10}).status_code == 200
    assert client.get("/api/ceni/data-quality", params={"limit": 2}).status_code == 200
    assert client.get("/api/ceni/import-batches").status_code == 200
    assert client.get("/api/ceni/classification/statistics").status_code == 200
    rules = client.get("/api/ceni/classification/rules").json()
    assert rules["engine_version"] == "fr-2.0.0-dnai"
    assert client.get("/api/ceni/classification/review").status_code == 200
    classification = client.get(f"/api/ceni/sites/{uid}/classification")
    assert classification.status_code == 200
    assert classification.json()["classification"]["source_name"]


def test_generated_registry_exists_outside_protected_work_directory():
    assert REGISTRY_PATH.exists()
    assert "work" not in {part.lower() for part in Path(REGISTRY_PATH).parts}
