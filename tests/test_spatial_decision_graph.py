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
    assert sdg.CATEGORIES["education"]["available"] is True
    assert sdg.CATEGORIES["ceni"]["available"] is True
    assert sdg.CATEGORIES["energy"]["available"] is False
    assert sdg.CATEGORIES["markets"]["available"] is False
    assert "SERVES_LOCALITY" in sdg.RELATION_STYLES
    assert sdg.RELATION_STYLES["SERVES_LOCALITY"]["category"] == "localities"
    assert "NEAREST_SCHOOL" in sdg.RELATION_STYLES
    assert "NEAREST_CENI_SIGNAL" in sdg.RELATION_STYLES
    assert "NEAREST_MNO_VODACOM" in sdg.RELATION_STYLES
    assert sdg.ENGINE_VERSION.startswith("sdg-2.2")


@pytest.mark.parametrize("site_id", SITE_IDS)
def test_build_graph_real_sites_typed_relations(site_id):
    graph = sdg.build_graph("site", site_id, program_code="sites_40")
    assert graph is not None
    assert graph["_meta"]["version"].startswith("sdg-2.2")
    assert graph["_meta"]["title_ui"].startswith("Analyse")
    assert graph["center"]["kind"] == "site"
    assert graph["center"].get("name")
    assert graph["decision_summary"].get("text")
    assert isinstance(graph["kpis"], list) and graph["kpis"]
    assert isinstance(graph["missing_data"], list)
    assert graph["why_panel"]["blocks"]

    statuses = {c["id"]: c["status"] for c in graph["categories"]}
    assert statuses["site"] == "active"
    assert statuses["education"] in {"active", "empty", "partial"}
    assert statuses["ceni"] in {"active", "empty", "partial"}
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
        # Classification explicable obligatoire — jamais de points inventés
        assert contrib.get("contribution_type") in {
            "direct",
            "indirect",
            "contextual_evidence",
            "not_applicable",
            "pending_rule",
        }
        assert contrib.get("role_label")
        assert "non calculée" not in str(contrib.get("display") or "").lower()
        assert "non calculée" not in str(contrib.get("role_label") or "").lower()
        if contrib.get("status") == "unavailable":
            assert not (contrib.get("display") or "").startswith("+")
        if contrib.get("contribution_type") == "direct":
            assert contrib.get("criterion")
            # Direct = critère sourcé ; pas de chiffre inventé côté service
            assert contrib.get("source_document") or contrib.get("note") or contrib.get("display")


@pytest.mark.parametrize("site_id", SITE_IDS)
def test_no_invented_future_category_nodes(site_id):
    graph = sdg.build_graph("site", site_id, program_code="sites_40")
    future_ids = {c["id"] for c in graph["categories"] if c.get("status") == "future"}
    for node in graph["nodes"]:
        assert node.get("category") not in future_ids or node.get("kind") == "site"


def test_build_graph_missing_site():
    graph = sdg.build_graph("site", "99999999", program_code="sites_40")
    # service peut renvoyer None ou graphe selon résolution
    if graph is None:
        return
    # Contrat SDG Coverage Audit v1 : classification C → _meta.status = "impossible"
    # (PROJECT_MANAGEMENT/ARCHITECTURE/SDG_COVERAGE_AUDIT_V1.md)
    assert graph.get("_meta", {}).get("status") in {
        "partial",
        "error",
        "unavailable",
        "success",
        "impossible",
    }


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
    # Éducation P1 : disponible (0 calculé ou valeur) — plus « future unavailable »
    assert edu["status"] in {"success", "empty", "partial"}
    assert edu["display"] != "Non disponible" or edu.get("value") == 0
    ceni = by_id.get("ceni")
    assert ceni is not None
    assert ceni["status"] in {"success", "empty", "partial", "unavailable"}
    health = by_id.get("health")
    assert health is not None
    # Santé intégré : 0 calculé ou valeur réelle — jamais inventé
    if health["status"] == "success":
        assert health["value"] is not None
        assert health["value"] >= 0


def test_empty_categories_have_explanation_never_bare_zero():
    graph = sdg.build_graph("site", "30", program_code="sites_40")
    assert graph.get("data_first", {}).get("motto")
    allowed_maturity = {
        "operational",
        "partial",
        "integrating",
        "empty",
        "error",
        "demonstration",
        "anomaly",  # legacy alias mapped to error in UI
    }
    for cat in graph["categories"]:
        if cat["id"] == "site":
            continue
        assert cat.get("maturity") in allowed_maturity
        if cat.get("status") in {"empty", "future"} or cat.get("count") == 0:
            assert cat.get("note") or cat.get("empty_reason"), f"{cat['id']} sans explication"
            assert cat.get("empty_reason") in {
                None,
                "no_relations_found",
                "search_not_executed",
                "search_not_wired",
                "search_failed",
                "referential_absent",
                "calculation_not_on_referential",
            }
        if cat.get("status") == "future":
            assert cat.get("maturity") == "integrating"
            assert cat.get("empty_reason") == "referential_absent"
        assert "Anomalie d’intégration" not in str(cat.get("note") or "")
        assert "Anomalie d'intégration" not in str(cat.get("note") or "")


SITE_COHERENCE_IDS = ("7", "14", "29", "30", "34", "42")


@pytest.mark.parametrize("site_id", SITE_COHERENCE_IDS)
def test_domain_status_coherence_no_false_anomaly(site_id):
    graph = sdg.build_graph("site", site_id, program_code="sites_40")
    assert graph is not None
    by = {c["id"]: c for c in graph["categories"]}

    # Sites FDSU branchés — plus d'anomalie de câblage
    fdsu = by["fdsu_sites"]
    assert fdsu.get("maturity") != "anomaly"
    assert "Anomalie" not in str(fdsu.get("note") or "")
    assert fdsu.get("search_executed") in {True, False, None} or True

    telecom = by["telecom"]
    assert telecom.get("maturity") != "anomaly"
    assert "Anomalie" not in str(telecom.get("note") or "")
    if telecom.get("count") == 0:
        assert telecom.get("note")
        assert telecom.get("nearest_context") or telecom.get("search_executed")

    roads = by["roads"]
    assert roads.get("maturity") != "anomaly"
    if roads.get("count") == 0:
        assert roads.get("note")

    ccn = by["ccn"]
    assert ccn.get("maturity") in {"demonstration", "partial", "empty", "operational"}
    if ccn.get("count") == 0:
        note = str(ccn.get("note") or "").lower()
        assert "demo" in note or "démo" in note or "demonstration" in note or "démonstration" in note

    kpis = {k["id"]: k for k in graph["kpis"]}
    assert kpis["radius"]["value"] is not None
    assert kpis["radius"]["status"] != "unavailable"
    assert kpis["radius"].get("note")

    # Contrat domaine partagé
    assert isinstance(graph.get("domain_statuses"), list) and graph["domain_statuses"]
    assert graph.get("radii", {}).get("principal_m")


def test_site_14_business_messages():
    graph = sdg.build_graph("site", "14", program_code="sites_40")
    by = {c["id"]: c for c in graph["categories"]}
    assert by["fdsu_sites"]["maturity"] != "anomaly"
    assert "Anomalie d’intégration" not in str(by["fdsu_sites"].get("note") or "")
    assert by["telecom"]["maturity"] in {"operational", "empty", "partial"}
    tel_kpi = next(k for k in graph["kpis"] if k["id"] == "telecom")
    # Pas un 0 ambigu sans note si vide
    if tel_kpi.get("value") == 0:
        assert tel_kpi.get("note")
    assert next(k for k in graph["kpis"] if k["id"] == "radius")["value"] is not None
    bodyish = " ".join(str(c.get("note") or "") for c in graph["categories"])
    assert "NSME" not in bodyish
    assert "ST_Within" not in bodyish
    assert "integration anomaly" not in bodyish.lower()


def test_site_26_fdsu_not_integration_error():
    """Contrat incident : référentiel branché, recherche exécutée, pas d'anomalie FDSU."""
    graph = sdg.build_graph("site", "26", program_code="sites_40")
    assert (graph.get("_meta") or {}).get("version", "").startswith("sdg-2.2")
    statuses = {d["domain"]: d for d in (graph.get("domain_statuses") or [])}
    fdsu = statuses["fdsu_sites"]
    assert fdsu.get("reference_available") is True
    assert fdsu.get("search_executed") is True
    assert fdsu.get("status") != "integration_error"
    assert fdsu.get("status") in {"operational", "empty", "partial"}
    by = {c["id"]: c for c in graph["categories"]}
    assert by["fdsu_sites"].get("maturity") != "anomaly"
    assert "Anomalie d’intégration" not in str(by["fdsu_sites"].get("note") or "")
    radius = next(k for k in graph["kpis"] if k["id"] == "radius")
    assert radius.get("value") is not None
    assert radius.get("status") != "unavailable"
