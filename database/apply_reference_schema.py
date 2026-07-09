#!/usr/bin/env python3
"""Applique le National Reference Framework et initialise le catalogue."""

from __future__ import annotations

import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import Json

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import DATABASE_URL

SCHEMA_SQL = PROJECT_ROOT / "database" / "reference_schema.sql"

CATALOG_ENTRIES = [
    {
        "code": "ADMIN",
        "name": "Référentiel administratif national",
        "category": "core",
        "description": "Provinces, territoires, collectivités, groupements, localités.",
        "source_name": "SIG-FDSU RDC",
        "source_type": "postgis",
        "update_frequency": "continuous",
        "status": "active",
        "metadata": {"layer": "administrative"},
    },
    {
        "code": "TELECOM",
        "name": "Référentiel Télécommunications",
        "category": "sectorial",
        "description": "Opérateurs, infrastructures, lignes et polygones de couverture.",
        "source_name": "MNO / FDSU",
        "source_type": "kmz",
        "update_frequency": "quarterly",
        "status": "active",
        "metadata": {"objects": 31401},
    },
    {
        "code": "PROGRAMS",
        "name": "Programmes FDSU",
        "category": "core",
        "description": "Sites 40, Sites 300 et catalogues programmes.",
        "source_name": "FDSU",
        "source_type": "kmz",
        "update_frequency": "monthly",
        "status": "active",
        "metadata": {},
    },
    {
        "code": "DECISION",
        "name": "Moteur de décision FDSU",
        "category": "analytics",
        "description": "Scores de priorisation des sites FDSU.",
        "source_name": "FDSU Decision Engine",
        "source_type": "computed",
        "update_frequency": "on_demand",
        "status": "active",
        "metadata": {"version": "1.0.0"},
    },
    {
        "code": "HEALTH",
        "name": "Référentiel Santé",
        "category": "sectorial",
        "description": "Structures sanitaires : hôpitaux, centres et postes de santé.",
        "source_name": "À intégrer",
        "source_type": "pending",
        "update_frequency": "unknown",
        "status": "in_progress",
        "metadata": {"version": "1.0.0"},
    },
    {
        "code": "EDUCATION",
        "name": "Référentiel Éducation",
        "category": "sectorial",
        "description": "Écoles, lycées et infrastructures éducatives.",
        "source_name": "À intégrer",
        "source_type": "planned",
        "update_frequency": "unknown",
        "status": "planned",
        "metadata": {},
    },
    {
        "code": "ENERGY",
        "name": "Référentiel Énergie",
        "category": "sectorial",
        "description": "Infrastructures énergétiques et réseaux électriques.",
        "source_name": "À intégrer",
        "source_type": "planned",
        "update_frequency": "unknown",
        "status": "planned",
        "metadata": {},
    },
    {
        "code": "ROADS",
        "name": "Référentiel Routes",
        "category": "sectorial",
        "description": "Réseau routier et axes de desserte.",
        "source_name": "À intégrer",
        "source_type": "planned",
        "update_frequency": "unknown",
        "status": "planned",
        "metadata": {},
    },
    {
        "code": "POPULATION",
        "name": "Référentiel Population",
        "category": "sectorial",
        "description": "Données démographiques et couverture populationnelle.",
        "source_name": "À intégrer",
        "source_type": "planned",
        "update_frequency": "unknown",
        "status": "planned",
        "metadata": {},
    },
]


def seed_catalog(conn) -> None:
    with conn.cursor() as cur:
        for entry in CATALOG_ENTRIES:
            cur.execute(
                """
                INSERT INTO reference.reference_catalog (
                    code, name, category, description, source_name, source_type,
                    update_frequency, status, metadata, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (code) DO UPDATE SET
                    name = EXCLUDED.name,
                    category = EXCLUDED.category,
                    description = EXCLUDED.description,
                    source_name = EXCLUDED.source_name,
                    source_type = EXCLUDED.source_type,
                    update_frequency = EXCLUDED.update_frequency,
                    status = EXCLUDED.status,
                    metadata = EXCLUDED.metadata,
                    updated_at = NOW()
                """,
                (
                    entry["code"],
                    entry["name"],
                    entry["category"],
                    entry["description"],
                    entry["source_name"],
                    entry["source_type"],
                    entry["update_frequency"],
                    entry["status"],
                    Json(entry["metadata"]),
                ),
            )
    conn.commit()


def main() -> None:
    sql = SCHEMA_SQL.read_text(encoding="utf-8")
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        seed_catalog(conn)
    print("Schéma reference appliqué et catalogue initialisé.")


if __name__ == "__main__":
    main()
