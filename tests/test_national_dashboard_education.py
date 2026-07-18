from fastapi.testclient import TestClient

from api.main import app
from api.services import education_referential_service, national_dashboard_service


def test_administrative_baseline_is_versioned_and_non_destructive():
    baseline = national_dashboard_service.baseline()
    assert baseline["_meta"]["registry_id"] == "rdc-administrative-baseline-unsd-ungegn-v1"
    assert baseline["_meta"]["is_2026_administrative_update"] is False
    assert baseline["provenance"]["organization"] == "UNSD / UNGEGN"
    assert baseline["provenance"]["reference_year"] is None
    assert {key: row["reference"] for key, row in baseline["levels"].items()} == {
        "provinces": 26, "villes": 33, "territoires": 145, "chefferies": 259,
        "secteurs": 478, "groupements": 6053, "villages": 78855,
    }
    assert "collectivites" in baseline["non_comparable"]


def test_education_statistics_match_current_ceni_projection():
    stats = education_referential_service.statistics()
    assert stats["establishments"] == 23604
    assert stats["quarantined_school_candidates"] == 90
    assert sum(stats["by_subtype"].values()) == 23604
    assert stats["by_quality_level"] == {"VALIDE": 4736, "PROBABLE": 18849, "A_VERIFIER": 19}
    assert stats["_meta"]["official_ministry_registry"] is False


def test_education_projection_preserves_source_and_provenance():
    payload = education_referential_service.list_establishments(limit=2)
    assert payload["classified_total"] == 23604
    assert payload["quarantined_school_candidates"] == 90
    assert payload["total"] == 23514 and len(payload["establishments"]) == 2
    row = payload["establishments"][0]
    assert row["source_system"] == "CENI"
    assert row["business_category"] == "ETABLISSEMENT_SCOLAIRE"
    assert row["source_id"].startswith("CENI-")
    assert row["provenance"]["derived_projection"] is True
    assert row["provenance"]["official_ministry_registry"] is False


def test_dashboard_summary_is_compact_and_keeps_programs_non_additive():
    summary = national_dashboard_service.build_summary(use_database=False)
    assert summary["_meta"] == {"payload_type": "aggregates_only", "massive_datasets_loaded_by_client": False}
    assert summary["national_kpis"]["fdsu_sites"]["value"] == 20476
    assert summary["national_kpis"]["fdsu_sites"]["program_300"] == 300
    assert "ne sont pas additionnés" in summary["national_kpis"]["fdsu_sites"]["counting_rule"]
    assert summary["national_kpis"]["ceni_sites"]["value"] == 31956
    assert summary["national_kpis"]["ceni_sites"]["source_available"] == 32221
    assert summary["national_kpis"]["ceni_sites"]["quarantined_coordinates"] == 265
    assert summary["national_kpis"]["ceni_sites"]["rejected_other"] == 0
    assert summary["national_kpis"]["telecom_infrastructure"]["value"] == 14580
    assert summary["national_kpis"]["telecom_infrastructure"]["geospatial_elements_total"] == 31401
    assert [row["level"] for row in summary["administrative_coverage"]] == ["provinces", "villes", "territoires", "secteurs", "chefferies", "groupements", "villages"]
    rows = {row["level"]: row for row in summary["administrative_coverage"]}
    assert rows["chefferies"]["integrated"] == 260 and rows["chefferies"]["reference"] == 259
    assert "audit" in rows["chefferies"]["comparison_note"]
    assert "indicative" in rows["villages"]["comparison_note"]
    assert summary["national_kpis"]["education_establishments"]["value"] == 23604
    assert all("features" not in row for row in summary["administrative_coverage"])


def test_education_api_is_paginated_and_uses_business_wording():
    client = TestClient(app)
    stats = client.get("/api/education/statistics")
    assert stats.status_code == 200 and stats.json()["establishments"] == 23604
    page = client.get("/api/education/establishments", params={"limit": 3, "quality": "A_VERIFIER"})
    assert page.status_code == 200
    assert page.json()["total"] == 19 and len(page.json()["establishments"]) == 3
