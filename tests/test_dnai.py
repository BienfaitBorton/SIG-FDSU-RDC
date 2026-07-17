from fastapi.testclient import TestClient

from api.main import app
from api.services.dnai_service import default_dnai
from api.services.national_semantic_classification_engine import default_engine


def test_mandatory_normalizations_are_explainable():
    service = default_dnai()
    expected = {
        "EP1 MFUAMBA": "ÉCOLE PRIMAIRE 1 MFUAMBA",
        "E.P2 BASANGA": "ÉCOLE PRIMAIRE 2 BASANGA",
        "IT PAPA DIANGIENDA": "INSTITUT TECHNIQUE PAPA DIANGIENDA",
        "ISP NGANDANJIKA": "INSTITUT SUPÉRIEUR PÉDAGOGIQUE NGANDANJIKA",
        "ISP/ARU": "INSTITUT SUPÉRIEUR PÉDAGOGIQUE ARU",
        "ISTM KISANTU": "INSTITUT SUPÉRIEUR DES TECHNIQUES MÉDICALES KISANTU",
        "HOPITAL DR RAU": "HÔPITAL DR RAU",
        "BAT.ADM BOTOKU": "BÂTIMENT ADMINISTRATIF BOTOKU",
        "CS KIMBA": "COMPLEXE SCOLAIRE KIMBA",
        "CS DE SANTE KIMBA": "CENTRE DE SANTÉ KIMBA",
    }
    for source, target in expected.items():
        result = service.normalize(source, "CENI")
        assert result.normalized_text == target
        assert result.rule_id and result.regex and result.justification


def test_unknowns_and_technical_identifiers_are_never_invented():
    service = default_dnai()
    unknown = service.normalize("EDAC/ISGEA", "CENI")
    assert unknown.status == "À vérifier" and unknown.expansion is None
    for value in ("CENI-EP-001", "REF_EP_001", "CODE_EP2", "FDSU_EP_001"):
        result = service.normalize(value, "CENI")
        assert result.technical_identifier and result.expansion is None
        assert default_engine().classify(value, raw_properties={"referential": "CENI"}).normalized_category_code == "UNCLASSIFIED"


def test_dnai_drives_semantic_classification():
    engine = default_engine()
    cases = {
        "EP1 MFUAMBA": "SCHOOL",
        "IT PAPA DIANGIENDA": "SCHOOL",
        "ISP NGANDANJIKA": "HIGHER_EDUCATION",
        "CENTRE HOSPITALIER CAHI": "HEALTH_FACILITY",
        "HOPITAL DR RAU": "HEALTH_FACILITY",
        "BAT.ADM BOTOKU": "ADMINISTRATIVE_BUILDING",
        "CS KIMBA": "SCHOOL",
        "CS DE SANTE KIMBA": "HEALTH_FACILITY",
    }
    for source, category in cases.items():
        result = engine.classify(source, raw_properties={"referential": "CENI"})
        assert result.normalized_category_code == category
        assert result.confidence >= .95


def test_dnai_api_contract():
    client = TestClient(app)
    assert client.get("/api/dnai/statistics").json()["abbreviations"] >= 10
    assert client.get("/api/dnai/search", params={"q": "ISP"}).json()["count"] >= 1
    assert client.get("/api/dnai/expand/ISP", params={"referential": "CENI"}).json()["expansion"] == "INSTITUT SUPÉRIEUR PÉDAGOGIQUE"
    payload = client.post("/api/dnai/normalize", json={"text": "EP2 BASANGA", "referential": "CENI"})
    assert payload.status_code == 200 and payload.json()["normalized_text"] == "ÉCOLE PRIMAIRE 2 BASANGA"
    assert client.get("/api/dnai/discover", params={"limit": 3}).status_code == 200
    assert client.get("/api/dnai/pending-validations").json()["count"] >= 4
