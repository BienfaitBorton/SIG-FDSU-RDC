from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from api.schemas.base import TerritorialEnrichmentSuggestionRead


class EnrichmentCompletenessItem(BaseModel):
    entity_key: str
    entity_type: str
    entity_id: int | None = None
    entity_name: str
    zone: str | None = None
    province: str | None = None
    territoire: str | None = None
    score: int = Field(0, ge=0, le=100)
    status: str
    fields: dict[str, int]
    missing_fields: list[str]
    priority_reasons: list[str] = Field(default_factory=list)
    map_color: str
    geometry_available: bool = False
    sources: list[str] = Field(default_factory=list)


class EnrichmentDashboard(BaseModel):
    national_score: int = Field(0, ge=0, le=100)
    total_entities: int
    complete_entities: int
    partial_entities: int
    insufficient_entities: int
    pending_suggestions: int
    validated_suggestions: int
    rejected_suggestions: int
    missing_value_label: str
    automatic_collection_enabled: bool
    official_publication_enabled: bool
    map_layer: dict[str, Any]
    entities: list[EnrichmentCompletenessItem]
    suggestions: list[TerritorialEnrichmentSuggestionRead]


class EnrichmentPriorities(BaseModel):
    items: list[EnrichmentCompletenessItem]


class EnrichmentSuggestionDecision(BaseModel):
    proposed_value: str | None = None
    review_note: str | None = None
    validated_by: str | None = "Administrateur"


class EnrichmentTraceabilityCheck(BaseModel):
    suggestion_id: int
    status: str
    traceable: bool
    published_to_official_referential: bool = False
    checked_at: datetime
