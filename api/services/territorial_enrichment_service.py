from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from api.schemas.base import TerritorialEnrichmentSuggestionCreate, TerritorialEnrichmentSuggestionUpdate
from api.schemas.enrichment import EnrichmentCompletenessItem, EnrichmentDashboard
from api.services.knowledge_service import DEMO_PROFILES, MISSING_VALUE
from app.models import TerritorialEnrichmentSuggestion

ALLOWED_SOURCE_NAMES = {
    "CAID",
    "Ministère de l'Intérieur RDC",
    "INS",
    "ARPTC",
    "Texte légal officiel",
    "Document public institutionnel",
    "OpenStreetMap",
    "CNCT",
    "Referentiel FDSU interne",
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
    "identite",
    "subdivision",
    "potentiel",
    "connectivite",
    "documents",
    "photos",
    "sources",
}

ALLOWED_STATUSES = {"proposé", "validé", "rejeté"}


ENRICHMENT_FIELDS = [
    ("identite", "Identite"),
    ("subdivision", "Subdivision"),
    ("activites_economiques_principales", "Activites economiques principales"),
    ("activites_economiques_secondaires", "Activites economiques secondaires"),
    ("particularites", "Particularites"),
    ("defis", "Defis"),
    ("potentiel", "Potentiel"),
    ("services_publics", "Services publics"),
    ("connectivite", "Connectivite"),
    ("documents", "Documents"),
    ("photos", "Photos"),
    ("sources", "Sources"),
]
FIELD_ALIASES = {
    "identite": ["presentation", "administration"],
    "subdivision": ["subdivision", "subdivision_administrative_reelle"],
    "potentiel": [
        "potentiel",
        "potentiel_agricole",
        "potentiel_minier",
        "potentiel_forestier",
        "potentiel_touristique",
        "potentiel_commercial",
        "potentiel_numerique",
    ],
    "connectivite": ["connectivite", "couverture_reseau"],
}
PRIORITY_RANK = {
    "entite strategique FDSU": 0,
    "localite prioritaire CCN": 1,
    "territoire a faible connectivite": 2,
    "entite sans activites economiques": 3,
    "entite sans defis": 4,
    "entite sans sources": 5,
}


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


def count_suggestions_by_status(session: Session) -> dict[str, int]:
    rows = session.query(TerritorialEnrichmentSuggestion.status).all()
    counts = {status: 0 for status in ALLOWED_STATUSES}
    for (status,) in rows:
        counts[status] = counts.get(status, 0) + 1
    return counts


def build_dashboard(session: Session) -> EnrichmentDashboard:
    items = build_completeness_items(session)
    counts = count_suggestions_by_status(session)
    suggestions = list_suggestions(session, limit=50)
    total = len(items)
    national_score = round(sum(item.score for item in items) / total) if total else 0
    return EnrichmentDashboard(
        national_score=national_score,
        total_entities=total,
        complete_entities=sum(1 for item in items if item.status == "complet"),
        partial_entities=sum(1 for item in items if item.status == "partiel"),
        insufficient_entities=sum(1 for item in items if item.status == "insuffisant"),
        pending_suggestions=counts.get("proposé", 0),
        validated_suggestions=counts.get("validé", 0),
        rejected_suggestions=counts.get("rejeté", 0),
        missing_value_label=MISSING_VALUE,
        automatic_collection_enabled=False,
        official_publication_enabled=False,
        map_layer={
            "available": any(item.geometry_available for item in items),
            "legend": {"complet": "vert", "partiel": "jaune", "insuffisant": "rouge"},
            "fallback": "tableau uniquement si la geometrie n'est pas disponible",
        },
        entities=items,
        suggestions=suggestions,
    )


def build_priority_items(session: Session) -> list[EnrichmentCompletenessItem]:
    items = build_completeness_items(session)
    return sorted(
        [item for item in items if item.priority_reasons],
        key=lambda item: (
            min(PRIORITY_RANK.get(reason, 99) for reason in item.priority_reasons),
            item.score,
            item.entity_name,
        ),
    )


def build_completeness_items(
    session: Session,
    *,
    zone: str | None = None,
    province: str | None = None,
    territoire: str | None = None,
    entity_type: str | None = None,
    completeness_level: str | None = None,
    missing_field: str | None = None,
    priority: str | None = None,
    source: str | None = None,
) -> list[EnrichmentCompletenessItem]:
    suggestions = list_suggestions(session, limit=500)
    suggestions_by_entity = _group_suggestions_by_entity(suggestions)
    items = [_build_profile_item(raw, suggestions_by_entity) for raw in DEMO_PROFILES.values()]
    return [
        item for item in items
        if _matches_filters(
            item,
            zone=zone,
            province=province,
            territoire=territoire,
            entity_type=entity_type,
            completeness_level=completeness_level,
            missing_field=missing_field,
            priority=priority,
            source=source,
        )
    ]


def _group_suggestions_by_entity(
    suggestions: list[TerritorialEnrichmentSuggestion],
) -> dict[tuple[str, str], list[TerritorialEnrichmentSuggestion]]:
    grouped: dict[tuple[str, str], list[TerritorialEnrichmentSuggestion]] = {}
    for suggestion in suggestions:
        entity_name = (suggestion.entity_name or str(suggestion.entity_id or "")).strip().lower()
        key = (suggestion.entity_type.strip().lower(), entity_name)
        grouped.setdefault(key, []).append(suggestion)
    return grouped


def _build_profile_item(
    raw: dict[str, Any],
    suggestions_by_entity: dict[tuple[str, str], list[TerritorialEnrichmentSuggestion]],
) -> EnrichmentCompletenessItem:
    entity_name = str(raw.get("title") or raw.get("entity") or MISSING_VALUE)
    entity_type = str(raw.get("entity_type") or "Entite territoriale")
    entity_key = str(raw.get("entity") or entity_name).lower()
    sections = raw.get("sections", {})
    entity_suggestions = suggestions_by_entity.get((entity_type.lower(), entity_name.lower()), [])
    fields = {}
    missing_fields = []
    for key, _label in ENRICHMENT_FIELDS:
        score = _field_score(key, sections, entity_suggestions)
        fields[key] = score
        if score == 0:
            missing_fields.append(key)
    score = round(sum(fields.values()) / len(fields)) if fields else 0
    return EnrichmentCompletenessItem(
        entity_key=entity_key,
        entity_type=entity_type,
        entity_id=None,
        entity_name=entity_name,
        zone=raw.get("zone"),
        province=_extract_province(raw),
        territoire=_extract_territoire(raw),
        score=score,
        status=_score_status(score),
        fields=fields,
        missing_fields=missing_fields,
        priority_reasons=_priority_reasons(entity_type, fields, sections, entity_suggestions),
        map_color=_score_color(score),
        geometry_available=False,
        sources=sorted({s.source_name for s in entity_suggestions if s.source_name}),
    )


def _field_score(
    field: str,
    sections: dict[str, Any],
    suggestions: list[TerritorialEnrichmentSuggestion],
) -> int:
    keys = FIELD_ALIASES.get(field, [field])
    if any(_has_value(sections.get(key)) for key in keys):
        return 100
    if any(s.status == "validé" and s.field_name in keys for s in suggestions):
        return 75
    if any(s.status == "proposé" and s.field_name in keys for s in suggestions):
        return 25
    return 0


def _has_value(value: Any) -> bool:
    if value is None or value == "" or value == MISSING_VALUE:
        return False
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _priority_reasons(
    entity_type: str,
    fields: dict[str, int],
    sections: dict[str, Any],
    suggestions: list[TerritorialEnrichmentSuggestion],
) -> list[str]:
    reasons = []
    if entity_type in {"Ville-Province", "Site FDSU"}:
        reasons.append("entite strategique FDSU")
    if entity_type in {"Localite", "Village"} and "CCN" in str(sections):
        reasons.append("localite prioritaire CCN")
    if fields.get("connectivite", 0) == 0:
        reasons.append("territoire a faible connectivite")
    if fields.get("activites_economiques_principales", 0) == 0:
        reasons.append("entite sans activites economiques")
    if fields.get("defis", 0) == 0:
        reasons.append("entite sans defis")
    if fields.get("sources", 0) == 0 and not any(s.source_name for s in suggestions):
        reasons.append("entite sans sources")
    return reasons


def _score_status(score: int) -> str:
    if score >= 80:
        return "complet"
    if score >= 40:
        return "partiel"
    return "insuffisant"


def _score_color(score: int) -> str:
    if score >= 80:
        return "vert"
    if score >= 40:
        return "jaune"
    return "rouge"


def _extract_province(raw: dict[str, Any]) -> str | None:
    entity_type = str(raw.get("entity_type") or "")
    if entity_type in {"Province", "Ville-Province"}:
        return raw.get("title")
    return raw.get("province")


def _extract_territoire(raw: dict[str, Any]) -> str | None:
    entity_type = str(raw.get("entity_type") or "")
    if entity_type == "Territoire":
        return raw.get("title")
    return raw.get("territoire")


def _matches_filters(
    item: EnrichmentCompletenessItem,
    *,
    zone: str | None,
    province: str | None,
    territoire: str | None,
    entity_type: str | None,
    completeness_level: str | None,
    missing_field: str | None,
    priority: str | None,
    source: str | None,
) -> bool:
    return all([
        _same_or_empty(item.zone, zone),
        _same_or_empty(item.province, province),
        _same_or_empty(item.territoire, territoire),
        _same_or_empty(item.entity_type, entity_type),
        _same_or_empty(item.status, completeness_level),
        not missing_field or missing_field in item.missing_fields,
        not priority or priority in item.priority_reasons,
        not source or source in item.sources,
    ])


def _same_or_empty(value: str | None, expected: str | None) -> bool:
    if not expected:
        return True
    return str(value or "").lower() == expected.lower()
