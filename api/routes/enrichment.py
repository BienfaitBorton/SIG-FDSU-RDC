from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas.base import (
    TerritorialEnrichmentSuggestionCreate,
    TerritorialEnrichmentSuggestionRead,
    TerritorialEnrichmentSuggestionUpdate,
)
from api.schemas.enrichment import (
    EnrichmentCompletenessItem,
    EnrichmentDashboard,
    EnrichmentPriorities,
    EnrichmentSuggestionDecision,
    EnrichmentTraceabilityCheck,
)
from api.services.territorial_enrichment_service import (
    build_completeness_items,
    build_dashboard,
    build_priority_items,
    create_suggestion,
    get_suggestion,
    list_suggestions,
    update_suggestion,
)

router = APIRouter()


@router.get("/dashboard", response_model=EnrichmentDashboard, summary="Assistant d'enrichissement")
def dashboard(db: Session = Depends(get_db)) -> EnrichmentDashboard:
    return build_dashboard(db)


@router.get(
    "/completeness",
    response_model=list[EnrichmentCompletenessItem],
    summary="Completeness territoriale filtrable",
)
def completeness(
    zone: str | None = Query(None),
    province: str | None = Query(None),
    territoire: str | None = Query(None),
    entity_type: str | None = Query(None),
    completeness_level: str | None = Query(None),
    missing_field: str | None = Query(None),
    priority: str | None = Query(None),
    source: str | None = Query(None),
    db: Session = Depends(get_db),
) -> list[EnrichmentCompletenessItem]:
    return build_completeness_items(
        db,
        zone=zone,
        province=province,
        territoire=territoire,
        entity_type=entity_type,
        completeness_level=completeness_level,
        missing_field=missing_field,
        priority=priority,
        source=source,
    )


@router.get("/priorities", response_model=EnrichmentPriorities, summary="Priorites d'enrichissement")
def priorities(db: Session = Depends(get_db)) -> EnrichmentPriorities:
    return EnrichmentPriorities(items=build_priority_items(db))


@router.get(
    "/suggestions",
    response_model=list[TerritorialEnrichmentSuggestionRead],
    summary="Propositions d'enrichissement",
)
def suggestions(
    status: str | None = Query(None),
    entity_type: str | None = Query(None),
    field_name: str | None = Query(None),
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
    summary="Creer une proposition manuelle",
)
def create(payload: TerritorialEnrichmentSuggestionCreate, db: Session = Depends(get_db)) -> TerritorialEnrichmentSuggestionRead:
    return create_suggestion(db, payload)


@router.patch(
    "/suggestions/{suggestion_id}/validate",
    response_model=TerritorialEnrichmentSuggestionRead,
    summary="Valider une proposition sans publication officielle",
)
def validate(
    suggestion_id: int,
    payload: EnrichmentSuggestionDecision | None = None,
    db: Session = Depends(get_db),
) -> TerritorialEnrichmentSuggestionRead:
    update_payload = payload or EnrichmentSuggestionDecision()
    data = update_payload.model_dump(exclude_unset=True)
    data["status"] = "validé"
    suggestion = update_suggestion(db, suggestion_id, TerritorialEnrichmentSuggestionUpdate(**data))
    if suggestion is None:
        raise HTTPException(status_code=404, detail="Proposition d'enrichissement non trouvee")
    return suggestion


@router.patch(
    "/suggestions/{suggestion_id}/reject",
    response_model=TerritorialEnrichmentSuggestionRead,
    summary="Rejeter une proposition",
)
def reject(
    suggestion_id: int,
    payload: EnrichmentSuggestionDecision | None = None,
    db: Session = Depends(get_db),
) -> TerritorialEnrichmentSuggestionRead:
    update_payload = payload or EnrichmentSuggestionDecision()
    data = update_payload.model_dump(exclude_unset=True)
    data["status"] = "rejeté"
    suggestion = update_suggestion(db, suggestion_id, TerritorialEnrichmentSuggestionUpdate(**data))
    if suggestion is None:
        raise HTTPException(status_code=404, detail="Proposition d'enrichissement non trouvee")
    return suggestion


@router.get(
    "/suggestions/{suggestion_id}/traceability",
    response_model=EnrichmentTraceabilityCheck,
    summary="Verifier la tracabilite d'une proposition",
)
def traceability(suggestion_id: int, db: Session = Depends(get_db)) -> EnrichmentTraceabilityCheck:
    suggestion = get_suggestion(db, suggestion_id)
    if suggestion is None:
        raise HTTPException(status_code=404, detail="Proposition d'enrichissement non trouvee")
    return EnrichmentTraceabilityCheck(
        suggestion_id=suggestion.id,
        status=suggestion.status,
        traceable=bool(suggestion.source_name and suggestion.source_url and suggestion.consulted_at),
        published_to_official_referential=False,
        checked_at=datetime.utcnow(),
    )
