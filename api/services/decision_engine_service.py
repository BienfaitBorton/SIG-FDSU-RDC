"""Moteur de Décision FDSU v1.0 — calcul et persistance des scores de priorité."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from psycopg2.extras import Json, RealDictCursor

from api.config import connect_db

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BUSINESS_DIR = PROJECT_ROOT / "data" / "business"

PRIORITY_LEVEL_LABELS = {
    "critical": "Priorité critique",
    "high": "Priorité élevée",
    "medium": "Priorité moyenne",
    "low": "Priorité faible",
}

PRIORITY_LEVEL_COLORS = {
    "critical": "#ef4444",
    "high": "#f97316",
    "medium": "#eab308",
    "low": "#64748b",
}

# Pondérations v1.0 — extensibles via critères sectoriels futurs (poids 0 = en attente).
CRITERIA_WEIGHTS: dict[str, float] = {
    "programme": 0.20,
    "deficit_couverture": 0.35,
    "contexte_administratif": 0.15,
    "analyse_spatiale": 0.15,
    "statut_execution": 0.15,
    # Sectoriels — données à compléter ultérieurement
    "infrastructures_publiques": 0.0,
    "population": 0.0,
    "potentiel_economique": 0.0,
    "sante": 0.0,
    "education": 0.0,
    "energie": 0.0,
    "routes": 0.0,
}

PENDING_SECTORIAL_CRITERIA = [
    "infrastructures_publiques",
    "population",
    "potentiel_economique",
    "sante",
    "education",
    "energie",
    "routes",
]

REL_NEAREST_INFRA = "nearest_infrastructure"
REL_ADMIN_PROVINCE = "administrative_province"
REL_ADMIN_TERRITOIRE = "administrative_territoire"


def _load_json(filename: str) -> dict[str, Any]:
    path = BUSINESS_DIR / filename
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _priority_thresholds() -> list[dict[str, Any]]:
    matrix = _load_json("priority_matrix.json")
    return matrix.get("priority_levels") or []


def score_to_priority_level(score: float) -> str:
    thresholds = _priority_thresholds()
    if not thresholds:
        if score >= 85:
            return "critical"
        if score >= 70:
            return "high"
        if score >= 50:
            return "medium"
        return "low"

    for level in sorted(thresholds, key=lambda item: item.get("rank", 99)):
        threshold = level.get("threshold") or {}
        min_score = float(threshold.get("min_score", 0))
        max_score = float(threshold.get("max_score", 100))
        if min_score <= score <= max_score:
            return str(level.get("id") or "low")
    return "low"


def _serialize_row(row: dict[str, Any]) -> dict[str, Any]:
    payload = dict(row)
    for key in ("computed_at", "created_at", "updated_at"):
        value = payload.get(key)
        if value is not None and hasattr(value, "isoformat"):
            payload[key] = value.isoformat()
    if payload.get("priority_score") is not None:
        payload["priority_score"] = float(payload["priority_score"])
    if isinstance(payload.get("criteria_details"), dict):
        pass
    elif payload.get("criteria_details") is not None:
        payload["criteria_details"] = dict(payload["criteria_details"])
    return payload


def _score_programme(program_code: str, program_status: str | None) -> tuple[float, str]:
    code = (program_code or "").upper()
    status = (program_status or "").lower()
    if code == "PROG_SITES_40" or "exécution" in status or "execution" in status:
        return 90.0, "Programme Sites 40 — déploiement en exécution"
    if code == "PROG_SITES_300" or "planif" in status:
        return 65.0, "Programme Sites 300 — planifié"
    return 55.0, f"Programme {program_code or 'inconnu'}"


def _score_deficit_couverture(distance_m: float | None, has_relation: bool) -> tuple[float, str]:
    if distance_m is None or not has_relation:
        return 50.0, "Distance télécom non calculée — lancer l'analyse spatiale"
    distance = float(distance_m)
    if distance <= 2000:
        score = 25.0
        label = f"Proximité infrastructure ({distance / 1000:.1f} km) — déficit faible"
    elif distance <= 10000:
        score = 45.0 + (distance - 2000) / 8000 * 25
        label = f"Distance opérateur {distance / 1000:.1f} km — déficit modéré"
    elif distance <= 30000:
        score = 70.0 + (distance - 10000) / 20000 * 15
        label = f"Distance opérateur {distance / 1000:.1f} km — déficit élevé"
    else:
        score = min(98.0, 85.0 + (distance - 30000) / 50000 * 13)
        label = f"Distance opérateur {distance / 1000:.1f} km — déficit majeur"
    return round(score, 2), label


def _score_admin_context(
    province: str | None,
    territoire: str | None,
    has_postgis_province: bool,
    has_postgis_territoire: bool,
) -> tuple[float, str]:
    province_ok = bool(province)
    territoire_ok = bool(territoire)
    postgis_ok = has_postgis_province and has_postgis_territoire
    if province_ok and territoire_ok and postgis_ok:
        return 100.0, f"Contexte admin validé PostGIS — {province} / {territoire}"
    if province_ok and territoire_ok:
        return 85.0, f"Province et territoire renseignés — {province} / {territoire}"
    if province_ok or territoire_ok:
        partial = province or territoire
        return 65.0, f"Contexte administratif partiel — {partial}"
    return 40.0, "Contexte administratif incomplet"


def _score_spatial_analysis(relation_count: int) -> tuple[float, str]:
    if relation_count >= 4:
        return 100.0, f"{relation_count} relations spatiales calculées"
    if relation_count >= 1:
        return 70.0, f"{relation_count} relation(s) spatiale(s) — analyse partielle"
    return 30.0, "Aucune relation spatiale — exécuter l'analyse spatiale"


def _score_execution_status(site_status: str | None, program_code: str) -> tuple[float, str]:
    status = (site_status or "").lower()
    if "exécution" in status or "execution" in status or "actif" in status:
        return 92.0, "Site en exécution"
    if program_code.upper() == "PROG_SITES_40":
        return 88.0, "Site du programme en cours de déploiement"
    if "planif" in status:
        return 55.0, "Site planifié"
    return 60.0, site_status or "Statut non renseigné"


def compute_site_score(site_row: dict[str, Any], relations: list[dict[str, Any]]) -> dict[str, Any]:
    program_code = site_row.get("program_code") or ""
    program_status = site_row.get("program_status")

    nearest_distance: float | None = None
    has_nearest_infra = False
    has_postgis_province = False
    has_postgis_territoire = False

    for relation in relations:
        rel_type = relation.get("relation_type")
        if rel_type == REL_NEAREST_INFRA:
            has_nearest_infra = True
            if relation.get("distance_m") is not None:
                nearest_distance = float(relation["distance_m"])
        elif rel_type == REL_ADMIN_PROVINCE:
            props = relation.get("properties") or {}
            if props.get("source") == "postgis":
                has_postgis_province = True
        elif rel_type == REL_ADMIN_TERRITOIRE:
            props = relation.get("properties") or {}
            if props.get("source") == "postgis":
                has_postgis_territoire = True

    criteria_scores: dict[str, dict[str, Any]] = {}

    prog_score, prog_label = _score_programme(program_code, program_status)
    criteria_scores["programme"] = {
        "score": prog_score,
        "weight": CRITERIA_WEIGHTS["programme"],
        "label": prog_label,
        "criterion_id": "classe_strategique",
    }

    deficit_score, deficit_label = _score_deficit_couverture(nearest_distance, has_nearest_infra)
    criteria_scores["deficit_couverture"] = {
        "score": deficit_score,
        "weight": CRITERIA_WEIGHTS["deficit_couverture"],
        "label": deficit_label,
        "criterion_id": "deficit_couverture",
        "distance_m": nearest_distance,
    }

    admin_score, admin_label = _score_admin_context(
        site_row.get("province"),
        site_row.get("territoire"),
        has_postgis_province,
        has_postgis_territoire,
    )
    criteria_scores["contexte_administratif"] = {
        "score": admin_score,
        "weight": CRITERIA_WEIGHTS["contexte_administratif"],
        "label": admin_label,
        "criterion_id": "classe_strategique",
    }

    spatial_score, spatial_label = _score_spatial_analysis(len(relations))
    criteria_scores["analyse_spatiale"] = {
        "score": spatial_score,
        "weight": CRITERIA_WEIGHTS["analyse_spatiale"],
        "label": spatial_label,
        "criterion_id": "faisabilite_technique",
        "relations_count": len(relations),
    }

    exec_score, exec_label = _score_execution_status(site_row.get("status"), program_code)
    criteria_scores["statut_execution"] = {
        "score": exec_score,
        "weight": CRITERIA_WEIGHTS["statut_execution"],
        "label": exec_label,
        "criterion_id": "classe_strategique",
    }

    pending_sectorial = [
        {
            "criterion_id": criterion_id,
            "label": "Données sectorielles à compléter",
            "status": "pending",
            "weight": CRITERIA_WEIGHTS.get(criterion_id, 0.0),
        }
        for criterion_id in PENDING_SECTORIAL_CRITERIA
        if CRITERIA_WEIGHTS.get(criterion_id, 0.0) == 0.0
    ]

    active_weight = sum(
        item["weight"]
        for item in criteria_scores.values()
        if float(item.get("weight") or 0) > 0
    )
    weighted_sum = sum(
        float(item["score"]) * float(item["weight"])
        for item in criteria_scores.values()
        if float(item.get("weight") or 0) > 0
    )
    priority_score = round(weighted_sum / active_weight, 2) if active_weight > 0 else 0.0
    priority_score = max(0.0, min(100.0, priority_score))
    priority_level = score_to_priority_level(priority_score)

    top_criteria = sorted(
        criteria_scores.values(),
        key=lambda item: float(item["score"]) * float(item["weight"]),
        reverse=True,
    )[:3]

    return {
        "site_id": int(site_row["id"]),
        "program_code": program_code,
        "priority_score": priority_score,
        "priority_level": priority_level,
        "priority_level_label": PRIORITY_LEVEL_LABELS.get(priority_level, priority_level),
        "criteria_details": {
            "criteria": criteria_scores,
            "top_factors": [
                {"label": item["label"], "score": item["score"], "weight": item["weight"]}
                for item in top_criteria
            ],
            "pending_sectorial": pending_sectorial,
            "engine_version": "1.0.0",
            "score_scale": {"min": 0, "max": 100},
        },
    }


def _fetch_all_sites_with_relations() -> list[tuple[dict[str, Any], list[dict[str, Any]]]]:
    sites_query = """
        SELECT
            s.id,
            s.site_code,
            s.site_name,
            s.province,
            s.territoire,
            s.zone,
            s.status,
            s.latitude,
            s.longitude,
            p.program_code,
            p.program_name,
            p.status AS program_status
        FROM programs.fdsu_sites s
        JOIN programs.fdsu_programs p ON p.id = s.program_id
        ORDER BY s.id
    """
    relations_query = """
        SELECT
            source_id,
            relation_type,
            distance_m,
            properties
        FROM analysis.spatial_relations
        WHERE source_type = 'fdsu_site'
        ORDER BY source_id, relation_type
    """
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sites_query)
            sites = [dict(row) for row in cur.fetchall()]
            cur.execute(relations_query)
            relation_rows = [dict(row) for row in cur.fetchall()]

    relations_by_site: dict[int, list[dict[str, Any]]] = {}
    for row in relation_rows:
        site_id = int(row["source_id"])
        relations_by_site.setdefault(site_id, []).append(row)

    return [(site, relations_by_site.get(int(site["id"]), [])) for site in sites]


def _upsert_site_score(payload: dict[str, Any]) -> None:
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO decision.fdsu_site_scores (
                    site_id, program_code, priority_score, priority_level,
                    criteria_details, computed_at
                )
                VALUES (%s, %s, %s, %s, %s, NOW())
                ON CONFLICT (site_id) DO UPDATE SET
                    program_code = EXCLUDED.program_code,
                    priority_score = EXCLUDED.priority_score,
                    priority_level = EXCLUDED.priority_level,
                    criteria_details = EXCLUDED.criteria_details,
                    computed_at = EXCLUDED.computed_at
                """,
                (
                    payload["site_id"],
                    payload["program_code"],
                    payload["priority_score"],
                    payload["priority_level"],
                    Json(payload["criteria_details"]),
                ),
            )
        conn.commit()


def recompute_all_site_scores() -> dict[str, Any]:
    pairs = _fetch_all_sites_with_relations()
    computed = 0
    for site_row, relations in pairs:
        score_payload = compute_site_score(site_row, relations)
        _upsert_site_score(score_payload)
        computed += 1

    summary = get_scores_summary()
    return {
        "status": "completed",
        "sites_computed": computed,
        "summary": summary,
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }


def get_scores_summary() -> dict[str, int]:
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT COUNT(*) AS count FROM decision.fdsu_site_scores")
            total = int(cur.fetchone()["count"])
            cur.execute(
                """
                SELECT priority_level, COUNT(*) AS count
                FROM decision.fdsu_site_scores
                GROUP BY priority_level
                """
            )
            by_level = {row["priority_level"]: int(row["count"]) for row in cur.fetchall()}

    return {
        "total": total,
        "critical": by_level.get("critical", 0),
        "high": by_level.get("high", 0),
        "medium": by_level.get("medium", 0),
        "low": by_level.get("low", 0),
    }


def list_site_scores(
    priority_level: str | None = None,
    program_code: str | None = None,
    limit: int = 500,
    offset: int = 0,
) -> dict[str, Any]:
    conditions: list[str] = []
    params: list[Any] = []

    if priority_level:
        conditions.append("sc.priority_level = %s")
        params.append(priority_level)
    if program_code:
        conditions.append("sc.program_code = %s")
        params.append(program_code)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = f"""
        SELECT
            sc.id,
            sc.site_id,
            sc.program_code,
            sc.priority_score,
            sc.priority_level,
            sc.criteria_details,
            sc.computed_at,
            s.site_code,
            s.site_name,
            s.province,
            s.territoire,
            s.zone,
            s.status,
            s.latitude,
            s.longitude,
            p.program_name
        FROM decision.fdsu_site_scores sc
        JOIN programs.fdsu_sites s ON s.id = sc.site_id
        JOIN programs.fdsu_programs p ON p.id = s.program_id
        {where_clause}
        ORDER BY sc.priority_score DESC, s.site_name
        LIMIT %s OFFSET %s
    """
    params.extend([limit, offset])

    count_query = f"""
        SELECT COUNT(*) AS count
        FROM decision.fdsu_site_scores sc
        {where_clause}
    """
    count_params = params[:-2]

    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(count_query, count_params)
            total_filtered = int(cur.fetchone()["count"])
            cur.execute(query, params)
            rows = [_serialize_row(dict(row)) for row in cur.fetchall()]

    sites = []
    for row in rows:
        criteria = row.get("criteria_details") or {}
        top_factors = criteria.get("top_factors") or []
        sites.append(
            {
                "id": row["id"],
                "site_id": row["site_id"],
                "site_code": row.get("site_code"),
                "site_name": row.get("site_name"),
                "program_code": row.get("program_code"),
                "program_name": row.get("program_name"),
                "province": row.get("province"),
                "territoire": row.get("territoire"),
                "zone": row.get("zone"),
                "status": row.get("status"),
                "latitude": row.get("latitude"),
                "longitude": row.get("longitude"),
                "priority_score": row.get("priority_score"),
                "priority_level": row.get("priority_level"),
                "priority_level_label": PRIORITY_LEVEL_LABELS.get(
                    row.get("priority_level"), row.get("priority_level")
                ),
                "priority_color": PRIORITY_LEVEL_COLORS.get(row.get("priority_level"), "#64748b"),
                "top_criteria": top_factors,
                "pending_sectorial": criteria.get("pending_sectorial") or [],
                "computed_at": row.get("computed_at"),
            }
        )

    summary = get_scores_summary()
    thresholds = _priority_thresholds()

    return {
        "_meta": {
            "engine": "FDSU Decision Engine",
            "version": "1.0.0",
            "total_filtered": total_filtered,
            "limit": limit,
            "offset": offset,
        },
        "summary": summary,
        "priority_levels": [
            {
                "id": level.get("id"),
                "label": PRIORITY_LEVEL_LABELS.get(level.get("id"), level.get("label")),
                "color": PRIORITY_LEVEL_COLORS.get(level.get("id"), "#64748b"),
                "threshold": level.get("threshold"),
                "count": summary.get(level.get("id"), 0),
            }
            for level in thresholds
        ]
        or [
            {"id": "critical", "label": PRIORITY_LEVEL_LABELS["critical"], "count": summary["critical"]},
            {"id": "high", "label": PRIORITY_LEVEL_LABELS["high"], "count": summary["high"]},
            {"id": "medium", "label": PRIORITY_LEVEL_LABELS["medium"], "count": summary["medium"]},
            {"id": "low", "label": PRIORITY_LEVEL_LABELS["low"], "count": summary["low"]},
        ],
        "sites": sites,
    }


def get_site_score(site_id: int) -> dict[str, Any] | None:
    query = """
        SELECT
            sc.id,
            sc.site_id,
            sc.program_code,
            sc.priority_score,
            sc.priority_level,
            sc.criteria_details,
            sc.computed_at,
            s.site_code,
            s.site_name,
            s.province,
            s.territoire,
            s.zone,
            s.status,
            s.latitude,
            s.longitude,
            p.program_name
        FROM decision.fdsu_site_scores sc
        JOIN programs.fdsu_sites s ON s.id = sc.site_id
        JOIN programs.fdsu_programs p ON p.id = s.program_id
        WHERE sc.site_id = %s
        LIMIT 1
    """
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (site_id,))
            row = cur.fetchone()
            if not row:
                return None
            row = _serialize_row(dict(row))

    criteria = row.get("criteria_details") or {}
    return {
        "id": row["id"],
        "site_id": row["site_id"],
        "site_code": row.get("site_code"),
        "site_name": row.get("site_name"),
        "program_code": row.get("program_code"),
        "program_name": row.get("program_name"),
        "province": row.get("province"),
        "territoire": row.get("territoire"),
        "zone": row.get("zone"),
        "status": row.get("status"),
        "latitude": row.get("latitude"),
        "longitude": row.get("longitude"),
        "priority_score": row.get("priority_score"),
        "priority_level": row.get("priority_level"),
        "priority_level_label": PRIORITY_LEVEL_LABELS.get(row.get("priority_level"), row.get("priority_level")),
        "priority_color": PRIORITY_LEVEL_COLORS.get(row.get("priority_level"), "#64748b"),
        "criteria_details": criteria,
        "top_criteria": criteria.get("top_factors") or [],
        "pending_sectorial": criteria.get("pending_sectorial") or [],
        "computed_at": row.get("computed_at"),
    }


def get_panel_payload() -> dict[str, Any]:
    summary = get_scores_summary()
    if summary["total"] == 0:
        return {
            "_meta": {"title": "Moteur de décision FDSU", "engine": "FDSU Decision Engine v1.0"},
            "summary": summary,
            "needs_recompute": True,
        }
    return {
        "_meta": {"title": "Moteur de décision FDSU", "engine": "FDSU Decision Engine v1.0"},
        "summary": summary,
        "needs_recompute": False,
    }
