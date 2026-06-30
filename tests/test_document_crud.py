from tests.test_mission_crud import MISSION_PAYLOAD, create_site

DOCUMENT_PAYLOAD = {
    "nom": "Rapport Test",
    "type": "PDF",
    "chemin": "/tmp/rapport_test.pdf",
}

UPDATED_DOCUMENT_PAYLOAD = {
    "nom": "Rapport mis à jour",
    "type": "DOCX",
    "chemin": "/tmp/rapport_test_updated.docx",
}


def create_mission(client):
    site = create_site(client)
    payload = {**MISSION_PAYLOAD, "site_id": site["id"]}
    response = client.post("/missions", json=payload)
    assert response.status_code == 200
    return response.json()


def test_document_crud_and_relationship(client):
    mission = create_mission(client)
    payload = {**DOCUMENT_PAYLOAD, "mission_id": mission["id"]}
    response = client.post("/documents", json=payload)
    assert response.status_code == 200
    document = response.json()
    assert document["mission_id"] == mission["id"]
    assert "created_at" in document

    document_id = document["id"]
    response = client.get(f"/documents/{document_id}")
    assert response.status_code == 200

    response = client.put(f"/documents/{document_id}", json={**UPDATED_DOCUMENT_PAYLOAD, "mission_id": mission["id"]})
    assert response.status_code == 200
    assert response.json()["nom"] == UPDATED_DOCUMENT_PAYLOAD["nom"]

    response = client.delete(f"/documents/{document_id}")
    assert response.status_code == 200
    assert response.json() == {"deleted": True}

    response = client.get(f"/documents/{document_id}")
    assert response.status_code == 404


def test_document_foreign_key_constraint(client):
    payload = {**DOCUMENT_PAYLOAD, "mission_id": 999999}
    response = client.post("/documents", json=payload)
    assert response.status_code == 400
    assert "Contrainte d'intégrité" in response.json()["detail"]
