from datetime import datetime

from sqlalchemy.orm import Session

from api.schemas.base import TerritorialEnrichmentSuggestionCreate, TerritorialEnrichmentSuggestionUpdate
from app.models import TerritorialEnrichmentSuggestion

ALLOWED_SOURCE_NAMES = {
    "CAID",
    "Ministère de l'Intérieur RDC",
    "INS",
    "ARPTC",
    "Texte légal officiel",
    "Document public institutionnel",
    "OpenStreetMap",
}

ALLOWED_FIELDS = {
    "subdivision_administrative_reelle",
    "activites_economiques_principales",
    "activites_economiques_secondaires",
    "particularites",
    "defis",
    "potentiel_agricole",
    "potentiel_minier",
    "potentiel_commercial",
    "potentiel_numerique",
    "services_publics",
    "couverture_reseau",
}

ALLOWED_STATUSES = {"proposé", "validé", "rejeté"}


def _validate_source(source_name: str) -> None:
    if source_name not in ALLOWED_SOURCE_NAMES:
        raise ValueError("Source non autorisée pour l'enrichissement territorial")


def _validate_field(field_name: str) -> None:
    if field_name not in ALLOWED_FIELDS:
        raise ValueError("Champ non autorisé pour l'enrichissement territorial")


def _validate_status(status: str) -> None:
    if status not in ALLOWED_STATUSES:
        raise ValueError("Statut d'enrichissement invalide")


def list_suggestions(
    session: Session,
    *,
    status: str | None = None,
    entity_type: str | None = None,
    field_name: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[TerritorialEnrichmentSuggestion]:
    query = session.query(TerritorialEnrichmentSuggestion)
    if status:
        _validate_status(status)
        query = query.filter(TerritorialEnrichmentSuggestion.status == status)
    if entity_type:
        query = query.filter(TerritorialEnrichmentSuggestion.entity_type == entity_type)
    if field_name:
        _validate_field(field_name)
        query = query.filter(TerritorialEnrichmentSuggestion.field_name == field_name)
    return (
        query.order_by(TerritorialEnrichmentSuggestion.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_suggestion(
    session: Session,
    payload: TerritorialEnrichmentSuggestionCreate,
) -> TerritorialEnrichmentSuggestion:
    _validate_source(payload.source_name)
    _validate_field(payload.field_name)
    suggestion = TerritorialEnrichmentSuggestion(**payload.model_dump(), status="proposé")
    session.add(suggestion)
    session.commit()
    session.refresh(suggestion)
    return suggestion


def get_suggestion(session: Session, suggestion_id: int) -> TerritorialEnrichmentSuggestion | None:
    return session.get(TerritorialEnrichmentSuggestion, suggestion_id)


def update_suggestion(
    session: Session,
    suggestion_id: int,
    payload: TerritorialEnrichmentSuggestionUpdate,
) -> TerritorialEnrichmentSuggestion | None:
    suggestion = session.get(TerritorialEnrichmentSuggestion, suggestion_id)
    if suggestion is None:
        return None

    data = payload.model_dump(exclude_unset=True)
    new_status = data.get("status")
    if new_status is not None:
        _validate_status(new_status)
        suggestion.status = new_status
        if new_status == "validé":
            suggestion.validated_at = datetime.utcnow()
            suggestion.validated_by = data.get("validated_by") or suggestion.validated_by
        elif new_status == "rejeté":
            suggestion.validated_at = None
    if "proposed_value" in data and data["proposed_value"] is not None:
        suggestion.proposed_value = data["proposed_value"]
    if "review_note" in data:
        suggestion.review_note = data["review_note"]
    if "validated_by" in data and new_status != "validé":
        suggestion.validated_by = data["validated_by"]

    session.commit()
    session.refresh(suggestion)
    return suggestion
