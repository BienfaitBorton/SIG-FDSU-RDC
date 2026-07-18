"""Contrat d'adaptation de sources pour NIRE Phase 1."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable

from api.services.national_semantic_classification_engine import normalize_name

from .models import EntityReference, NationalEvidence


class SourceAdapter(ABC):
    @abstractmethod
    def get_source_name(self) -> str: ...

    @abstractmethod
    def get_entity_type(self) -> str: ...

    @abstractmethod
    def get_entities(self) -> Iterable[dict[str, Any]]: ...

    @abstractmethod
    def get_entity_by_id(self, entity_id: str) -> dict[str, Any] | None: ...

    @abstractmethod
    def normalize_entity(self, entity: dict[str, Any]) -> EntityReference: ...

    @abstractmethod
    def extract_identity_features(self, entity: dict[str, Any]) -> dict[str, Any]: ...

    def extract_evidence(self, source: EntityReference, target: EntityReference) -> tuple[NationalEvidence, ...]:
        return ()


class InMemorySourceAdapter(SourceAdapter):
    """Adaptateur fictif et déterministe réservé aux tests et démonstrations."""

    def __init__(self, source_name: str, entity_type: str, entities: Iterable[dict[str, Any]]) -> None:
        self._source_name = source_name
        self._entity_type = entity_type
        self._entities = {str(row["id"]): dict(row) for row in entities}

    def get_source_name(self) -> str:
        return self._source_name

    def get_entity_type(self) -> str:
        return self._entity_type

    def get_entities(self) -> Iterable[dict[str, Any]]:
        return tuple(dict(row) for row in self._entities.values())

    def get_entity_by_id(self, entity_id: str) -> dict[str, Any] | None:
        row = self._entities.get(str(entity_id))
        return dict(row) if row else None

    def normalize_entity(self, entity: dict[str, Any]) -> EntityReference:
        features = self.extract_identity_features(entity)
        return EntityReference(entity_id=str(entity["id"]), source_name=self._source_name, entity_type=str(entity.get("entity_type") or self._entity_type), attributes=features)

    def extract_identity_features(self, entity: dict[str, Any]) -> dict[str, Any]:
        features = dict(entity)
        features["name"] = str(entity.get("name") or "").strip()
        features["normalized_name"] = normalize_name(features["name"])
        for key in ("province", "territory", "locality", "operator", "institutional_id"):
            if entity.get(key) is not None:
                features[key] = normalize_name(str(entity[key]))
        return features
