"""Endpoints REST du Moteur de Décision FDSU v1.0."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from api.config import DATA_MODE
from api.services import (
    decision_demo_service,
    decision_engine_service,
    decision_kpi_detail_service,
    decision_scenarios_service,
    explainable_decision_service,
    fdsu_site_priority_service,
    fdsu_sites_import_service,
)

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


@router.get("/scenarios", summary="Catalogue des scénarios décisionnels v1.2")
def list_decision_scenarios() -> dict[str, Any]:
    _ensure_db_mode()
    return decision_scenarios_service.list_scenarios()


@router.get("/scenarios/{scenario_id}", summary="Métadonnées d’un scénario décisionnel")
def get_decision_scenario(scenario_id: str) -> dict[str, Any]:
    _ensure_db_mode()
    item = decision_scenarios_service.get_scenario(scenario_id)
    if not item:
        raise HTTPException(status_code=404, detail="Scénario introuvable.")
    return {"scenario": item, "_meta": {"version": decision_scenarios_service.ENGINE_VERSION}}


@router.get("/scenarios/{scenario_id}/run", summary="Exécuter un scénario décisionnel (orchestration)")
def run_decision_scenario(
    scenario_id: str,
    program_code: str | None = Query(None),
    territory_id: str | None = Query(None),
    asset_id: str | None = Query(None),
    site_id: str | None = Query(None),
) -> dict[str, Any]:
    _ensure_db_mode()
    if not decision_scenarios_service.get_scenario(scenario_id):
        raise HTTPException(status_code=404, detail="Scénario introuvable.")
    context = {
        "program_code": program_code,
        "territory_id": territory_id,
        "asset_id": asset_id or site_id,
        "site_id": site_id or asset_id,
    }
    context = {k: v for k, v in context.items() if v is not None}
    return decision_scenarios_service.run_scenario(scenario_id, context)


def _detail_filters(
    province: str | None,
    territoire: str | None,
    programme: str | None,
    priority_level: str | None,
    status: str | None,
    category: str | None,
    q: str | None,
) -> dict[str, Any]:
    return {
        "province": province,
        "territoire": territoire,
        "programme": programme,
        "priority_level": priority_level,
        "status": status,
        "category": category,
        "q": q,
    }


@router.get("/details", summary="Catalogue des KPI décisionnels (Decision Detail Workspace)")
def decision_details_catalog() -> dict[str, Any]:
    return decision_kpi_detail_service.list_kpi_catalog()


@router.get("/details/{kpi_code}", summary="Vue détail d'un KPI décisionnel")
def decision_detail(
    kpi_code: str,
    province: str | None = Query(None),
    territoire: str | None = Query(None),
    programme: str | None = Query(None),
    priority_level: str | None = Query(None),
    status: str | None = Query(None),
    category: str | None = Query(None),
    q: str | None = Query(None),
    limit: int = Query(100, gt=0, le=2000),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    result = decision_kpi_detail_service.build_detail(
        kpi_code,
        province=province,
        territoire=territoire,
        programme=programme,
        priority_level=priority_level,
        status=status,
        category=category,
        q=q,
        limit=limit,
        offset=offset,
    )
    if not result:
        raise HTTPException(status_code=404, detail=f"KPI inconnu: {kpi_code}")
    return result


@router.get("/details/{kpi_code}/map", summary="GeoJSON du KPI")
def decision_detail_map(
    kpi_code: str,
    province: str | None = Query(None),
    territoire: str | None = Query(None),
    programme: str | None = Query(None),
    priority_level: str | None = Query(None),
    status: str | None = Query(None),
    q: str | None = Query(None),
) -> dict[str, Any]:
    result = decision_kpi_detail_service.build_map(
        kpi_code,
        **_detail_filters(province, territoire, programme, priority_level, status, None, q),
    )
    if not result:
        raise HTTPException(status_code=404, detail=f"KPI inconnu: {kpi_code}")
    return result


@router.get("/details/{kpi_code}/charts", summary="Graphiques EDVS du KPI")
def decision_detail_charts(
    kpi_code: str,
    province: str | None = Query(None),
    territoire: str | None = Query(None),
    programme: str | None = Query(None),
    priority_level: str | None = Query(None),
    status: str | None = Query(None),
    q: str | None = Query(None),
) -> dict[str, Any]:
    result = decision_kpi_detail_service.build_charts(
        kpi_code,
        **_detail_filters(province, territoire, programme, priority_level, status, None, q),
    )
    if not result:
        raise HTTPException(status_code=404, detail=f"KPI inconnu: {kpi_code}")
    return result


@router.get("/details/{kpi_code}/items", summary="Liste paginée des éléments du KPI")
def decision_detail_items(
    kpi_code: str,
    province: str | None = Query(None),
    territoire: str | None = Query(None),
    programme: str | None = Query(None),
    priority_level: str | None = Query(None),
    status: str | None = Query(None),
    category: str | None = Query(None),
    q: str | None = Query(None),
    limit: int = Query(100, gt=0, le=2000),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    result = decision_kpi_detail_service.build_items(
        kpi_code,
        limit=limit,
        offset=offset,
        **_detail_filters(province, territoire, programme, priority_level, status, category, q),
    )
    if not result:
        raise HTTPException(status_code=404, detail=f"KPI inconnu: {kpi_code}")
    return result


@router.get("/details/{kpi_code}/explain", summary="Justification du KPI")
def decision_detail_explain(
    kpi_code: str,
    province: str | None = Query(None),
    territoire: str | None = Query(None),
    programme: str | None = Query(None),
    priority_level: str | None = Query(None),
    q: str | None = Query(None),
) -> dict[str, Any]:
    result = decision_kpi_detail_service.build_explain(
        kpi_code,
        **_detail_filters(province, territoire, programme, priority_level, None, None, q),
    )
    if not result:
        raise HTTPException(status_code=404, detail=f"KPI inconnu: {kpi_code}")
    return result


@router.get("/details/{kpi_code}/export", summary="Export Excel/CSV/GeoJSON du KPI")
def decision_detail_export(
    kpi_code: str,
    format: str = Query("csv", description="csv | excel | geojson | json"),
    province: str | None = Query(None),
    territoire: str | None = Query(None),
    programme: str | None = Query(None),
    priority_level: str | None = Query(None),
    status: str | None = Query(None),
    q: str | None = Query(None),
) -> dict[str, Any]:
    result = decision_kpi_detail_service.build_export(
        kpi_code,
        format=format,
        **_detail_filters(province, territoire, programme, priority_level, status, None, q),
    )
    if not result:
        raise HTTPException(status_code=404, detail=f"KPI inconnu: {kpi_code}")
    return result


@router.get("/case/{asset_id}", summary="Dossier de Décision (Decision Case File)")
def decision_case(
    asset_id: str,
    asset_type: str | None = Query(None, description="ccn | site"),
    program_code: str | None = Query(None),
) -> dict[str, Any]:
    try:
        result = explainable_decision_service.get_decision_case(
            asset_id,
            asset_type=asset_type,
            program_code=program_code,
        )
    except Exception as exc:  # noqa: BLE001 — ne jamais exposer Extra data / stack au client
        raise HTTPException(
            status_code=503,
            detail="Dossier de décision temporairement indisponible. Réessayez.",
        ) from exc
    if not result:
        raise HTTPException(status_code=404, detail="Dossier de décision introuvable pour cet actif.")
    return result


@router.get("/explain/{asset_id}", summary="Justification détaillée d'une recommandation")
def explain_decision(
    asset_id: str,
    asset_type: str | None = Query(None, description="ccn | site"),
    program_code: str | None = Query(None),
) -> dict[str, Any]:
    result = explainable_decision_service.explain_decision(
        asset_id,
        asset_type=asset_type,
        program_code=program_code,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Justification introuvable pour cet actif.")
    return result


@router.get("/doctrine/{doctrine_id}", summary="Doctrine métier utilisée par le moteur")
def decision_doctrine(doctrine_id: str) -> dict[str, Any]:
    result = explainable_decision_service.get_doctrine_payload(doctrine_id)
    if not result:
        raise HTTPException(status_code=404, detail="Doctrine introuvable.")
    return result


@router.get("/case-history", summary="Historique / traçabilité des dossiers de décision")
def decision_case_history(
    case_id: str | None = Query(None),
    limit: int = Query(50, gt=0, le=500),
) -> dict[str, Any]:
    return explainable_decision_service.get_case_history(case_id=case_id, limit=limit)


@router.get("/pdf-template", summary="Modèle PDF Dossier de Décision (structure only)")
def decision_pdf_template() -> dict[str, Any]:
    template = explainable_decision_service.pdf_template()
    if not template:
        raise HTTPException(status_code=404, detail="Modèle PDF introuvable.")
    return template


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
