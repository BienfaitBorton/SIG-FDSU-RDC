"""Data Activation P1 — Éducation / CENI / Télécom DXL / NIRE localités."""

from __future__ import annotations

import pytest


def test_education_nearest_and_nsme_matcher():
    from api.services import education_referential_service as edu
    from api.services.spatial_matching_service import match_site_to_schools

    stats = edu.statistics()
    assert int(stats.get("establishments") or 0) > 20_000

    # Kinshasa-ish probe
    payload = edu.nearest_establishment(-4.325, 15.322, radius_m=25_000, limit=5)
    assert payload["search_executed"] is True
    assert payload["data_available"] is True
    assert payload["derived_projection"] is True

    asset = {
        "id": 29,
        "site_code": "TEST-EDU",
        "latitude": -4.325,
        "longitude": 15.322,
        "program_code": "PROG_SITES_40",
        "province": "Kinshasa",
    }
    matches = match_site_to_schools(asset)
    rels = {m.get("relation_type") for m in matches}
    assert "NEAREST_SCHOOL" in rels or "NEAR_SCHOOL" in rels or "EDUCATION_SEARCH_EXECUTED" in rels
    assert all(m.get("category") == "education" for m in matches)


def test_ceni_signal_not_fdsu_and_nsme():
    from api.services import ceni_registry_service as ceni
    from api.services.spatial_matching_service import match_site_to_ceni_signal

    stats = ceni.statistics()
    assert int(stats.get("integrated") or 0) > 30_000

    payload = ceni.nearest_signals(-4.325, 15.322, radius_m=15_000, limit=5, exclude_schools=True)
    assert payload["not_fdsu_sites"] is True
    assert payload["scoring_weighted"] is False

    asset = {
        "id": 29,
        "site_code": "TEST-CENI",
        "latitude": -4.325,
        "longitude": 15.322,
        "program_code": "PROG_SITES_40",
    }
    matches = match_site_to_ceni_signal(asset)
    assert matches
    assert all(m.get("category") == "ceni" for m in matches)
    assert all((m.get("properties") or {}).get("not_fdsu_site") is True or m.get("relation_type") == "CENI_SEARCH_EXECUTED" for m in matches)
    assert any(
        m.get("relation_type") in {"NEAREST_CENI_SIGNAL", "NEAR_CENI_SITE", "CENI_SEARCH_EXECUTED"}
        for m in matches
    )


def test_sdg_probes_education_and_ceni_wired():
    from api.services.spatial_decision_graph_service import _probe_referential_availability

    probes = _probe_referential_availability(15.322, -4.325)
    assert probes["education"]["referential_exists"] is True
    assert probes["education"]["nsme_wired"] is True
    assert probes["ceni"]["referential_exists"] is True
    assert probes["ceni"]["nsme_wired"] is True
    assert probes["ceni"].get("scoring_weighted") is False


def test_site_case_exposes_telecom_education_ceni_contexts():
    from api.services.explainable_decision_service import build_site_case

    case = build_site_case("29", program_code="sites_40")
    if case is None:
        pytest.skip("Doctrine / site 29 indisponible dans cet environnement")
    assert "telecom_context" in case
    assert "education_context" in case
    assert "ceni_context" in case
    tel = case["telecom_context"]
    if tel.get("available"):
        assert "operators" in tel
        assert "fiber" in tel or tel.get("distance_to_fiber_m") is not None
        assert isinstance(tel.get("summary_lines"), list)


def test_nire_locality_coverage_classifications_fixture():
    from api.services.nire import locality_coverage as lc

    lc.reset_state()
    covered = [
        {
            "id": "NCI-COV-1",
            "dataset": "population_coverage",
            "coverage_status": "covered",
            "name": "X1",
            "destination": "Likati",
            "province": "Bas-Uele",
            "territoire": "Aketi",
            "latitude": 3.43,
            "longitude": 23.78,
            "population": 1000,
            "project": "CENI",
        },
        {
            "id": "NCI-COV-DUP",
            "dataset": "population_coverage",
            "coverage_status": "covered",
            "name": "X2",
            "destination": "Likati",
            "province": "Bas-Uele",
            "territoire": "Aketi",
            "latitude": 3.431,
            "longitude": 23.781,
            "population": 900,
            "duplicate": True,
            "project": "CENI",
        },
    ]
    uncovered = [
        {
            "id": "NCI-UNC-1",
            "dataset": "localities_uncovered",
            "coverage_status": "uncovered",
            "name": "Y1",
            "destination": "Likati",
            "province": "Bas-Uele",
            "territoire": "Aketi",
            # Même cellule géo → dual-source (revue neutre, pas conflit auto)
            "latitude": 3.43,
            "longitude": 23.78,
            "population": 2000,
            "project": "CENI",
        },
        {
            "id": "NCI-UNC-2",
            "dataset": "localities_uncovered",
            "coverage_status": "uncovered",
            "name": "Z1",
            "destination": "VillageInconnuXYZ",
            "province": "Haut-Uele",
            "territoire": "Dungu",
            "latitude": 3.5,
            "longitude": 28.5,
            "population": 500,
            "project": "New planning 20476 sites",
        },
    ]
    admin = [
        {
            "admin_id": "ADM-1",
            "nom": "Likati",
            "province": "Bas-Uele",
            "territoire": "Aketi",
            "latitude": 3.4305,
            "longitude": 23.7805,
            "source": "fixture",
        },
        {
            "admin_id": "ADM-2",
            "nom": "Likati",
            "province": "Haut-Uele",
            "territoire": "Dungu",
            "latitude": 3.6,
            "longitude": 28.6,
            "source": "fixture",
        },
    ]
    state = lc.run_locality_coverage(
        covered_rows=covered,
        uncovered_rows=uncovered,
        admin_rows=admin,
        write_cache=False,
    )
    assert state.executed
    by_class = state.kpis["by_classification"]
    # Dual-source + match admin → MATCHED conservé ; dual sans match → REQUIRES_REVIEW
    assert by_class.get("CONFLICTING_COVERAGE_STATUS", 0) == 0
    assert by_class.get("UNMATCHED_UNCOVERED", 0) >= 1
    assert state.kpis["universes_not_forced_equal"] is True
    assert state.kpis["coverage_semantics"]["not_global_binary"] is True
    assert "funnel" in state.kpis

    rows = lc.list_rows(limit=20)["rows"]
    # Homonyme Likati Haut-Uele ne doit pas matcher une observation Bas-Uele
    for r in rows:
        if r.get("nci_id") in {"NCI-COV-1", "NCI-UNC-1"} and r.get("admin_id"):
            assert r.get("admin_province") == "Bas-Uele"
            assert r.get("admin_id") == "ADM-1"
    # Toutes les observations source conservées
    assert len(rows) == 4


def test_nire_homonym_different_province_not_merged():
    from api.services.nire import locality_coverage as lc

    score, evidence = lc._score_pair(
        {
            "destination": "Kabinda",
            "province": "Lomami",
            "territoire": "Kabinda",
            "latitude": -6.1,
            "longitude": 24.5,
        },
        {
            "nom": "Kabinda",
            "province": "Haut-Lomami",
            "territoire": "Kamina",
            "latitude": -8.7,
            "longitude": 25.0,
        },
    )
    assert score == 0.0
    assert "PROVINCE_MISMATCH_BLOCKED" in evidence


def test_nire_homonym_different_territory_not_merged():
    from api.services.nire import locality_coverage as lc

    score, evidence = lc._score_pair(
        {
            "destination": "Bunia",
            "province": "Ituri",
            "territoire": "Irumu",
            "latitude": 1.56,
            "longitude": 30.25,
        },
        {
            "nom": "Bunia",
            "province": "Ituri",
            "territoire": "Djugu",
            "latitude": 1.9,
            "longitude": 30.5,
        },
    )
    assert score == 0.0
    assert "TERRITORY_MISMATCH_BLOCKED" in evidence


def test_nire_dual_source_is_review_not_conflict():
    from api.services.nire import locality_coverage as lc

    assert lc._apply_dual_source_policy("UNMATCHED_UNCOVERED", dual_source=True) == "COVERAGE_STATUS_REQUIRES_REVIEW"
    assert lc._apply_dual_source_policy("MATCHED_LOCALITY", dual_source=True) == "MATCHED_LOCALITY"
    assert lc._apply_dual_source_policy("UNMATCHED_COVERED", dual_source=False) == "UNMATCHED_COVERED"


def test_population_territorial_aggregates_available():
    from api.services import coverage_intelligence_service as nci

    provinces = nci.list_provinces(limit=5)["provinces"]
    assert provinces
    assert provinces[0].get("population_covered") is not None or provinces[0].get("population_uncovered") is not None
    territories = nci.list_territories(limit=5)["territories"]
    assert territories


def test_enrichment_orthographic_variant_existing():
    from api.services.nire import locality_coverage as lc
    from api.services.nire import locality_enrichment_audit as lea

    lea.reset_state()
    admin = [
        {
            "admin_id": "ADM-LIK",
            "nom": "Likati",
            "province": "Bas-Uele",
            "territoire": "Aketi",
            "latitude": 3.437,
            "longitude": 23.789,
            "source": "fixture",
        }
    ]
    uncovered = [
        {
            "id": "NCI-UNC-VAR",
            "destination": "Likatti",
            "name": "x",
            "province": "Bas-Uele",
            "territoire": "Aketi",
            "latitude": 3.4372,
            "longitude": 23.7889,
            "coverage_status": "uncovered",
            "population": 100,
            "dataset": "localities_uncovered",
        }
    ]
    cov = lc.run_locality_coverage(
        covered_rows=[], uncovered_rows=uncovered, admin_rows=admin, write_cache=False
    )
    state = lea.run_enrichment_audit(
        coverage_rows=cov.rows,
        covered_rows=[],
        uncovered_rows=uncovered,
        admin_rows=admin,
        run_coverage_if_needed=False,
        write_cache=False,
    )
    primary = [r for r in state.rows if r.get("is_canonical_representative")]
    assert primary
    assert primary[0]["enrichment_class"] == "EXISTING_LOCALITY_VARIANT"
    assert state.kpis["auto_creation_disabled"] is True
    assert state.kpis["referential_not_modified"] is True


def test_enrichment_homonym_different_territory():
    from api.services.nire import locality_coverage as lc
    from api.services.nire import locality_enrichment_audit as lea

    lea.reset_state()
    admin = [
        {
            "admin_id": "ADM-KAS-A",
            "nom": "Kasongo",
            "province": "Maniema",
            "territoire": "Kasongo",
            "latitude": -4.45,
            "longitude": 26.66,
            "source": "fixture",
        }
    ]
    uncovered = [
        {
            "id": "NCI-UNC-HOM",
            "destination": "Kasongo",
            "name": "x",
            "province": "Maniema",
            "territoire": "Kibombo",
            "latitude": -3.90,
            "longitude": 25.90,
            "coverage_status": "uncovered",
            "population": 200,
            "dataset": "localities_uncovered",
        }
    ]
    cov = lc.run_locality_coverage(
        covered_rows=[], uncovered_rows=uncovered, admin_rows=admin, write_cache=False
    )
    state = lea.run_enrichment_audit(
        coverage_rows=cov.rows,
        covered_rows=[],
        uncovered_rows=uncovered,
        admin_rows=admin,
        run_coverage_if_needed=False,
        write_cache=False,
    )
    primary = [r for r in state.rows if r.get("is_canonical_representative")][0]
    assert primary["enrichment_class"] == "HOMONYM_DIFFERENT_LOCALITY"


def test_enrichment_duplicate_nci_and_single_canonical():
    from api.services.nire import locality_coverage as lc
    from api.services.nire import locality_enrichment_audit as lea

    lea.reset_state()
    admin = [{"admin_id": "ADM-Z", "nom": "ZongoFar", "province": "Sud-Ubangi", "territoire": "Zongo", "latitude": 4.3, "longitude": 18.6, "source": "fixture"}]
    shared = {
        "destination": "Village Nouveau XYZ",
        "province": "Haut-Katanga",
        "territoire": "Kipushi",
        "latitude": -11.760,
        "longitude": 27.250,
        "population": 500,
    }
    covered = [{**shared, "id": "NCI-COV-DUP", "name": "a", "coverage_status": "covered", "dataset": "population_coverage"}]
    uncovered = [{**shared, "id": "NCI-UNC-DUP", "name": "b", "coverage_status": "uncovered", "dataset": "localities_uncovered"}]
    cov = lc.run_locality_coverage(
        covered_rows=covered, uncovered_rows=uncovered, admin_rows=admin, write_cache=False
    )
    state = lea.run_enrichment_audit(
        coverage_rows=cov.rows,
        covered_rows=covered,
        uncovered_rows=uncovered,
        admin_rows=admin,
        run_coverage_if_needed=False,
        write_cache=False,
    )
    primaries = [r for r in state.rows if r.get("is_canonical_representative")]
    extras = [r for r in state.rows if not r.get("is_canonical_representative")]
    assert len(primaries) == 1
    assert len(extras) == 1
    assert extras[0]["enrichment_class"] == "DUPLICATE_NCI_OBSERVATION"
    assert primaries[0]["enrichment_class"] in {
        "NEW_LOCALITY_CANDIDATE_HIGH_CONFIDENCE",
        "NEW_LOCALITY_CANDIDATE_REVIEW",
    }


def test_enrichment_high_confidence_new_locality():
    from api.services.nire import locality_coverage as lc
    from api.services.nire import locality_enrichment_audit as lea

    lea.reset_state()
    # Admin ailleurs — bbox province ; proximité ≠ critère d'identité
    admin = [
        {
            "admin_id": "ADM-LUB",
            "nom": "LubumbashiCentre",
            "province": "Haut-Katanga",
            "territoire": "Lubumbashi",
            "latitude": -11.66,
            "longitude": 27.48,
            "source": "fixture",
        },
        {
            "admin_id": "ADM-KIP",
            "nom": "KipushiVille",
            "province": "Haut-Katanga",
            "territoire": "Kipushi",
            "latitude": -11.76,
            "longitude": 27.25,
            "source": "fixture",
        },
    ]
    uncovered = [
        {
            "id": "NCI-UNC-NEW",
            "destination": "Mwanga Nouveau Camp Unique",
            "name": "tech",
            "province": "Haut-Katanga",
            "territoire": "Kipushi",
            # ~0.05° ≈ 5.5 km du plus proche admin KipushiVille
            "latitude": -11.85,
            "longitude": 27.35,
            "coverage_status": "uncovered",
            "population": 900,
            "dataset": "localities_uncovered",
        }
    ]
    cov = lc.run_locality_coverage(
        covered_rows=[], uncovered_rows=uncovered, admin_rows=admin, write_cache=False
    )
    state = lea.run_enrichment_audit(
        coverage_rows=cov.rows,
        covered_rows=[],
        uncovered_rows=uncovered,
        admin_rows=admin,
        run_coverage_if_needed=False,
        write_cache=False,
    )
    primary = [r for r in state.rows if r.get("is_canonical_representative")][0]
    assert primary["enrichment_class"] == "NEW_LOCALITY_CANDIDATE_HIGH_CONFIDENCE"
    assert primary.get("auto_created") is False
    assert primary.get("future_canonical_id", "").startswith("RDC-NCI-LOC-")
    assert state.kpis["POTENTIAL_ENRICHED_LOCALITY_COUNT"] == 2 + 1


def test_enrichment_insufficient_becomes_review_or_unresolved():
    from api.services.nire import locality_coverage as lc
    from api.services.nire import locality_enrichment_audit as lea

    lea.reset_state()
    admin = [
        {
            "admin_id": "ADM-1",
            "nom": "Somewhere",
            "province": "Kinshasa",
            "territoire": "Kinshasa",
            "latitude": -4.3,
            "longitude": 15.3,
            "source": "fixture",
        }
    ]
    # Coords + province but no territory → REVIEW
    uncovered = [
        {
            "id": "NCI-UNC-WEAK",
            "destination": "Camp Temporaire Alpha",
            "name": "x",
            "province": "Kinshasa",
            "territoire": "",
            "latitude": -4.31,
            "longitude": 15.31,
            "coverage_status": "uncovered",
            "population": 10,
            "dataset": "localities_uncovered",
        }
    ]
    cov = lc.run_locality_coverage(
        covered_rows=[], uncovered_rows=uncovered, admin_rows=admin, write_cache=False
    )
    state = lea.run_enrichment_audit(
        coverage_rows=cov.rows,
        covered_rows=[],
        uncovered_rows=uncovered,
        admin_rows=admin,
        run_coverage_if_needed=False,
        write_cache=False,
    )
    primary = [r for r in state.rows if r.get("is_canonical_representative")][0]
    assert primary["enrichment_class"] in {
        "NEW_LOCALITY_CANDIDATE_REVIEW",
        "UNRESOLVED_LOCALITY",
    }


def test_enrichment_no_merge_on_name_alone():
    from api.services.nire import locality_enrichment_audit as lea

    admin_by_name = {
        "kasongo": [
            {
                "admin_id": "A1",
                "nom": "Kasongo",
                "province": "Maniema",
                "territoire": "Kasongo",
                "latitude": -4.45,
                "longitude": 26.66,
            }
        ]
    }
    admin_by_province = {"lomami": []}
    decision = lea.classify_enrichment_observation(
        {
            "toponym": "Kasongo",
            "province": "Lomami",
            "territoire": "Kabinda",
            "latitude": -6.1,
            "longitude": 24.5,
        },
        is_duplicate_extra=False,
        admin_by_name=admin_by_name,
        admin_by_province=admin_by_province,
        province_bboxes={},
    )
    assert decision["enrichment_class"] == "HOMONYM_DIFFERENT_LOCALITY"


def test_enrichment_idempotent_blueprint_stable():
    from api.services.nire import locality_enrichment_audit as lea

    row = {
        "toponym": "Mwanga Nouveau Camp Unique",
        "province": "Haut-Katanga",
        "territoire": "Kipushi",
        "latitude": -11.80,
        "longitude": 27.30,
        "nci_id": "NCI-1",
        "enrichment_class": "NEW_LOCALITY_CANDIDATE_HIGH_CONFIDENCE",
    }
    a = lea.build_integration_blueprint(row)
    b = lea.build_integration_blueprint(row)
    assert a["canonical_id"] == b["canonical_id"]
    assert a["applied"] is False
    assert a["integration_date"] is None
    method = lea.describe_integration_method()
    assert method["auto_create_during_audit"] is False


def _admin_hk():
    return [
        {
            "admin_id": "ADM-A",
            "nom": "Village Alpha",
            "province": "Haut-Katanga",
            "territoire": "Kipushi",
            "latitude": -11.76,
            "longitude": 27.25,
            "source": "fixture",
        },
        {
            "admin_id": "ADM-B",
            "nom": "Village Beta",
            "province": "Haut-Katanga",
            "territoire": "Kipushi",
            "latitude": -11.77,
            "longitude": 27.26,
            "source": "fixture",
        },
        {
            "admin_id": "ADM-C",
            "nom": "Village Gamma",
            "province": "Haut-Katanga",
            "territoire": "Kipushi",
            "latitude": -11.78,
            "longitude": 27.27,
            "source": "fixture",
        },
        {
            "admin_id": "ADM-KAS",
            "nom": "Kasongo",
            "province": "Maniema",
            "territoire": "Kasongo",
            "latitude": -4.45,
            "longitude": 26.66,
            "source": "fixture",
        },
    ]


def test_preintegration_nearby_villages_remain_distinct():
    """Deux villages proches mais différents restent distincts — distance ≠ fusion."""
    from api.services.nire import locality_preintegration_validation as piv

    indexes = piv._build_admin_indexes(_admin_hk())
    a = {
        "toponym": "Camp Nord Unique",
        "province": "Haut-Katanga",
        "territoire": "Kipushi",
        "latitude": -11.7605,
        "longitude": 27.2505,
    }
    b = {
        "toponym": "Camp Sud Unique",
        "province": "Haut-Katanga",
        "territoire": "Kipushi",
        "latitude": -11.7610,
        "longitude": 27.2510,
    }
    da = piv.classify_ready_candidate(a, is_duplicate_extra=False, indexes=indexes)
    db = piv.classify_ready_candidate(b, is_duplicate_extra=False, indexes=indexes)
    assert da["final_class"] != "DUPLICATE_NCI_OBSERVATION"
    assert db["final_class"] != "DUPLICATE_NCI_OBSERVATION"
    assert da["final_class"] in {"READY_FOR_INTEGRATION", "REQUIRES_HUMAN_REVIEW", "HOMONYM_DISTINCT_CONFIRMED"}
    assert db["final_class"] in {"READY_FOR_INTEGRATION", "REQUIRES_HUMAN_REVIEW", "HOMONYM_DISTINCT_CONFIRMED"}
    assert "DISTANCE_NOT_USED_AS_IDENTITY_RULE" in da["proofs"]


def test_preintegration_homonym_two_territories_distinct():
    from api.services.nire import locality_preintegration_validation as piv

    indexes = piv._build_admin_indexes(_admin_hk())
    obs = {
        "toponym": "Kasongo",
        "province": "Haut-Katanga",
        "territoire": "Kipushi",
        "latitude": -11.77,
        "longitude": 27.26,
    }
    d = piv.classify_homonym(obs, indexes=indexes)
    assert d["homonym_class"] in {"HOMONYM_NEW_LOCALITY_READY", "HOMONYM_REQUIRES_REVIEW"}
    assert d["homonym_class"] != "HOMONYM_ALREADY_IN_REFERENTIAL"


def test_preintegration_orthographic_variant_not_ready():
    from api.services.nire import locality_preintegration_validation as piv

    indexes = piv._build_admin_indexes(_admin_hk())
    obs = {
        "toponym": "Village Alphaa",
        "province": "Haut-Katanga",
        "territoire": "Kipushi",
        "latitude": -11.76,
        "longitude": 27.25,
    }
    d = piv.classify_ready_candidate(obs, is_duplicate_extra=False, indexes=indexes)
    assert d["final_class"] == "EXISTING_LOCALITY_VARIANT"


def test_preintegration_duplicate_nci_not_added():
    from api.services.nire import locality_preintegration_validation as piv

    indexes = piv._build_admin_indexes(_admin_hk())
    obs = {
        "toponym": "Nouveau Village XYZ",
        "province": "Haut-Katanga",
        "territoire": "Kipushi",
        "latitude": -11.79,
        "longitude": 27.28,
    }
    d = piv.classify_ready_candidate(obs, is_duplicate_extra=True, indexes=indexes)
    assert d["final_class"] == "DUPLICATE_NCI_OBSERVATION"


def test_preintegration_strong_identity_ready_weak_review():
    from api.services.nire import locality_preintegration_validation as piv

    indexes = piv._build_admin_indexes(_admin_hk())
    strong = {
        "toponym": "Mwanga Nouveau Unique",
        "province": "Haut-Katanga",
        "territoire": "Kipushi",
        "latitude": -11.775,
        "longitude": 27.265,
    }
    weak = {
        "toponym": "Part2_99999_NewSite",
        "province": "Haut-Katanga",
        "territoire": "Kipushi",
        "latitude": -11.775,
        "longitude": 27.265,
    }
    ds = piv.classify_ready_candidate(strong, is_duplicate_extra=False, indexes=indexes)
    dw = piv.classify_ready_candidate(weak, is_duplicate_extra=False, indexes=indexes)
    assert ds["final_class"] == "READY_FOR_INTEGRATION"
    assert dw["final_class"] == "REQUIRES_HUMAN_REVIEW"


def test_preintegration_simulation_no_real_creation():
    from api.services.nire import locality_coverage as lc
    from api.services.nire import locality_enrichment_audit as lea
    from api.services.nire import locality_preintegration_validation as piv

    piv.reset_state()
    lea.reset_state()
    admin = _admin_hk()
    uncovered = [
        {
            "id": "NCI-UNC-R1",
            "destination": "Localite Nouvelle Preinteg",
            "name": "x",
            "province": "Haut-Katanga",
            "territoire": "Kipushi",
            "latitude": -11.774,
            "longitude": 27.264,
            "coverage_status": "uncovered",
            "population": 120,
            "dataset": "localities_uncovered",
        }
    ]
    cov = lc.run_locality_coverage(
        covered_rows=[], uncovered_rows=uncovered, admin_rows=admin, write_cache=False
    )
    en = lea.run_enrichment_audit(
        coverage_rows=cov.rows,
        covered_rows=[],
        uncovered_rows=uncovered,
        admin_rows=admin,
        run_coverage_if_needed=False,
        write_cache=False,
    )
    state = piv.run_preintegration_validation(
        enrichment_rows=en.rows,
        admin_rows=admin,
        run_upstream_if_needed=False,
        write_cache=False,
    )
    assert state.kpis["referential_not_modified"] is True
    assert state.kpis["auto_creation_disabled"] is True
    assert state.simulation["applied"] is False
    assert state.kpis["CURRENT_LOCALITIES"] == len(admin)
    for r in state.rows:
        assert r.get("auto_created") is False
        assert r.get("referential_modified") is False


def test_controlled_geometry_and_identity_rules(tmp_path, monkeypatch):
    from api.services.nire import locality_controlled_integration as lci

    official = {
        "locality_referential": [
            {
                "canonical_id": "ADM-A",
                "nom": "Village Alpha",
                "province": "Haut-Katanga",
                "territoire": "Kipushi",
                "geometry": {"type": "Point", "coordinates": [27.25, -11.76, 0]},
            }
        ]
    }
    off_path = tmp_path / "official.json"
    enr_path = tmp_path / "enrichment.json"
    off_path.write_text(__import__("json").dumps(official), encoding="utf-8")
    monkeypatch.setattr(lci, "OFFICIAL_JSON", off_path)
    monkeypatch.setattr(lci, "ENRICHMENT_JSON", enr_path)
    monkeypatch.setattr(lci, "MANIFEST_JSON", tmp_path / "manifest.json")
    monkeypatch.setattr(lci, "QUALITY_JSON", tmp_path / "quality.json")
    monkeypatch.setattr(lci, "PRE_STATE_JSON", tmp_path / "pre.json")
    monkeypatch.setattr(lci, "RUN_CACHE_JSON", tmp_path / "run.json")

    # Valid + absent → integrate
    # Invalid geom → not
    # Existing same context → already
    # Homonym other territory → integrate distinct
    # Nearby different name → integrate distinct
    # Covered+uncovered same identity → one
    covered = [
        {
            "id": "C1",
            "destination": "Village Alpha",
            "name": "x",
            "province": "Haut-Katanga",
            "territoire": "Kipushi",
            "latitude": -11.76,
            "longitude": 27.25,
            "coverage_status": "covered",
            "population": 10,
        },
        {
            "id": "C2",
            "destination": "Kasongo",
            "name": "x",
            "province": "Haut-Katanga",
            "territoire": "Kipushi",
            "latitude": -11.77,
            "longitude": 27.26,
            "coverage_status": "covered",
            "population": 20,
        },
    ]
    uncovered = [
        {
            "id": "U1",
            "destination": "Village Alpha",
            "name": "x",
            "province": "Haut-Katanga",
            "territoire": "Kipushi",
            "latitude": -11.76,
            "longitude": 27.25,
            "coverage_status": "uncovered",
            "population": 10,
        },
        {
            "id": "U2",
            "destination": "Camp Nord Unique",
            "name": "x",
            "province": "Haut-Katanga",
            "territoire": "Kipushi",
            "latitude": -11.7605,
            "longitude": 27.2505,
            "coverage_status": "uncovered",
            "population": 30,
        },
        {
            "id": "U3",
            "destination": "Bad Point",
            "name": "x",
            "province": "Haut-Katanga",
            "territoire": "Kipushi",
            "latitude": 0,
            "longitude": 0,
            "coverage_status": "uncovered",
            "population": 1,
        },
        {
            "id": "U4",
            "destination": "Village Alphaa",
            "name": "x",
            "province": "Haut-Katanga",
            "territoire": "Kipushi",
            "latitude": -11.761,
            "longitude": 27.251,
            "coverage_status": "uncovered",
            "population": 5,
        },
    ]

    st1 = lci.run_controlled_integration(
        covered_rows=covered, uncovered_rows=uncovered, apply=True, write_cache=True
    )
    assert st1.kpis["INSERTED_SECOND_RUN"] == 0
    assert st1.kpis["idempotent"] is True
    assert st1.kpis["OLD_LOCALITIES"] == 1
    by = {r["nci_id"]: r["classification"] for r in st1.rows if r.get("is_canonical_representative")}
    # Village Alpha covered+uncovered → already (one identity)
    alpha_rows = [r for r in st1.rows if r.get("toponym") == "Village Alpha"]
    assert any(r["classification"] == "ALREADY_IN_REFERENTIAL" for r in alpha_rows if r.get("is_canonical_representative"))
    assert sum(1 for r in alpha_rows if r["classification"] == "DUPLICATE_NCI_OBSERVATION") >= 1
    assert by.get("U3") == "INVALID_GEOMETRY" or any(
        r["nci_id"] == "U3" and r["classification"] == "INVALID_GEOMETRY" for r in st1.rows
    )
    assert any(
        r.get("toponym") == "Camp Nord Unique" and r["classification"] == "NEW_LOCALITY_WITH_VALID_GEOMETRY"
        for r in st1.rows
        if r.get("is_canonical_representative")
    )
    assert any(
        r.get("toponym") == "Kasongo" and r["classification"] == "NEW_LOCALITY_WITH_VALID_GEOMETRY"
        for r in st1.rows
        if r.get("is_canonical_representative")
    )
    # Variante Alphaa → already
    assert any(
        r.get("toponym") == "Village Alphaa" and r["classification"] == "ALREADY_IN_REFERENTIAL"
        for r in st1.rows
        if r.get("is_canonical_representative")
    )
    # Nearby distinct
    assert st1.kpis["NEW_LOCALITIES_ADDED"] >= 2
    ids = [x["canonical_id"] for x in lci.load_enrichment_doc().get("locality_referential") or []]
    assert len(ids) == len(set(ids))

    st2 = lci.run_controlled_integration(
        covered_rows=covered, uncovered_rows=uncovered, apply=True, write_cache=False
    )
    assert st2.kpis["INSERTED_FIRST_RUN"] == 0
    assert st2.kpis["INSERTED_SECOND_RUN"] == 0


def test_national_referential_fusion_totals():
    from api.services.nire import locality_controlled_integration as lci

    base = lci.national_locality_count(include_enrichment=False)
    enr = len(lci.load_enrichment_doc().get("locality_referential") or [])
    total = lci.national_locality_count(include_enrichment=True)
    assert base == 26710
    assert enr == 20420
    assert total == 47130
    assert base + enr == total
    # Pas de collision d'id entre couches
    official_ids = {
        x.get("canonical_id")
        for x in __import__("json").loads(
            lci.OFFICIAL_JSON.read_text(encoding="utf-8")
        ).get("locality_referential")
        or []
    }
    nci_ids = {x.get("canonical_id") for x in lci.load_enrichment_doc().get("locality_referential") or []}
    assert official_ids.isdisjoint(nci_ids)
    assert all(str(i).startswith("RDC-NCI-LOC-") for i in nci_ids)


def test_localites_count_api_uses_fusion_even_in_db_mode(monkeypatch):
    """Le total national enrichi ne doit pas être écrasé par COUNT(*) Postgres historique."""
    from fastapi.testclient import TestClient

    import api.main as main_mod

    monkeypatch.setattr(main_mod, "use_database", lambda: True)
    client = TestClient(main_mod.app)
    resp = client.get("/localites/count")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 47130
    assert body.get("base_count") == 26710
    assert body.get("enrichment_count") == 20420
    assert "nci_enrichment" in body.get("source", "")


def test_enriched_locality_searchable_by_name():
    from api.services.nire import locality_controlled_integration as lci

    items = lci.load_national_locality_items(include_enrichment=True)
    hit = next((x for x in items if (x.get("nom") or "").startswith("Likati") and str(x.get("canonical_id") or "").startswith("RDC-NCI-LOC-")), None)
    assert hit is not None
    assert hit.get("provenance") in {"nci_fdsu", "NCI/FDSU"} or hit.get("source") == "NCI/FDSU"
