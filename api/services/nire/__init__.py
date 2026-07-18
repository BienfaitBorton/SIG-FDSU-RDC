"""NIRE Phase 1 — noyau de résolution d'identité, sans persistance ni fusion."""

from .adapters import InMemorySourceAdapter, SourceAdapter
from .engine import EvidenceFusionEngine, IdentityResolutionEngine
from .models import (
    AmbiguityLevel,
    CandidateStatus,
    DecisionType,
    EntityReference,
    EvidenceStatus,
    NationalEvidence,
    ResolutionCandidate,
    ResolutionDecision,
    ResolutionRun,
)
from .rules import NationalRuleRegistry, default_rule_registry

__all__ = [
    "AmbiguityLevel", "CandidateStatus", "DecisionType", "EntityReference",
    "EvidenceFusionEngine", "EvidenceStatus", "IdentityResolutionEngine",
    "InMemorySourceAdapter", "NationalEvidence", "NationalRuleRegistry",
    "ResolutionCandidate", "ResolutionDecision", "ResolutionRun", "SourceAdapter",
    "default_rule_registry",
]
