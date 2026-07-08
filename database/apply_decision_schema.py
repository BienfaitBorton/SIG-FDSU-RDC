#!/usr/bin/env python3
"""Applique le schéma decision (Moteur de Décision FDSU v1.0)."""

from __future__ import annotations

import sys
from pathlib import Path

import psycopg2

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import DATABASE_URL

SCHEMA_SQL = PROJECT_ROOT / "database" / "decision_schema.sql"


def main() -> None:
    sql = SCHEMA_SQL.read_text(encoding="utf-8")
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
    print("Schéma decision appliqué.")


if __name__ == "__main__":
    main()
