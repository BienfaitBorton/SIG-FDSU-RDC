"""Tests National Coverage Intelligence (NCI)."""

from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
COVERAGE_DIR = PROJECT_ROOT / "data" / "coverage"


@pytest.fixture(scope="module")
def nci():
    from api.services import coverage_intelligence_service as svc

    return svc


def test_import_artifacts_exist():
    assert (COVERAGE_DIR / "manifest.json").exists()
    assert (COVERAGE_DIR / "aggregates.json").exists()
    assert (COVERAGE_DIR / "localities_uncovered.jsonl").exists()
    assert (COVERAGE_DIR / "localities_covered.jsonl").exists()
    assert (COVERAGE_DIR / "nci_config.json").exists()
    assert (COVERAGE_DIR / "quality_report.json").exists()


def test_national_counts(nci):
    stats = nci.statistics()
    kpis = stats["kpis"]
    assert kpis["localities_uncovered"] >= 24000
    assert kpis["localities_covered"] >= 4000
    assert kpis["population_uncovered"] > 50_000_000
    assert kpis["population_covered"] > 20_000_000
    assert kpis["population_remaining"] == kpis["population_uncovered"]


def test_aggregations_provinces_territories(nci):
    provinces = nci.list_provinces(limit=20)
    assert provinces["_meta"]["count"] > 0
    assert provinces["provinces"][0].get("population_uncovered") is not None

    territories = nci.list_territories(limit=50)
    assert territories["_meta"]["count"] > 0
    top = territories["territories"][0]
    assert "ndci" in top
    assert top["ndci"].get("index") is not None


def test_api_overview_and_filters(nci):
    overview = nci.overview()
    assert "national" in overview
    assert "/api/coverage/statistics" in overview["endpoints"]

    locs = nci.list_localities(status="uncovered", priority="High", limit=10)
    assert locs["_meta"]["total"] >= 0
    assert len(locs["localities"]) <= 10
    for row in locs["localities"]:
        assert row["priority"] == "High"
        assert row["coverage_status"] == "uncovered"


def test_population_priority_categories_infra(nci):
    pop = nci.population_payload()
    assert pop["national"]["population_covered"] > 0
    assert pop["national"]["population_remaining"] > 0

    pri = nci.priority_payload()
    assert "High" in pri["uncovered"] or "Low" in pri["uncovered"]

    cats = nci.categories_payload()
    assert cats["categories"]

    infra = nci.infrastructure_payload()
    assert infra["infra_types"]


def test_map_and_explain(nci):
    geo = nci.map_payload(status="uncovered", limit=50)
    assert geo["type"] == "FeatureCollection"
    assert len(geo["features"]) <= 50

    national = nci.explain_territory_index("__missing__")
    assert national["available"] is False

    # Use a real territory from aggregates
    by_t = nci.get_aggregates().get("by_territory") or {}
    name = next(iter(by_t))
    explained = nci.explain_territory_index(name)
    assert explained["available"] is True
    assert explained.get("ndci") is not None
    assert "population" in explained
    assert "priority" in explained
    assert "confidence_level" in explained


def test_ndci_config_weights(nci):
    cfg = nci.get_config()
    weights = cfg["national_digital_coverage_index"]["weights"]
    assert sum(weights.values()) == 100
    assert set(weights) >= {"population", "priority", "category", "distance", "infrastructure"}


def test_knowledge_hub_domain():
    from api.services import knowledge_hub_service

    domain = knowledge_hub_service.get_domain("national_coverage")
    assert domain is not None
    assert domain["domain"]["id"] == "national_coverage"
    assert "coverage" in domain
    assert domain["coverage"]["kpis"]["localities_uncovered"] > 0


def test_territorial_intelligence_coverage_section():
    from api.services import territorial_intelligence_service as tis

    # Dungu demo focus — coverage may or may not match name; use any master territory
    # Prefer a territory known in NCI aggregates
    from api.services import coverage_intelligence_service as nci

    by_t = nci.get_aggregates().get("by_territory") or {}
    sample_name = next(iter(by_t))
    cov = nci.get_territory_coverage(sample_name)
    assert cov is not None
    assert cov["territory"]["localities_uncovered"] >= 0

    # Profile via TI if Dungu resolves
    profile = tis.build_territorial_profile("TERRITOIRE-05-002")
    if profile:
        assert "coverage" in profile["sections"]
        assert "needs" in profile
        recs = tis.build_recommendations("TERRITOIRE-05-002")
        assert recs is not None
        assert "recommendations" in recs


def test_decision_engine_nci_context():
    from api.services import coverage_intelligence_service as nci

    explained = nci.explain_territory_index(next(iter(nci.get_aggregates()["by_territory"])))
    assert explained["available"]
    assert explained.get("why")
    assert "components" in explained


def test_edvs_charts(nci):
    charts = nci.edvs_charts()
    for key in ("kpis", "bars", "priority_split", "categories", "treemap", "heatmap", "radar", "waterfall"):
        assert key in charts
    assert len(charts["kpis"]) >= 4


def test_executive_cockpit_includes_nci():
    from api.services import executive_cockpit_service

    payload = executive_cockpit_service.build_cockpit_payload()
    kpi_ids = {k["id"] for k in payload.get("kpis") or []}
    assert "pop_covered_nci" in kpi_ids
    assert "pop_remaining_nci" in kpi_ids
    assert "loc_uncovered_nci" in kpi_ids
    assert payload.get("nci")
    assert payload.get("priority_split")
    assert payload.get("heatmap")
