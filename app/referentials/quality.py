from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(slots=True)
class QualityIndicator:
    """Quality indicator values for one referential."""

    referential_name: str
    completeness: float | None = None
    consistency: float | None = None
    valid_geometries: float | None = None
    duplicates: float | None = None
    global_quality: float | None = None


@dataclass(slots=True)
class QualityReport:
    """Aggregated quality output."""

    indicators: list[QualityIndicator] = field(default_factory=list)


class QualityService:
    """Future quality engine facade (computation intentionally deferred)."""

    def evaluate(self, referentials: Iterable[str]) -> QualityReport:
        """Return a structural report without metric computation yet."""

        indicators = [QualityIndicator(referential_name=name) for name in referentials]
        return QualityReport(indicators=indicators)
