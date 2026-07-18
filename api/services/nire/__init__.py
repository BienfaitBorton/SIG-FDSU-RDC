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
from .candidate_generation import CandidateGenerationEngine, CandidateGenerationMetrics, CandidateIndex, CandidateProposal, MemoryCandidateIndex
from .source_adapters import AdministrativeSourceAdapter, CeniSourceAdapter, EducationSourceAdapter, FdsuSiteSourceAdapter, HealthSourceAdapter, TelecomSourceAdapter
from .evidence_extractors import AdministrativeEvidenceExtractor, EntityTypeEvidenceExtractor, GeographicEvidenceExtractor, InstitutionalEvidenceExtractor, LexicalEvidenceExtractor, OperatorEvidenceExtractor, SourceQualityEvidenceExtractor, extract_all
from .calibration import CalibrationMetrics, calculate_calibration, synthetic_ground_truth_cases

__all__ = [
    "AmbiguityLevel", "CandidateStatus", "DecisionType", "EntityReference",
    "EvidenceFusionEngine", "EvidenceStatus", "IdentityResolutionEngine",
    "InMemorySourceAdapter", "NationalEvidence", "NationalRuleRegistry",
    "ResolutionCandidate", "ResolutionDecision", "ResolutionRun", "SourceAdapter",
    "default_rule_registry",
    "AdministrativeSourceAdapter", "CeniSourceAdapter", "EducationSourceAdapter", "FdsuSiteSourceAdapter", "HealthSourceAdapter", "TelecomSourceAdapter",
    "CandidateGenerationEngine", "CandidateGenerationMetrics", "CandidateIndex", "CandidateProposal", "MemoryCandidateIndex",
    "AdministrativeEvidenceExtractor", "EntityTypeEvidenceExtractor", "GeographicEvidenceExtractor", "InstitutionalEvidenceExtractor", "LexicalEvidenceExtractor", "OperatorEvidenceExtractor", "SourceQualityEvidenceExtractor", "extract_all",
    "CalibrationMetrics", "calculate_calibration", "synthetic_ground_truth_cases",
]
