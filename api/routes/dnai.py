from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from api.services.dnai_service import default_dnai

router = APIRouter()


class NormalizeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    referential: str = Field(default="national", max_length=80)


@router.get("/search")
def search(q: str = Query("", max_length=100), family: str | None = None) -> dict[str, Any]:
    rows = default_dnai().search(q, family)
    return {"count": len(rows), "entries": rows}


@router.get("/expand/{abbr}")
def expand(abbr: str, referential: str = "national") -> dict[str, Any]:
    return default_dnai().expand(abbr, referential).as_dict()


@router.post("/normalize")
def normalize(payload: NormalizeRequest) -> dict[str, Any]:
    return default_dnai().normalize(payload.text, payload.referential).as_dict()


@router.get("/statistics")
def statistics() -> dict[str, Any]:
    return default_dnai().statistics()


@router.get("/discover")
def discover(limit: int = Query(100, ge=1, le=1000)) -> dict[str, Any]:
    payload = default_dnai().discover_ceni()
    payload["discoveries"] = payload.get("discoveries", [])[:limit]
    return payload


@router.get("/pending-validations")
def pending_validations() -> dict[str, Any]:
    rows = default_dnai().pending_validations()
    return {"count": len(rows), "items": rows}
