"""API du Référentiel Éducation provisoire."""

from typing import Any
from fastapi import APIRouter, Query
from api.services import education_referential_service as service

router = APIRouter()


@router.get("/statistics", summary="Statistiques agrégées du Référentiel Éducation")
def statistics() -> dict[str, Any]: return service.statistics()


@router.get("/establishments", summary="Établissements scolaires dérivés des Sites CENI")
def establishments(subtype: str | None = None, quality: str | None = None, province: str | None = None, limit: int = Query(100, ge=1, le=5000), offset: int = Query(0, ge=0)) -> dict[str, Any]:
    return service.list_establishments(subtype=subtype, quality=quality, province=province, limit=limit, offset=offset)
