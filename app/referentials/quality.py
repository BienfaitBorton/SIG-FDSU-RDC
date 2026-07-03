from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


@dataclass(slots=True)
class QualityIndicator:
    """Quality indicator values for one referential."""

    referential_name: str
    completeness: float | None = None
    consistency: float | None = None
    valid_geometries: float | None = None
    duplicates: float | None = None
    global_quality: float | None = None
    entity_count: int | None = None
    orphan_count: int | None = None
    issue_count: int | None = None


@dataclass(slots=True)
class QualityReport:
    """Aggregated quality output."""

    indicators: list[QualityIndicator] = field(default_factory=list)
    global_quality: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "indicators": [
                {
                    "referential_name": indicator.referential_name,
                    "completeness": indicator.completeness,
                    "consistency": indicator.consistency,
                    "valid_geometries": indicator.valid_geometries,
                    "duplicates": indicator.duplicates,
                    "global_quality": indicator.global_quality,
                    "entity_count": indicator.entity_count,
                    "orphan_count": indicator.orphan_count,
                    "issue_count": indicator.issue_count,
                }
                for indicator in self.indicators
            ],
            "global_quality": self.global_quality,
        }


class QualityService:
    """Future quality engine facade (computation intentionally deferred)."""

    def evaluate(
        self,
        referentials: Iterable[str],
        metrics: dict[str, dict[str, Any]] | None = None,
    ) -> QualityReport:
        """Return a quality report, optionally enriched with computed metrics."""

        indicators: list[QualityIndicator] = []
        quality_values: list[float] = []

        for name in referentials:
            metric = metrics.get(name, {}) if metrics else {}
            indicator = QualityIndicator(
                referential_name=name,
                completeness=self._as_float(metric.get("completeness")),
                consistency=self._as_float(metric.get("consistency")),
                valid_geometries=self._as_float(metric.get("valid_geometries")),
                duplicates=self._as_float(metric.get("duplicates")),
                global_quality=self._as_float(metric.get("global_quality")),
                entity_count=self._as_int(metric.get("entity_count")),
                orphan_count=self._as_int(metric.get("orphan_count")),
                issue_count=self._as_int(metric.get("issue_count")),
            )
            if indicator.global_quality is not None:
                quality_values.append(indicator.global_quality)
            indicators.append(indicator)

        global_quality = round(sum(quality_values) / len(quality_values), 2) if quality_values else None
        return QualityReport(indicators=indicators, global_quality=global_quality)

    def _as_float(self, value: Any) -> float | None:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _as_int(self, value: Any) -> int | None:
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
