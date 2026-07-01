from datetime import date

import pytest

PROVINCE_PAYLOAD = {
    "nom": "Province Test",
    "code": "11",
    "zone": "ND",
    "chef_lieu": "Testville",
    "population": 123456,
    "superficie": 789.5,
}

TERRITOIRE_PAYLOAD = {
    "nom": "Territoire Test",
    "code": "145",
    "chef_lieu": "Territoireville",
}

COLLECTIVITE_PAYLOAD = {
    "nom": "Collectivité Test",
    "code": "001",
    "type_collectivite": "Secteur",
}

GROUPEMENT_PAYLOAD = {
    "nom": "Groupement Test",
    "code": "001",
}

VILLAGE_PAYLOAD = {
    "nom": "Village Test",
    "code": "001",
}

SITE_PAYLOAD = {
    "nom": "Site Test",
    "code_fdsu": "FDSU_ND_11_145_001_001",
    "zone_fdsu": "ND",
    "statut": "Actif",
    "type_site": "BTS",
    "operateur": "Vodacom",
    "technologie": "4G",
    "alimentation": "Solaire",
    "adresse": "Avenue du Centre, Village Test",
    "date_creation": "2026-01-01",
    "date_installation": "2026-02-01",
    "date_mise_service": "2026-03-01",
    "hauteur_pylone": 30.5,
    "capacite": 500,
    "altitude": 1000.0,
    "precision_gps": 5.0,
    "observations": "Site de test",
    "latitude": -4.4419,
    "longitude": 15.2663,
}

MISSION_PAYLOAD = {
    "titre": "Mission Test",
    "description": "Mission de vérification",
    "date_debut": "2026-04-01",
    "date_fin": "2026-04-15",
}

DOCUMENT_PAYLOAD = {
    "nom": "Rapport Test",
    "type": "PDF",
    "chemin": "/tmp/rapport_test.pdf",
}

PHOTO_PAYLOAD = {
    "nom": "Photo Test",
    "caption": "Photo du site",
    "chemin": "/tmp/photo_test.jpg",
}


def create_province(client):
    response = client.post("/provinces", json=PROVINCE_PAYLOAD)
    assert response.status_code == 200
    return response.json()


def create_territoire(client, province_id: int):
    payload = {**TERRITOIRE_PAYLOAD, "province_id": province_id}
    response = client.post("/territoires", json=payload)
    assert response.status_code == 200
    return response.json()


def create_collectivite(client, territoire_id: int):
    payload = {**COLLECTIVITE_PAYLOAD, "territoire_id": territoire_id}
    response = client.post("/collectivites", json=payload)
    assert response.status_code == 200
    return response.json()


def create_groupement(client, collectivite_id: int):
    payload = {**GROUPEMENT_PAYLOAD, "collectivite_id": collectivite_id}
    response = client.post("/groupements", json=payload)
    assert response.status_code == 200
    return response.json()


def create_village(client, groupement_id: int):
    payload = {**VILLAGE_PAYLOAD, "groupement_id": groupement_id}
    response = client.post("/villages", json=payload)
    assert response.status_code == 200
    return response.json()


def create_site(client, village_id: int):
    payload = {**SITE_PAYLOAD, "village_id": village_id}
    response = client.post("/sites", json=payload)
    assert response.status_code == 200
    return response.json()


def create_mission(client, site_id: int):
    payload = {**MISSION_PAYLOAD, "site_id": site_id}
    response = client.post("/missions", json=payload)
    assert response.status_code == 200
    return response.json()


def create_document(client, mission_id: int):
    payload = {**DOCUMENT_PAYLOAD, "mission_id": mission_id}
    response = client.post("/documents", json=payload)
    assert response.status_code == 200
    return response.json()


def create_photo(client, mission_id: int):
    payload = {**PHOTO_PAYLOAD, "mission_id": mission_id}
    response = client.post("/photos", json=payload)
    assert response.status_code == 200
    return response.json()


def test_full_administrative_hierarchy_and_site_crud(client):
    province = create_province(client)
    assert province["nom"] == PROVINCE_PAYLOAD["nom"]
    assert province["code"] == PROVINCE_PAYLOAD["code"]

    territoire = create_territoire(client, province["id"])
    assert territoire["province_id"] == province["id"]

    collectivite = create_collectivite(client, territoire["id"])
    assert collectivite["territoire_id"] == territoire["id"]

    groupement = create_groupement(client, collectivite["id"])
    assert groupement["collectivite_id"] == collectivite["id"]

    village = create_village(client, groupement["id"])
    assert village["groupement_id"] == groupement["id"]

    site = create_site(client, village["id"])
    assert site["village_id"] == village["id"]
    assert site["code_site"].startswith("FDSU_")
    assert site["statut"] == SITE_PAYLOAD["statut"]

    response = client.get(f"/sites/{site['id']}")
    assert response.status_code == 200
    assert response.json()["code_site"] == site["code_site"]

    updated_payload = {**SITE_PAYLOAD, "village_id": village["id"], "operateur": "Airtel"}
    response = client.put(f"/sites/{site['id']}", json=updated_payload)
    assert response.status_code == 200
    assert response.json()["operateur"] == "Airtel"
    assert response.json()["code_site"] == site["code_site"]

    response = client.get("/sites")
    assert response.status_code == 200
    assert any(item["id"] == site["id"] for item in response.json())

    delete_response = client.delete(f"/sites/{site['id']}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"deleted": True}

    response = client.get(f"/sites/{site['id']}")
    assert response.status_code == 404


def test_mission_document_and_photo_crud(client):
    province = create_province(client)
    territoire = create_territoire(client, province["id"])
    collectivite = create_collectivite(client, territoire["id"])
    groupement = create_groupement(client, collectivite["id"])
    village = create_village(client, groupement["id"])
    site = create_site(client, village["id"])

    mission = create_mission(client, site["id"])
    assert mission["titre"] == MISSION_PAYLOAD["titre"]
    assert mission["site_id"] == site["id"]

    document = create_document(client, mission["id"])
    assert document["nom"] == DOCUMENT_PAYLOAD["nom"]
    assert document["mission_id"] == mission["id"]
    assert "created_at" in document

    photo = create_photo(client, mission["id"])
    assert photo["nom"] == PHOTO_PAYLOAD["nom"]
    assert photo["mission_id"] == mission["id"]
    assert "created_at" in photo

    updated_mission_payload = {**MISSION_PAYLOAD, "site_id": site["id"], "titre": "Mission Mise à jour"}
    response = client.put(f"/missions/{mission['id']}", json=updated_mission_payload)
    assert response.status_code == 200
    assert response.json()["titre"] == "Mission Mise à jour"

    updated_document_payload = {**DOCUMENT_PAYLOAD, "mission_id": mission["id"], "nom": "Document Mis à jour"}
    response = client.put(f"/documents/{document['id']}", json=updated_document_payload)
    assert response.status_code == 200
    assert response.json()["nom"] == "Document Mis à jour"

    updated_photo_payload = {**PHOTO_PAYLOAD, "mission_id": mission["id"], "nom": "Photo Mise à jour"}
    response = client.put(f"/photos/{photo['id']}", json=updated_photo_payload)
    assert response.status_code == 200
    assert response.json()["nom"] == "Photo Mise à jour"

    response = client.get("/missions")
    assert response.status_code == 200
    assert any(item["id"] == mission["id"] for item in response.json())

    response = client.get("/documents")
    assert response.status_code == 200
    assert any(item["id"] == document["id"] for item in response.json())

    response = client.get("/photos")
    assert response.status_code == 200
    assert any(item["id"] == photo["id"] for item in response.json())

    delete_response = client.delete(f"/photos/{photo['id']}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"deleted": True}

    delete_response = client.delete(f"/documents/{document['id']}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"deleted": True}

    delete_response = client.delete(f"/missions/{mission['id']}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"deleted": True}

    response = client.get(f"/missions/{mission['id']}")
    assert response.status_code == 404
