"""Tests ciblés — pas de run_mno_audit si staging FDSU MNO déjà peuplé."""

from __future__ import annotations

import os
from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest

os.environ.setdefault("DATA_MODE", os.environ.get("DATA_MODE", "json"))


@pytest.fixture()
def telecom_mod(monkeypatch):
    from api.services import telecom_service as ts
    from api.services import shared_spatial_context as ssc

    audit_calls = {"n": 0}

    def fake_audit(*_a, **_k):
        audit_calls["n"] += 1
        return {
            "row_id": "AUDIT-1",
            "operator_code": "AIRTEL",
            "site_name": "AuditSite",
            "distance_m": 100.0,
            "data_source": "FDSU_MNO_AUDIT",
        }

    monkeypatch.setattr(ts, "_nearest_mno_audit_operator", fake_audit)
    yield ts, ssc, audit_calls


def _fake_connect(fetchone_result):
    """Context manager mimant connect_db + cursor.fetchone."""

    @contextmanager
    def _cm(**_kwargs):
        conn = MagicMock()
        cur = MagicMock()
        cur.fetchone.return_value = fetchone_result
        cur_cm = MagicMock()
        cur_cm.__enter__.return_value = cur
        cur_cm.__exit__.return_value = False
        conn.cursor.return_value = cur_cm
        yield conn

    return _cm


def test_staging_ready_operator_miss_returns_none_no_audit(telecom_mod, monkeypatch):
    ts, ssc, audit_calls = telecom_mod
    monkeypatch.setattr(ssc, "ensure_fdsu_mno_staging_ready", lambda **_k: {"ready": True, "rows": 12611})
    monkeypatch.setattr(ts, "connect_db", _fake_connect(None))

    out = ts._nearest_fdsu_operator(-4.3, 15.3, "AIRTEL", 25000)
    assert out is None
    assert audit_calls["n"] == 0


def test_staging_ready_hit_returns_staging_row(telecom_mod, monkeypatch):
    ts, ssc, audit_calls = telecom_mod
    monkeypatch.setattr(ssc, "ensure_fdsu_mno_staging_ready", lambda **_k: {"ready": True, "rows": 12611})
    row = {
        "row_id": "R1",
        "operator_code": "AIRTEL",
        "site_name": "SiteA",
        "status_normalized": "ON_AIR",
        "nire_quality_status": "ok",
        "latitude": -4.3,
        "longitude": 15.3,
        "distance_m": 120.0,
    }
    monkeypatch.setattr(ts, "connect_db", _fake_connect(row))

    out = ts._nearest_fdsu_operator(-4.3, 15.3, "AIRTEL", 25000)
    assert out is not None
    assert out["data_source"] == "FDSU_MNO_STAGING"
    assert out["row_id"] == "R1"
    assert audit_calls["n"] == 0


def test_staging_empty_allows_audit_fallback(telecom_mod, monkeypatch):
    ts, ssc, audit_calls = telecom_mod
    monkeypatch.setattr(ssc, "ensure_fdsu_mno_staging_ready", lambda **_k: {"ready": True, "rows": 0})
    monkeypatch.setattr(ts, "connect_db", _fake_connect(None))

    out = ts._nearest_fdsu_operator(-4.3, 15.3, "AIRTEL", 25000)
    assert out is not None
    assert out["data_source"] == "FDSU_MNO_AUDIT"
    assert audit_calls["n"] == 1


def test_postgis_exception_with_staging_ready_no_audit(telecom_mod, monkeypatch):
    ts, ssc, audit_calls = telecom_mod
    monkeypatch.setattr(ssc, "ensure_fdsu_mno_staging_ready", lambda **_k: {"ready": True, "rows": 12611})

    @contextmanager
    def boom(**_kwargs):
        raise RuntimeError("postgis-down")
        yield  # pragma: no cover

    monkeypatch.setattr(ts, "connect_db", boom)

    out = ts._nearest_fdsu_operator(-4.3, 15.3, "AFRICELL", 25000)
    assert out is None
    assert audit_calls["n"] == 0
