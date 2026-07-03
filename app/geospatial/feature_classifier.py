from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import re


@dataclass(slots=True)
class FeatureClassification:
    entity_type: str
    confidence: float
    matched_terms: list[str]


class FeatureClassifier:
    """Déduit le type d'entité géographique à partir des métadonnées."""

    RULES: dict[str, tuple[str, ...]] = {
        "Province": ("province",),
        "Territoire": ("territoire",),
        "Secteur": ("secteur",),
        "Chefferie": ("chefferie",),
        "Collectivite": ("collectivite", "collectivité"),
        "Groupement": ("groupement",),
        "Village": ("village",),
        "Site": ("site", "fdsu site", "station", "antenne"),
        "Ville": ("ville",),
        "Commune": ("commune",),
    }

    def classify(self, properties: dict[str, Any], description_values: dict[str, str] | None = None) -> FeatureClassification:
        haystack = self._build_haystack(properties, description_values)
        for entity_type, keywords in self.RULES.items():
            matched_terms = [keyword for keyword in keywords if keyword in haystack]
            if matched_terms:
                confidence = min(1.0, 0.4 + (0.15 * len(matched_terms)))
                return FeatureClassification(entity_type=entity_type, confidence=confidence, matched_terms=matched_terms)
        return FeatureClassification(entity_type="Inconnu", confidence=0.0, matched_terms=[])

    def _build_haystack(self, properties: dict[str, Any], description_values: dict[str, str] | None) -> str:
        pieces: list[str] = []
        for value in properties.values():
            if value is not None:
                pieces.append(str(value))
        if description_values:
            pieces.extend(description_values.keys())
            pieces.extend(description_values.values())
        normalized = " ".join(pieces).lower()
        normalized = normalized.replace("é", "e").replace("è", "e").replace("à", "a")
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized
