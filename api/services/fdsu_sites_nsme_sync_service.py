"""Synchronisation idempotente Sites 20 476 → programs.fdsu_sites (NSME natif).

Source autoritative lecture : data/programs/sites_20476/sites_20476.json
(issu de data/imports/PROGRAMME 20476 SITES.csv via fdsu_sites_import_service).

Chemin nominal NSME après sync : programs.fdsu_sites (PROG_SITES_20476).
Fallback fichier : conserve via site_entity_resolver / load_program_sites
lorsque DATA_MODE≠db ou programme absent / incomplet en DB.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from psycopg2.extras import RealDictCursor, execute_batch

from api.config import DATA_MODE, connect_db
from api.services import fdsu_sites_import_service
from api.services.site_display_name import enrich_site_labels, is_technical_site_identifier

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENRICHMENT_SQL = PROJECT_ROOT / "database" / "programs_national_enrichment.sql"
PROGRAM_DB_CODE = "PROG_SITES_20476"
PROGRAM_FILE_CODE = "sites_20476"
BATCH_SIZE = 500


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_national_schema(conn=None) -> None:
    """Applique le DDL d’enrichissement national (idempotent)."""
    sql = ENRICHMENT_SQL.read_text(encoding="utf-8")
    owns = conn is None
    if owns:
        conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
    finally:
        if owns:
            conn.close()


def _ensure_program(conn) -> int:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT id FROM programs.fdsu_programs WHERE program_code = %s",
            (PROGRAM_DB_CODE,),
        )
        row = cur.fetchone()
        if row:
            return int(row["id"])
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
                PROGRAM_DB_CODE,
                "Sites 20 476",
                "Programme national complet FDSU (5 ans)",
                "PLANIFIE",
                20476,
                0,
                0,
            ),
        )
        program_id = int(cur.fetchone()["id"])
        conn.commit()
        return program_id


def _count_program_sites(conn, program_id: int) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM programs.fdsu_sites WHERE program_id = %s",
            (program_id,),
        )
        return int(cur.fetchone()[0])


def _load_source_sites() -> list[dict[str, Any]]:
    payload = fdsu_sites_import_service.load_program_sites(PROGRAM_FILE_CODE)
    return list(payload.get("sites") or [])


def _prepare_row(site: dict[str, Any], program_id: int) -> tuple[tuple[Any, ...], dict[str, Any]]:
    labeled = enrich_site_labels(site)
    lat = labeled.get("latitude")
    lon = labeled.get("longitude")
    technical = labeled.get("technical_id") or (
        labeled.get("site_name") if is_technical_site_identifier(labeled.get("site_name")) else None
    )
    display = labeled.get("display_name") or labeled.get("name") or labeled.get("site_name") or "Site FDSU"
    site_code = labeled.get("site_code") or f"SITES_20476_{int(labeled.get('site_id') or 0):05d}"
    lat_f = float(lat) if lat is not None else None
    lon_f = float(lon) if lon is not None else None
    row = (
        program_id,
        str(site_code),
        str(display)[:512],
        labeled.get("province"),
        labeled.get("territoire"),
        labeled.get("zone"),
        labeled.get("status") or "Programme national",
        labeled.get("priority_status") or labeled.get("priority_level"),
        labeled.get("fdsu_score") or labeled.get("priority_score"),
        lat_f,
        lon_f,
        lon_f,  # geom null-check lon
        lat_f,  # geom null-check lat
        lon_f,  # MakePoint x
        lat_f,  # MakePoint y
        labeled.get("source") or "PROGRAMME 20476 SITES.csv",
        labeled.get("population"),
        labeled.get("population_range"),
        labeled.get("nearest_site"),
        labeled.get("distance"),
        labeled.get("distance_level"),
        bool(labeled.get("is_300_planned")),
        labeled.get("phase") or "national",
        technical,
        display,
        labeled.get("infra_name"),
        int(labeled["site_id"]) if labeled.get("site_id") is not None else None,
        labeled.get("display_name_source"),
    )
    stats = {
        "has_geom": lat_f is not None and lon_f is not None,
        "business_name": not bool(labeled.get("display_name_is_technical_fallback")),
        "is_300_planned": bool(labeled.get("is_300_planned")),
    }
    return row, stats


_UPSERT_SQL = """
INSERT INTO programs.fdsu_sites (
    program_id, site_code, site_name, province, territoire, zone,
    status, priority_status, fdsu_score, latitude, longitude, geom, source,
    population, population_range, nearest_site, distance_m, distance_level,
    is_300_planned, phase, technical_id, display_name, infra_name,
    source_site_id, display_name_source, updated_at
)
VALUES (
    %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s,
    CASE WHEN %s IS NOT NULL AND %s IS NOT NULL
         THEN ST_SetSRID(ST_MakePoint(%s, %s), 4326)
         ELSE NULL END,
    %s,
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s,
    %s, %s, NOW()
)
ON CONFLICT (program_id, site_code)
DO UPDATE SET
    site_name = EXCLUDED.site_name,
    province = EXCLUDED.province,
    territoire = EXCLUDED.territoire,
    zone = EXCLUDED.zone,
    status = EXCLUDED.status,
    priority_status = EXCLUDED.priority_status,
    fdsu_score = EXCLUDED.fdsu_score,
    latitude = EXCLUDED.latitude,
    longitude = EXCLUDED.longitude,
    geom = EXCLUDED.geom,
    source = EXCLUDED.source,
    population = EXCLUDED.population,
    population_range = EXCLUDED.population_range,
    nearest_site = EXCLUDED.nearest_site,
    distance_m = EXCLUDED.distance_m,
    distance_level = EXCLUDED.distance_level,
    is_300_planned = EXCLUDED.is_300_planned,
    phase = EXCLUDED.phase,
    technical_id = EXCLUDED.technical_id,
    display_name = EXCLUDED.display_name,
    infra_name = EXCLUDED.infra_name,
    source_site_id = EXCLUDED.source_site_id,
    display_name_source = EXCLUDED.display_name_source,
    updated_at = NOW()
"""


def sync_sites_20476_to_nsme(*, dry_run: bool = False) -> dict[str, Any]:
    """Charge / met à jour les 20 476 sites dans programs.fdsu_sites.

    Idempotent : clé (program_id, site_code). Une 2ᵉ exécution ne duplique pas.
    """
    if DATA_MODE != "db":
        raise RuntimeError("Sync NSME disponible uniquement en DATA_MODE=db.")

    source_sites = _load_source_sites()
    source_count = len(source_sites)
    if source_count == 0:
        raise FileNotFoundError("Aucun site source dans data/programs/sites_20476.")

    with connect_db() as conn:
        ensure_national_schema(conn)
        program_id = _ensure_program(conn)
        before = _count_program_sites(conn, program_id)

        prepared: list[tuple[Any, ...]] = []
        with_geom = without_geom = display_business = technical_fallback = is_300 = 0
        for site in source_sites:
            row, stats = _prepare_row(site, program_id)
            prepared.append(row)
            if stats["has_geom"]:
                with_geom += 1
            else:
                without_geom += 1
            if stats["business_name"]:
                display_business += 1
            else:
                technical_fallback += 1
            if stats["is_300_planned"]:
                is_300 += 1

        if dry_run:
            return {
                "_meta": {
                    "dry_run": True,
                    "program_code": PROGRAM_FILE_CODE,
                    "program_code_db": PROGRAM_DB_CODE,
                    "computed_at": _now(),
                },
                "source_count": source_count,
                "nsme_count_before": before,
                "would_upsert": source_count,
                "estimated_new": max(0, source_count - before),
                "estimated_updated": min(before, source_count),
                "with_geometry": with_geom,
                "without_geometry": without_geom,
                "display_name_business": display_business,
                "technical_fallback": technical_fallback,
                "is_300_planned": is_300,
            }

        with conn.cursor() as cur:
            execute_batch(cur, _UPSERT_SQL, prepared, page_size=BATCH_SIZE)
            cur.execute(
                """
                UPDATE programs.fdsu_programs
                SET executed_sites = %s,
                    planned_sites = GREATEST(planned_sites, %s),
                    updated_at = NOW()
                WHERE id = %s
                """,
                (source_count, source_count, program_id),
            )
        conn.commit()
        after = _count_program_sites(conn, program_id)

        return {
            "_meta": {
                "dry_run": False,
                "program_code": PROGRAM_FILE_CODE,
                "program_code_db": PROGRAM_DB_CODE,
                "source_authoritative": "data/programs/sites_20476/sites_20476.json",
                "nominal_path": "programs.fdsu_sites",
                "fallback_path": "data/programs/sites_20476 (fichier) via site_entity_resolver",
                "computed_at": _now(),
                "idempotent_key": "(program_id, site_code)",
            },
            "source_count": source_count,
            "nsme_count_before": before,
            "nsme_count_after": after,
            "upserted": source_count,
            "new_rows": max(0, after - before),
            "duplicates_avoided_on_rerun": before if before > 0 else 0,
            "with_geometry": with_geom,
            "without_geometry": without_geom,
            "display_name_business": display_business,
            "technical_fallback": technical_fallback,
            "is_300_planned": is_300,
            "integrated_natively": after >= source_count,
        }


def nsme_status_20476() -> dict[str, Any]:
    """État courant NSME pour le programme national."""
    source_count = len(_load_source_sites())
    if DATA_MODE != "db":
        return {
            "available": False,
            "reason": "DATA_MODE != db",
            "nsme_count": 0,
            "source_count": source_count,
            "native": False,
            "pending": source_count,
            "nominal_path": "file_fallback",
        }
    with connect_db() as conn:
        try:
            ensure_national_schema(conn)
            program_id = _ensure_program(conn)
            nsme_count = _count_program_sites(conn, program_id)
        except Exception as exc:  # noqa: BLE001
            return {
                "available": False,
                "reason": str(exc),
                "nsme_count": 0,
                "source_count": source_count,
                "native": False,
                "pending": source_count,
                "nominal_path": "file_fallback",
            }
    native = nsme_count >= source_count and source_count > 0
    return {
        "available": True,
        "program_code": PROGRAM_FILE_CODE,
        "program_code_db": PROGRAM_DB_CODE,
        "source_count": source_count,
        "nsme_count": nsme_count,
        "native": native,
        "pending": max(0, source_count - nsme_count),
        "nominal_path": "programs.fdsu_sites" if native else "file_fallback",
    }
