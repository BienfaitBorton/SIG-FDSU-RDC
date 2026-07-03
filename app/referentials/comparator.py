from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable


class ChangeType(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    GEOMETRY_MODIFIED = "geometry_modified"
    ATTRIBUTES_MODIFIED = "attributes_modified"


@dataclass(slots=True)
class ChangeRecord:
    """Represents one diff event between two referential versions."""

    object_id: str
    change_type: ChangeType
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ComparisonReport:
    """Comparison output placeholder for future UI/API integration."""

    source_name: str
    left_version: str
    right_version: str
    changes: list[ChangeRecord] = field(default_factory=list)


class ReferentialComparator:
    """Compares two referential versions (architecture only)."""

    def compare(
        self,
        source_name: str,
        left_version: str,
        right_version: str,
        left_records: Iterable[dict[str, Any]],
        right_records: Iterable[dict[str, Any]],
    ) -> ComparisonReport:
        """Return a report scaffold; diff algorithm is intentionally deferred."""

        _ = left_records
        _ = right_records
        return ComparisonReport(
            source_name=source_name,
            left_version=left_version,
            right_version=right_version,
        )
