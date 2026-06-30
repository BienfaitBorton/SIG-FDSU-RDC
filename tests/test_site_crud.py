from tests.test_village_crud import VILLAGE_PAYLOAD, create_groupement

SITE_PAYLOAD = {
    "nom": "Site Test",
    "zone_fdsu": "ND",
    "operateur": "Vodacom",
    "technologie": "4G",
    "energie": "Fibre",
    "statut": "Actif",
    "date_creation": "2026-01-01",
    "date_installation": "2026-02-01",
    "date_mise_service": "2026-03-01",
    "altitude": 1000.0,
    "precision_gps": 5.0,
    "observations": "Site de test",
    "latitude": -4.4419,
    "longitude": 15.2663,
}

UPDATED_SITE_PAYLOAD = {
    "nom": "Site mis à jour",
    "zone_fdsu": "SD",
    "operateur": "Airtel",
    "technologie": "5G",
    "energie": "Solaire",
    "statut": "Maintenance",
    "date_creation": "2026-05-01",
    "date_installation": "2026-06-01",
    "date_mise_service": "2026-07-01",
    "altitude": 1200.0,
    "precision_gps": 3.0,
    "observations": "Site mis à jour",
    "latitude": -4.4420,
    "longitude": 15.2670,
}


def create_village(client):
    groupement = create_groupement(client)
    payload = {**VILLAGE_PAYLOAD, "groupement_id": groupement["id"]}
    response = client.post("/villages", json=payload)
    assert response.status_code == 200
    return response.json()


def test_site_crud_and_code_generation(client):
    village = create_village(client)
    payload = {**SITE_PAYLOAD, "village_id": village["id"]}
    response = client.post("/sites", json=payload)
    assert response.status_code == 200
    site = response.json()
    assert site["village_id"] == village["id"]
    assert site["code_site"].startswith("FDSU_")

    site_id = site["id"]
    response = client.get(f"/sites/{site_id}")
    assert response.status_code == 200

    response = client.put(
        f"/sites/{site_id}",
        json={**UPDATED_SITE_PAYLOAD, "village_id": village["id"]},
    )
    assert response.status_code == 200
    assert response.json()["operateur"] == UPDATED_SITE_PAYLOAD["operateur"]
    assert response.json()["code_site"] == site["code_site"]

    response = client.delete(f"/sites/{site_id}")
    assert response.status_code == 200
    assert response.json() == {"deleted": True}

    response = client.get(f"/sites/{site_id}")
    assert response.status_code == 404


def test_site_foreign_key_constraint(client):
    payload = {**SITE_PAYLOAD, "village_id": 999999}
    response = client.post("/sites", json=payload)
    assert response.status_code == 400
    assert "Impossible de générer code_site" in response.json()["detail"]
