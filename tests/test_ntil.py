from fastapi.testclient import TestClient

from api.main import app
from api.services.dnai_service import default_dnai
from api.services.ntil_service import default_ntil


def test_ntr_contract_and_governance():
    service = default_ntil()
    assert service.registry["_meta"]["raw_sources_modified"] is False
    assert service.registry["workflow_states"] == ["DÉCOUVERT", "EN ANALYSE", "EN VALIDATION", "VALIDÉ", "PUBLIÉ", "DÉPRÉCIÉ"]
    required = {"id", "term", "type", "category", "family", "expansion", "status", "confidence", "referentials", "first_seen", "last_seen", "last_validation", "source", "version", "comments", "original_text", "normalized_text", "rule", "context", "justification"}
    assert all(required <= term.keys() for term in service.terms)
    assert all(term["expansion"] is None for term in service.terms if term["term"] in {"EDAC", "ISGEA", "IS", "ISIPA"})


def test_mandatory_terms_and_contexts_are_registered():
    service = default_ntil()
    assert {"EP", "IT", "ISP", "ISTM", "HOPITAL", "EDAC", "ISGEA", "CS", "HGR", "BAT.ADM"} <= {term["term"] for term in service.terms}
    cs = [term for term in service.terms if term["term"] == "CS"]
    assert {term["expansion"] for term in cs} == {"COMPLEXE SCOLAIRE", "CENTRE DE SANTÉ"}
    assert service.term("NTR-EDAC")["status"] == "EN VALIDATION"


def test_quality_engine_is_bounded_and_explainable():
    quality = default_ntil().quality()
    assert 0 <= quality["terminology_quality_score"] <= 100
    assert quality["quality_by_referential"][0]["referential"] == "CENI"
    assert set(quality["metrics"]) == {"normalization_rate", "recognition_rate", "ambiguity_resolution_rate", "unknown_term_rate", "validation_rate", "average_confidence"}
    assert quality["formula"]


def test_discovery_comparison_only_creates_proposals():
    result = default_ntil().compare_discoveries(["EDAC/ISGEA", "NOUV SIGLE XYZ"], "CENI")
    assert result["proposals"]
    assert all(item["publication_automatic"] is False for item in result["proposals"])
    assert all(item["proposed_state"] in {"DÉCOUVERT", "EN ANALYSE"} for item in result["proposals"])


def test_technical_identifiers_remain_excluded_through_ntil_stack():
    for value in ("REF_EP_001", "CENI-EP-001"):
        result = default_dnai().normalize(value, "CENI")
        assert result.technical_identifier and result.expansion is None


def test_all_ntil_api_routes():
    client = TestClient(app)
    assert client.get("/api/ntil/statistics").status_code == 200
    registry = client.get("/api/ntil/registry", params={"q": "ISP"}).json()
    assert registry["total"] >= 1
    assert client.get("/api/ntil/term/NTR-ISP").json()["term"]["expansion"] == "INSTITUT SUPÉRIEUR PÉDAGOGIQUE"
    assert client.get("/api/ntil/term/ABSENT").status_code == 404
    assert client.get("/api/ntil/discoveries").json()["publication_automatic"] is False
    assert client.get("/api/ntil/quality").json()["terminology_quality_score"] > 0
    assert client.get("/api/ntil/history").json()["count"] >= 1
    assert client.get("/api/ntil/families").json()["count"] >= 4
    assert client.get("/api/ntil/dashboard").status_code == 200
