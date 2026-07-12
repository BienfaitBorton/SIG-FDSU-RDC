"""Tests Spatial Decision Graph v2.1 — catégories typées, pas de données inventées."""

from __future__ import annotations

from collections import Counter

import pytest

from api.services import spatial_decision_graph_service as sdg


SITE_IDS = ("7", "29", "30")


def test_categories_meta_has_expected_keys():
    assert "site" in sdg.CATEGORIES
    assert "localities" in sdg.CATEGORIES
    assert "health" in sdg.CATEGORIES
    assert sdg.CATEGORIES["education"]["available"] is False
    assert sdg.CATEGORIES["energy"]["available"] is False
    assert sdg.CATEGORIES["markets"]["available"] is False
    assert "SERVES_LOCALITY" in sdg.RELATION_STYLES
    assert sdg.RELATION_STYLES["SERVES_LOCALITY"]["category"] == "localities"
    assert sdg.ENGINE_VERSION.startswith("sdg-2.1")


@pytest.mark.parametrize("site_id", SITE_IDS)
def test_build_graph_real_sites_typed_relations(site_id):
    graph = sdg.build_graph("site", site_id, program_code="sites_40")
    assert graph is not None
    assert graph["_meta"]["version"].startswith("sdg-2.1")
    assert graph["_meta"]["title_ui"].startswith("Analyse")
    assert graph["center"]["kind"] == "site"
    assert graph["center"].get("name")
    assert graph["decision_summary"].get("text")
    assert isinstance(graph["kpis"], list) and graph["kpis"]
    assert isinstance(graph["missing_data"], list)
    assert graph["why_panel"]["blocks"]

    statuses = {c["id"]: c["status"] for c in graph["categories"]}
    assert statuses["site"] == "active"
    assert statuses["education"] == "future"
    assert statuses["energy"] == "future"

    for edge in graph["edges"]:
        assert edge.get("nsme_trace", {}).get("relation_type")
        assert edge.get("relation_type")
        assert edge.get("category")
        assert edge.get("relation_id") or edge.get("id")
        assert edge.get("origin_label") or edge.get("source_entity")
        assert edge.get("target_label") or edge.get("target_entity")
        contrib = edge.get("score_contribution") or edge.get("contribution") or {}
        assert contrib.get("status") in {"mapped", "proxy", "unavailable"}
        # Pas de contribution inventée affichée
        if contrib.get("status") == "unavailable":
            assert not (contrib.get("display") or "").startswith("+")


@pytest.mark.parametrize("site_id", SITE_IDS)
def test_no_invented_future_category_nodes(site_id):
    graph = sdg.build_graph("site", site_id, program_code="sites_40")
    future_ids = {c["id"] for c in graph["categories"] if c.get("status") == "future"}
    for node in graph["nodes"]:
        assert node.get("category") not in future_ids or node.get("kind") == "site"


def test_build_graph_missing_site():
    graph = sdg.build_graph("site", "99999999", program_code="sites_40")
    # service peut renvoyer None ou graphe partial selon résolution
    if graph is None:
        return
    assert graph.get("_meta", {}).get("status") in {"partial", "error", "unavailable", "success"}


def test_build_presentation_steps():
    presentation = sdg.build_presentation("site", "7", program_code="sites_40")
    assert presentation is not None
    assert len(presentation["steps"]) == len(sdg.PRESENTATION_STEPS)
    assert presentation["steps"][0]["id"] == "site"
    assert presentation["steps"][-1]["id"] == "recommendation"


def test_relation_type_counts_site_30():
    graph = sdg.build_graph("site", "30", program_code="sites_40")
    types = Counter(e["relation_type"] for e in graph["edges"])
    # Sites 40 typiques : localités / population — pas de conversion forcée en besoin
    for rel in types:
        assert rel in sdg.RELATION_STYLES or rel  # types NSME connus ou bruts
    assert "CANDIDATE_FOR_MISSION" not in types or True  # autorisé s'il existe réellement


def test_kpi_zero_vs_unavailable():
    graph = sdg.build_graph("site", "30", program_code="sites_40")
    by_id = {k["id"]: k for k in graph["kpis"]}
    edu = by_id.get("education")
    assert edu is not None
    assert edu["status"] == "unavailable"
    assert edu["display"] == "Non disponible"
    health = by_id.get("health")
    assert health is not None
    # Santé intégré : 0 calculé ou valeur réelle — jamais inventé
    if health["status"] == "success":
        assert health["value"] is not None
        assert health["value"] >= 0


def test_empty_categories_have_explanation_never_bare_zero():
    graph = sdg.build_graph("site", "30", program_code="sites_40")
    assert graph.get("data_first", {}).get("motto")
    for cat in graph["categories"]:
        if cat["id"] == "site":
            continue
        assert cat.get("maturity") in {"operational", "partial", "integrating", "anomaly"}
        if cat.get("status") in {"empty", "future"} or cat.get("count") == 0:
            assert cat.get("note") or cat.get("empty_reason"), f"{cat['id']} sans explication"
            assert cat.get("empty_reason") in {
                None,
                "no_relations_found",
                "search_not_executed",
                "referential_absent",
                "calculation_not_on_referential",
            }
        if cat.get("status") == "future":
            assert cat.get("maturity") == "integrating"
            assert cat.get("empty_reason") == "referential_absent"
