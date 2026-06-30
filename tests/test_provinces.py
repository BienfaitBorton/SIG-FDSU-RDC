PROVINCE_PAYLOAD = {
    "nom": "Test Province",
    "code": "TST",
    "zone": "ND",
    "chef_lieu": "Testville",
    "population": 123456,
    "superficie": 789.5,
}

UPDATED_PROVINCE_PAYLOAD = {
    "nom": "Updated Province",
    "code": "TST2",
    "zone": "SD",
    "chef_lieu": "Updatedville",
    "population": 654321,
    "superficie": 987.5,
}


def test_create_read_update_delete_province(client):
    response = client.post("/provinces", json=PROVINCE_PAYLOAD)
    assert response.status_code == 200
    province = response.json()
    assert province["code"] == PROVINCE_PAYLOAD["code"]
    assert province["nom"] == PROVINCE_PAYLOAD["nom"]

    province_id = province["id"]

    response = client.get("/provinces")
    assert response.status_code == 200
    assert any(item["id"] == province_id for item in response.json())

    response = client.get(f"/provinces/{province_id}")
    assert response.status_code == 200
    assert response.json()["id"] == province_id

    response = client.put(f"/provinces/{province_id}", json=UPDATED_PROVINCE_PAYLOAD)
    assert response.status_code == 200
    updated = response.json()
    assert updated["code"] == UPDATED_PROVINCE_PAYLOAD["code"]
    assert updated["nom"] == UPDATED_PROVINCE_PAYLOAD["nom"]

    response = client.delete(f"/provinces/{province_id}")
    assert response.status_code == 200
    assert response.json() == {"deleted": True}

    response = client.get(f"/provinces/{province_id}")
    assert response.status_code == 404
