"""Tests intégration native Sites 20 476 → programs.fdsu_sites / NSME."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("DATA_MODE", "db")

from api.config import DATA_MODE
from api.services import (
    fdsu_site_priority_service,
    fdsu_sites_inventory_service,
    fdsu_sites_nsme_sync_service,
    spatial_matching_service,
)
from api.services.sdg_coverage_service import build_coverage_report
from api.services.site_display_name import is_technical_site_identifier


pytestmark = pytest.mark.skipif(DATA_MODE != "db", reason="Nécessite DATA_MODE=db")


@pytest.fixture(scope="module")
def sync_once():
    status = fdsu_sites_nsme_sync_service.nsme_status_20476()
    if not status.get("native"):
        return fdsu_sites_nsme_sync_service.sync_sites_20476_to_nsme()
    return {
        "nsme_count_after": status["nsme_count"],
        "source_count": status["source_count"],
        "integrated_natively": True,
    }


def test_nsme_20476_integrated(sync_once):
    assert sync_once["integrated_natively"] or sync_once.get("nsme_count_after") == 20476
    status = fdsu_sites_nsme_sync_service.nsme_status_20476()
    assert status["native"] is True
    assert status["nsme_count"] == 20476
    assert status["pending"] == 0
    assert status["nominal_path"] == "programs.fdsu_sites"
    assert spatial_matching_service.count_fdsu_sites(program_code="sites_20476") == 20476


def test_idempotence_no_duplication(sync_once):
    before = spatial_matching_service.count_fdsu_sites(program_code="sites_20476")
    second = fdsu_sites_nsme_sync_service.sync_sites_20476_to_nsme()
    after = spatial_matching_service.count_fdsu_sites(program_code="sites_20476")
    assert before == after == 20476
    assert second["new_rows"] == 0
    assert second["duplicates_avoided_on_rerun"] == 20476
    assert second["nsme_count_after"] == 20476


def test_technical_id_and_display_name_preserved(sync_once):
    rows = spatial_matching_service.list_fdsu_sites(program_code="sites_20476", limit=50)
    assert rows
    with_tech = [r for r in rows if r.get("technical_id")]
    assert len(with_tech) >= 40
    for row in with_tech[:10]:
        assert is_technical_site_identifier(row["technical_id"])
        assert row.get("display_name") or row.get("site_name")
        # Libellé principal ≠ technique lorsque infra_name disponible
        if row.get("infra_name"):
            assert row["display_name"] == row["infra_name"] or row["site_name"] == row["infra_name"]
            assert row["technical_id"] != row["display_name"]


def test_programs_40_300_not_regressed(sync_once):
    assert spatial_matching_service.count_fdsu_sites(program_code="sites_40") == 40
    assert spatial_matching_service.count_fdsu_sites(program_code="sites_300") == 300
    inv = fdsu_sites_inventory_service.inventory_summary()
    assert inv["counts"]["sites_40"] == 40
    assert inv["counts"]["sites_300"] == 300
    assert inv["counts"]["portfolio_340"] == 340
    assert inv["counts"]["primary"] == 20476
    labels = [p.get("label") for p in inv["programs"]]
    assert not any("340" in str(l) and "Sites" in str(l) for l in labels if "20" not in str(l))


def test_is_300_planned_flag_count(sync_once):
    # Compte via sync meta ou inventaire
    dry = fdsu_sites_nsme_sync_service.sync_sites_20476_to_nsme(dry_run=True)
    assert dry["is_300_planned"] == 272


def test_sdg_uses_native_nsme_not_file_fallback(sync_once):
    report = build_coverage_report(deep_sample_per_program=0, include_ccn=True)
    meta = report["_meta"]["nsme_20476"]
    assert meta["native"] is True
    assert meta["nsme_count"] == 20476
    assert meta["nominal_path"] == "programs.fdsu_sites"
    assert report["pending_nsme_load"] == 0
    assert report["nsme_native_rate"] >= 99.0
    note = report["programs"]["sites_20476"]["note"]
    assert "fallback fichier" not in note.lower() or "natif" in note.lower()
    assert "Absent de programs.fdsu_sites" not in note
    assert "NSME natif" in note or "programs.fdsu_sites" in note


def test_decision_center_still_scores_20476(sync_once):
    top = fdsu_site_priority_service.top_priorities("sites_20476", limit=3)
    assert top["summary"]["total"] == 20476
    site = top["sites"][0]
    assert site.get("display_name")
    assert site.get("technical_id") or is_technical_site_identifier(site.get("site_name"))


def test_sites_inventory_still_works(sync_once):
    page = fdsu_sites_inventory_service.list_inventory(program_code="sites_20476", limit=5)
    assert page["total"] == 20476
    assert page["sites"][0]["display_name"]
