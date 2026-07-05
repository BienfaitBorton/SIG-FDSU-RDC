from datetime import datetime


def _payload(entity_name: str = "Kinshasa", field_name: str = "defis") -> dict[str, str]:
    return {
        "entity_type": "Ville-Province",
        "entity_name": entity_name,
        "field_name": field_name,
        "proposed_value": "Valeur a verifier par validation metier.",
        "source_name": "CNCT",
        "source_url": "https://example.local/source",
        "consulted_at": datetime.utcnow().isoformat(),
        "confidence_level": "a verifier",
    }


def test_enrichment_dashboard_and_completeness_filters(client):
    dashboard = client.get("/enrichment/dashboard")
    assert dashboard.status_code == 200
    data = dashboard.json()
    assert data["automatic_collection_enabled"] is False
    assert data["official_publication_enabled"] is False
    assert data["missing_value_label"]
    assert data["total_entities"] >= 1

    completeness = client.get("/enrichment/completeness", params={"province": "Kinshasa"})
    assert completeness.status_code == 200
    rows = completeness.json()
    assert any(row["entity_name"] == "Kinshasa" for row in rows)

    missing = client.get("/enrichment/completeness", params={"missing_field": "defis"})
    assert missing.status_code == 200
    assert all("defis" in row["missing_fields"] for row in missing.json())


def test_manual_suggestion_validate_reject_and_traceability(client):
    created = client.post("/enrichment/suggestions", json=_payload())
    assert created.status_code == 200
    suggestion = created.json()
    assert suggestion["status"] == "proposé"
    assert suggestion["source_name"] == "CNCT"

    validated = client.patch(
        f"/enrichment/suggestions/{suggestion['id']}/validate",
        json={"review_note": "Source conservee, validation fonctionnelle.", "validated_by": "test"},
    )
    assert validated.status_code == 200
    validated_data = validated.json()
    assert validated_data["status"] == "validé"
    assert validated_data["validated_at"] is not None

    traceability = client.get(f"/enrichment/suggestions/{suggestion['id']}/traceability")
    assert traceability.status_code == 200
    traceability_data = traceability.json()
    assert traceability_data["traceable"] is True
    assert traceability_data["published_to_official_referential"] is False

    rejected = client.post("/enrichment/suggestions", json=_payload(entity_name="Territoire exemple", field_name="sources"))
    assert rejected.status_code == 200
    rejected_id = rejected.json()["id"]
    decision = client.patch(
        f"/enrichment/suggestions/{rejected_id}/reject",
        json={"review_note": "Source insuffisante.", "validated_by": "test"},
    )
    assert decision.status_code == 200
    assert decision.json()["status"] == "rejeté"

    suggestions = client.get("/enrichment/suggestions", params={"status": "rejeté"})
    assert suggestions.status_code == 200
    assert any(item["id"] == rejected_id for item in suggestions.json())
