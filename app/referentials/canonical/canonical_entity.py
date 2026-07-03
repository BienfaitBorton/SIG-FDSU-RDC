from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .canonical_schema import CanonicalLevel, CanonicalStatus, SourceKey


@dataclass(slots=True)
class CanonicalCodeSet:
    """Holds canonical and source-specific identifiers for one entity."""

    canonical_code: str | None = None
    national_code: str | None = None
    external_codes: dict[str, str] = field(default_factory=dict)

    def add_external_code(self, source: SourceKey, code: str | None) -> None:
        if not code:
            return
        normalized = "".join(str(code).strip().split()).upper()
        if normalized:
            self.external_codes[source.value] = normalized


@dataclass(slots=True)
class CanonicalSourceReference:
    """Traceability record linking canonical entity to an upstream source row."""

    source: SourceKey
    source_record_id: str
    source_code: str | None = None
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CanonicalAdministrativeEntity:
    """Unique administrative unit representation for the RDC national referential."""

    canonical_id: str
    level: CanonicalLevel
    name: str
    normalized_name: str
    status: CanonicalStatus = CanonicalStatus.DRAFT
    parent_id: str | None = None
    country_code: str = "COD"
    aliases: list[str] = field(default_factory=list)
    code_set: CanonicalCodeSet = field(default_factory=CanonicalCodeSet)
    source_references: list[CanonicalSourceReference] = field(default_factory=list)
    geometry_type: str | None = None
    geometry: dict[str, Any] | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_source_reference(self, reference: CanonicalSourceReference) -> None:
        self.source_references.append(reference)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["level"] = self.level.value
        payload["status"] = self.status.value
        return payload
