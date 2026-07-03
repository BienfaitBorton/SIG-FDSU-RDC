"""Referentials module scaffolding for official sources integration."""

from .source_manager import OfficialSourceType, SourceDescriptor, SourceManager
from .validator import ReferentialValidator, ValidationIssue, ValidationReport
from .comparator import ReferentialComparator, ComparisonReport, ChangeRecord
from .publisher import PublicationWorkflow, PublicationStage
from .quality import QualityService, QualityIndicator, QualityReport
from .source_explorer import SourceExplorerService, SourceAnalyzer, SourceReader, SourceReportWriter
from .province_official import ProvinceOfficialReferentialService, ProvinceKMZReader, ProvinceSourceReadError
from .territory_hierarchy import TerritoryHierarchyService, TerritoryHierarchyReportWriter
from .city_official import CityOfficialReferentialService, CityReportWriter

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
    "SourceExplorerService",
    "SourceAnalyzer",
    "SourceReader",
    "SourceReportWriter",
    "ProvinceOfficialReferentialService",
    "ProvinceKMZReader",
    "ProvinceSourceReadError",
    "TerritoryHierarchyService",
    "TerritoryHierarchyReportWriter",
    "CityOfficialReferentialService",
    "CityReportWriter",
]
