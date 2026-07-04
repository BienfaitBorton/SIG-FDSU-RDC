from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class KnowledgeSource(BaseModel):
    source: str
    author: str | None = None
    date: str | None = None
    url: str | None = None
    confidence_level: str = "à vérifier"
    status: str = "proposé"


class KnowledgeSection(BaseModel):
    key: str
    label: str
    value: str | list[str] | dict[str, Any] = "Donnée non encore renseignée"
    completeness: int = Field(0, ge=0, le=100)
    sources: list[KnowledgeSource] = Field(default_factory=list)


class KnowledgeProfile(BaseModel):
    entity: str
    entity_type: str
    title: str
    updated_at: datetime
    workflow: list[str]
    sections: list[KnowledgeSection]
    completeness: dict[str, int]
    intelligence_links: list[str]


class KnowledgeSummary(BaseModel):
    complete_profiles: int
    incomplete_profiles: int
    profiles_without_photo: int
    profiles_without_activities: int
    profiles_without_challenges: int
    profiles_without_public_services: int
    profiles_without_connectivity: int
    profiles_without_documents: int
    workflow: list[str]


class KnowledgePriority(BaseModel):
    province: str
    territoire: str
    completeness: int
    missing_fields_count: int
    priority: str
    last_updated_at: str


class KnowledgeSearchResult(BaseModel):
    entity: str
    entity_type: str
    matched_fields: list[str]
    excerpt: str
    completeness: int


class KnowledgeSuggestionsResponse(BaseModel):
    workflow: list[str]
    automatic_collection_enabled: bool
    suggestions_ready: bool
    items: list[dict[str, Any]]
