from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from itertools import combinations
from typing import Any

from .normalizer import StagingEntity


@dataclass(slots=True)
class MatchCandidate:
    left_entity_id: str
    right_entity_id: str
    confidence: float
    reasons: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)


class EntityMatcher:
    """Suggests likely same-object pairs without performing merges."""

    def find_matches(self, entities: list[StagingEntity]) -> list[MatchCandidate]:
        candidates: list[MatchCandidate] = []
        for left, right in combinations(entities, 2):
            candidate = self._score_pair(left, right)
            if candidate is not None:
                candidates.append(candidate)
        return sorted(candidates, key=lambda item: item.confidence, reverse=True)

    def _score_pair(self, left: StagingEntity, right: StagingEntity) -> MatchCandidate | None:
        if left.entity_type != right.entity_type:
            return None

        score = 0.0
        reasons: list[str] = []
        if left.normalized_code and right.normalized_code and left.normalized_code == right.normalized_code:
            score += 0.7
            reasons.append("same_code")

        if left.normalized_name and right.normalized_name:
            ratio = SequenceMatcher(a=left.normalized_name, b=right.normalized_name).ratio()
            if ratio >= 0.92:
                score += 0.25
                reasons.append("close_name")
            elif ratio >= 0.82:
                score += 0.15
                reasons.append("similar_name")

        if left.parent_code and right.parent_code and left.parent_code == right.parent_code:
            score += 0.05
            reasons.append("same_parent")

        if score < 0.6:
            return None

        return MatchCandidate(
            left_entity_id=left.source_id,
            right_entity_id=right.source_id,
            confidence=round(min(score, 0.99), 2),
            reasons=reasons,
            context={"entity_type": left.entity_type},
        )
