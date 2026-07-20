"""Façade API — réutilise la configuration centrale `app.config`."""

from __future__ import annotations

import os

from app.config import (
    DATA_MODE,
    DATABASE_URL,
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_USER,
    build_database_url,
)

__all__ = [
    "DATA_MODE",
    "DATABASE_URL",
    "DB_HOST",
    "DB_NAME",
    "DB_PASSWORD",
    "DB_PORT",
    "DB_USER",
    "DEFAULT_DB_CONNECT_TIMEOUT_SECONDS",
    "DEFAULT_DB_STATEMENT_TIMEOUT_MS",
    "build_database_url",
    "connect_db",
]

DEFAULT_DB_CONNECT_TIMEOUT_SECONDS = 5
DEFAULT_DB_STATEMENT_TIMEOUT_MS = 30000


def _positive_int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not str(raw).strip():
        return default
    try:
        value = int(str(raw).strip())
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


def _options_has_statement_timeout(options: object) -> bool:
    if options is None:
        return False
    return "statement_timeout" in str(options).lower()


def _with_defensive_timeouts(kwargs: dict) -> dict:
    """Apply default connect/statement timeouts unless the caller already set them."""
    params = dict(kwargs)

    if "connect_timeout" not in params:
        params["connect_timeout"] = _positive_int_env(
            "DB_CONNECT_TIMEOUT_SECONDS",
            DEFAULT_DB_CONNECT_TIMEOUT_SECONDS,
        )

    if not _options_has_statement_timeout(params.get("options")):
        statement_ms = _positive_int_env(
            "DB_STATEMENT_TIMEOUT_MS",
            DEFAULT_DB_STATEMENT_TIMEOUT_MS,
        )
        timeout_opt = f"-c statement_timeout={statement_ms}"
        existing = params.get("options")
        if existing is not None and str(existing).strip():
            params["options"] = f"{str(existing).strip()} {timeout_opt}"
        else:
            params["options"] = timeout_opt

    return params


def connect_db(**kwargs):
    """Open a psycopg2 connection using the project DATABASE_URL."""
    import psycopg2

    params = _with_defensive_timeouts(kwargs)
    try:
        return psycopg2.connect(DATABASE_URL, **params)
    except UnicodeDecodeError as exc:
        # Sur Windows (locale fr), libpq peut renvoyer des messages d'erreur en CP1252
        # avant la négociation client_encoding ; psycopg2 les décode alors en UTF-8.
        raise psycopg2.OperationalError(
            "Connexion PostgreSQL impossible : vérifiez DATABASE_URL, DB_PASSWORD "
            "et l'existence de la base (message serveur encodé CP1252 masqué)."
        ) from exc
