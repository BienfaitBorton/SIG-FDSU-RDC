"""Endpoints REST — Module de Géocodage Intelligent FDSU."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from api.services import geocoding_service

router = APIRouter()


def _job_response(job: dict[str, Any]) -> dict[str, Any]:
    summary = job.get("summary") or {}
    return {
        "job_id": job.get("job_id"),
        "status": job.get("status"),
        "kind": job.get("kind"),
        "created_at": job.get("created_at"),
        "updated_at": job.get("updated_at"),
        "error": job.get("error"),
        "rows_analyzed": summary.get("rows_analyzed", 0),
        "valid_kept": summary.get("valid_kept", summary.get("valid_kept_candidate", 0)),
        "corrected": summary.get("corrected", 0),
        "approximate": summary.get("approximate", 0),
        "failed": summary.get("failed", summary.get("to_geocode", 0)),
        "anomalies": summary.get("anomalies", {}),
        "export_path": job.get("export_path") or summary.get("export_path"),
        "export_filename": summary.get("export_filename"),
        "summary": summary,
        "results_preview": job.get("results_preview") or [],
        "geojson": job.get("geojson"),
        "meta": {
            "source_file": (job.get("meta") or {}).get("source_file"),
            "sheet": (job.get("meta") or {}).get("sheet") or summary.get("sheet"),
            "columns": (job.get("meta") or {}).get("columns") or summary.get("columns"),
            "enable_nominatim": (job.get("meta") or {}).get("enable_nominatim"),
            "enable_offline": (job.get("meta") or {}).get("enable_offline"),
        },
    }


@router.post("/analyze-excel", summary="Analyser la qualité des coordonnées d'un Excel FDSU")
async def analyze_excel(
    file: UploadFile = File(...),
    sheet_name: str | None = Form(None),
) -> dict[str, Any]:
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xlsm")):
        raise HTTPException(status_code=400, detail="Fichier Excel (.xlsx) requis.")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Fichier vide.")
    path = geocoding_service.resolve_upload_path(file.filename, content)
    try:
        job = geocoding_service.analyze_excel_file(path, sheet_name=sheet_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analyse impossible : {exc}") from exc
    return _job_response(job)


@router.post("/geocode-excel", summary="Géocoder / corriger un Excel FDSU de façon contrôlée")
async def geocode_excel(
    file: UploadFile = File(...),
    sheet_name: str | None = Form(None),
    enable_nominatim: bool = Form(False),
    enable_offline: bool = Form(True),
    max_external_calls: int = Form(30),
) -> dict[str, Any]:
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xlsm")):
        raise HTTPException(status_code=400, detail="Fichier Excel (.xlsx) requis.")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Fichier vide.")
    path = geocoding_service.resolve_upload_path(file.filename, content)
    try:
        job = geocoding_service.geocode_excel_file(
            path,
            sheet_name=sheet_name,
            enable_nominatim=enable_nominatim,
            enable_offline=enable_offline,
            max_external_calls=max(0, min(max_external_calls, 200)),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Géocodage impossible : {exc}") from exc
    return _job_response(job)


@router.get("/jobs/{job_id}", summary="Statut et résultats d'un job de géocodage")
def get_job(job_id: str) -> dict[str, Any]:
    job = geocoding_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job introuvable.")
    return _job_response(job)


@router.get("/export/{job_id}", summary="Télécharger l'Excel géocodé")
def export_job(job_id: str) -> FileResponse:
    job = geocoding_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job introuvable.")
    export_path = job.get("export_path") or (job.get("summary") or {}).get("export_path")
    if not export_path:
        raise HTTPException(status_code=404, detail="Aucun export disponible pour ce job.")
    path = Path(export_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Fichier export introuvable sur le disque.")
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=path.name,
    )


@router.get("/schema/postgis", summary="Schéma PostGIS préparé pour les résultats de géocodage")
def postgis_schema() -> dict[str, Any]:
    return {
        "table": "geocoding.geocoding_results",
        "sql": geocoding_service.get_postgis_schema_sql(),
        "fields": [
            "site_id",
            "nom_site",
            "adresse_originale",
            "latitude",
            "longitude",
            "geom",
            "source_geocoding",
            "confidence_level",
            "validation_status",
            "created_at",
            "updated_at",
        ],
    }


@router.post("/analyze-path", summary="Analyser un fichier Excel déjà présent sur le serveur")
def analyze_path(
    path: str = Query(..., description="Chemin absolu ou relatif au projet"),
    sheet_name: str | None = Query(None),
) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.is_absolute():
        file_path = geocoding_service.PROJECT_ROOT / path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier introuvable.")
    try:
        job = geocoding_service.analyze_excel_file(file_path, sheet_name=sheet_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _job_response(job)


@router.post("/geocode-path", summary="Géocoder un fichier Excel déjà présent sur le serveur")
def geocode_path(
    path: str = Query(..., description="Chemin absolu ou relatif au projet"),
    sheet_name: str | None = Query(None),
    enable_nominatim: bool = Query(False),
    enable_offline: bool = Query(True),
    max_external_calls: int = Query(30, ge=0, le=200),
) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.is_absolute():
        file_path = geocoding_service.PROJECT_ROOT / path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier introuvable.")
    try:
        job = geocoding_service.geocode_excel_file(
            file_path,
            sheet_name=sheet_name,
            enable_nominatim=enable_nominatim,
            enable_offline=enable_offline,
            max_external_calls=max_external_calls,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _job_response(job)
