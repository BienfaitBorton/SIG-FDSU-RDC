PROVINCE_PAYLOAD = {
    "nom": "Province Test",
    "code": "11",
    "zone": "ND",
    "chef_lieu": "Testville",
    "population": 123456,
    "superficie": 789.5,
}

UPDATED_PROVINCE_PAYLOAD = {
    "nom": "Province Mise à jour",
    "code": "12",
    "zone": "SD",
    "chef_lieu": "Updatedville",
    "population": 654321,
    "superficie": 987.5,
}


def test_province_crud_happy_path(client):
    response = client.post("/provinces", json=PROVINCE_PAYLOAD)
    assert response.status_code == 200
    province = response.json()
    assert province["nom"] == PROVINCE_PAYLOAD["nom"]
    assert province["code"] == PROVINCE_PAYLOAD["code"]

    province_id = province["id"]

    response = client.get(f"/provinces/{province_id}")
    assert response.status_code == 200
    assert response.json()["id"] == province_id

    response = client.put(f"/provinces/{province_id}", json=UPDATED_PROVINCE_PAYLOAD)
    assert response.status_code == 200
    assert response.json()["nom"] == UPDATED_PROVINCE_PAYLOAD["nom"]
    assert response.json()["zone"] == UPDATED_PROVINCE_PAYLOAD["zone"]

    response = client.delete(f"/provinces/{province_id}")
    assert response.status_code == 200
    assert response.json() == {"deleted": True}

    response = client.get(f"/provinces/{province_id}")
    assert response.status_code == 404


def test_province_unique_code_constraint(client):
    first = client.post("/provinces", json=PROVINCE_PAYLOAD)
    assert first.status_code == 200

    duplicate = client.post("/provinces", json=PROVINCE_PAYLOAD)
    assert duplicate.status_code == 400
    assert "Contrainte d'intégrité" in duplicate.json()["detail"]


def test_province_not_found_errors(client):
    response = client.get("/provinces/999999")
    assert response.status_code == 404

    response = client.put("/provinces/999999", json=UPDATED_PROVINCE_PAYLOAD)
    assert response.status_code == 404

    response = client.delete("/provinces/999999")
    assert response.status_code == 404
