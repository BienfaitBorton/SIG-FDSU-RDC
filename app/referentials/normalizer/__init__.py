"""Administrative referential normalization engine."""

from .normalizer import (
    DEFAULT_REFERENCE_COUNTS,
    NormalizationIssue,
    NormalizationIssueCode,
    NormalizationIssueLevel,
    NormalizationReport,
    NormalizationResult,
    ReferentialNormalizer,
    SourceKind,
    StagingEntity,
)
from .adapters import ExcelFDSUAdapter, HDXAdapter, KMZAdapter
from .entity_classifier import AdministrativeEntityType, EntityClassifier
from .hierarchy import HierarchyResolver
from .entity_matcher import EntityMatcher, MatchCandidate
from .entity_validator import EntityValidator
from .entity_merger import EntityMerger, MergeProposal
from .entity_statistics import EntityStatisticsService
from .integration import NormalizationModuleBridge, NormalizationModuleSnapshot, NormalizationRunRequest
from .report_generator import ReportGenerator
from .source_interfaces import BaseStagingAdapter, CaidStagingAdapter, CeniStagingAdapter, HdxStagingAdapter, InsStagingAdapter

__all__ = [
    "DEFAULT_REFERENCE_COUNTS",
    "NormalizationIssue",
    "NormalizationIssueCode",
    "NormalizationIssueLevel",
    "NormalizationReport",
    "NormalizationResult",
    "ReferentialNormalizer",
    "SourceKind",
    "StagingEntity",
    "ExcelFDSUAdapter",
    "HDXAdapter",
    "KMZAdapter",
    "AdministrativeEntityType",
    "EntityClassifier",
    "HierarchyResolver",
    "EntityMatcher",
    "MatchCandidate",
    "EntityValidator",
    "EntityMerger",
    "MergeProposal",
    "EntityStatisticsService",
    "NormalizationModuleBridge",
    "NormalizationModuleSnapshot",
    "NormalizationRunRequest",
    "ReportGenerator",
    "BaseStagingAdapter",
    "CaidStagingAdapter",
    "CeniStagingAdapter",
    "HdxStagingAdapter",
    "InsStagingAdapter",
]
