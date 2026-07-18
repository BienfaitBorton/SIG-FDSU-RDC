"""Modèles métier immuables de NIRE Phase 1."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class EvidenceStatus(StrEnum):
    SUPPORTING = "SUPPORTING"
    CONFLICTING = "CONFLICTING"
    NEUTRAL = "NEUTRAL"


class CandidateStatus(StrEnum):
    PENDING = "PENDING"
    PROBABLE_MATCH = "PROBABLE_MATCH"
    STRONG_MATCH = "STRONG_MATCH"
    AMBIGUOUS = "AMBIGUOUS"
    CONFLICT = "CONFLICT"
    REJECTED = "REJECTED"
    VALIDATED_MATCH = "VALIDATED_MATCH"


class DecisionType(StrEnum):
    MATCH_RECOMMENDED = "MATCH_RECOMMENDED"
    POSSIBLE_MATCH = "POSSIBLE_MATCH"
    AMBIGUOUS = "AMBIGUOUS"
    NO_MATCH = "NO_MATCH"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class AmbiguityLevel(StrEnum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True, slots=True)
class EntityReference:
    entity_id: str
    source_name: str
    entity_type: str
    attributes: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class NationalEvidence:
    evidence_id: str
    evidence_type: str
    source_name: str
    source_entity_id: str
    target_entity_id: str
    value: Any
    normalized_value: Any
    weight: float
    confidence: float
    reliability: float
    status: EvidenceStatus
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now)

    @property
    def contribution(self) -> float:
        return round(self.weight * self.confidence * self.reliability, 4)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload


@dataclass(frozen=True, slots=True)
class ResolutionCandidate:
    candidate_id: str
    source_entity: EntityReference
    target_entity: EntityReference
    evidences: tuple[NationalEvidence, ...]
    positive_evidence_score: float
    negative_evidence_score: float
    resolution_score: float
    confidence: float
    status: CandidateStatus
    ambiguity_level: AmbiguityLevel
    explanation: str

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        payload["ambiguity_level"] = self.ambiguity_level.value
        return payload


@dataclass(frozen=True, slots=True)
class ResolutionDecision:
    decision_id: str
    candidate_id: str
    decision: DecisionType
    score: float
    confidence: float
    evidences_used: tuple[str, ...]
    positive_evidences: tuple[str, ...]
    negative_evidences: tuple[str, ...]
    blocking_rules: tuple[str, ...]
    warnings: tuple[str, ...]
    explanation: str
    requires_human_review: bool
    engine_version: str

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["decision"] = self.decision.value
        return payload


@dataclass(slots=True)
class ResolutionRun:
    run_id: str
    started_at: str
    completed_at: str | None
    source_type: str
    target_type: str
    source_count: int
    candidate_count: int
    resolved_count: int
    ambiguous_count: int
    conflict_count: int
    insufficient_count: int
    engine_version: str
    rule_registry_version: str

    def complete(self) -> None:
        self.completed_at = utc_now()

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
