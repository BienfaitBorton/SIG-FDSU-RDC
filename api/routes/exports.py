"""API REST — Exports partagés FDSU (Zero Decorative Actions)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from api.services import export_service

router = APIRouter()


@router.get("/capabilities", summary="Capacités d’export et d’actions UI")
def get_export_capabilities() -> dict[str, Any]:
    return export_service.get_capabilities()


@router.get(
    "/decision-case/{entity_type}/{entity_id}/excel",
    summary="Export Excel réel du dossier de décision",
)
def export_decision_case_excel(
    entity_type: str,
    entity_id: str,
    program_code: str | None = Query(default=None),
) -> Response:
    try:
        payload, filename, _meta = export_service.build_decision_case_excel(
            entity_type,
            entity_id,
            program_code=program_code,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 — message métier, détail technique journalisé
        raise HTTPException(status_code=500, detail="Impossible de générer l’export Excel.") from exc

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "X-FDSU-Export-Filename": filename,
    }
    return Response(
        content=payload,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.get(
    "/decision-case/{entity_type}/{entity_id}/pdf",
    summary="Export PDF du dossier (non activé)",
)
def export_decision_case_pdf(entity_type: str, entity_id: str) -> None:
    raise HTTPException(
        status_code=501,
        detail="Export PDF non encore activé pour ce dossier",
    )


@router.get(
    "/decision-case/{entity_type}/{entity_id}/powerpoint",
    summary="Export PowerPoint du dossier (non activé)",
)
def export_decision_case_powerpoint(entity_type: str, entity_id: str) -> None:
    raise HTTPException(
        status_code=501,
        detail="Export PowerPoint non encore activé pour ce dossier",
    )
