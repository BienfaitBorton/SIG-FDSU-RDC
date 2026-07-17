from typing import Any

from fastapi import APIRouter, HTTPException, Query

from api.services.ntil_service import default_ntil

router = APIRouter()


@router.get("/statistics")
def statistics() -> dict[str, Any]:
    return default_ntil().statistics()


@router.get("/registry")
def registry(q: str = Query("", max_length=100), status: str | None = None, family: str | None = None, referential: str | None = None, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000)) -> dict[str, Any]:
    return default_ntil().list_terms(query=q, status=status, family=family, referential=referential, skip=skip, limit=limit)


@router.get("/term/{term_id}")
def term(term_id: str) -> dict[str, Any]:
    row = default_ntil().term(term_id)
    if not row: raise HTTPException(status_code=404, detail="Terme NTR introuvable")
    return {"term": row, "history": default_ntil().histories(term_id)["items"]}


@router.get("/discoveries")
def discoveries() -> dict[str, Any]:
    return default_ntil().discoveries()


@router.get("/quality")
def quality() -> dict[str, Any]:
    return default_ntil().quality()


@router.get("/history")
def history(term_id: str | None = None) -> dict[str, Any]:
    return default_ntil().histories(term_id)


@router.get("/families")
def families() -> dict[str, Any]:
    return default_ntil().families()


@router.get("/dashboard")
def dashboard() -> dict[str, Any]:
    return default_ntil().dashboard()
