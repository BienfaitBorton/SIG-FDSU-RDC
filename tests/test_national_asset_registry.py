"""Contrats National FDSU Asset Registry v1 — Data First."""

from api.services import national_asset_registry_service as registry


def test_manifest_prepares_all_asset_types_without_inventing_counts():
    manifest = registry.manifest()
    codes = {item["code"] for item in manifest["asset_types"]}
    assert {"FDSU_SITE", "CCN", "TELECOM", "HEALTH", "EDUCATION", "ENERGY", "ROAD", "POPULATION", "LOCALITY", "ECONOMIC_CORRIDOR", "PRIORITY_ZONE"} <= codes
    stats = registry.statistics()
    planned = {item["code"]: item for item in stats["asset_types"]}
    assert planned["EDUCATION"]["count"] is None
    assert planned["ENERGY"]["count"] is None


def test_real_program_counts_and_governance():
    stats = registry.statistics()
    assert stats["by_program"]["sites_40"] == 40
    assert stats["by_program"]["sites_300"] == 300
    assert stats["by_program"]["sites_20476"] == 20476
    assert stats["total_assets"] >= 20816
    assert stats["population"]["coverage_national"] is None


def test_asset_identity_territory_population_and_ccn_structure():
    payload = registry.list_assets(program="sites_20476", limit=1)
    asset = payload["assets"][0]
    assert asset["uuid"] and asset["business_code"] and asset["source"]["path"]
    assert asset["program"] == "sites_20476"
    assert asset["territory"]["province"]
    assert asset["location"]["latitude"] is not None
    assert "covered" in asset["population"]
    assert asset["ccn_readiness"]["status"] == "structure_prepared_no_ccn_engine"


def test_relationships_lifecycle_and_explainability_reference_existing_engines():
    asset = registry.list_assets(program="sites_40", limit=1)["assets"][0]
    relations = registry.relationships(asset["uuid"])
    assert relations and relations["count"] >= 1
    assert all(item["source"] for item in relations["relationships"])
    lifecycle = registry.lifecycle(asset["uuid"])
    assert lifecycle and lifecycle["_meta"]["engine"].startswith("ple-")
    explain = registry.explainability(asset["uuid"], field="population")
    assert explain["source"]["path"]
    assert explain["calculation"] is None


def test_registry_api_contract(client):
    assert client.get("/registry/manifest").status_code == 200
    stats = client.get("/registry/statistics")
    assert stats.status_code == 200
    assert stats.json()["by_program"]["sites_20476"] == 20476
    assets = client.get("/registry/assets", params={"program": "sites_300", "limit": 2})
    assert assets.status_code == 200
    first = assets.json()["assets"][0]
    asset_id = first["uuid"]
    for suffix in ("", "/relationships", "/population", "/lifecycle", "/impact", "/explainability"):
        assert client.get(f"/registry/assets/{asset_id}{suffix}").status_code == 200


def test_ccn_assets_remain_explicitly_demonstration():
    payload = registry.list_assets(program="ccn", limit=20)
    assert payload["_meta"]["total"] >= 1
    assert all(item["data_status"] == "demonstration" for item in payload["assets"])
    assert all(item["confidence"] == "low" for item in payload["assets"])
