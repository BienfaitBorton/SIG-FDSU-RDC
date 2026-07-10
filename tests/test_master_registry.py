"""Tests Référentiel National des Actifs FDSU + nomenclature officielle."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.services import fdsu_code_service, master_registry_service

CLIENT = TestClient(app)
EXAMPLE = "FDSU_ND_18_003_10100"


@pytest.fixture()
def isolated_registry(tmp_path, monkeypatch):
    registry_path = tmp_path / "registry.json"
    monkeypatch.setattr(master_registry_service, "MASTER_DIR", tmp_path)
    monkeypatch.setattr(master_registry_service, "REGISTRY_PATH", registry_path)
    # Force bootstrap
    if registry_path.exists():
        registry_path.unlink()
    payload = master_registry_service._ensure_store()
    return payload


def test_parse_official_fdsu_code():
    parsed = fdsu_code_service.parse_fdsu_code(EXAMPLE)
    assert parsed.valid_format is True
    assert parsed.prefix == "FDSU"
    assert parsed.zone == "ND"
    assert parsed.province_code == "18"
    assert parsed.territoire_code == "003"
    assert parsed.site_code == "10100"
    assert parsed.province_name == "MONGALA"
    assert "LISALA" in (parsed.territoire_name or "").upper()


def test_reject_artificial_site_id():
    parsed = fdsu_code_service.parse_fdsu_code("SITE-FDSU-000001")
    assert parsed.valid_format is False
    assert any("artificiel" in err.lower() for err in parsed.errors)


def test_validate_code_against_nomenclature():
    ok = fdsu_code_service.validate_fdsu_code(EXAMPLE)
    assert ok.is_valid is True
    assert ok.nomenclature_match is True
    assert ok.territory_consistent is True

    bad_zone = fdsu_code_service.validate_fdsu_code("FDSU_ET_18_003_10100")
    assert bad_zone.is_valid is False


def test_generate_fdsu_code():
    generated = fdsu_code_service.generate_fdsu_code(
        zone="ND",
        province_code=18,
        territoire_code=3,
        site_number=10100,
        site_width=5,
    )
    assert generated["business_id"] == EXAMPLE
    assert generated["is_valid"] is True


def test_detect_duplicates(isolated_registry):
    site = master_registry_service.create_entity(
        {
            "entity_type": "SITE",
            "business_id": EXAMPLE,
            "name": "Site Lisala test",
            "source": "test",
        },
        payload=isolated_registry,
        persist=True,
    )
    assert site["business_id"] == EXAMPLE
    dupes = master_registry_service.detect_duplicates(
        business_id=EXAMPLE,
        entity_type="SITE",
        payload=isolated_registry,
    )
    assert any(item["severity"] == "exact_business_id" for item in dupes)

    with pytest.raises(ValueError, match="Doublon"):
        master_registry_service.create_entity(
            {
                "entity_type": "SITE",
                "business_id": EXAMPLE,
                "name": "Doublon",
            },
            payload=isolated_registry,
            persist=True,
        )


def test_search_and_statistics(isolated_registry):
    master_registry_service.create_entity(
        {
            "entity_type": "SITE",
            "business_id": EXAMPLE,
            "name": "Site Lisala test",
        },
        payload=isolated_registry,
        persist=True,
    )
    search = master_registry_service.search_entities("LISALA", limit=20)
    assert search["_meta"]["total"] >= 1
    stats = master_registry_service.statistics()
    assert stats["totals"]["entities"] > 0
    assert "PROVINCE" in stats["by_type"]
    assert stats["totals"]["fdsu_codes_valid"] >= 1


def test_api_fdsu_validate_and_generate():
    response = CLIENT.post(
        "/api/master/fdsu-code/validate",
        json={"business_id": EXAMPLE},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["is_valid"] is True

    generated = CLIENT.post(
        "/api/master/fdsu-code/generate",
        json={
            "zone": "ND",
            "province_code": "18",
            "territoire_code": "003",
            "site_number": "10100",
        },
    )
    assert generated.status_code == 200
    assert generated.json()["business_id"] == EXAMPLE


def test_api_statistics_and_get_code():
    stats = CLIENT.get("/api/master/statistics")
    assert stats.status_code == 200
    assert "totals" in stats.json()

    detail = CLIENT.get(f"/api/master/fdsu-code/{EXAMPLE}")
    assert detail.status_code == 200
    assert detail.json()["validation"]["parsed"]["zone"] == "ND"


def test_api_entities_list():
    response = CLIENT.get("/api/master/entities?entity_type=PROVINCE&limit=10")
    assert response.status_code == 200
    payload = response.json()
    assert payload["_meta"]["count"] >= 1
    assert all(item["entity_type"] == "PROVINCE" for item in payload["entities"])


def test_nomenclature_source_documented():
    path = Path("data/reports/fdsu_nomenclature.json")
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "FDSU_<CODE_ZONE>_<CODE_PROVINCE>_<CODE_TERRITOIRE>_<CODE_SITE>" in data["codification_format"]
    assert data["source"] == "data/raw/FDSU Structure code Territoire zones.xlsx"
    assert "zones(2)" not in data["source"]
    assert "zones(3)" not in data["source"]
    assert Path(data["source"]).exists()


def test_official_structure_constant():
    from app.fdsu_nomenclature import OFFICIAL_STRUCTURE_RELATIVE, OFFICIAL_STRUCTURE_XLSX

    assert OFFICIAL_STRUCTURE_RELATIVE == "data/raw/FDSU Structure code Territoire zones.xlsx"
    assert OFFICIAL_STRUCTURE_XLSX.exists()
    assert "zones(2)" not in OFFICIAL_STRUCTURE_RELATIVE
    assert "zones(3)" not in OFFICIAL_STRUCTURE_RELATIVE
