from tests.test_mission_crud import MISSION_PAYLOAD, create_site

PHOTO_PAYLOAD = {
    "nom": "Photo Test",
    "caption": "Photo du site",
    "chemin": "/tmp/photo_test.jpg",
}

UPDATED_PHOTO_PAYLOAD = {
    "nom": "Photo mise à jour",
    "caption": "Photo mise à jour",
    "chemin": "/tmp/photo_test_updated.jpg",
}


def create_mission(client):
    site = create_site(client)
    payload = {**MISSION_PAYLOAD, "site_id": site["id"]}
    response = client.post("/missions", json=payload)
    assert response.status_code == 200
    return response.json()


def test_photo_crud_and_relationship(client):
    mission = create_mission(client)
    payload = {**PHOTO_PAYLOAD, "mission_id": mission["id"]}
    response = client.post("/photos", json=payload)
    assert response.status_code == 200
    photo = response.json()
    assert photo["mission_id"] == mission["id"]
    assert "created_at" in photo

    photo_id = photo["id"]
    response = client.get(f"/photos/{photo_id}")
    assert response.status_code == 200

    response = client.put(f"/photos/{photo_id}", json={**UPDATED_PHOTO_PAYLOAD, "mission_id": mission["id"]})
    assert response.status_code == 200
    assert response.json()["nom"] == UPDATED_PHOTO_PAYLOAD["nom"]

    response = client.delete(f"/photos/{photo_id}")
    assert response.status_code == 200
    assert response.json() == {"deleted": True}

    response = client.get(f"/photos/{photo_id}")
    assert response.status_code == 404


def test_photo_foreign_key_constraint(client):
    payload = {**PHOTO_PAYLOAD, "mission_id": 999999}
    response = client.post("/photos", json=payload)
    assert response.status_code == 400
    assert "Contrainte d'intégrité" in response.json()["detail"]
