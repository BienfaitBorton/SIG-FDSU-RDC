#!/usr/bin/env python3
"""Initialise le schéma programs et importe Sites 40 / Sites 300 depuis GeoJSON.

Usage:
  python database/seed_programs_sites.py
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import DATABASE_URL

PROGRAMS_SCHEMA_SQL = PROJECT_ROOT / "database" / "programs_schema.sql"
FDSU_PROGRAMS_JSON = PROJECT_ROOT / "data" / "business" / "fdsu_programs.json"
SITES_40_GEOJSON = PROJECT_ROOT / "data" / "programs" / "sites_40" / "sites_40.geojson"
SITES_300_GEOJSON = PROJECT_ROOT / "data" / "programs" / "sites_300" / "sites_300.geojson"

EXTRA_PROGRAMS = [
    {
        "program_code": "PROG_MNO",
        "program_name": "MNO",
        "description": "Programme de partenariat avec les opérateurs mobiles (MNO) pour l'extension du service universel.",
        "status": "PLANIFIE",
        "planned_sites": 0,
    },
    {
        "program_code": "PROG_ENERGIE",
        "program_name": "Énergie",
        "description": "Programme sectoriel d'alimentation énergétique des sites et infrastructures FDSU.",
        "status": "PLANIFIE",
        "planned_sites": 0,
    },
    {
        "program_code": "PROG_ROUTES",
        "program_name": "Routes",
        "description": "Programme de connectivité routière et d'accès aux sites FDSU en zones reculées.",
        "status": "PLANIFIE",
        "planned_sites": 0,
    },
]

PROGRAM_STATUS_MAP = {
    "EN_EXECUTION": "EN_EXECUTION",
    "PLANIFIE": "PLANIFIE",
    "active": "EN_EXECUTION",
    "planned": "PLANIFIE",
    "defined": "PLANIFIE",
    "paused": "EN_PREPARATION",
    "completed": "TERMINE",
}

IMPORT_TARGETS = [
    {
        "program_code": "PROG_SITES_40",
        "geojson_path": SITES_40_GEOJSON,
        "expected_count": 40,
        "default_site_status": "En exécution",
    },
    {
        "program_code": "PROG_SITES_300",
        "geojson_path": SITES_300_GEOJSON,
        "expected_count": 300,
        "default_site_status": "Planifié",
    },
]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def apply_schema(conn) -> None:
    sql = PROGRAMS_SCHEMA_SQL.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def resolve_program_status(program: dict[str, Any]) -> str:
    if program.get("program_status"):
        return str(program["program_status"])
    return PROGRAM_STATUS_MAP.get(str(program.get("status", "")).strip(), "PLANIFIE")


def seed_program_catalog(conn) -> dict[str, int]:
    payload = load_json(FDSU_PROGRAMS_JSON)
    program_ids: dict[str, int] = {}

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("DELETE FROM programs.fdsu_sites")
        cur.execute("DELETE FROM programs.fdsu_programs")

        for program in payload.get("programs", []):
            code = str(program.get("code") or "").strip()
            if not code:
                continue
            planned_sites = int(program.get("site_count") or 0)
            status = resolve_program_status(program)
            cur.execute(
                """
                INSERT INTO programs.fdsu_programs (
                    program_code, program_name, description, status,
                    planned_sites, executed_sites, progress
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    code,
                    str(program.get("name") or program.get("short_label") or code),
                    str(program.get("description") or "").strip() or None,
                    status,
                    planned_sites,
                    0,
                    0,
                ),
            )
            program_ids[code] = int(cur.fetchone()["id"])

        for program in EXTRA_PROGRAMS:
            code = program["program_code"]
            if code in program_ids:
                continue
            cur.execute(
                """
                INSERT INTO programs.fdsu_programs (
                    program_code, program_name, description, status,
                    planned_sites, executed_sites, progress
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    code,
                    program["program_name"],
                    program["description"],
                    program["status"],
                    program["planned_sites"],
                    0,
                    0,
                ),
            )
            program_ids[code] = int(cur.fetchone()["id"])

    conn.commit()
    return program_ids


def site_code_from_feature(feature: dict[str, Any], index: int) -> str:
    props = feature.get("properties") or {}
    for key in ("site_code", "code", "id"):
        value = props.get(key) if key in props else feature.get(key)
        if value not in (None, ""):
            return str(value)
    return f"SITE-{index:04d}"


def import_geojson_sites(conn, program_code: str, program_id: int, geojson_path: Path, default_status: str, expected_count: int) -> int:
    payload = load_json(geojson_path)
    features = payload.get("features") or []
    if len(features) != expected_count:
        raise ValueError(f"{geojson_path.name}: attendu {expected_count} sites, trouvé {len(features)}")

    inserted = 0
    with conn.cursor() as cur:
        cur.execute("DELETE FROM programs.fdsu_sites WHERE program_id = %s", (program_id,))
        for index, feature in enumerate(features, start=1):
            props = feature.get("properties") or {}
            geometry = feature.get("geometry") or {}
            coordinates = geometry.get("coordinates") or []
            longitude = props.get("longitude")
            latitude = props.get("latitude")
            if longitude is None and len(coordinates) >= 2:
                longitude = coordinates[0]
            if latitude is None and len(coordinates) >= 2:
                latitude = coordinates[1]
            if longitude is None or latitude is None:
                raise ValueError(f"Coordonnées manquantes pour le site #{index} dans {geojson_path.name}")

            site_status = str(props.get("status") or default_status).strip() or default_status
            fdsu_score = props.get("fdsu_score")
            cur.execute(
                """
                INSERT INTO programs.fdsu_sites (
                    program_id, site_code, site_name, province, territoire, zone,
                    status, priority_status, fdsu_score, latitude, longitude, geom, source
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                    %s
                )
                """,
                (
                    program_id,
                    site_code_from_feature(feature, index),
                    str(props.get("name") or props.get("site_name") or f"Site {index}"),
                    props.get("province"),
                    props.get("territoire"),
                    props.get("zone"),
                    site_status,
                    props.get("priority_status"),
                    fdsu_score,
                    float(latitude),
                    float(longitude),
                    float(longitude),
                    float(latitude),
                    props.get("source"),
                ),
            )
            inserted += 1

        cur.execute(
            """
            UPDATE programs.fdsu_programs
            SET executed_sites = %s,
                planned_sites = CASE WHEN planned_sites > 0 THEN planned_sites ELSE %s END,
                progress = CASE
                    WHEN %s > 0 AND status = 'EN_EXECUTION'
                    THEN LEAST(100, ROUND((%s::numeric / NULLIF(planned_sites, 0)) * 100, 2))
                    ELSE 0
                END,
                updated_at = NOW()
            WHERE id = %s
            """,
            (inserted, inserted, inserted, inserted, program_id),
        )

    conn.commit()
    return inserted


def print_summary(conn) -> None:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT COUNT(*) AS count FROM programs.fdsu_programs")
        program_count = int(cur.fetchone()["count"])
        cur.execute("SELECT COUNT(*) AS count FROM programs.fdsu_sites")
        site_count = int(cur.fetchone()["count"])
        cur.execute(
            """
            SELECT p.program_code, p.program_name, p.status, COUNT(s.id) AS site_count
            FROM programs.fdsu_programs p
            LEFT JOIN programs.fdsu_sites s ON s.program_id = p.id
            GROUP BY p.id, p.program_code, p.program_name, p.status
            ORDER BY p.program_code
            """
        )
        rows = cur.fetchall()

    print("")
    print("=== Import programmes FDSU terminé ===")
    print(f"Programmes : {program_count}")
    print(f"Sites      : {site_count}")
    for row in rows:
        if int(row["site_count"]) > 0:
            print(f"  - {row['program_code']} ({row['program_name']}) : {row['site_count']} sites [{row['status']}]")


def main() -> None:
    with psycopg2.connect(DATABASE_URL) as conn:
        print("Application du schéma programs…")
        apply_schema(conn)
        print("Initialisation du catalogue programmes…")
        program_ids = seed_program_catalog(conn)
        for target in IMPORT_TARGETS:
            program_code = target["program_code"]
            program_id = program_ids.get(program_code)
            if program_id is None:
                raise RuntimeError(f"Programme introuvable: {program_code}")
            print(f"Import {target['geojson_path'].name} -> {program_code}…")
            count = import_geojson_sites(
                conn,
                program_code,
                program_id,
                target["geojson_path"],
                target["default_site_status"],
                target["expected_count"],
            )
            print(f"  {count} sites importés.")
        print_summary(conn)
        # Programme national : sync idempotente séparée (évite de charger 20k GeoJSON ici)
        print("Synchronisation Sites 20 476 → programs.fdsu_sites (NSME)…")
        from api.services import fdsu_sites_nsme_sync_service as nsme_sync

        result = nsme_sync.sync_sites_20476_to_nsme()
        print(
            f"  NSME 20476 : {result.get('nsme_count_after')} sites "
            f"(new={result.get('new_rows')}, géom={result.get('with_geometry')})."
        )
        print_summary(conn)


if __name__ == "__main__":
    main()
