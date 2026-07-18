"""Tests consolidation FDSU sites opérateurs — pas d'infra physique mutualisée."""
from __future__ import annotations

from pathlib import Path

import openpyxl

from api.services.telecom_operator_sites_consolidation import (
    consolidate_mobile_operator_sites,
)


def _mno(path: Path, rows: list[list]) -> Path:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Site Name", "Latitude", "Longitude", "RAT", "Status", "Operator name"])
    for row in rows:
        ws.append(row)
    wb.save(path)
    return path


def test_vodacom_same_site_counted_once(tmp_path):
    db = {
        "VODACOM": [
            {
                "id": 1,
                "infra_name": "SiteAlpha_KIN",
                "latitude": -4.320000,
                "longitude": 15.310000,
                "status": "Online",
                "properties": {"Site_Name": "SiteAlpha_KIN"},
            }
        ],
        "ORANGE": [],
    }
    # Small GPS drift, same name
    mno = _mno(
        tmp_path / "m.xlsx",
        [["SiteAlpha_KIN", -4.320100, 15.310000, "2G", "Online", "Vodacom"]],
    )
    res = consolidate_mobile_operator_sites(mno, db_by_operator=db)
    assert res.by_operator["VODACOM"]["correspondances_doublons_ancien_nouveau"] == 1
    assert res.by_operator["VODACOM"]["nouveaux_sites_ajoutes"] == 0
    assert res.by_operator["VODACOM"]["total_consolide"] == 1


def test_vodacom_new_added_old_kept(tmp_path):
    db = {
        "VODACOM": [
            {
                "id": 1,
                "infra_name": "OldOnly",
                "latitude": -4.0,
                "longitude": 15.0,
                "status": "Online",
                "properties": {},
            }
        ],
        "ORANGE": [],
    }
    mno = _mno(
        tmp_path / "m.xlsx",
        [["BrandNew", -5.0, 16.0, "2G", "Online", "Vodacom"]],
    )
    res = consolidate_mobile_operator_sites(mno, db_by_operator=db)
    assert res.by_operator["VODACOM"]["nouveaux_sites_ajoutes"] == 1
    assert res.by_operator["VODACOM"]["anciens_conserves_absents_mno"] == 1
    assert res.by_operator["VODACOM"]["total_consolide"] == 2


def test_orange_same_and_new(tmp_path):
    db = {
        "VODACOM": [],
        "ORANGE": [
            {
                "id": 10,
                "infra_name": "OrangeOne",
                "latitude": -4.5,
                "longitude": 15.5,
                "status": "Online",
                "properties": {"Site_Name": "OrangeOne"},
            }
        ],
    }
    mno = _mno(
        tmp_path / "m.xlsx",
        [
            ["OrangeOne", -4.500050, 15.500000, "2G", "Online", "Orange"],
            ["OrangeNew", -6.0, 20.0, "2G", "Online", "Orange"],
        ],
    )
    res = consolidate_mobile_operator_sites(mno, db_by_operator=db)
    assert res.by_operator["ORANGE"]["correspondances_doublons_ancien_nouveau"] == 1
    assert res.by_operator["ORANGE"]["nouveaux_sites_ajoutes"] == 1
    assert res.by_operator["ORANGE"]["total_consolide"] == 2


def test_airtel_africell_kept(tmp_path):
    db = {"VODACOM": [], "ORANGE": []}
    mno = _mno(
        tmp_path / "m.xlsx",
        [
            ["A1", -4.1, 15.1, "2G", "Online", "Airtel"],
            ["A2", -4.2, 15.2, "2G", "Planned", "Airtel"],
            ["F1", -4.3, 15.3, "2G", "Online", "Africell"],
        ],
    )
    res = consolidate_mobile_operator_sites(mno, db_by_operator=db)
    assert res.by_operator["AIRTEL"]["total_consolide"] == 2
    assert res.by_operator["AFRICELL"]["total_consolide"] == 1
    assert res.totals["TOTAL_PLANNED"] == 1
    assert res.totals["TOTAL_EXISTING_MOBILE_OPERATOR_SITES"] == 2


def test_vodacom_airtel_same_coords_two_operator_sites(tmp_path):
    db = {
        "VODACOM": [
            {
                "id": 1,
                "infra_name": "SharedPlace",
                "latitude": -4.32,
                "longitude": 15.31,
                "status": "Online",
                "properties": {"Site_Name": "SharedPlace"},
            }
        ],
        "ORANGE": [],
    }
    mno = _mno(
        tmp_path / "m.xlsx",
        [
            ["SharedPlace", -4.32, 15.31, "2G", "Online", "Vodacom"],
            ["AirtelHere", -4.32, 15.31, "2G", "Online", "Airtel"],
        ],
    )
    res = consolidate_mobile_operator_sites(mno, db_by_operator=db)
    assert res.by_operator["VODACOM"]["total_consolide"] == 1
    assert res.by_operator["AIRTEL"]["total_consolide"] == 1
    assert res.totals["TOTAL_MOBILE_OPERATOR_SITES_ALL"] == 2


def test_planned_excluded_from_existing_only(tmp_path):
    db = {"VODACOM": [], "ORANGE": []}
    mno = _mno(
        tmp_path / "m.xlsx",
        [
            ["P1", -4.0, 15.0, "2G", "Planned", "Airtel"],
            ["E1", -4.1, 15.1, "2G", "Online", "Airtel"],
        ],
    )
    res = consolidate_mobile_operator_sites(mno, db_by_operator=db)
    assert res.totals["TOTAL_MOBILE_OPERATOR_SITES_ALL"] == 2
    assert res.totals["TOTAL_EXISTING_MOBILE_OPERATOR_SITES"] == 1
    assert res.totals["TOTAL_PLANNED"] == 1


def test_proximity_alone_does_not_merge_vodacom(tmp_path):
    db = {
        "VODACOM": [
            {
                "id": 1,
                "infra_name": "TowerAlpha",
                "latitude": -4.320000,
                "longitude": 15.310000,
                "status": "Online",
                "properties": {},
            }
        ],
        "ORANGE": [],
    }
    mno = _mno(
        tmp_path / "m.xlsx",
        [["TowerBetaTotallyDifferent", -4.320100, 15.310000, "2G", "Online", "Vodacom"]],
    )
    res = consolidate_mobile_operator_sites(mno, db_by_operator=db)
    assert res.by_operator["VODACOM"]["correspondances_doublons_ancien_nouveau"] == 0
    assert res.by_operator["VODACOM"]["total_consolide"] == 2
