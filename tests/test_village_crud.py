from tests.test_groupement_crud import GROUPEMENT_PAYLOAD, create_collectivite

VILLAGE_PAYLOAD = {
    "nom": "Village Test",
    "code": "001",
}

UPDATED_VILLAGE_PAYLOAD = {
    "nom": "Village Mis à jour",
    "code": "002",
}


def create_groupement(client):
    collectivite = create_collectivite(client)
    payload = {**GROUPEMENT_PAYLOAD, "collectivite_id": collectivite["id"]}
    response = client.post("/groupements", json=payload)
    assert response.status_code == 200
    return response.json()


def test_village_crud_and_relationship(client):
    groupement = create_groupement(client)
    payload = {**VILLAGE_PAYLOAD, "groupement_id": groupement["id"]}
    response = client.post("/villages", json=payload)
    assert response.status_code == 200
    village = response.json()
    assert village["groupement_id"] == groupement["id"]

    village_id = village["id"]
    response = client.get(f"/villages/{village_id}")
    assert response.status_code == 200

    response = client.put(
        f"/villages/{village_id}",
        json={**UPDATED_VILLAGE_PAYLOAD, "groupement_id": groupement["id"]},
    )
    assert response.status_code == 200
    assert response.json()["code"] == UPDATED_VILLAGE_PAYLOAD["code"]

    response = client.delete(f"/villages/{village_id}")
    assert response.status_code == 200
    assert response.json() == {"deleted": True}

    response = client.get(f"/villages/{village_id}")
    assert response.status_code == 404


def test_village_foreign_key_constraint(client):
    payload = {**VILLAGE_PAYLOAD, "groupement_id": 999999}
    response = client.post("/villages", json=payload)
    assert response.status_code == 400
    assert "Contrainte d'intégrité" in response.json()["detail"]
