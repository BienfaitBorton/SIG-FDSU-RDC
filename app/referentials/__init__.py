"""Referentials module scaffolding for official sources integration."""

from .source_manager import OfficialSourceType, SourceDescriptor, SourceManager
from .validator import ReferentialValidator, ValidationIssue, ValidationReport
from .comparator import ReferentialComparator, ComparisonReport, ChangeRecord
from .publisher import PublicationWorkflow, PublicationStage
from .quality import QualityService, QualityIndicator, QualityReport

__all__ = [
    "OfficialSourceType",
    "SourceDescriptor",
    "SourceManager",
    "ReferentialValidator",
    "ValidationIssue",
    "ValidationReport",
    "ReferentialComparator",
    "ComparisonReport",
    "ChangeRecord",
    "PublicationWorkflow",
    "PublicationStage",
    "QualityService",
    "QualityIndicator",
    "QualityReport",
]
