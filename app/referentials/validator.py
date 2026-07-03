from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable


class ValidationLevel(str, Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(slots=True)
class ValidationIssue:
    """Single validation issue placeholder."""

    level: ValidationLevel
    message: str
    field: str | None = None


@dataclass(slots=True)
class ValidationReport:
    """Validation result for a referential payload."""

    source_name: str
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return all(issue.level != ValidationLevel.ERROR for issue in self.issues)


class ReferentialValidator:
    """Future validation engine entrypoint (schema/content/consistency)."""

    def validate(self, source_name: str, records: Iterable[dict[str, Any]]) -> ValidationReport:
        """Validate records with future business rules.

        This method currently returns an empty report by design.
        """

        _ = records
        return ValidationReport(source_name=source_name)
