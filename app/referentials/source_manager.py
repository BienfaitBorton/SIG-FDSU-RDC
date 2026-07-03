from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Iterable


class OfficialSourceType(str, Enum):
    """Official providers and geometry source used by SIG-FDSU."""

    CENI = "ceni"
    CAID = "caid"
    INS = "ins"
    FDSU = "fdsu"
    KMZ = "kmz"


SOURCE_ROLES: Dict[OfficialSourceType, str] = {
    OfficialSourceType.CENI: "administrative referential",
    OfficialSourceType.CAID: "statistical indicators",
    OfficialSourceType.INS: "official nomenclatures",
    OfficialSourceType.KMZ: "geometry",
    OfficialSourceType.FDSU: "business data",
}


@dataclass(slots=True)
class SourceDescriptor:
    """Describes a source location and metadata for future synchronization."""

    source: OfficialSourceType
    root_path: Path
    role: str


class SourceManager:
    """Central registry for official referential sources (architecture only)."""

    def __init__(self, sources_root: Path | str = Path("data/sources")) -> None:
        self.sources_root = Path(sources_root)
        self._registry: Dict[OfficialSourceType, SourceDescriptor] = {}

    def register_default_sources(self) -> None:
        """Register the expected official sources in memory."""

        for source_type, role in SOURCE_ROLES.items():
            if source_type == OfficialSourceType.KMZ:
                # KMZ is a format/source role for geometry and can be resolved later.
                continue
            self._registry[source_type] = SourceDescriptor(
                source=source_type,
                root_path=self.sources_root / source_type.value,
                role=role,
            )

    def list_sources(self) -> Iterable[SourceDescriptor]:
        """Return registered sources for orchestration layers."""

        return self._registry.values()

    def get_source(self, source_type: OfficialSourceType) -> SourceDescriptor:
        """Return a source descriptor or raise when not registered."""

        if source_type not in self._registry:
            raise KeyError(f"Source not registered: {source_type.value}")
        return self._registry[source_type]
