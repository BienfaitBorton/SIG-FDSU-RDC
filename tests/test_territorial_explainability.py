"""Tests Territorial Explainability & Drill-down v1.0."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app
from api.services import territorial_explainability_service as tex
from api.services import territorial_intelligence_service as tis

CLIENT = TestClient(app)

TERRITORIES = ("TERRITOIRE-05-002", "AKETI", "BASANKUSU", "BUKAMA")
INTERNAL_CODES = ("unmatched_needs", "true", "false")


def _assert_domain_contract(payload: dict, *, domain: str) -> None:
    assert payload is not None
    assert payload["domain"] == domain or payload["domain"].startswith("sites") or payload["domain"] in {
        "admin",
        "localites",
        "groupements",
        "collectivites",
        "ccn",
        "fiber",
        "health",
        "routes",
        "telecom",
        "programs",
    }
    summary = payload["summary"]
    assert "count" in summary
    assert summary.get("status")
    assert summary.get("source")
    assert summary.get("confidence") in {"high", "medium", "low"}
    assert summary.get("headline")
    assert summary.get("business_impact")
    assert summary.get("recommendation")
    assert isinstance(payload.get("breakdown"), list)
    assert isinstance(payload.get("top_items"), list)
    assert isinstance(payload.get("actions"), list)
    assert payload["actions"], "actions must be non-empty (no decorative empty CTA set)"
    # Métier : headline/impact ne doivent pas exposer les codes internes bruts
    blob = f"{summary['headline']} {summary['business_impact']} {summary['recommendation']}"
    for code in INTERNAL_CODES:
        assert code not in blob.lower().split() or code not in blob


def test_dungu_telecom_breakdown_and_operators():
    payload = tex.build_telecom_explain("TERRITOIRE-05-002", page=1, page_size=50)
    assert payload is not None
    assert payload["summary"]["count"] == 22
    assert payload["breakdown"], "répartition par type attendue"
    operators = payload.get("operators") or []
    assert operators, "liste opérateurs attendue"
    names = " ".join(o["label"].lower() for o in operators)
    assert any(tok in names for tok in ("vodacom", "airtel", "helios", "opérateur", "fttx"))
    assert any(a["id"] == "details" for a in payload["actions"])
    _assert_domain_contract(payload, domain="telecom")


def test_dungu_health_no_false_zero_typology():
    payload = tex.build_health_explain("TERRITOIRE-05-002")
    assert payload is not None
    assert payload["summary"]["count"] == 121
    typology = payload.get("typology") or []
    assert typology
    labels = {t["label"]: t for t in typology}
    # Si typologie non normalisée : HGR/CS/PS = Non calculable, pas 0 trompeur
    other = next((t for t in typology if "OTHER" in t["label"].upper() or "non class" in t["label"].lower()), None)
    assert other is not None
    if other.get("count", 0) == 121:
        for key in ("HGR", "Centres de santé", "Postes"):
            match = next((t for t in typology if key.split()[0] in t["label"]), None)
            if match and match.get("count") is None:
                assert match.get("display") == "Non calculable"
    _assert_domain_contract(payload, domain="health")


def test_dungu_routes_fiber_programs_admin():
    routes = tex.build_routes_explain("TERRITOIRE-05-002")
    assert routes is not None
    assert routes["summary"]["count"] == 19
    assert routes["summary"]["headline"]
    fiber = tex.build_fiber_explain("TERRITOIRE-05-002")
    assert fiber is not None
    assert fiber["summary"]["count"] is not None
    assert "nœud" in fiber["summary"]["headline"].lower() or "fibre" in fiber["summary"]["headline"].lower()
    prog = tex.build_programs_explain("TERRITOIRE-05-002", program="sites_20476")
    assert prog is not None
    assert prog["summary"]["count"] == 88
    admin = tex.build_admin_explain("TERRITOIRE-05-002", level="groupements")
    assert admin is not None
    assert admin["summary"]["count"] == 5
    localites = tex.build_admin_explain("TERRITOIRE-05-002", level="localites")
    assert localites is not None
    assert localites["summary"]["count"] == 218


def test_profile_embeds_explainability_bundle():
    profile = tis.build_territorial_profile("TERRITOIRE-05-002")
    assert profile is not None
    ex = profile.get("explainability") or {}
    assert ex.get("telecom")
    assert ex["telecom"]["summary"]["count"] == 22
    assert ex.get("health")
    assert ex.get("routes")
    assert ex.get("fiber")


def test_api_explainability_and_details():
    bundle = CLIENT.get("/api/territorial-intelligence/territories/TERRITOIRE-05-002/explainability")
    assert bundle.status_code == 200
    body = bundle.json()
    assert body["telecom"]["summary"]["count"] == 22
    assert body["health"]["summary"]["count"] == 121

    details = CLIENT.get(
        "/api/territorial-intelligence/territories/TERRITOIRE-05-002/details/telecom?page=1&page_size=10"
    )
    assert details.status_code == 200
    d = details.json()
    assert len(d["top_items"]) >= 1
    assert d["pagination"]["total"] == 22
    row = d["top_items"][0]
    assert "name" in row and "coordinates" in row and "source" in row


def test_multi_territory_explainability_smoke():
    for ref in TERRITORIES:
        for domain in ("telecom", "health", "routes", "fiber"):
            payload = tex.build_domain_explain(ref, domain, page=1, page_size=5)
            if payload is None:
                # nom texte non résolu éventuel
                continue
            _assert_domain_contract(payload, domain=domain)
            # faux zéro : count None seulement si anomalie / pending
            if payload["summary"]["status"] in {"operational", "partial", "confirmed"}:
                assert payload["summary"]["count"] is not None
                assert payload["summary"]["count"] >= 0
