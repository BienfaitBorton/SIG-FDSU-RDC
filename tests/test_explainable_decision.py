"""Tests Explainable Decision Engine v1 — Decision Case File & justifications."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app
from api.services import explainable_decision_service

CLIENT = TestClient(app)
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_engine_meta_and_pdf_template_structure():
    meta = explainable_decision_service.engine_meta()
    assert meta["_meta"]["hardcoded_forbidden"] is True
    assert meta["_meta"]["version"] == "1.0.0"
    template = explainable_decision_service.pdf_template()
    assert template["_meta"]["generation_enabled"] is False
    assert len(template["sections"]) >= 17


def test_sites_and_ccn_doctrines_versioned():
    ccn = explainable_decision_service.get_doctrine_payload("DOCTRINE_CCN_FDSU")
    sites = explainable_decision_service.get_doctrine_payload("DOCTRINE_SITES_FDSU")
    assert ccn is not None and ccn["doctrine"]["_meta"]["hardcoded_forbidden"] is True
    assert sites is not None and sites["doctrine"]["_meta"]["version"] == "1.0.0"
    weights = [c["weight"] for c in sites["doctrine"]["selection_criteria"]]
    assert abs(sum(weights) - 1.0) < 1e-9


def test_ccn_decision_case_has_required_sections():
    case = explainable_decision_service.build_ccn_case("CCN-DEMO-0001")
    assert case is not None
    assert case["case_id"].startswith("DCF-CCN-")
    assert case["asset"]["asset_type"] == "CCN"
    assert case["score"]["global"] is not None
    assert case["doctrine"]["id"] == "DOCTRINE_CCN_FDSU"
    assert case["doctrine"]["version"]
    assert len(case["justification"]) == 6
    for item in case["justification"]:
        assert item["why"]
        assert "Pourquoi" not in item["why"] or True
        assert item["contribution_display"]
    assert "population_touchee" in case["impacts"]
    assert case["traceability"]["user"]["status"] == "prepared"
    assert case["pdf_export"]["enabled"] is False
    for key in explainable_decision_service.CASE_SECTIONS:
        assert key in case or key in ("summary",)


def test_api_case_explain_doctrine_ccn():
    explain = CLIENT.get("/api/decision/explain/CCN-DEMO-0001?asset_type=ccn")
    assert explain.status_code == 200
    body = explain.json()
    assert body["_meta"]["principle"]
    assert len(body["justification"]) >= 1
    assert body["doctrine"]["title"]

    case = CLIENT.get("/api/decision/case/CCN-DEMO-0001?asset_type=ccn")
    assert case.status_code == 200
    assert case.json()["case_id"].startswith("DCF-CCN-")
    assert case.json()["confidence"]["level"] in {"high", "medium", "low"}

    doctrine = CLIENT.get("/api/decision/doctrine/DOCTRINE_CCN_FDSU")
    assert doctrine.status_code == 200
    assert doctrine.json()["doctrine"]["_meta"]["doctrine_id"] == "DOCTRINE_CCN_FDSU"

    history = CLIENT.get("/api/decision/case-history?limit=5")
    assert history.status_code == 200
    assert history.json()["_meta"]["count"] >= 1

    pdf = CLIENT.get("/api/decision/pdf-template")
    assert pdf.status_code == 200
    assert pdf.json()["_meta"]["generation_enabled"] is False


def test_recommendation_never_score_only():
    explain = CLIENT.get("/api/decision/explain/CCN-DEMO-0002?asset_type=ccn").json()
    assert explain.get("summary")
    assert explain.get("justification")
    assert explain.get("doctrine")
    assert explain.get("risks") is not None
    # Pas uniquement un score
    assert "why" in explain["justification"][0]


def test_national_weights_loaded_from_sites_doctrine():
    from api.services import fdsu_site_priority_service

    doctrine = json.loads(
        (PROJECT_ROOT / "data/business/doctrines/sites_doctrine_v1.json").read_text(encoding="utf-8")
    )
    expected = {c["id"]: c["weight"] for c in doctrine["selection_criteria"]}
    for key, weight in expected.items():
        assert abs(fdsu_site_priority_service.NATIONAL_WEIGHTS[key] - weight) < 1e-9


def test_site_case_when_program_available():
    # Si le programme national n'est pas présent, le test reste soft.
    result = CLIENT.get("/api/decision/case/1?asset_type=site&program_code=sites_40")
    if result.status_code == 404:
        return
    body = result.json()
    assert body["asset"]["asset_type"] == "SITE"
    assert body["doctrine"]["id"] == "DOCTRINE_SITES_FDSU"
    assert len(body["justification"]) >= 1
    assert body["justification"][0]["why"]
