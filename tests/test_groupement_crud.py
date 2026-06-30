from tests.test_collectivite_crud import COLLECTIVITE_PAYLOAD, create_territoire

GROUPEMENT_PAYLOAD = {
    "nom": "Groupement Test",
    "code": "001",
}

UPDATED_GROUPEMENT_PAYLOAD = {
    "nom": "Groupement Mis à jour",
    "code": "002",
}


def create_collectivite(client):
    territoire = create_territoire(client)
    payload = {**COLLECTIVITE_PAYLOAD, "territoire_id": territoire["id"]}
    response = client.post("/collectivites", json=payload)
    assert response.status_code == 200
    return response.json()


def test_groupement_crud_and_relationship(client):
    collectivite = create_collectivite(client)
    payload = {**GROUPEMENT_PAYLOAD, "collectivite_id": collectivite["id"]}
    response = client.post("/groupements", json=payload)
    assert response.status_code == 200
    groupement = response.json()
    assert groupement["collectivite_id"] == collectivite["id"]

    groupement_id = groupement["id"]
    response = client.get(f"/groupements/{groupement_id}")
    assert response.status_code == 200

    response = client.put(
        f"/groupements/{groupement_id}",
        json={**UPDATED_GROUPEMENT_PAYLOAD, "collectivite_id": collectivite["id"]},
    )
    assert response.status_code == 200
    assert response.json()["code"] == UPDATED_GROUPEMENT_PAYLOAD["code"]

    response = client.delete(f"/groupements/{groupement_id}")
    assert response.status_code == 200
    assert response.json() == {"deleted": True}

    response = client.get(f"/groupements/{groupement_id}")
    assert response.status_code == 404


def test_groupement_foreign_key_constraint(client):
    payload = {**GROUPEMENT_PAYLOAD, "collectivite_id": 999999}
    response = client.post("/groupements", json=payload)
    assert response.status_code == 400
    assert "Contrainte d'intégrité" in response.json()["detail"]
