"""Priorisation nationale générique FDSU — Sites 40 / 300 / 20 476 / vagues futures.

La matrice des 300 sites sert de calibration officielle des seuils
(priority_matrix.json), sans enfermer le moteur dans ce seul périmètre.

Identité territoriale / codes sites : nomenclature officielle unique
data/raw/FDSU Structure code Territoire zones.xlsx
(via app.fdsu_nomenclature / Référentiel National).
"""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from api.services import decision_engine_service, fdsu_sites_import_service
from api.services.site_display_name import apply_display_name, enrich_site_labels

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUSINESS_DIR = PROJECT_ROOT / "data" / "business"
EXPORT_DIR = PROJECT_ROOT / "data" / "exports" / "priorities"
SITES_DOCTRINE_PATH = BUSINESS_DIR / "doctrines" / "sites_doctrine_v1.json"

# Fallback uniquement si doctrine absente — le moteur doit lire la doctrine.
_FALLBACK_WEIGHTS: dict[str, float] = {
    "population": 0.30,
    "deficit_distance": 0.30,
    "wave_calibration": 0.20,
    "contexte_administratif": 0.10,
    "phase_programme": 0.10,
}


def _load_national_weights() -> dict[str, float]:
    if not SITES_DOCTRINE_PATH.exists():
        return dict(_FALLBACK_WEIGHTS)
    try:
        doctrine = json.loads(SITES_DOCTRINE_PATH.read_text(encoding="utf-8"))
        weights = {
            str(item.get("id")): float(item.get("weight") or 0)
            for item in doctrine.get("selection_criteria") or []
            if item.get("id")
        }
        return weights or dict(_FALLBACK_WEIGHTS)
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return dict(_FALLBACK_WEIGHTS)


NATIONAL_WEIGHTS: dict[str, float] = _load_national_weights()

PRIORITY_LEVEL_LABELS = {
    "critical": "Priorité critique",
    "high": "Priorité élevée",
    "medium": "Priorité moyenne",
    "low": "Priorité faible",
}

# Cache scores nationaux (clé = program_code + mtime JSON)
_SCORED_CACHE: dict[str, tuple[float, list[dict[str, Any]]]] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _program_json_mtime(program_code: str) -> float:
    code = fdsu_sites_import_service.normalize_program_code(program_code)
    path = fdsu_sites_import_service.program_output_dir(code) / f"{code}.json"
    try:
        return path.stat().st_mtime if path.exists() else 0.0
    except OSError:
        return 0.0


def _scored_sites_cached(program_code: str) -> list[dict[str, Any]]:
    code = fdsu_sites_import_service.normalize_program_code(program_code)
    mtime = _program_json_mtime(code)
    cached = _SCORED_CACHE.get(code)
    if cached and cached[0] == mtime:
        return cached[1]
    sites = _sites_for_program(code)
    scored = [compute_national_site_score(site) for site in sites]
    scored.sort(key=lambda item: (-float(item["priority_score"]), str(item.get("site_name") or "")))
    _SCORED_CACHE[code] = (mtime, scored)
    return scored


def _load_priority_thresholds() -> list[dict[str, Any]]:
    path = BUSINESS_DIR / "priority_matrix.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("priority_levels") or []


def score_to_priority_level(score: float) -> str:
    thresholds = _load_priority_thresholds()
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


def _score_population(population: int | None, population_range: str | None) -> tuple[float, str]:
    if population is not None and population > 0:
        if population >= 10000:
            return 95.0, f"Population élevée ({population:,} hab.)".replace(",", " ")
        if population >= 3000:
            return 80.0, f"Population significative ({population:,} hab.)".replace(",", " ")
        if population >= 1000:
            return 65.0, f"Population intermédiaire ({population:,} hab.)".replace(",", " ")
        return 45.0, f"Population limitée ({population:,} hab.)".replace(",", " ")
    text = (population_range or "").lower()
    if "10k" in text or ">10" in text:
        return 90.0, f"Classe population {population_range}"
    if "3k" in text or "5k" in text:
        return 75.0, f"Classe population {population_range}"
    if "1k" in text:
        return 60.0, f"Classe population {population_range}"
    return 40.0, "Population non renseignée"


def _score_deficit_distance(distance: float | None, distance_level: str | None) -> tuple[float, str]:
    level = (distance_level or "").lower()
    if distance is not None:
        if distance >= 10000:
            return 95.0, f"Éloignement fort ({distance / 1000:.1f} km) — déficit couverture élevé"
        if distance >= 5000:
            return 80.0, f"Éloignement notable ({distance / 1000:.1f} km)"
        if distance >= 2000:
            return 55.0, f"Distance modérée ({distance / 1000:.1f} km)"
        return 30.0, f"Proximité site existant ({distance / 1000:.1f} km)"
    if ">5" in level or "5km" in level:
        return 82.0, f"Niveau distance {distance_level}"
    if ">2" in level or "2km" in level:
        return 58.0, f"Niveau distance {distance_level}"
    if distance_level:
        return 45.0, f"Niveau distance {distance_level}"
    return 50.0, "Distance non renseignée — score neutre"


def _score_wave_calibration(is_300_planned: bool, program_code: str) -> tuple[float, str]:
    if is_300_planned:
        return 92.0, "Site inclus dans la calibration officielle 300 sites"
    code = fdsu_sites_import_service.normalize_program_code(program_code)
    if code == "sites_300":
        return 88.0, "Site de la première vague opérationnelle (300)"
    if code == "sites_40":
        return 95.0, "Site de la phase pilote (40)"
    return 55.0, "Site du programme national — hors vague 300"


def _score_admin(province: str | None, territoire: str | None, zone: str | None) -> tuple[float, str]:
    filled = sum(1 for value in (province, territoire, zone) if value)
    if filled == 3:
        return 100.0, f"Contexte complet — {province} / {territoire} / {zone}"
    if province and territoire:
        return 85.0, f"Province et territoire — {province} / {territoire}"
    if province or territoire:
        return 60.0, f"Contexte partiel — {province or territoire}"
    return 35.0, "Contexte administratif incomplet"


def _score_phase(program_code: str) -> tuple[float, str]:
    code = fdsu_sites_import_service.normalize_program_code(program_code)
    meta = fdsu_sites_import_service.program_meta(code)
    phase = meta.get("phase")
    if phase == "pilot":
        return 90.0, "Phase pilote — priorité opérationnelle immédiate"
    if phase == "first_wave":
        return 75.0, "Première vague opérationnelle"
    if phase == "national":
        return 60.0, "Programme national pluriannuel (5 ans)"
    return 50.0, f"Vague {code}"


def compute_national_site_score(site: dict[str, Any]) -> dict[str, Any]:
    program_code = site.get("program_code") or "sites_20476"
    criteria: dict[str, dict[str, Any]] = {}

    pop_score, pop_label = _score_population(site.get("population"), site.get("population_range"))
    criteria["population"] = {
        "score": pop_score,
        "weight": NATIONAL_WEIGHTS["population"],
        "label": pop_label,
        "criterion_id": "population",
    }

    dist_score, dist_label = _score_deficit_distance(site.get("distance"), site.get("distance_level"))
    criteria["deficit_distance"] = {
        "score": dist_score,
        "weight": NATIONAL_WEIGHTS["deficit_distance"],
        "label": dist_label,
        "criterion_id": "deficit_couverture",
        "distance": site.get("distance"),
        "distance_level": site.get("distance_level"),
    }

    wave_score, wave_label = _score_wave_calibration(bool(site.get("is_300_planned")), program_code)
    criteria["wave_calibration"] = {
        "score": wave_score,
        "weight": NATIONAL_WEIGHTS["wave_calibration"],
        "label": wave_label,
        "criterion_id": "classe_strategique",
        "is_300_planned": bool(site.get("is_300_planned")),
    }

    admin_score, admin_label = _score_admin(site.get("province"), site.get("territoire"), site.get("zone"))
    criteria["contexte_administratif"] = {
        "score": admin_score,
        "weight": NATIONAL_WEIGHTS["contexte_administratif"],
        "label": admin_label,
        "criterion_id": "classe_strategique",
    }

    phase_score, phase_label = _score_phase(program_code)
    criteria["phase_programme"] = {
        "score": phase_score,
        "weight": NATIONAL_WEIGHTS["phase_programme"],
        "label": phase_label,
        "criterion_id": "classe_strategique",
    }

    active_weight = sum(float(item["weight"]) for item in criteria.values() if float(item["weight"]) > 0)
    weighted = sum(float(item["score"]) * float(item["weight"]) for item in criteria.values() if float(item["weight"]) > 0)
    priority_score = round(weighted / active_weight, 2) if active_weight else 0.0
    priority_score = max(0.0, min(100.0, priority_score))
    priority_level = score_to_priority_level(priority_score)

    top_factors = sorted(
        criteria.values(),
        key=lambda item: float(item["score"]) * float(item["weight"]),
        reverse=True,
    )[:3]

    scored = {
        "site_id": site.get("site_id"),
        "site_code": site.get("site_code"),
        "site_name": site.get("site_name"),
        "name": site.get("name"),
        "village_name": site.get("village_name"),
        "locality_name": site.get("locality_name") or site.get("localite"),
        "infra_name": site.get("infra_name"),
        "nearest_site": site.get("nearest_site"),
        "program_code": fdsu_sites_import_service.normalize_program_code(program_code),
        "province": site.get("province"),
        "territoire": site.get("territoire"),
        "zone": site.get("zone"),
        "latitude": site.get("latitude"),
        "longitude": site.get("longitude"),
        "population": site.get("population"),
        "distance": site.get("distance"),
        "distance_level": site.get("distance_level"),
        "is_300_planned": bool(site.get("is_300_planned")),
        "priority_score": priority_score,
        "priority_level": priority_level,
        "priority_level_label": PRIORITY_LEVEL_LABELS.get(priority_level, priority_level),
        "criteria_details": {
            "criteria": criteria,
            "top_factors": [
                {"label": item["label"], "score": item["score"], "weight": item["weight"]}
                for item in top_factors
            ],
            "calibration": {
                "source": "data/business/priority_matrix.json",
                "matrix_reference": "data/strategic/matrice_priorisation_300_sites.xlsx",
                "note": "Seuils calibrés sur la matrice 300 ; scoring applicable à toutes les vagues.",
            },
            "engine_version": "national-1.0.0",
            "weights": NATIONAL_WEIGHTS,
        },
    }
    # Enrichissement libellé (NCI infra_name) pour Sites 20 476 — sans perdre site_name technique
    try:
        return enrich_site_labels(scored)
    except Exception:
        return apply_display_name(scored)


def _sites_from_db_program(program_code: str) -> list[dict[str, Any]]:
    """Fallback DB pour Sites 40 / 300 lorsque les JSON programme sont absents."""
    code = fdsu_sites_import_service.normalize_program_code(program_code)
    meta = fdsu_sites_import_service.program_meta(code)
    db_code = meta.get("program_code_db") or f"PROG_{code.upper()}"
    try:
        payload = decision_engine_service.list_site_scores(program_code=db_code, limit=5000)
    except Exception:
        return []
    sites = []
    for index, site in enumerate(payload.get("sites") or [], start=1):
        sites.append(
            {
                "site_id": site.get("site_id") or index,
                "site_code": site.get("site_code") or site.get("code") or f"{code.upper()}_{index:05d}",
                "site_name": site.get("site_name") or site.get("name"),
                "latitude": site.get("latitude"),
                "longitude": site.get("longitude"),
                "province": site.get("province"),
                "territoire": site.get("territoire"),
                "zone": site.get("zone"),
                "population": site.get("population"),
                "population_range": site.get("population_range"),
                "nearest_site": site.get("nearest_site"),
                "distance": site.get("distance") or site.get("distance_m"),
                "distance_level": site.get("distance_level"),
                "is_300_planned": bool(site.get("is_300_planned")) or code == "sites_300",
                "program_code": code,
            }
        )
    return sites


def _sites_for_program(program_code: str) -> list[dict[str, Any]]:
    code = fdsu_sites_import_service.normalize_program_code(program_code)
    if code == "sites_20476":
        payload = fdsu_sites_import_service.load_program_sites(code)
        return list(payload.get("sites") or [])
    if code in {"sites_40", "sites_300"}:
        # Prefer JSON program files when present; fallback to DB engine scores.
        json_path = fdsu_sites_import_service.program_output_dir(code) / f"{code}.json"
        if json_path.exists():
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            sites = list(payload.get("sites") or [])
            normalized = []
            for index, site in enumerate(sites, start=1):
                normalized.append(
                    {
                        "site_id": site.get("site_id") or index,
                        "site_code": site.get("site_code") or site.get("code") or f"{code.upper()}_{index:05d}",
                        "site_name": site.get("site_name") or site.get("name"),
                        "latitude": site.get("latitude"),
                        "longitude": site.get("longitude"),
                        "province": site.get("province"),
                        "territoire": site.get("territoire"),
                        "zone": site.get("zone"),
                        "population": site.get("population"),
                        "population_range": site.get("population_range"),
                        "nearest_site": site.get("nearest_site"),
                        "distance": site.get("distance"),
                        "distance_level": site.get("distance_level"),
                        "is_300_planned": bool(site.get("is_300_planned")) or code == "sites_300",
                        "program_code": code,
                    }
                )
            return normalized
        return _sites_from_db_program(code)
    # Vague future : tenter JSON générique data/programs/<code>/<code>.json
    json_path = fdsu_sites_import_service.program_output_dir(code) / f"{code}.json"
    if json_path.exists():
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        return list(payload.get("sites") or [])
    return []


def list_priorities(
    program_code: str = "sites_20476",
    *,
    priority_level: str | None = None,
    limit: int = 500,
    offset: int = 0,
) -> dict[str, Any]:
    code = fdsu_sites_import_service.normalize_program_code(program_code)
    scored = list(_scored_sites_cached(code))

    if priority_level:
        scored = [item for item in scored if item.get("priority_level") == priority_level]

    summary = {
        "total": len(scored),
        "critical": sum(1 for item in scored if item["priority_level"] == "critical"),
        "high": sum(1 for item in scored if item["priority_level"] == "high"),
        "medium": sum(1 for item in scored if item["priority_level"] == "medium"),
        "low": sum(1 for item in scored if item["priority_level"] == "low"),
        "is_300_planned": sum(1 for item in scored if item.get("is_300_planned")),
    }
    page = scored[offset: offset + limit]
    meta = fdsu_sites_import_service.program_meta(code)
    return {
        "_meta": {
            "title": "Priorisation nationale des sites FDSU",
            "program_code": code,
            "program_label": meta.get("label"),
            "phase": meta.get("phase"),
            "calibration": "matrice_priorisation_300_sites",
            "computed_at": _now(),
        },
        "summary": summary,
        "count": len(page),
        "offset": offset,
        "limit": limit,
        "sites": page,
    }


def top_priorities(program_code: str = "sites_20476", *, limit: int = 50) -> dict[str, Any]:
    payload = list_priorities(program_code, limit=limit, offset=0)
    return {
        "_meta": {
            **payload["_meta"],
            "title": "Top priorités nationales FDSU",
        },
        "summary": payload["summary"],
        "sites": payload["sites"],
    }


def explain_site(site_id: int, program_code: str | None = None) -> dict[str, Any] | None:
    codes = []
    if program_code:
        codes.append(fdsu_sites_import_service.normalize_program_code(program_code))
    else:
        codes.extend(["sites_20476", "sites_300", "sites_40"])

    for code in codes:
        try:
            sites = _sites_for_program(code)
        except FileNotFoundError:
            continue
        for site in sites:
            if int(site.get("site_id") or -1) == int(site_id):
                scored = compute_national_site_score(site)
                return {
                    "_meta": {
                        "title": "Explication du score de priorité FDSU",
                        "program_code": code,
                        "site_id": site_id,
                        "computed_at": _now(),
                    },
                    "site": scored,
                    "explanation": {
                        "question": "Pourquoi ce site est-il prioritaire ?",
                        "answer": (
                            f"Score {scored['priority_score']} / 100 — niveau {scored['priority_level_label']}."
                        ),
                        "criteria": scored["criteria_details"]["criteria"],
                        "top_factors": scored["criteria_details"]["top_factors"],
                        "calibration_note": scored["criteria_details"]["calibration"]["note"],
                    },
                }
    # Fallback DB engine for numeric site ids already scored
    try:
        db_score = decision_engine_service.get_site_score(site_id)
        if db_score:
            return {
                "_meta": {
                    "title": "Explication du score (moteur DB)",
                    "program_code": db_score.get("program_code"),
                    "site_id": site_id,
                    "computed_at": _now(),
                    "source": "decision.fdsu_site_scores",
                },
                "site": db_score,
                "explanation": {
                    "question": "Pourquoi ce site est-il prioritaire ?",
                    "answer": f"Score {db_score.get('priority_score')} — {db_score.get('priority_level_label')}",
                    "criteria": (db_score.get("criteria_details") or {}).get("criteria"),
                    "top_factors": (db_score.get("criteria_details") or {}).get("top_factors"),
                },
            }
    except Exception:
        pass
    return None


def export_priorities(program_code: str = "sites_20476", *, limit: int = 50000) -> dict[str, Any]:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    payload = list_priorities(program_code, limit=limit, offset=0)
    code = fdsu_sites_import_service.normalize_program_code(program_code)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = EXPORT_DIR / f"priorities_{code}_{stamp}.csv"

    fieldnames = [
        "site_id",
        "site_code",
        "site_name",
        "program_code",
        "province",
        "territoire",
        "zone",
        "latitude",
        "longitude",
        "population",
        "distance",
        "distance_level",
        "is_300_planned",
        "priority_score",
        "priority_level",
        "priority_level_label",
        "top_factor_1",
        "top_factor_2",
        "top_factor_3",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        for site in payload["sites"]:
            tops = (site.get("criteria_details") or {}).get("top_factors") or []
            writer.writerow(
                {
                    "site_id": site.get("site_id"),
                    "site_code": site.get("site_code"),
                    "site_name": site.get("site_name"),
                    "program_code": site.get("program_code"),
                    "province": site.get("province"),
                    "territoire": site.get("territoire"),
                    "zone": site.get("zone"),
                    "latitude": site.get("latitude"),
                    "longitude": site.get("longitude"),
                    "population": site.get("population"),
                    "distance": site.get("distance"),
                    "distance_level": site.get("distance_level"),
                    "is_300_planned": site.get("is_300_planned"),
                    "priority_score": site.get("priority_score"),
                    "priority_level": site.get("priority_level"),
                    "priority_level_label": site.get("priority_level_label"),
                    "top_factor_1": (tops[0]["label"] if len(tops) > 0 else ""),
                    "top_factor_2": (tops[1]["label"] if len(tops) > 1 else ""),
                    "top_factor_3": (tops[2]["label"] if len(tops) > 2 else ""),
                }
            )

    return {
        "program_code": code,
        "export_path": str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "absolute_path": str(path),
        "count": len(payload["sites"]),
        "summary": payload["summary"],
        "filename": path.name,
    }


def list_supported_programs() -> list[dict[str, Any]]:
    programs = []
    for code in ("sites_40", "sites_300", "sites_20476"):
        meta = fdsu_sites_import_service.program_meta(code)
        json_path = fdsu_sites_import_service.program_output_dir(code) / f"{code}.json"
        count = None
        if json_path.exists():
            try:
                count = json.loads(json_path.read_text(encoding="utf-8")).get("_meta", {}).get("count")
            except Exception:
                count = None
        programs.append({**meta, "data_available": json_path.exists(), "site_count": count})
    return programs
