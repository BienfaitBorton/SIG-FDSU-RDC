from api.services.documentary_enrichment_service import (
    confidence_score,
    extract_from_internal_text,
    merge_findings,
)


def test_extracts_structured_fields_from_tshopo_description():
    text = """
    Province de Tshopo
    Chef-lieu : Kisangani
    Superficie : 199 567 km²
    Population : 2,4 millions d'habitants
    """

    findings = extract_from_internal_text("Tshopo", "Province", text, "docs/tshopo.md")
    values = {item.field_name: item.proposed_value for item in findings}

    assert values["chef_lieu"] == "Kisangani"
    assert values["superficie"] == "199 567 km²"
    assert values["population"] == "2,4 millions d'habitants"
    assert all(item.status == "proposé" for item in findings)


def test_confidence_score_and_merge_keep_multiple_sources():
    first = extract_from_internal_text(
        "Dungu",
        "Territoire",
        "Potentiel agricole : cultures vivrières.",
        "data/reports/internal_a.md",
    )[0]
    second = extract_from_internal_text(
        "Dungu",
        "Territoire",
        "Potentiel agricole : cultures vivrières.",
        "data/reports/internal_b.md",
    )[0]

    merged = merge_findings([first, second])

    assert len(merged) == 1
    assert merged[0].field_name == "potentiel_agricole"
    assert len(merged[0].sources) == 2
    assert confidence_score(["CAID", "INS", "OpenStreetMap"]) == 90


def test_documentary_cnct_endpoints(client):
    audit = client.get("/knowledge/documentary/audit")
    assert audit.status_code == 200
    assert audit.json()["supported_files"] >= 0

    origins = client.get("/knowledge/documentary/origins")
    assert origins.status_code == 200
    data = origins.json()
    assert data["automatic_web_collection_enabled"] is False
    assert data["official_publication_enabled"] is False
    assert any(row["origin"] == "PostgreSQL / PostGIS" for row in data["origins"])

    demo = client.get("/knowledge/demo-enrichment")
    assert demo.status_code == 200
    demo_data = demo.json()
    assert demo_data["demo_enrichment_mode"] is True
    names = {item["entity_name"] for item in demo_data["entities"]}
    assert {"Tshopo", "Kinshasa", "Dungu", "Banalia"}.issubset(names)
