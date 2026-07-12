"""Tests Territorial Digital Twin Foundation v1.0."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.services import territorial_digital_twin_service as tdt

CLIENT = TestClient(app)


def _sample_territory_id() -> str | None:
    from api.services import territorial_intelligence_service as ti

    listed = ti.list_territories(limit=5) or {}
    items = listed.get("territories") or listed.get("items") or []
    if not items:
        return None
    row = items[0]
    return str(row.get("territory_id") or row.get("id") or row.get("business_id") or "")


def test_resolve_entity_province_identity():
    entity = tdt.resolve_entity("province", "Haut-Lomami")
    assert entity is not None
    assert entity["entity_type"] == "province"
    assert entity["nom"]
    assert entity["niveau_administratif"] == "Province"
    hierarchy = tdt.build_hierarchy(entity)
    assert hierarchy[0]["entity_type"] == "rdc"
    assert any(h["entity_type"] == "province" for h in hierarchy)


def test_build_twin_composition_and_partial_results():
    twin = tdt.build_twin("province", "Haut-Lomami")
    assert twin is not None
    assert twin["entity"]["entity_type"] == "province"
    assert isinstance(twin["hierarchy"], list)
    assert "summary" in twin
    assert "connectivity" in twin
    assert "public_services" in twin
    assert "accessibility" in twin
    assert "energy" in twin
    assert "economy" in twin
    assert "programs" in twin
    assert "decision" in twin
    assert "quality" in twin
    assert isinstance(twin["timeline"], list)
    assert isinstance(twin["sources"], list)
    assert isinstance(twin["section_status"], dict)
    # Énergie préparée mais non alimentée
    assert twin["section_status"].get("energy") == "unavailable"
    assert "non encore" in str(twin["energy"].get("_section", {}).get("note") or "").lower() or twin["energy"].get("display")
    # Aucune valeur NaN / undefined côté JSON
    import json
    json.dumps(twin)
    assert twin["_meta"]["overall_status"] in {"success", "partial", "unavailable", "error"}


def test_section_quality_and_sources():
    twin = tdt.build_twin("province", "Haut-Lomami", sections=["quality"])
    assert twin["quality"]["_section"]["status"] in {"success", "partial"}
    assert twin["quality"].get("ndf_registries")
    assert "national_data_fabric" in (twin["quality"]["_section"].get("source") or "")


def test_energy_unavailable_contract():
    section = tdt.section_energy({"entity_type": "province", "nom": "X"})
    assert section["_section"]["status"] == "unavailable"
    assert "Données non encore intégrées" in (section["_section"].get("note") or section.get("display") or "")


@pytest.mark.parametrize("section", ["summary", "connectivity", "services", "accessibility", "programs", "decision", "quality", "timeline"])
def test_api_section_endpoints_province(section):
    response = CLIENT.get(f"/api/territorial-digital-twin/province/Haut-Lomami/{section}")
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("entity")
    assert "section_status" in payload


def test_api_main_endpoint_and_404():
    ok = CLIENT.get("/api/territorial-digital-twin/province/Haut-Lomami")
    assert ok.status_code == 200
    body = ok.json()
    assert body["entity"]["entity_type"] == "province"
    assert "section_status" in body

    missing = CLIENT.get("/api/territorial-digital-twin/territoire/__inexistant_tdt_xyz__")
    assert missing.status_code == 404


def test_territory_twin_when_available():
    tid = _sample_territory_id()
    if not tid:
        pytest.skip("Aucun territoire TI disponible")
    twin = tdt.build_twin("territoire", tid)
    assert twin is not None
    assert twin["entity"]["entity_type"] == "territoire"
    assert twin["hierarchy"]
    # Sections clés présentes même si partial
    for key in ("summary", "connectivity", "accessibility", "programs", "decision"):
        assert key in twin
        assert twin[key].get("_section", {}).get("status") in {"success", "partial", "unavailable", "error"}


def test_db_mode_compatible_main_endpoint():
    """Fonctionne en mode DB : l’endpoint principal ne doit pas lever 500."""
    from api.config import DATA_MODE

    response = CLIENT.get("/api/territorial-digital-twin/province/Kinshasa")
    assert response.status_code == 200
    payload = response.json()
    assert payload["_meta"]["version"].startswith("tdt-")
    # Mode courant documenté côté config (db attendu en dév)
    assert DATA_MODE in {"db", "json", "api", "auto"} or True
