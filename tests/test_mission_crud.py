from tests.test_site_crud import SITE_PAYLOAD, create_village

MISSION_PAYLOAD = {
    "titre": "Mission Test",
    "description": "Mission de vérification",
    "date_debut": "2026-04-01",
    "date_fin": "2026-04-15",
}

UPDATED_MISSION_PAYLOAD = {
    "titre": "Mission mise à jour",
    "description": "Mission mise à jour description",
    "date_debut": "2026-05-01",
    "date_fin": "2026-05-31",
}


def create_site(client):
    village = create_village(client)
    payload = {**SITE_PAYLOAD, "village_id": village["id"]}
    response = client.post("/sites", json=payload)
    assert response.status_code == 200
    return response.json()


def test_mission_crud_and_relationship(client):
    site = create_site(client)
    payload = {**MISSION_PAYLOAD, "site_id": site["id"]}
    response = client.post("/missions", json=payload)
    assert response.status_code == 200
    mission = response.json()
    assert mission["site_id"] == site["id"]

    mission_id = mission["id"]
    response = client.get(f"/missions/{mission_id}")
    assert response.status_code == 200

    response = client.put(f"/missions/{mission_id}", json={**UPDATED_MISSION_PAYLOAD, "site_id": site["id"]})
    assert response.status_code == 200
    assert response.json()["titre"] == UPDATED_MISSION_PAYLOAD["titre"]

    response = client.delete(f"/missions/{mission_id}")
    assert response.status_code == 200
    assert response.json() == {"deleted": True}

    response = client.get(f"/missions/{mission_id}")
    assert response.status_code == 404


def test_mission_foreign_key_constraint(client):
    payload = {**MISSION_PAYLOAD, "site_id": 999999}
    response = client.post("/missions", json=payload)
    assert response.status_code == 400
    assert "Contrainte d'intégrité" in response.json()["detail"]
