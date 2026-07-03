from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .canonical_schema import CanonicalLevel, SourceKey


@dataclass(slots=True)
class SourceDefinition:
    """Static source descriptor used by the canonical layer."""

    key: SourceKey
    display_name: str
    description: str
    supported_levels: tuple[CanonicalLevel, ...] = ()
    official: bool = True
    active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


class SourceRegistry:
    """Registry of known sources without loading/connecting any source."""

    def __init__(self) -> None:
        self._definitions: dict[SourceKey, SourceDefinition] = {}

    def register(self, definition: SourceDefinition) -> None:
        self._definitions[definition.key] = definition

    def get(self, key: SourceKey) -> SourceDefinition:
        if key not in self._definitions:
            raise KeyError(f"Unknown source key '{key.value}'.")
        return self._definitions[key]

    def has(self, key: SourceKey) -> bool:
        return key in self._definitions

    def list_definitions(self) -> list[SourceDefinition]:
        return list(self._definitions.values())


def build_default_source_registry() -> SourceRegistry:
    """Declare currently planned sources for canonicalization."""

    all_levels = (
        CanonicalLevel.PROVINCE,
        CanonicalLevel.VILLE,
        CanonicalLevel.TERRITOIRE,
        CanonicalLevel.COMMUNE,
        CanonicalLevel.SECTEUR,
        CanonicalLevel.CHEFFERIE,
        CanonicalLevel.GROUPEMENT,
        CanonicalLevel.QUARTIER,
        CanonicalLevel.VILLAGE,
    )

    registry = SourceRegistry()
    registry.register(
        SourceDefinition(
            key=SourceKey.HDX,
            display_name="HDX COD Administrative Boundaries",
            description="HDX/OCHA COD administrative boundaries reference.",
            supported_levels=all_levels,
            metadata={"connected": False, "mode": "registry_only"},
        )
    )
    registry.register(
        SourceDefinition(
            key=SourceKey.CENI,
            display_name="CENI RDC",
            description="Official CENI administrative and electoral nomenclature.",
            supported_levels=all_levels,
            metadata={"connected": False, "mode": "registry_only"},
        )
    )
    registry.register(
        SourceDefinition(
            key=SourceKey.CAID,
            display_name="CAID RDC",
            description="CAID official territorial delimitations and coding.",
            supported_levels=all_levels,
            metadata={"connected": False, "mode": "registry_only"},
        )
    )
    registry.register(
        SourceDefinition(
            key=SourceKey.KMZ,
            display_name="KMZ SIG Legacy",
            description="Legacy KMZ cartographic source for reconciliation workflows.",
            supported_levels=all_levels,
            official=False,
            metadata={"connected": False, "mode": "registry_only"},
        )
    )
    registry.register(
        SourceDefinition(
            key=SourceKey.EXCEL_FDSU,
            display_name="Excel FDSU",
            description="FDSU tabular operational source used for normalization.",
            supported_levels=all_levels,
            official=False,
            metadata={"connected": False, "mode": "registry_only"},
        )
    )
    return registry
