"""Tests unitaires Spatial Decision Graph v2.0."""

from __future__ import annotations

from api.services import spatial_decision_graph_service as sdg


def test_categories_meta_has_expected_keys():
    assert "site" in sdg.CATEGORIES
    assert "localities" in sdg.CATEGORIES
    assert "health" in sdg.CATEGORIES
    assert sdg.CATEGORIES["education"]["available"] is False
    assert "SERVES_LOCALITY" in sdg.RELATION_STYLES
    assert sdg.RELATION_STYLES["SERVES_LOCALITY"]["category"] == "localities"


def test_build_graph_nsme_only_no_invented_edges():
    graph = sdg.build_graph("site", "7", program_code="sites_40")
    assert graph is not None
    assert graph["_meta"]["title_ui"].startswith("Analyse")
    assert graph["center"]["kind"] == "site"
    assert graph["why_panel"]["blocks"]
    for edge in graph["edges"]:
        assert edge.get("nsme_trace", {}).get("relation_type")
        assert edge.get("relation_type")
        # pas de contribution inventée au-delà des statuts autorisés
        assert edge.get("contribution", {}).get("status") in {"mapped", "proxy", "unavailable"}


def test_build_presentation_steps():
    presentation = sdg.build_presentation("site", "7", program_code="sites_40")
    assert presentation is not None
    assert len(presentation["steps"]) == len(sdg.PRESENTATION_STEPS)
    assert presentation["steps"][0]["id"] == "site"
    assert presentation["steps"][-1]["id"] == "recommendation"
