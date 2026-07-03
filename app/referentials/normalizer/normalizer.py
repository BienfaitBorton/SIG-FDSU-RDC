from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Iterable


class SourceKind(str, Enum):
    EXCEL_FDSU = "excel_fdsu"
    KMZ = "kmz"
    GEOJSON = "geojson"
    SHAPEFILE = "shapefile"
    HDX = "hdx"
    CENI = "ceni"
    CAID = "caid"
    INS = "ins"
    UNKNOWN = "unknown"


class NormalizationIssueLevel(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class NormalizationIssueCode(str, Enum):
    DUPLICATE_NAME = "duplicate_name"
    DUPLICATE_CODE = "duplicate_code"
    MISSING_CODE = "missing_code"
    MISSING_PARENT = "missing_parent"
    INVALID_HIERARCHY = "invalid_hierarchy"
    INVALID_GEOMETRY = "invalid_geometry"
    INCONSISTENT_TYPE = "inconsistent_type"
    EMPTY_NAME = "empty_name"
    ORPHAN_ENTITY = "orphan_entity"
    REFERENCE_COUNT_GAP = "reference_count_gap"


DEFAULT_REFERENCE_COUNTS: dict[str, int] = {
    "province": 26,
    "ville": 33,
    "territoire": 145,
    "chefferie": 259,
    "secteur": 478,
    "commune_urbaine": 137,
    "commune_rurale": 202,
    "groupement": 6053,
    "groupement_incorpore": 87,
    "quartier": 2187,
    "village": 78855,
}


@dataclass(slots=True)
class StagingEntity:
    """Working copy entity used by the normalization engine."""

    source_id: str
    source_kind: SourceKind
    raw_name: str | None = None
    raw_code: str | None = None
    normalized_name: str = ""
    normalized_code: str | None = None
    entity_type: str | None = None
    parent_source_id: str | None = None
    parent_code: str | None = None
    zone_code: str | None = None
    province_name: str | None = None
    territoire_name: str | None = None
    geometry_type: str | None = None
    geometry: dict[str, Any] | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class NormalizationIssue:
    level: NormalizationIssueLevel
    code: NormalizationIssueCode
    message: str
    entity_id: str | None = None
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class NormalizationReport:
    source_name: str
    source_kind: SourceKind
    entity_count: int
    issues: list[NormalizationIssue] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    duplicates: list[dict[str, Any]] = field(default_factory=list)
    orphans: list[str] = field(default_factory=list)
    hierarchy: dict[str, int] = field(default_factory=dict)
    statistics: dict[str, Any] = field(default_factory=dict)
    quality: dict[str, Any] = field(default_factory=dict)
    merge_candidates: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["source_kind"] = self.source_kind.value
        return data


@dataclass(slots=True)
class NormalizationResult:
    entities: list[StagingEntity]
    report: NormalizationReport
    markdown_report: str


class ReferentialNormalizer:
    """Coordinates normalization on staging data without touching the database."""

    def __init__(
        self,
        classifier: Any,
        hierarchy_resolver: Any,
        validator: Any,
        matcher: Any,
        merger: Any,
        statistics_service: Any,
        report_generator: Any,
    ) -> None:
        self.classifier = classifier
        self.hierarchy_resolver = hierarchy_resolver
        self.validator = validator
        self.matcher = matcher
        self.merger = merger
        self.statistics_service = statistics_service
        self.report_generator = report_generator

    def normalize(
        self,
        source_name: str,
        source_kind: SourceKind,
        entities: Iterable[StagingEntity],
        reference_counts: dict[str, int] | None = None,
    ) -> NormalizationResult:
        working_entities = [self._prepare_entity(entity) for entity in entities]

        for entity in working_entities:
            entity.entity_type = self.classifier.classify(entity).value

        self.hierarchy_resolver.build_hierarchy(working_entities)
        issues = self.validator.validate(working_entities, reference_counts or DEFAULT_REFERENCE_COUNTS)
        match_candidates = self.matcher.find_matches(working_entities)
        merge_proposals = self.merger.build_proposals(match_candidates, working_entities)
        statistics = self.statistics_service.compute(working_entities, issues)

        report = NormalizationReport(
            source_name=source_name,
            source_kind=source_kind,
            entity_count=len(working_entities),
            issues=issues,
            duplicates=[proposal.to_dict() for proposal in merge_proposals],
            orphans=[issue.entity_id for issue in issues if issue.code == NormalizationIssueCode.ORPHAN_ENTITY and issue.entity_id],
            hierarchy=statistics.get("by_level", {}),
            statistics=statistics,
            quality=statistics.get("quality", {}),
            merge_candidates=[proposal.to_dict() for proposal in merge_proposals],
        )
        markdown_report = self.report_generator.to_markdown(report)
        return NormalizationResult(entities=working_entities, report=report, markdown_report=markdown_report)

    def _prepare_entity(self, entity: StagingEntity) -> StagingEntity:
        entity.normalized_name = self._normalize_text(entity.raw_name)
        entity.normalized_code = self._normalize_code(entity.raw_code)
        entity.geometry_type = self._normalize_geometry_type(entity.geometry_type, entity.geometry)
        return entity

    def _normalize_text(self, value: str | None) -> str:
        if not value:
            return ""
        normalized = value.strip().upper()
        replacements = {
            "’": "'",
            "`": "'",
            "´": "'",
            "-": " ",
            "_": " ",
        }
        accent_replacements = str.maketrans(
            {
                "À": "A",
                "Â": "A",
                "Ä": "A",
                "É": "E",
                "È": "E",
                "Ê": "E",
                "Ë": "E",
                "Î": "I",
                "Ï": "I",
                "Ô": "O",
                "Ö": "O",
                "Ù": "U",
                "Û": "U",
                "Ü": "U",
                "Ç": "C",
            }
        )
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        normalized = normalized.translate(accent_replacements)
        normalized = " ".join(normalized.split())
        return normalized

    def _normalize_code(self, value: str | None) -> str | None:
        if not value:
            return None
        normalized = "".join(str(value).strip().split())
        return normalized.upper() or None

    def _normalize_geometry_type(self, geometry_type: str | None, geometry: dict[str, Any] | None) -> str | None:
        if geometry_type:
            return geometry_type
        if geometry and geometry.get("type"):
            return str(geometry["type"])
        return None
