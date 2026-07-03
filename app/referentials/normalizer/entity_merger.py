from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .entity_matcher import MatchCandidate
from .normalizer import StagingEntity


@dataclass(slots=True)
class MergeProposal:
    left_entity_id: str
    right_entity_id: str
    confidence: float
    reasons: list[str] = field(default_factory=list)
    auto_merge: bool = False
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "left_entity_id": self.left_entity_id,
            "right_entity_id": self.right_entity_id,
            "confidence": self.confidence,
            "reasons": list(self.reasons),
            "auto_merge": self.auto_merge,
            "context": dict(self.context),
        }


class EntityMerger:
    """Builds merge proposals but never merges automatically."""

    def build_proposals(
        self,
        candidates: list[MatchCandidate],
        entities: list[StagingEntity],
    ) -> list[MergeProposal]:
        _ = entities
        return [
            MergeProposal(
                left_entity_id=candidate.left_entity_id,
                right_entity_id=candidate.right_entity_id,
                confidence=candidate.confidence,
                reasons=candidate.reasons,
                auto_merge=False,
                context=candidate.context,
            )
            for candidate in candidates
        ]
