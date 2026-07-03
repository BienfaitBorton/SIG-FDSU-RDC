from __future__ import annotations

from typing import Any

from .canonical_entity import CanonicalAdministrativeEntity, CanonicalCodeSet, CanonicalSourceReference
from .canonical_schema import CanonicalStatus, SourceKey, parse_level
from .mapping_registry import MappingRegistry


class CanonicalMapper:
    """Converts source records into canonical administrative entities."""

    def __init__(self, mapping_registry: MappingRegistry) -> None:
        self.mapping_registry = mapping_registry

    def map_record(
        self,
        source: SourceKey,
        record: dict[str, Any],
        source_record_id: str,
    ) -> CanonicalAdministrativeEntity:
        profile = self.mapping_registry.get(source)
        payload = profile.to_canonical_payload(record)

        name = self._normalize_text(payload.get("name"))
        canonical_id = self._build_canonical_id(source, source_record_id, payload.get("code"))
        code = self._normalize_code(payload.get("code"))
        parent_code = self._normalize_code(payload.get("parent_code"))

        entity = CanonicalAdministrativeEntity(
            canonical_id=canonical_id,
            level=parse_level(payload.get("level")),
            name=name or "UNNAMED",
            normalized_name=name,
            status=CanonicalStatus.DRAFT,
            parent_id=parent_code,
            code_set=CanonicalCodeSet(canonical_code=code, national_code=code),
            attributes=self._extract_attributes(payload),
            metadata={
                "source_profile_version": profile.version,
                "source_profile_meta": profile.metadata,
            },
        )
        entity.code_set.add_external_code(source, code)
        entity.add_source_reference(
            CanonicalSourceReference(
                source=source,
                source_record_id=source_record_id,
                source_code=code,
                metadata={"parent_code": parent_code},
            )
        )
        return entity

    def _build_canonical_id(self, source: SourceKey, source_record_id: str, code: str | None) -> str:
        if code:
            return f"CAN::{source.value.upper()}::{self._normalize_code(code)}"
        return f"CAN::{source.value.upper()}::ROW::{source_record_id.strip()}"

    def _normalize_text(self, value: Any) -> str:
        if value is None:
            return ""
        text = str(value).strip().upper()
        return " ".join(text.split())

    def _normalize_code(self, value: Any) -> str | None:
        if value is None:
            return None
        code = "".join(str(value).strip().split()).upper()
        return code or None

    def _extract_attributes(self, payload: dict[str, Any]) -> dict[str, Any]:
        reserved = {"name", "level", "code", "parent_code"}
        return {key: value for key, value in payload.items() if key not in reserved}
