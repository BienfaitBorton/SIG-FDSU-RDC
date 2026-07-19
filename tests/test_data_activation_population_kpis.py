"""Data Activation Audit — KPI population Centre de Décision branchés sur NCI."""

from __future__ import annotations


def test_national_panel_population_kpis_from_nci():
    from api.services.coverage_intelligence_service import statistics
    from api.services.decision_engine_service import get_national_panel_payload

    nci = (statistics() or {}).get("kpis") or {}
    panel = get_national_panel_payload()
    kpis = panel.get("kpis") or {}

    covered = kpis.get("population_covered") or {}
    uncovered = kpis.get("population_uncovered") or {}

    assert covered.get("available") is True
    assert uncovered.get("available") is True
    assert covered.get("value") == int(nci["population_covered"])
    assert uncovered.get("value") == int(nci["population_uncovered"])
    assert covered["value"] > 20_000_000
    assert uncovered["value"] > 50_000_000


def test_explainable_kpis_expose_nci_population():
    from api.services.decision_demo_service import build_explainable_kpis

    kpis = build_explainable_kpis()
    covered = kpis["population_covered"]
    uncovered = kpis["population_uncovered"]

    assert covered["available"] is True
    assert uncovered["available"] is True
    assert covered["value"] == 20_690_227
    assert uncovered["value"] == 52_575_042
    blob = f"{covered.get('source_label') or ''} {covered.get('definition') or ''}"
    assert "Coverage Intelligence" in blob or "NCI" in blob


def test_sites_300_scores_available_for_activation():
    from api.services.decision_engine_service import list_site_scores

    payload = list_site_scores(program_code="PROG_SITES_300", limit=3)
    meta = payload.get("_meta") or {}
    sites = payload.get("sites") or []

    assert int(meta.get("total_filtered") or 0) == 300
    assert sites
    assert sites[0].get("priority_score") is not None
