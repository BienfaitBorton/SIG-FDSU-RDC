"""Façade API — réutilise la configuration centrale `app.config`."""

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
    "build_database_url",
    "connect_db",
]


def connect_db(**kwargs):
    """Open a psycopg2 connection using the project DATABASE_URL."""
    import psycopg2

    try:
        return psycopg2.connect(DATABASE_URL, **kwargs)
    except UnicodeDecodeError as exc:
        # Sur Windows (locale fr), libpq peut renvoyer des messages d'erreur en CP1252
        # avant la négociation client_encoding ; psycopg2 les décode alors en UTF-8.
        raise psycopg2.OperationalError(
            "Connexion PostgreSQL impossible : vérifiez DATABASE_URL, DB_PASSWORD "
            "et l'existence de la base (message serveur encodé CP1252 masqué)."
        ) from exc
