"""Service PostgreSQL/PostGIS pour les programmes FDSU."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from api.config import connect_db
from psycopg2.extras import RealDictCursor


PROGRAM_COLUMNS = """
    id,
    program_code,
    program_name,
    description,
    status,
    start_date,
    end_date,
    planned_sites,
    executed_sites,
    progress,
    created_at,
    updated_at
"""

SITE_COLUMNS = """
    s.id,
    s.program_id,
    p.program_code,
    p.program_name,
    s.site_code,
    s.site_name,
    s.province,
    s.territoire,
    s.zone,
    s.status,
    s.priority_status,
    s.fdsu_score,
    s.latitude,
    s.longitude,
    s.source,
    s.created_at,
    s.updated_at,
    CASE WHEN s.geom IS NULL THEN NULL ELSE ST_AsGeoJSON(s.geom)::json END AS geometry
"""


def _serialize_row(row: dict[str, Any]) -> dict[str, Any]:
    payload = dict(row)
    for key in ("start_date", "end_date", "created_at", "updated_at"):
        value = payload.get(key)
        if value is not None and hasattr(value, "isoformat"):
            payload[key] = value.isoformat()
    if payload.get("progress") is not None:
        payload["progress"] = float(payload["progress"])
    if payload.get("fdsu_score") is not None:
        payload["fdsu_score"] = float(payload["fdsu_score"])
    return payload


def list_programs() -> list[dict[str, Any]]:
    query = f"""
        SELECT {PROGRAM_COLUMNS}
        FROM programs.fdsu_programs
        ORDER BY program_code
    """
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return [_serialize_row(dict(row)) for row in cur.fetchall()]


def get_program(program_ref: str) -> dict[str, Any] | None:
    query = f"""
        SELECT {PROGRAM_COLUMNS}
        FROM programs.fdsu_programs
        WHERE program_code = %s
           OR CAST(id AS TEXT) = %s
        LIMIT 1
    """
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (program_ref, program_ref))
            row = cur.fetchone()
            return _serialize_row(dict(row)) if row else None


def list_sites(
    program_code: str | None = None,
    skip: int = 0,
    limit: int = 5000,
) -> list[dict[str, Any]]:
    filters = []
    params: list[Any] = []
    if program_code:
        filters.append("p.program_code = %s")
        params.append(program_code)
    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    query = f"""
        SELECT {SITE_COLUMNS}
        FROM programs.fdsu_sites s
        JOIN programs.fdsu_programs p ON p.id = s.program_id
        {where_clause}
        ORDER BY s.id
        OFFSET %s LIMIT %s
    """
    params.extend([skip, limit])
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, tuple(params))
            return [_serialize_row(dict(row)) for row in cur.fetchall()]


def site_to_feature(site: dict[str, Any], feature_id: int) -> dict[str, Any]:
    geometry = site.get("geometry")
    if not geometry:
        longitude = site.get("longitude")
        latitude = site.get("latitude")
        if longitude is not None and latitude is not None:
            geometry = {"type": "Point", "coordinates": [float(longitude), float(latitude)]}
    properties = {
        "name": site.get("site_name"),
        "province": site.get("province"),
        "territoire": site.get("territoire"),
        "zone": site.get("zone"),
        "latitude": site.get("latitude"),
        "longitude": site.get("longitude"),
        "programme": site.get("program_name"),
        "status": site.get("status"),
        "priority_status": site.get("priority_status"),
        "fdsu_score": site.get("fdsu_score"),
        "source": site.get("source"),
        "site_code": site.get("site_code"),
    }
    return {
        "type": "Feature",
        "id": feature_id,
        "geometry": geometry,
        "properties": {key: value for key, value in properties.items() if value not in (None, "")},
    }


def sites_to_geojson(sites: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "type": "FeatureCollection",
        "features": [site_to_feature(site, index + 1) for index, site in enumerate(sites)],
    }


def sites_to_panel_payload(program_code: str, sites: list[dict[str, Any]]) -> dict[str, Any]:
    from api.services import program_lifecycle_engine as ple

    program = get_program(program_code) or {}
    life = ple.resolve_program_lifecycle(program_code)
    program_status_code = (life.get("program_status") or {}).get("code")
    # Compatibilité : conserver deployment_status textuel dérivé du PLE (pas inventé)
    deployment_map = {
        "deployment_in_progress": "EN_COURS",
        "planned": "NON_DEMARRE",
        "strategic_planning": "NON_DEMARRE",
        "preparation": "PREPARATION",
    }
    deployment_status = deployment_map.get(program_status_code or "", "A_CONSOLIDER")
    scoring_status = "INTEGRE" if "40" in str(program_code) else "A_CALCULER"
    return {
        "_meta": {
            "program": program.get("program_name"),
            "program_status": program_status_code or program.get("status"),
            "program_status_label": (life.get("program_status") or {}).get("label"),
            "data_status": (life.get("data_status") or {}).get("code"),
            "data_status_label": (life.get("data_status") or {}).get("label"),
            "count": len(sites),
            "deployment_status": deployment_status,
            "scoring_status": scoring_status,
            "lifecycle": life,
            "note": "program_status ≠ operationalité physique ; data_status = intégration SIG.",
        },
        "sites": [
            {
                "name": site.get("site_name"),
                "province": site.get("province"),
                "territoire": site.get("territoire"),
                "zone": site.get("zone"),
                "latitude": site.get("latitude"),
                "longitude": site.get("longitude"),
                "programme": site.get("program_name"),
                "status": site.get("status"),
                "lifecycle": ple.resolve_asset_lifecycle(
                    program_code=program_code,
                    asset_id=site.get("id") or site.get("site_code"),
                    raw_status=site.get("status"),
                ),
                "priority_status": site.get("priority_status"),
                "fdsu_score": site.get("fdsu_score"),
                "source": site.get("source"),
            }
            for site in sites
        ],
    }


def get_program_sites_geojson(program_code: str) -> dict[str, Any]:
    return sites_to_geojson(list_sites(program_code=program_code, limit=10000))


def get_program_sites_panel(program_code: str) -> dict[str, Any]:
    return sites_to_panel_payload(program_code, list_sites(program_code=program_code, limit=10000))


def get_program_statistics() -> dict[str, Any]:
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT COUNT(*) AS count FROM programs.fdsu_programs")
            program_count = int(cur.fetchone()["count"])

            cur.execute("SELECT COUNT(*) AS count FROM programs.fdsu_sites")
            total_sites = int(cur.fetchone()["count"])

            cur.execute(
                """
                SELECT COUNT(*) AS count
                FROM programs.fdsu_sites
                WHERE LOWER(status) LIKE '%exécution%'
                   OR LOWER(status) LIKE '%execution%'
                   OR status IN ('En exécution', 'EN_EXECUTION', 'à qualifier')
                """
            )
            sites_in_execution = int(cur.fetchone()["count"])

            cur.execute(
                """
                SELECT COUNT(*) AS count
                FROM programs.fdsu_sites
                WHERE LOWER(status) LIKE '%planifi%'
                   OR status IN ('Planifié', 'PLANIFIE')
                """
            )
            sites_planned = int(cur.fetchone()["count"])

            cur.execute(
                """
                SELECT p.program_code, p.program_name, p.status, COUNT(s.id) AS site_count
                FROM programs.fdsu_programs p
                LEFT JOIN programs.fdsu_sites s ON s.program_id = p.id
                GROUP BY p.id, p.program_code, p.program_name, p.status
                ORDER BY site_count DESC, p.program_code
                """
            )
            by_program = [dict(row) for row in cur.fetchall()]

            cur.execute(
                """
                SELECT COALESCE(NULLIF(TRIM(province), ''), 'Non renseigné') AS province,
                       COUNT(*) AS site_count
                FROM programs.fdsu_sites
                GROUP BY 1
                ORDER BY site_count DESC, province
                """
            )
            by_province = [dict(row) for row in cur.fetchall()]

    return {
        "program_count": program_count,
        "total_sites": total_sites,
        "sites_in_execution": sites_in_execution,
        "sites_planned": sites_planned,
        "by_program": by_program,
        "by_province": by_province,
    }


STATUS_TO_FILL = "Statuts opérationnels à renseigner"
PENDING_CCN = "Données en cours d'intégration"


def _status_bucket_template(labels: list[str]) -> dict[str, Any]:
    return {label: None for label in labels}


def _program_site_status_breakdown(program_code: str) -> dict[str, Any]:
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT COUNT(*) AS total
                FROM programs.fdsu_sites s
                JOIN programs.fdsu_programs p ON p.id = s.program_id
                WHERE p.program_code = %s
                """,
                (program_code,),
            )
            total = int(cur.fetchone()["total"])
            cur.execute(
                """
                SELECT COALESCE(NULLIF(TRIM(s.status), ''), 'Non renseigné') AS status, COUNT(*) AS count
                FROM programs.fdsu_sites s
                JOIN programs.fdsu_programs p ON p.id = s.program_id
                WHERE p.program_code = %s
                GROUP BY 1
                ORDER BY count DESC, status
                """,
                (program_code,),
            )
            by_status = [dict(row) for row in cur.fetchall()]
            cur.execute(
                """
                SELECT p.program_code, p.program_name, p.status AS program_status,
                       p.planned_sites, p.executed_sites, p.progress
                FROM programs.fdsu_programs p
                WHERE p.program_code = %s
                LIMIT 1
                """,
                (program_code,),
            )
            program = dict(cur.fetchone() or {})

    detailed_statuses_present = any(
        str(row.get("status") or "").lower()
        in {
            "installé",
            "installe",
            "opérationnel",
            "operationnel",
            "bloqué",
            "bloque",
            "en cours d'installation",
            "non démarré",
            "non demarre",
            "en étude",
            "en etude",
            "prêt à déployer",
            "pret a deployer",
            "priorisé",
            "priorise",
        }
        for row in by_status
    )

    return {
        "program_code": program_code,
        "program_name": program.get("program_name"),
        "program_status": program.get("program_status"),
        "total": total,
        "by_raw_status": by_status,
        "detailed_statuses_available": detailed_statuses_present,
        "status_message": None if detailed_statuses_present else STATUS_TO_FILL,
        "planned_sites": program.get("planned_sites"),
        "executed_sites": program.get("executed_sites"),
        "progress": program.get("progress"),
    }


def get_status_summary() -> dict[str, Any]:
    stats = get_program_statistics()
    return {
        "_meta": {
            "title": "Synthèse des statuts programmes FDSU",
            "last_updated": datetime.now(timezone.utc).isoformat(),
        },
        "program_count": stats["program_count"],
        "total_sites": stats["total_sites"],
        "sites_in_execution": stats["sites_in_execution"],
        "sites_planned": stats["sites_planned"],
        "by_program": stats["by_program"],
        "limitations": STATUS_TO_FILL,
        "recommended_action": "Renseigner les statuts opérationnels détaillés des sites.",
    }


def get_sites_followup() -> dict[str, Any]:
    from api.services import program_lifecycle_engine as ple

    sites_40 = _program_site_status_breakdown("PROG_SITES_40")
    sites_300 = _program_site_status_breakdown("PROG_SITES_300")

    sites_40_followup = {
        **sites_40,
        "metrics": {
            "total_sites": sites_40["total"],
            "installes": None,
            "en_cours_installation": None,
            "operationnels": None,
            "non_demarres": None,
            "bloques": None,
            "taux_avancement": None,
        },
        "metrics_status": STATUS_TO_FILL,
        "raw_status_available": sites_40["by_raw_status"],
        "definition": "Suivi opérationnel du programme pilote Sites 40.",
        "source_table": "programs.fdsu_sites",
        "calculation_method": "Agrégation par statut opérationnel (champs détaillés à renseigner).",
        "recommended_action": "Suivre les 40 sites pilotes",
    }

    sites_300_followup = {
        **sites_300,
        "metrics": {
            "total": sites_300["total"],
            "planifies": sites_300["total"] if sites_300["total"] else None,
            "priorises": None,
            "en_etude": None,
            "prets_a_deployer": None,
            "bloques": None,
            "taux_preparation": None,
        },
        "metrics_status": STATUS_TO_FILL,
        "raw_status_available": sites_300["by_raw_status"],
        "definition": "Suivi de préparation du programme Sites 300 (matrice de priorisation).",
        "source_table": "programs.fdsu_sites",
        "calculation_method": "Agrégation par statut de préparation (champs détaillés à renseigner).",
        "recommended_action": "Suivre les 300 sites planifiés",
        "strategic_reference": "data/strategic/matrice_priorisation_300_sites.xlsx",
    }

    ccn_followup = {
        "program_code": "PROG_CCN",
        "program_name": "Centres Communautaires Numériques",
        "metrics": {
            "ccn_planifies": None,
            "ccn_installes": None,
            "ccn_operationnels": None,
        },
        "metrics_status": PENDING_CCN,
        "display": PENDING_CCN,
        "definition": "Suivi CCN selon la stratégie FDSU–CCN 2026–2030.",
        "source_table": "programme CCN (non intégré opérationnellement)",
        "calculation_method": "Non calculable sans inventaire CCN.",
        "recommended_action": "Planifier les CCN",
        "strategic_reference": "data/strategic/strategie_fdsu_ccn_2026_2030.docx",
        "available": False,
    }

    return {
        "_meta": {
            "title": "Suivi opérationnel des programmes FDSU",
            "architecture": "extensible",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "lifecycle_engine": "ple-1.0.0",
        },
        "sites_40": {
            **sites_40_followup,
            "lifecycle": ple.resolve_program_lifecycle("sites_40"),
        },
        "sites_300": {
            **sites_300_followup,
            "lifecycle": ple.resolve_program_lifecycle("sites_300"),
        },
        "sites_20476": {
            "program_code": "PROG_SITES_20476",
            "lifecycle": ple.resolve_program_lifecycle("sites_20476"),
            "metrics": {
                "total_sites": None,
                "engages": None,
                "operationnels": None,
            },
            "metrics_status": "Cible nationale ≠ sites engagés — À consolider",
        },
        "ccn": {
            **ccn_followup,
            "lifecycle": ple.resolve_program_lifecycle("ccn"),
            "metrics_status": "Inventaire DEMO — ≠ opérationnel production",
        },
        "programs_board": ple.build_programs_board(),
        "global_limitations": (
            "Les compteurs installé / mis en service / opérationnel restent null tant que "
            "les preuves individuelles ne sont pas disponibles. "
            f"{STATUS_TO_FILL}."
        ),
        "recommended_action": "Consolider les statuts individuels avec preuves avant tout badge « opérationnel ».",
        "extensible_fields": [
            "operational_status",
            "installation_started_at",
            "operational_at",
            "blocked_reason",
            "preparation_stage",
        ],
    }
