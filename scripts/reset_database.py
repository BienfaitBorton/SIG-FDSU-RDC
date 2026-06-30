#!/usr/bin/env python3
"""Reset the database schema and recreate SQLAlchemy models.

Usage:
  - Configure connection via environment variable `DATABASE_URL` or
    the following vars: `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`.
  - Defaults: user=postgres, password=test123, host=localhost, port=5432, db=postgres

This script will:
  1. Connect to PostgreSQL
  2. Drop all tables present in schema `public` (using SQLAlchemy metadata drop)
  3. Recreate tables with `Base.metadata.create_all(engine)`
  4. Verify `provinces` has expected columns and print a summary
"""
from __future__ import annotations

import os
import sys
import logging
from typing import List

from sqlalchemy import create_engine, inspect, MetaData, text
from sqlalchemy.exc import SQLAlchemyError

# Ensure project root is on sys.path so `app` package can be imported
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.models import Base

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def get_database_url() -> str:
    env = os.environ
    url = env.get("DATABASE_URL")
    if url:
        return url

    user = env.get("DB_USER", "postgres")
    password = env.get("DB_PASSWORD", "test123")
    host = env.get("DB_HOST", "localhost")
    port = env.get("DB_PORT", "5432")
    db = env.get("DB_NAME", "postgres")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


def drop_public_tables(engine) -> List[str]:
    inspector = inspect(engine)
    tables = inspector.get_table_names(schema="public")
    # Exclude PostGIS/extension-managed tables
    EXCLUDE_TABLES = {
        "spatial_ref_sys",
        "geometry_columns",
        "geography_columns",
        "raster_columns",
        "raster_overviews",
    }

    user_tables = [t for t in tables if t not in EXCLUDE_TABLES]
    if not user_tables:
        logging.info("No user tables found in schema 'public'. Nothing to drop.")
        return []

    metadata = MetaData()
    # reflect only user tables in public
    metadata.reflect(bind=engine, only=user_tables, schema="public")

    logging.info("Dropping tables: %s", ", ".join(user_tables))
    metadata.drop_all(bind=engine)
    return user_tables


def recreate_models(engine) -> None:
    logging.info("Creating tables from SQLAlchemy models...")
    Base.metadata.create_all(engine)


def verify_provinces_columns(engine) -> bool:
    inspector = inspect(engine)
    try:
        cols = inspector.get_columns("provinces", schema="public")
    except Exception:
        logging.error("Table 'provinces' does not exist after create_all().")
        return False

    col_names = {c['name'] for c in cols}
    expected = {"zone", "chef_lieu", "population", "superficie", "geom"}
    missing = expected - col_names
    if missing:
        logging.error("Missing expected columns in 'provinces': %s", ", ".join(sorted(missing)))
        return False

    logging.info("All expected columns present in 'provinces'.")
    return True


def print_schema_summary(engine) -> None:
    inspector = inspect(engine)
    tables = inspector.get_table_names(schema="public")
    if not tables:
        logging.info("No tables to summarize in schema 'public'.")
        return

    logging.info("Schema summary (schema=public):")
    for t in sorted(tables):
        logging.info("- Table: %s", t)
        cols = inspector.get_columns(t, schema="public")
        for c in cols:
            name = c.get("name")
            dtype = c.get("type")
            logging.info("    - %s: %s", name, dtype)


def main() -> int:
    url = get_database_url()
    logging.info("Connecting to database: %s", url)

    try:
        engine = create_engine(url, future=True)
    except Exception as exc:
        logging.error("Failed to create engine: %s", exc)
        return 2

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.commit()
            logging.info("Connection successful.")

            # Ensure PostGIS is available before creating geometry columns
            try:
                logging.info("Ensuring PostGIS extension is installed...")
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
                conn.commit()
            except Exception:
                logging.warning("Failed to create/verify PostGIS extension; continuing and hoping it's present.")

            dropped = drop_public_tables(engine)

            recreate_models(engine)

            ok = verify_provinces_columns(engine)

            print_schema_summary(engine)

            if not ok:
                logging.error("Verification failed. See errors above.")
                return 3

    except SQLAlchemyError as exc:
        logging.error("Database error: %s", exc)
        return 1
    except Exception as exc:
        logging.error("Unexpected error: %s", exc)
        return 1

    logging.info("Reset complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
