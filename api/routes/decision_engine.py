"""Endpoints REST du Moteur de Décision FDSU v1.0."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from api.config import DATA_MODE
from api.services import decision_demo_service, decision_engine_service, fdsu_site_priority_service, fdsu_sites_import_service

router = APIRouter()


class RecomputePayload(BaseModel):
    program_codes: list[str] | None = None


class ImportNationalPayload(BaseModel):
    csv_path: str | None = None
    program_code: str = "sites_20476"


def _ensure_db_mode() -> None:
    if DATA_MODE != "db":
        raise HTTPException(
            status_code=503,
            detail="Endpoint disponible uniquement en mode DB (DATA_MODE=db).",
        )


@router.get("/site-scores", summary="Liste des scores de priorité FDSU")
def list_site_scores(
    priority_level: str | None = Query(None, description="Filtrer par niveau: critical, high, medium, low"),
    program_code: str | None = Query(None, description="Filtrer par code programme"),
    limit: int = Query(500, gt=0, le=2000),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    _ensure_db_mode()
    return decision_engine_service.list_site_scores(
        priority_level=priority_level,
        program_code=program_code,
        limit=limit,
        offset=offset,
    )


@router.get("/site-scores/{site_id}", summary="Score de priorité d'un site FDSU")
def get_site_score(site_id: int) -> dict[str, Any]:
    _ensure_db_mode()
    result = decision_engine_service.get_site_score(site_id)
    if not result:
        raise HTTPException(status_code=404, detail="Score introuvable pour ce site.")
    return result


@router.post("/recompute-site-scores", summary="Recalculer tous les scores de priorité")
def recompute_site_scores(_payload: RecomputePayload | None = None) -> dict[str, Any]:
    _ensure_db_mode()
    return decision_engine_service.recompute_all_site_scores()


@router.get("/panel", summary="Synthèse Centre de Décision — moteur de décision")
def decision_panel() -> dict[str, Any]:
    _ensure_db_mode()
    return decision_engine_service.get_panel_payload()


@router.get("/national-panel", summary="Panneau national du Centre de Décision — KPI réels")
def national_panel() -> dict[str, Any]:
    _ensure_db_mode()
    return decision_engine_service.get_national_panel_payload()


@router.get("/explain-kpi", summary="KPI explicables du Centre de Décision")
def explain_kpi(kpi_key: str | None = Query(None, description="Clé KPI optionnelle")) -> dict[str, Any]:
    _ensure_db_mode()
    payload = decision_demo_service.get_explain_kpi_payload(kpi_key)
    if payload.get("error"):
        raise HTTPException(status_code=404, detail=payload["error"])
    return payload


@router.get("/decision-intents", summary="Questions métier — Que voulez-vous décider aujourd’hui ?")
def decision_intents() -> dict[str, Any]:
    _ensure_db_mode()
    return decision_demo_service.get_decision_intents()


@router.get("/demo-scenarios", summary="Mode démonstration — scénarios superviseur")
def demo_scenarios() -> dict[str, Any]:
    _ensure_db_mode()
    return decision_demo_service.get_demo_scenarios()


@router.get("/sites/programs", summary="Programmes / vagues supportés par la priorisation nationale")
def list_priority_programs() -> dict[str, Any]:
    return {
        "_meta": {
            "title": "Vagues FDSU supportées",
            "note": "40 = pilote ; 300 = première vague ; 20 476 = national ; extensible.",
        },
        "programs": fdsu_site_priority_service.list_supported_programs(),
    }


@router.get("/sites/priorities", summary="Priorisation nationale des sites FDSU")
def sites_priorities(
    program_code: str = Query("sites_20476", description="sites_40 | sites_300 | sites_20476"),
    priority_level: str | None = Query(None),
    limit: int = Query(200, gt=0, le=5000),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    try:
        return fdsu_site_priority_service.list_priorities(
            program_code,
            priority_level=priority_level,
            limit=limit,
            offset=offset,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/sites/top-priorities", summary="Top priorités nationales FDSU")
def sites_top_priorities(
    program_code: str = Query("sites_20476"),
    limit: int = Query(50, gt=0, le=500),
) -> dict[str, Any]:
    try:
        return fdsu_site_priority_service.top_priorities(program_code, limit=limit)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/sites/{site_id}/explain", summary="Expliquer le score d'un site FDSU")
def explain_site_priority(
    site_id: int,
    program_code: str | None = Query(None),
) -> dict[str, Any]:
    result = fdsu_site_priority_service.explain_site(site_id, program_code=program_code)
    if not result:
        raise HTTPException(status_code=404, detail="Site introuvable pour explication.")
    return result


@router.get("/sites/export", summary="Exporter la priorisation nationale (CSV)")
def export_site_priorities(
    program_code: str = Query("sites_20476"),
    limit: int = Query(50000, gt=0, le=100000),
) -> dict[str, Any]:
    try:
        return fdsu_site_priority_service.export_priorities(program_code, limit=limit)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/sites/import-national", summary="Importer le programme national (CSV 20 476)")
def import_national_sites(payload: ImportNationalPayload | None = None) -> dict[str, Any]:
    body = payload or ImportNationalPayload()
    csv_path = Path(body.csv_path) if body.csv_path else None
    if csv_path and not csv_path.is_absolute():
        csv_path = fdsu_sites_import_service.PROJECT_ROOT / csv_path
    try:
        result = fdsu_sites_import_service.import_sites_csv(
            csv_path,
            program_code=body.program_code,
            write_outputs=True,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    # Ne pas renvoyer les 20k sites dans la réponse HTTP
    return {
        "program_code": result["program_code"],
        "count": result["count"],
        "statistics": result["statistics"],
        "outputs": result["outputs"],
        "meta": result["meta"],
    }
