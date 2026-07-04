from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas.base import (
    TerritorialEnrichmentSuggestionCreate,
    TerritorialEnrichmentSuggestionRead,
    TerritorialEnrichmentSuggestionUpdate,
)
from api.services.territorial_enrichment_service import (
    ALLOWED_FIELDS,
    ALLOWED_SOURCE_NAMES,
    ALLOWED_STATUSES,
    create_suggestion,
    get_suggestion,
    list_suggestions,
    update_suggestion,
)

router = APIRouter()


@router.get("/sources", summary="Lister les sources autorisées")
def sources() -> dict[str, list[str]]:
    return {"sources": sorted(ALLOWED_SOURCE_NAMES)}


@router.get("/fields", summary="Lister les champs enrichissables")
def fields() -> dict[str, list[str]]:
    return {"fields": sorted(ALLOWED_FIELDS)}


@router.get("/statuses", summary="Lister les statuts de revue")
def statuses() -> dict[str, list[str]]:
    return {"statuses": sorted(ALLOWED_STATUSES)}


@router.get(
    "/suggestions",
    response_model=list[TerritorialEnrichmentSuggestionRead],
    summary="Lister les propositions d'enrichissement",
)
def read_suggestions(
    status: str | None = Query(None, description="Filtrer par statut: proposé, validé ou rejeté."),
    entity_type: str | None = Query(None, description="Filtrer par niveau territorial."),
    field_name: str | None = Query(None, description="Filtrer par champ enrichissable."),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, gt=0, le=500),
    db: Session = Depends(get_db),
) -> list[TerritorialEnrichmentSuggestionRead]:
    return list_suggestions(
        db,
        status=status,
        entity_type=entity_type,
        field_name=field_name,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/suggestions",
    response_model=TerritorialEnrichmentSuggestionRead,
    summary="Créer une proposition contrôlée",
)
def create(payload: TerritorialEnrichmentSuggestionCreate, db: Session = Depends(get_db)) -> TerritorialEnrichmentSuggestionRead:
    return create_suggestion(db, payload)


@router.get(
    "/suggestions/{suggestion_id}",
    response_model=TerritorialEnrichmentSuggestionRead,
    summary="Consulter une proposition d'enrichissement",
)
def read_one(suggestion_id: int, db: Session = Depends(get_db)) -> TerritorialEnrichmentSuggestionRead:
    suggestion = get_suggestion(db, suggestion_id)
    if suggestion is None:
        raise HTTPException(status_code=404, detail="Proposition d'enrichissement non trouvée")
    return suggestion


@router.patch(
    "/suggestions/{suggestion_id}",
    response_model=TerritorialEnrichmentSuggestionRead,
    summary="Modifier une proposition avant décision",
)
def update(
    suggestion_id: int,
    payload: TerritorialEnrichmentSuggestionUpdate,
    db: Session = Depends(get_db),
) -> TerritorialEnrichmentSuggestionRead:
    suggestion = update_suggestion(db, suggestion_id, payload)
    if suggestion is None:
        raise HTTPException(status_code=404, detail="Proposition d'enrichissement non trouvée")
    return suggestion


@router.post(
    "/suggestions/{suggestion_id}/accept",
    response_model=TerritorialEnrichmentSuggestionRead,
    summary="Accepter une proposition",
)
def accept(
    suggestion_id: int,
    payload: TerritorialEnrichmentSuggestionUpdate | None = None,
    db: Session = Depends(get_db),
) -> TerritorialEnrichmentSuggestionRead:
    update_payload = payload or TerritorialEnrichmentSuggestionUpdate()
    data = update_payload.model_dump(exclude_unset=True)
    data["status"] = "validé"
    suggestion = update_suggestion(db, suggestion_id, TerritorialEnrichmentSuggestionUpdate(**data))
    if suggestion is None:
        raise HTTPException(status_code=404, detail="Proposition d'enrichissement non trouvée")
    return suggestion


@router.post(
    "/suggestions/{suggestion_id}/reject",
    response_model=TerritorialEnrichmentSuggestionRead,
    summary="Rejeter une proposition",
)
def reject(
    suggestion_id: int,
    payload: TerritorialEnrichmentSuggestionUpdate | None = None,
    db: Session = Depends(get_db),
) -> TerritorialEnrichmentSuggestionRead:
    update_payload = payload or TerritorialEnrichmentSuggestionUpdate()
    data = update_payload.model_dump(exclude_unset=True)
    data["status"] = "rejeté"
    suggestion = update_suggestion(db, suggestion_id, TerritorialEnrichmentSuggestionUpdate(**data))
    if suggestion is None:
        raise HTTPException(status_code=404, detail="Proposition d'enrichissement non trouvée")
    return suggestion
