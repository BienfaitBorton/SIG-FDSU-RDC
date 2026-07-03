from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .normalizer import NormalizationResult, ReferentialNormalizer, SourceKind
from .source_interfaces import BaseStagingAdapter


@dataclass(slots=True)
class NormalizationRunRequest:
    source_name: str
    source_kind: SourceKind
    source_path: Path


@dataclass(slots=True)
class NormalizationModuleSnapshot:
    source_name: str
    entity_count: int
    quality_score: float | None
    error_count: int
    duplicate_count: int
    orphan_count: int
    by_level: dict[str, int]
    markdown_report: str

    def to_dict(self) -> dict[str, object]:
        return {
            "source_name": self.source_name,
            "entity_count": self.entity_count,
            "quality_score": self.quality_score,
            "error_count": self.error_count,
            "duplicate_count": self.duplicate_count,
            "orphan_count": self.orphan_count,
            "by_level": dict(self.by_level),
            "markdown_report": self.markdown_report,
        }


class NormalizationModuleBridge:
    """Bridges source adapters and the normalization engine for referential governance."""

    def __init__(self, normalizer: ReferentialNormalizer, adapters: dict[SourceKind, BaseStagingAdapter]) -> None:
        self.normalizer = normalizer
        self.adapters = dict(adapters)

    def available_sources(self) -> list[str]:
        return [source_kind.value for source_kind in self.adapters]

    def run(self, request: NormalizationRunRequest) -> NormalizationResult:
        adapter = self.adapters.get(request.source_kind)
        if adapter is None:
            raise KeyError(f"No staging adapter registered for {request.source_kind.value}")
        entities = adapter.load(request.source_path)
        return self.normalizer.normalize(request.source_name, request.source_kind, entities)

    def build_snapshot(self, result: NormalizationResult) -> NormalizationModuleSnapshot:
        quality = result.report.quality or {}
        return NormalizationModuleSnapshot(
            source_name=result.report.source_name,
            entity_count=result.report.entity_count,
            quality_score=quality.get("quality_score"),
            error_count=quality.get("error_count", 0),
            duplicate_count=len(result.report.duplicates),
            orphan_count=len(result.report.orphans),
            by_level=result.report.statistics.get("by_level", {}),
            markdown_report=result.markdown_report,
        )