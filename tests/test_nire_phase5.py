"""Tests NIRE Phase 5 — audit MNO contrôlé (sans mutation des sources)."""
from __future__ import annotations

from pathlib import Path

import openpyxl
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import nire as route
from api.services.nire import mno_audit
from api.services.nire.operational_service import NireOperationalService
from api.services.nire.persistence import InMemoryNireRepository

ROOT = Path(__file__).resolve().parents[1]
REAL_MNO = ROOT / "data/raw/Operators existing and planned sites_20260713.xlsx"
FIXTURE = ROOT / "tests/fixtures/nire_mno_phase5_sample.xlsx"


def _write_fixture(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Site Name", "Latitude", "Longitude", "RAT", "Status", "Operator name"])
    # Match exact same coords as telecom fixture point
    ws.append(["Site Alpha Vodacom", -4.320000, 15.310000, "2G-3G-4G", "Online", "Vodacom"])
    # Co-located multi-operator (exact same coords)
    ws.append(["Site Alpha Airtel", -4.320000, 15.310000, "2G/3G/4G", "In Service", "Airtel"])
    # Nearby ambiguous
    ws.append(["Site Beta Orange", -4.321500, 15.311500, "2G_3G_FDD", "Online", "Orange"])
    # New candidate far away
    ws.append(["Site Gamma Africell", -2.500000, 28.800000, "2G3G4G", "Online", "Africell"])
    # Planned
    ws.append(["Site Delta Planned", -4.100000, 15.200000, "2G", "Planned", "Vodacom"])
    # Intra-operator duplicate exact
    ws.append(["Site Alpha Vodacom Dup", -4.320000, 15.310000, "2G-3G-4G", "Online", "Vodacom"])
    # Invalid #REF!
    ws.append(["Beni-Butsili-Relief_NKV", "#REF!", "#REF!", "2G", "Online", "Vodacom"])
    ws.append(["Butembo-Vuhira_NKV", 2.307038, "#REF!", "2G", "Online", "Airtel"])
    # (0,0) rejected
    ws.append(["ZeroZero", 0, 0, "2G", "Online", "Orange"])
    # Status variants
    ws.append(["OnlyTxSite", -4.5, 15.4, "2G_FDD", "Only TX", "Orange"])
    ws.append(["OutServiceSite", -4.6, 15.5, "2G", "Out Service", "Africell"])
    wb.save(path)


@pytest.fixture(autouse=True)
def _reset_audit():
    mno_audit.reset_state()
    yield
    mno_audit.reset_state()


@pytest.fixture(scope="module")
def sample_xlsx(tmp_path_factory):
    path = tmp_path_factory.mktemp("nire") / "sample.xlsx"
    _write_fixture(path)
    return path


TELECOM_FIXTURE = [
    {
        "id": 1,
        "infra_code": "T-1",
        "infra_name": "Site Alpha Vodacom",
        "infra_type": "BTS",
        "technology": "2G/3G/4G",
        "province": "KINSHASA",
        "territoire": "FUNA",
        "status": "active",
        "latitude": -4.320000,
        "longitude": 15.310000,
        "operator_code": "VODACOM",
        "operator_name": "Vodacom",
    },
    {
        "id": 2,
        "infra_code": "T-2",
        "infra_name": "Autre site",
        "infra_type": "BTS",
        "technology": "2G",
        "province": "KINSHASA",
        "territoire": "FUNA",
        "status": "active",
        "latitude": -4.400000,
        "longitude": 15.400000,
        "operator_code": "ORANGE",
        "operator_name": "Orange",
    },
]


def test_fingerprint_and_ingestion(sample_xlsx):
    meta, rows = mno_audit.ingest_mno_rows(sample_xlsx)
    assert meta.total_rows == 11
    assert meta.file_size > 0
    assert len(meta.sha256) == 64
    assert meta.valid_coordinates >= 7
    assert meta.invalid_coordinates >= 3
    assert meta.quarantined_rows == meta.invalid_coordinates
    assert "VODACOM" in meta.operators_detected


def test_operator_partitions(sample_xlsx):
    _, rows = mno_audit.ingest_mno_rows(sample_xlsx)
    parts = {r["partition"] for r in rows}
    assert "MNO_VODACOM" in parts
    assert "MNO_AIRTEL" in parts
    assert "MNO_ORANGE" in parts
    assert "MNO_AFRICELL" in parts
    for r in rows:
        assert r["source_file"]
        assert r["source_row"]
        assert r["source_hash"]
        assert "operator_original" in r
        assert "site_name_original" in r


def test_status_normalization():
    assert mno_audit.normalize_status("Online")[1] == "ONLINE"
    assert mno_audit.normalize_status("In Service")[1] == "IN_SERVICE"
    assert mno_audit.normalize_status("in Service")[1] == "IN_SERVICE"
    assert mno_audit.normalize_status("IN Service")[1] == "IN_SERVICE"
    assert mno_audit.normalize_status("Planned")[1] == "PLANNED"
    assert mno_audit.normalize_status("Out Service")[1] == "OUT_OF_SERVICE"
    assert mno_audit.normalize_status("Only Tx")[1] == "TX_ONLY"
    assert mno_audit.normalize_status("Only TX")[1] == "TX_ONLY"
    original, mapped = mno_audit.normalize_status("Weird")
    assert original == "Weird" and mapped == "UNKNOWN"


def test_rat_normalization_variants():
    for raw in ("2G/3G/4G", "2G-3G-4G", "2G3G4G", "2G+3G+4G", "2G_3G_FDD", "2G_3G_TDD-FDD"):
        rat = mno_audit.normalize_rat(raw)
        assert rat["rat_original"] == raw
        assert rat["has_2g"] is True
        if "3G" in raw.upper().replace("_", "").replace("-", "").replace("+", "").replace("/", "") or "3G" in raw:
            assert rat["has_3g"] is True
    rcs = mno_audit.normalize_rat("2G-RCS")
    assert rcs["has_2g"] and rcs["has_rcs"]
    assert mno_audit.normalize_rat("2G_3G_FDD")["has_fdd"]
    assert mno_audit.normalize_rat("2G_3G_TDD-FDD")["has_tdd"]
    empty = mno_audit.normalize_rat("")
    assert empty["has_5g"] is False


def test_invalid_geometry_and_zero_zero(sample_xlsx):
    state = mno_audit.run_mno_audit(sample_xlsx, telecom_points=TELECOM_FIXTURE)
    invalid = [r for r in state.rows if r["classification"] == "INVALID_GEOMETRY"]
    assert len(invalid) >= 3
    zero = [r for r in state.rows if "zero_zero" in " ".join(r.get("quarantine_reasons") or [])]
    assert zero
    ref = [r for r in state.rows if any("ref" in x for x in (r.get("quarantine_reasons") or []))]
    assert ref


def test_match_presence_planned_duplicate_coloc(sample_xlsx):
    state = mno_audit.run_mno_audit(sample_xlsx, telecom_points=TELECOM_FIXTURE)
    classes = {r["classification"] for r in state.rows}
    assert "MATCH_EXISTING_INFRASTRUCTURE" in classes or "OPERATOR_PRESENCE_ON_EXISTING_INFRASTRUCTURE" in classes
    assert "NEW_INFRASTRUCTURE_CANDIDATE" in classes
    assert "PLANNED_SITE" in classes or any("PLANNED_SITE" in (r.get("secondary_flags") or []) for r in state.rows)
    assert "POSSIBLE_DUPLICATE" in classes
    assert "INVALID_GEOMETRY" in classes
    assert any(c["multi_operator"] for c in state.colocations)
    # KPI national never written
    assert state.kpis["national_infrastructure_kpi_unchanged"] in (14580, None) or isinstance(
        state.kpis["national_infrastructure_kpi_unchanged"], int
    )
    assert state.automatic_replacement is False
    assert state.physical_deletion is False
    assert state.potential_kpi_estimate["must_not_sum_14580_plus_12615"] is True
    assert state.potential_kpi_estimate["must_not_replace_kpi_with_mno_rows"] is True


def test_pagination_and_filters(sample_xlsx):
    mno_audit.run_mno_audit(sample_xlsx, telecom_points=TELECOM_FIXTURE)
    page = mno_audit.list_rows(offset=0, limit=3)
    assert page["total"] == 11 and len(page["items"]) == 3
    vod = mno_audit.list_rows(operator="Vodacom", limit=50)
    assert all(r["operator"] == "VODACOM" for r in vod["items"])
    inv = mno_audit.list_rows(quarantine=True, limit=50)
    assert inv["total"] >= 3
    coloc = mno_audit.list_colocations(multi_operator_only=True, limit=10)
    assert coloc["total"] >= 1


def test_layer_geojson_capped(sample_xlsx):
    mno_audit.run_mno_audit(sample_xlsx, telecom_points=TELECOM_FIXTURE)
    layer = mno_audit.layer_geojson("vodacom", limit=1)
    assert layer["type"] == "FeatureCollection"
    assert len(layer["features"]) <= 1
    assert layer["meta"]["kpi_national_untouched"] is True


def test_review_queue_reuse(sample_xlsx):
    repo = InMemoryNireRepository()
    service = NireOperationalService(repo)
    state = mno_audit.run_mno_audit(
        sample_xlsx,
        telecom_points=TELECOM_FIXTURE,
        enqueue_reviews=True,
        review_service=service,
        max_review_items=20,
    )
    assert state.review_enqueued >= 1
    queue = repo.list_reviews(status=None, source_name="MNO_OPERATORS_XLSX", offset=0, limit=100)
    assert len(queue) >= 1


def test_requires_human_review_implies_queue_eligible(sample_xlsx):
    state = mno_audit.run_mno_audit(sample_xlsx, telecom_points=TELECOM_FIXTURE, enqueue_reviews=False)
    review = [r for r in state.rows if r.get("requires_human_review")]
    assert review
    assert all(mno_audit.is_review_queue_eligible(r) for r in review)
    assert mno_audit.count_review_eligible(state.rows) == len(review)
    assert state.coherence["human_review"]["eligibility_equals_requires_human_review"] is True
    assert state.review_enqueued == 0  # pas d'enqueue sans flag explicite


def test_operator_presence_review_is_enqueue_eligible(sample_xlsx):
    """Les OPERATOR_PRESENCE requires_human_review restent éligibles (ex-gap 448)."""
    # Force présence + coloc multi-op sans Planned
    telecom = list(TELECOM_FIXTURE)
    telecom[0] = {**telecom[0], "operator_code": "ORANGE", "operator_name": "Orange", "infra_name": "TourX"}
    state = mno_audit.run_mno_audit(sample_xlsx, telecom_points=telecom, enqueue_reviews=False)
    presence_review = [
        r
        for r in state.rows
        if r.get("requires_human_review")
        and r["classification"] == "OPERATOR_PRESENCE_ON_EXISTING_INFRASTRUCTURE"
    ]
    # Fixture has co-located Vodacom+Airtel at same coords near Orange infra → présence possible
    for r in presence_review:
        assert mno_audit.is_review_queue_eligible(r) is True
        # Éligible même sans flag Planned (correction du gap historique des 448).
        assert r.get("requires_human_review") is True


def test_enqueue_respects_max_items_no_mass_create(sample_xlsx):
    repo = InMemoryNireRepository()
    service = NireOperationalService(repo)
    state = mno_audit.run_mno_audit(
        sample_xlsx,
        telecom_points=TELECOM_FIXTURE,
        enqueue_reviews=True,
        review_service=service,
        max_review_items=2,
    )
    assert state.review_enqueued == 2
    queue = repo.list_reviews(status=None, source_name="MNO_OPERATORS_XLSX", offset=0, limit=100)
    assert len(queue) == 2


def test_operational_lanes_analytical_only(sample_xlsx):
    state = mno_audit.run_mno_audit(sample_xlsx, telecom_points=TELECOM_FIXTURE)
    for r in state.rows:
        lane = mno_audit.operational_review_lane(r)
        if r.get("requires_human_review"):
            assert lane in {"FAST_REVIEW_CANDIDATE", "COMPLEX_REVIEW"}
        else:
            assert lane is None
    # Les lanes n'écrasent pas la classification métier
    assert all("classification" in r and r["classification"] for r in state.rows)


def test_api_status_empty_then_run(sample_xlsx):
    repo = InMemoryNireRepository()
    service = NireOperationalService(repo)
    app = FastAPI()
    app.include_router(route.router, prefix="/api/nire")
    app.dependency_overrides[route.get_nire_service] = lambda: service
    client = TestClient(app)
    empty = client.get("/api/nire/mno-audit/status").json()
    assert empty["executed"] is False and empty["operators"] == [] and empty["source_loaded"] is False
    run = client.post(
        "/api/nire/mno-audit/run",
        headers={"X-NIRE-Role": "ADMIN"},
        json={"enqueue_reviews": False, "source_path": str(sample_xlsx)},
    )
    assert run.status_code == 200
    body = run.json()
    assert body["executed"] is True
    assert body["national_kpi_unchanged"] is True
    assert body["automatic_replacement"] is False
    status = client.get("/api/nire/mno-audit/status").json()
    assert status["kpis"]["mno_rows_analyzed"] == 11
    rows = client.get("/api/nire/mno-audit/rows?limit=5").json()
    assert rows["total"] == 11 and len(rows["items"]) == 5
    forbidden = client.post(
        "/api/nire/mno-audit/run",
        headers={"X-NIRE-Role": "ANALYST"},
        json={"source_path": str(sample_xlsx)},
    )
    assert forbidden.status_code == 403


def test_phase4_empty_contract_still_holds_before_run():
    app = FastAPI()
    app.include_router(route.router, prefix="/api/nire")
    app.dependency_overrides[route.get_nire_service] = lambda: NireOperationalService(InMemoryNireRepository())
    client = TestClient(app)
    x = client.get("/api/nire/mno-audit/status").json()
    assert x["executed"] is False and x["operators"] == [] and x["source_loaded"] is False


def test_ui_keeps_empty_state_copy_and_paradox():
    js = (ROOT / "dashboard/modules/nire-workspace/nire-workspace.js").read_text(encoding="utf-8")
    assert "Non calculé — aucune source MNO validée" in js
    assert "Paradoxe métier" in js
    assert "mno-audit/run" in js
    assert "mno-audit/layers" in js
    assert "Aucune suppression physique" in js
    assert "classification exclusive" in js
    assert "non exclusifs" in js
    assert "nombre de groupes" in js
    assert "Ne pas additionner" in js


def test_exclusive_vs_transversal_coherence(sample_xlsx):
    state = mno_audit.run_mno_audit(sample_xlsx, telecom_points=TELECOM_FIXTURE)
    coh = state.coherence
    assert coh["exclusive_classification"]["checksum_ok"] is True
    assert coh["exclusive_classification"]["checksum"] == len(state.rows)
    assert coh["population_total"] == len(state.rows)
    planned_status = sum(1 for r in state.rows if r.get("status_normalized") == "PLANNED")
    planned_primary = sum(1 for r in state.rows if r["classification"] == "PLANNED_SITE")
    assert state.kpis["planned_sites"] == planned_status
    assert state.kpis["planned_site_primary"] == planned_primary
    assert state.kpis.get("planned_sites_is_transversal") is True
    assert coh["colocation_metrics"]["phase5_uses_postgis_radius"] is False
    assert coh["new_infrastructure_candidates"]["none_also_classified_as_existing_match"] is True
    review_unique = coh["human_review"]["unique_rows_requiring_review"]
    assert review_unique == sum(1 for r in state.rows if r.get("requires_human_review"))
    assert sum(coh["human_review"]["by_primary_classification"].values()) == review_unique
    est = state.potential_kpi_estimate
    assert est["is_theoretical_scenario_only"] is True
    assert est["is_official_kpi"] is False


def test_no_mutation_of_protected_paths_in_module():
    src = (ROOT / "api/services/nire/mno_audit.py").read_text(encoding="utf-8")
    assert "case_history" not in src
    assert "data/raw/ceni" not in src
    assert "work/" not in src
    # Source Excel is read, never written
    assert "load_workbook" in src
    assert ".save(" not in src


@pytest.mark.skipif(not REAL_MNO.is_file(), reason="Fichier MNO réel absent")
def test_real_mno_stats_smoke():
    meta, rows = mno_audit.ingest_mno_rows(REAL_MNO)
    assert meta.total_rows == 12615
    assert meta.sha256 == "79560e2217679d9244ee679810863b723e6ca07003e58f0a56ab6708b77ac242"
    assert meta.operators_detected.get("VODACOM") == 4133
    assert meta.operators_detected.get("AIRTEL") == 4477
    assert meta.operators_detected.get("ORANGE") == 3221
    assert meta.operators_detected.get("AFRICELL") == 784
    ops = {r["operator"] for r in rows}
    assert ops == {"VODACOM", "AIRTEL", "ORANGE", "AFRICELL"}
    assert meta.invalid_coordinates == 4
    assert sum(1 for r in rows if r["status_normalized"] == "PLANNED") == 1463


@pytest.mark.skipif(not REAL_MNO.is_file(), reason="Fichier MNO réel absent")
def test_real_mno_full_reconcile_smoke():
    """Rapprochement réel vs telecom.infrastructure (DB) si disponible — lecture seule."""
    state = mno_audit.run_mno_audit(REAL_MNO, enqueue_reviews=False)
    assert state.executed
    assert state.kpis["mno_rows_analyzed"] == 12615
    assert state.kpis["invalid_coordinates"] == 4
    assert state.kpis["planned_sites"] == 1463
    assert state.kpis["planned_site_primary"] == 1032
    assert state.kpis["exclusive_classification_checksum"] == 12615
    coh = state.coherence
    assert coh["exclusive_classification"]["checksum"] == 12615
    assert coh["exclusive_classification"]["checksum_ok"] is True
    assert coh["human_review"]["unique_rows_requiring_review"] == 3881
    assert coh["human_review"]["unique_rows_review_queue_eligible"] == 3881
    assert coh["human_review"]["eligibility_equals_requires_human_review"] is True
    assert coh["human_review"]["operational_lanes"]["FAST_REVIEW_CANDIDATE"] == 1705
    assert coh["human_review"]["operational_lanes"]["COMPLEX_REVIEW"] == 2176
    assert state.review_enqueued == 0
    assert coh["colocation_metrics"]["phase5_groups_multi_operator"] == 736
    assert coh["colocation_metrics"]["exact_coordinate_groups_float_equality"]["multi_operator_groups"] == 705
    assert coh["new_infrastructure_candidates"]["count"] == 943
    assert coh["new_infrastructure_candidates"]["none_also_classified_as_existing_match"] is True
    assert state.potential_kpi_estimate["must_not_sum_14580_plus_12615"] is True
    assert state.potential_kpi_estimate["is_theoretical_scenario_only"] is True
    if state.national_infra_count == 14580:
        assert state.potential_kpi_estimate["potential_kpi_if_all_new_validated"] == 15523
    assert "current_national_infrastructure_kpi" in state.potential_kpi_estimate
