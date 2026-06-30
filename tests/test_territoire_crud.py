from tests.test_province_crud import PROVINCE_PAYLOAD

TERRITOIRE_PAYLOAD = {
    "nom": "Territoire Test",
    "code": "145",
    "chef_lieu": "Territoireville",
}

UPDATED_TERRITOIRE_PAYLOAD = {
    "nom": "Territoire Mise à jour",
    "code": "146",
    "chef_lieu": "TerritoireCity",
}


def create_province(client):
    response = client.post("/provinces", json=PROVINCE_PAYLOAD)
    assert response.status_code == 200
    return response.json()


def test_territoire_crud_and_relationship(client):
    province = create_province(client)
    payload = {**TERRITOIRE_PAYLOAD, "province_id": province["id"]}
    response = client.post("/territoires", json=payload)
    assert response.status_code == 200
    territoire = response.json()
    assert territoire["province_id"] == province["id"]

    territoire_id = territoire["id"]
    response = client.get(f"/territoires/{territoire_id}")
    assert response.status_code == 200

    response = client.put(
        f"/territoires/{territoire_id}",
        json={**UPDATED_TERRITOIRE_PAYLOAD, "province_id": province["id"]},
    )
    assert response.status_code == 200
    assert response.json()["code"] == UPDATED_TERRITOIRE_PAYLOAD["code"]

    response = client.delete(f"/territoires/{territoire_id}")
    assert response.status_code == 200
    assert response.json() == {"deleted": True}

    response = client.get(f"/territoires/{territoire_id}")
    assert response.status_code == 404


def test_territoire_foreign_key_constraint(client):
    payload = {**TERRITOIRE_PAYLOAD, "province_id": 999999}
    response = client.post("/territoires", json=payload)
    assert response.status_code == 400
    assert "Contrainte d'intégrité" in response.json()["detail"]
