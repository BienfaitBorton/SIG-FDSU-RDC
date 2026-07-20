"""Tests unitaires — timeouts défensifs de connect_db (aucun réseau/DB réel)."""

from __future__ import annotations

import pytest


def _clear_timeout_env(monkeypatch):
    monkeypatch.delenv("DB_CONNECT_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("DB_STATEMENT_TIMEOUT_MS", raising=False)


def test_connect_db_applies_default_timeouts(monkeypatch):
    import api.config as cfg

    _clear_timeout_env(monkeypatch)
    captured = {}

    def fake_connect(dsn, **kwargs):
        captured["dsn"] = dsn
        captured["kwargs"] = kwargs
        return object()

    monkeypatch.setattr("psycopg2.connect", fake_connect)

    cfg.connect_db()

    assert captured["dsn"] == cfg.DATABASE_URL
    assert captured["kwargs"]["connect_timeout"] == 5
    assert captured["kwargs"]["options"] == "-c statement_timeout=30000"


def test_connect_db_respects_env_overrides(monkeypatch):
    import api.config as cfg

    monkeypatch.setenv("DB_CONNECT_TIMEOUT_SECONDS", "12")
    monkeypatch.setenv("DB_STATEMENT_TIMEOUT_MS", "45000")
    captured = {}

    def fake_connect(dsn, **kwargs):
        captured["dsn"] = dsn
        captured["kwargs"] = kwargs
        return object()

    monkeypatch.setattr("psycopg2.connect", fake_connect)

    cfg.connect_db()

    assert captured["dsn"] == cfg.DATABASE_URL
    assert captured["kwargs"]["connect_timeout"] == 12
    assert captured["kwargs"]["options"] == "-c statement_timeout=45000"


def test_connect_db_preserves_caller_overrides(monkeypatch):
    import api.config as cfg

    _clear_timeout_env(monkeypatch)
    captured = {}

    def fake_connect(dsn, **kwargs):
        captured["dsn"] = dsn
        captured["kwargs"] = kwargs
        return object()

    monkeypatch.setattr("psycopg2.connect", fake_connect)

    cfg.connect_db(
        connect_timeout=99,
        options="-c search_path=telecom -c statement_timeout=90000",
    )

    assert captured["dsn"] == cfg.DATABASE_URL
    assert captured["kwargs"]["connect_timeout"] == 99
    assert (
        captured["kwargs"]["options"]
        == "-c search_path=telecom -c statement_timeout=90000"
    )


def test_connect_db_merges_statement_timeout_into_caller_options(monkeypatch):
    import api.config as cfg

    _clear_timeout_env(monkeypatch)
    captured = {}

    def fake_connect(dsn, **kwargs):
        captured["kwargs"] = kwargs
        return object()

    monkeypatch.setattr("psycopg2.connect", fake_connect)

    cfg.connect_db(options="-c search_path=public")

    assert captured["kwargs"]["connect_timeout"] == 5
    assert (
        captured["kwargs"]["options"]
        == "-c search_path=public -c statement_timeout=30000"
    )


def test_connect_db_preserves_database_url(monkeypatch):
    import api.config as cfg

    _clear_timeout_env(monkeypatch)
    expected_url = cfg.DATABASE_URL
    assert expected_url  # sanity
    captured = {}

    def fake_connect(dsn, **kwargs):
        captured["dsn"] = dsn
        return object()

    monkeypatch.setattr("psycopg2.connect", fake_connect)

    cfg.connect_db()

    assert captured["dsn"] is expected_url
    assert cfg.DATABASE_URL == expected_url


def test_connect_db_does_not_retry_on_statement_timeout_error(monkeypatch):
    import api.config as cfg
    import psycopg2

    _clear_timeout_env(monkeypatch)
    calls = {"n": 0}

    def fake_connect(dsn, **kwargs):
        calls["n"] += 1
        raise psycopg2.OperationalError(
            "canceling statement due to statement timeout"
        )

    monkeypatch.setattr("psycopg2.connect", fake_connect)

    with pytest.raises(psycopg2.OperationalError, match="statement timeout"):
        cfg.connect_db()

    assert calls["n"] == 1
