#!/usr/bin/env python3
"""Initialize the database schema for development.

Usage:
  python scripts/init_db.py

This script calls `app.database.create_all_tables()` to create tables defined
by SQLAlchemy models. For production use, prefer Alembic migrations instead.
"""
from app.database import create_all_tables


def main() -> None:
    print("Creating database tables from SQLAlchemy models (development).")
    create_all_tables()
    print("Done.")


if __name__ == "__main__":
    main()
