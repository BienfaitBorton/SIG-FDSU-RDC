from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app
from app.referentials.ceni_official.models import CeniCategory
from app.referentials.ceni_official.service import CeniRegistryService, REGISTRY_PATH, SOURCE_PATH

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


def test_api_routes_and_filters():
    client = TestClient(app)
    assert client.get("/api/ceni/statistics").status_code == 200
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
    assert rules["engine_version"] == "fr-1.0.0"
    assert client.get("/api/ceni/classification/review").status_code == 200
    classification = client.get(f"/api/ceni/sites/{uid}/classification")
    assert classification.status_code == 200
    assert classification.json()["classification"]["source_name"]


def test_generated_registry_exists_outside_protected_work_directory():
    assert REGISTRY_PATH.exists()
    assert "work" not in {part.lower() for part in Path(REGISTRY_PATH).parts}
