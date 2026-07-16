"""Contrats NTIE v1 : multi-echelle, Data First et explicabilite."""

import pytest

from api.services import national_territorial_intelligence_engine as ntie


REAL_LEVEL_REFS = (
    ("PROVINCE-9", "Province"),
    ("TERRITOIRE-05-002", "Territoire"),
    ("SECTEUR-3", "Secteur"),
    ("CHEFFERIE-1", "Chefferie"),
    ("COLLECTIVITE-326", "Chefferie"),
    ("GROUPEMENT-1", "Groupement"),
    ("LOCALITE-64", "Village"),
)


@pytest.mark.parametrize(("entity_ref", "admin_type"), REAL_LEVEL_REFS)
def test_real_administrative_levels_have_traceable_profiles(entity_ref, admin_type):
    profile = ntie.build_profile(entity_ref)
    assert profile is not None
    assert profile["entity"]["admin_type"] == admin_type
    assert profile["_meta"]["data_first"] is True
    assert profile["_meta"]["no_invented_values"] is True
    assert len(profile["indicators"]) == len(ntie.DIMENSIONS)
    for indicator in profile["indicators"]:
        assert {"source", "version", "date", "confidence", "quality", "method"} <= indicator.keys()
        if indicator["value"] is None:
            assert indicator["status"] == "unavailable"


def test_dungu_population_coverage_and_registry_counts_are_federated():
    profile = ntie.build_profile("TERRITOIRE-05-002")
    indicators = profile["indicator_index"]
    assert indicators["population"]["value"] == 129675
    assert indicators["population_covered"]["value"] == 29172
    assert indicators["population_uncovered"]["value"] == 100503
    assert indicators["localities"]["value"] == 97
    assert indicators["fdsu_sites"]["source"] == "National FDSU Asset Registry"


def test_score_does_not_invent_weights_and_evolution_does_not_invent_impact():
    profile = ntie.build_profile("TERRITOIRE-05-002")
    assert profile["score"]["label"] == "Score indicatif"
    assert profile["score"]["value"] is None
    assert profile["score"]["weights"] is None
    assert profile["score"]["confidence_limited"] is True
    future = [row for row in profile["evolution"] if row["id"] != "today"]
    assert {row["id"] for row in future} == {"after_40", "after_300", "after_20476", "after_ccn"}
    assert all(row["projected_impact"] is None for row in future)
    assert all(row["coverage_rate_pct"] is None for row in future)


def test_ntie_api_contract(client):
    assert client.get("/territorial-profile").status_code == 200
    profile = client.get("/territorial-profile/TERRITOIRE-05-002")
    assert profile.status_code == 200
    assert profile.json()["_meta"]["engine"] == ntie.ENGINE_VERSION
    for suffix in ("score", "population", "coverage", "explainability", "evolution"):
        assert client.get(f"/territorial-profile/TERRITOIRE-05-002/{suffix}").status_code == 200
    assert client.get("/territorial-profile/UNKNOWN-999").status_code == 404


def test_catalog_rejects_unsupported_levels():
    with pytest.raises(ValueError):
        ntie.list_profiles(level="district")
