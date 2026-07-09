#!/usr/bin/env python3
"""Applique le référentiel Santé v1.0 (structure + types, sans données fictives)."""

from __future__ import annotations

import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import Json

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import DATABASE_URL

SCHEMA_SQL = PROJECT_ROOT / "database" / "health_schema.sql"

FACILITY_TYPES = [
    ("HGR", "Hôpital Général de Référence", "Hôpital de référence", "hospital", {"color": "#dc2626", "icon": "hospital"}),
    ("HOSPITAL", "Hôpital", "Hôpital", "hospital", {"color": "#b91c1c", "icon": "hospital"}),
    ("CH", "Centre Hospitalier", "Centre hospitalier", "hospital", {"color": "#ef4444", "icon": "hospital"}),
    ("CS", "Centre de Santé", "Centre de santé de proximité", "health_center", {"color": "#ea580c", "icon": "clinic"}),
    ("CSR", "Centre de Santé de Référence", "Centre de santé de référence", "health_center", {"color": "#f97316", "icon": "clinic"}),
    ("PS", "Poste de Santé", "Poste de santé communautaire", "health_post", {"color": "#eab308", "icon": "health-post"}),
    ("CM", "Centre Médical", "Centre médical", "clinic", {"color": "#a855f7", "icon": "clinic"}),
    ("CLINIC", "Clinique", "Clinique privée ou associée", "clinic", {"color": "#8b5cf6", "icon": "clinic"}),
    ("POLYCLINIC", "Polyclinique", "Polyclinique", "clinic", {"color": "#7c3aed", "icon": "clinic"}),
    ("DISP", "Dispensaire", "Dispensaire", "health_post", {"color": "#ca8a04", "icon": "health-post"}),
    ("SSC", "Site Soin Communautaire", "Site de soin communautaire", "community", {"color": "#16a34a", "icon": "community"}),
    ("BCZS", "Bureau Central de la Zone de Santé", "Bureau central de zone de santé", "admin", {"color": "#0f766e", "icon": "admin"}),
    ("MAT", "Maternité", "Structure maternelle", "maternity", {"color": "#ec4899", "icon": "maternity"}),
    ("OTHER", "Autre structure sanitaire", "Autre type de structure", "other", {"color": "#64748b", "icon": "other"}),
]

HEALTH_OBJECT_TYPES = [
    ("HGR", "Hôpital Général de Référence", "Hôpital de référence", {"color": "#dc2626"}),
    ("HOSPITAL", "Hôpital", "Hôpital", {"color": "#b91c1c"}),
    ("CH", "Centre Hospitalier", "Centre hospitalier", {"color": "#ef4444"}),
    ("CS", "Centre de Santé", "Centre de santé", {"color": "#ea580c"}),
    ("CSR", "Centre de Santé de Référence", "CSR", {"color": "#f97316"}),
    ("PS", "Poste de Santé", "Poste de santé", {"color": "#eab308"}),
    ("CM", "Centre Médical", "Centre médical", {"color": "#a855f7"}),
    ("CLINIC", "Clinique", "Clinique", {"color": "#8b5cf6"}),
    ("POLYCLINIC", "Polyclinique", "Polyclinique", {"color": "#7c3aed"}),
    ("DISP", "Dispensaire", "Dispensaire", {"color": "#ca8a04"}),
    ("SSC", "Site Soin Communautaire", "Site de soin communautaire", {"color": "#16a34a"}),
    ("BCZS", "Bureau Central de la Zone de Santé", "BCZS", {"color": "#0f766e"}),
    ("MAT", "Maternité", "Maternité", {"color": "#ec4899"}),
    ("OTHER", "Autre structure sanitaire", "Autre", {"color": "#64748b"}),
]


def seed_facility_types(conn) -> None:
    with conn.cursor() as cur:
        for code, name, description, category, symbology in FACILITY_TYPES:
            cur.execute(
                """
                INSERT INTO health.health_facility_types (code, name, description, category, symbology)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (code) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    category = EXCLUDED.category,
                    symbology = EXCLUDED.symbology
                """,
                (code, name, description, category, Json(symbology)),
            )
    conn.commit()


def seed_reference_object_types(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO reference.reference_catalog (code, name, category, status, metadata)
            VALUES ('HEALTH', 'Référentiel Santé', 'sectorial', 'in_progress', '{}'::jsonb)
            ON CONFLICT (code) DO NOTHING
            """
        )
        for type_code, type_name, description, symbology in HEALTH_OBJECT_TYPES:
            cur.execute(
                """
                INSERT INTO reference.reference_object_types (
                    reference_code, type_code, type_name, description, symbology
                )
                VALUES ('HEALTH', %s, %s, %s, %s)
                ON CONFLICT (reference_code, type_code) DO UPDATE SET
                    type_name = EXCLUDED.type_name,
                    description = EXCLUDED.description,
                    symbology = EXCLUDED.symbology
                """,
                (type_code, type_name, description, Json(symbology)),
            )
    conn.commit()


def seed_empty_statistics(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO health.health_statistics (
                scope_type, scope_name, total_facilities, hospitals, health_centers,
                health_posts, facilities_with_geometry, facilities_without_geometry,
                facilities_with_electricity, facilities_with_internet, details
            )
            SELECT 'national', 'RDC', 0, 0, 0, 0, 0, 0, 0, 0, '{"status":"empty"}'::jsonb
            WHERE NOT EXISTS (
                SELECT 1 FROM health.health_statistics
                WHERE scope_type = 'national' AND scope_name = 'RDC'
            )
            """
        )
    conn.commit()


def main() -> None:
    sql = SCHEMA_SQL.read_text(encoding="utf-8")
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        seed_facility_types(conn)
        seed_reference_object_types(conn)
        seed_empty_statistics(conn)
    print("Schéma health appliqué (types initiaux, statistiques vides).")


if __name__ == "__main__":
    main()
