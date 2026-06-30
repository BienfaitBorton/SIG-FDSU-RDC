from tests.test_province_crud import PROVINCE_PAYLOAD
from tests.test_territoire_crud import TERRITOIRE_PAYLOAD, create_province

COLLECTIVITE_PAYLOAD = {
    "nom": "Collectivité Test",
    "code": "001",
    "type_collectivite": "Secteur",
}

UPDATED_COLLECTIVITE_PAYLOAD = {
    "nom": "Collectivité Mise à jour",
    "code": "002",
    "type_collectivite": "Chefferie",
}


def create_territoire(client):
    province = create_province(client)
    payload = {**TERRITOIRE_PAYLOAD, "province_id": province["id"]}
    response = client.post("/territoires", json=payload)
    assert response.status_code == 200
    return response.json()


def test_collectivite_crud_and_relationship(client):
    territoire = create_territoire(client)
    payload = {**COLLECTIVITE_PAYLOAD, "territoire_id": territoire["id"]}
    response = client.post("/collectivites", json=payload)
    assert response.status_code == 200
    collectivite = response.json()
    assert collectivite["territoire_id"] == territoire["id"]

    collecte_id = collectivite["id"]
    response = client.get(f"/collectivites/{collecte_id}")
    assert response.status_code == 200

    response = client.put(
        f"/collectivites/{collecte_id}",
        json={**UPDATED_COLLECTIVITE_PAYLOAD, "territoire_id": territoire["id"]},
    )
    assert response.status_code == 200
    assert response.json()["code"] == UPDATED_COLLECTIVITE_PAYLOAD["code"]

    response = client.delete(f"/collectivites/{collecte_id}")
    assert response.status_code == 200
    assert response.json() == {"deleted": True}

    response = client.get(f"/collectivites/{collecte_id}")
    assert response.status_code == 404


def test_collectivite_foreign_key_constraint(client):
    payload = {**COLLECTIVITE_PAYLOAD, "territoire_id": 999999}
    response = client.post("/collectivites", json=payload)
    assert response.status_code == 400
    assert "Contrainte d'intégrité" in response.json()["detail"]
