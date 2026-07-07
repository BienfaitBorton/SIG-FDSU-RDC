"""Configuration centrale SIG-FDSU RDC.

Source unique pour PostgreSQL/PostGIS et le mode de données (json / db).
Les variables d'environnement priment sur le fichier `.env` à la racine du projet.
"""
from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Valeurs par défaut unifiées (PostgreSQL local de développement).
DEFAULT_DB_HOST = "localhost"
DEFAULT_DB_PORT = "5432"
DEFAULT_DB_NAME = "sig_fdsu_rdc"
DEFAULT_DB_USER = "postgres"
DEFAULT_DB_PASSWORD = "test123"
DEFAULT_DATA_MODE = "json"


def load_dotenv_file() -> None:
    """Charge `.env` depuis la racine du projet si le fichier existe."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    env_path = PROJECT_ROOT / ".env"
    if env_path.is_file():
        load_dotenv(env_path, override=False)


load_dotenv_file()


def _env(key: str, default: str) -> str:
    value = os.environ.get(key)
    if value is None or not str(value).strip():
        return default
    return str(value).strip()


DB_HOST = _env("DB_HOST", DEFAULT_DB_HOST)
DB_PORT = _env("DB_PORT", DEFAULT_DB_PORT)
DB_NAME = _env("DB_NAME", DEFAULT_DB_NAME)
DB_USER = _env("DB_USER", DEFAULT_DB_USER)
DB_PASSWORD = _env("DB_PASSWORD", DEFAULT_DB_PASSWORD)


def build_database_url() -> str:
    """Construit l'URL PostgreSQL à partir de DATABASE_URL ou des variables DB_*."""
    explicit = os.environ.get("DATABASE_URL")
    if explicit and str(explicit).strip():
        return str(explicit).strip()
    return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


DATABASE_URL = build_database_url()
DATA_MODE = _env("DATA_MODE", DEFAULT_DATA_MODE).lower()
