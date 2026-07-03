from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class TerritoryRecord:
    nom: str
    province: str
    zone_fdsu: str
    chemin_hierarchique: list[str]
    geometry: dict[str, Any] | None
    attributs: dict[str, Any] = field(default_factory=dict)
    score_qualite: float = 0.0
    incoherences: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "nom": self.nom,
            "province": self.province,
            "zone_fdsu": self.zone_fdsu,
            "chemin_hierarchique": list(self.chemin_hierarchique),
            "geometry": self.geometry,
            "attributs": dict(self.attributs),
            "score_qualite": self.score_qualite,
            "incoherences": list(self.incoherences),
        }


@dataclass(slots=True)
class TerritoryHierarchyReport:
    source_file: str
    generated_at: datetime
    territory_count: int
    incoherence_count: int
    territories: list[TerritoryRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "generated_at": self.generated_at.isoformat(timespec="seconds"),
            "territory_count": self.territory_count,
            "incoherence_count": self.incoherence_count,
            "territories": [item.to_dict() for item in self.territories],
        }


@dataclass(slots=True)
class TerritoryHierarchyRunResult:
    source_path: Path
    report_json_path: Path
    report_markdown_path: Path
    report: TerritoryHierarchyReport
