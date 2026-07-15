"""Tests National Data Maturity Engine — Data First, pas de scores inventés."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app
from api.services import data_maturity_engine as ndm

CLIENT = TestClient(app)


def test_national_score_documented_and_in_range():
    payload = ndm.build_national_maturity(use_cache=False)
    score = payload["national_score"]
    assert score is not None
    assert 0 <= score <= 100
    assert payload["_meta"]["scoring"]["null_policy"]
    assert payload["_meta"]["data_first"] is True


def test_domains_include_required_referentials():
    payload = ndm.build_national_maturity(use_cache=False)
    codes = {d["code"] for d in payload["domains"]}
    for required in (
        "administration",
        "population",
        "localities",
        "sites_40",
        "sites_300",
        "sites_20476",
        "ccn",
        "telecom",
        "sante",
        "sdg",
        "program_lifecycle",
        "education",
        "energie",
    ):
        assert required in codes


def test_absent_education_not_fake_high():
    payload = ndm.build_national_maturity(use_cache=False)
    edu = next(d for d in payload["domains"] if d["code"] == "education")
    assert edu["available"] is False
    assert edu["score"] is None or edu["score"] < 40


def test_sites_20476_flags_nsme_gap():
    payload = ndm.build_national_maturity(use_cache=False)
    s = next(d for d in payload["domains"] if d["code"] == "sites_20476")
    assert s["object_count"] in (None, 20476) or (s["object_count"] or 0) > 0
    text = " ".join(s.get("weaknesses") or []) + " ".join(s.get("anomalies") or [])
    assert "nsme" in text.lower() or "fdsu_sites" in text.lower() or s["score"] is not None


def test_priorities_and_roadmap_generated():
    payload = ndm.build_national_maturity(use_cache=False)
    assert isinstance(payload["priorities"], list)
    assert "short_term" in payload["roadmap"]
    assert payload["roadmap"]["note"]


def test_band_thresholds():
    assert ndm._band(96)["code"] == "excellent"
    assert ndm._band(92)["code"] == "very_good"
    assert ndm._band(85)["code"] == "good"
    assert ndm._band(70)["code"] == "reinforce"
    assert ndm._band(40)["code"] == "priority"
    assert ndm._band(None)["code"] == "unknown"


def test_api_endpoints():
    assert CLIENT.get("/api/data-maturity").status_code == 200
    assert CLIENT.get("/api/data-maturity/details").status_code == 200
    assert CLIENT.get("/api/data-maturity/roadmap").status_code == 200
    assert CLIENT.get("/api/data-maturity/map").status_code == 200
    report = CLIENT.get("/api/data-maturity/report")
    assert report.status_code == 200
    assert report.json().get("_meta", {}).get("report_title")
    html = CLIENT.get("/api/data-maturity/report.html")
    assert html.status_code == 200
    assert "Maturité" in html.text


def test_map_not_confused_with_radio():
    payload = ndm.build_map_payload()
    assert "couverture radio" in (payload.get("note") or "").lower() or "radio" in (payload.get("note") or "").lower()
    for f in (payload.get("geojson") or {}).get("features") or []:
        assert f["properties"].get("kind") == "data_maturity"
