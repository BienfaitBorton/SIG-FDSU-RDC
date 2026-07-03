from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class CityCanonicalEntity:
    canonical_id: str
    nom: str
    niveau: str
    province: str
    zone_fdsu: str
    geometry: dict[str, Any] | None
    source: str
    statut: str
    qualite: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_id": self.canonical_id,
            "nom": self.nom,
            "niveau": self.niveau,
            "province": self.province,
            "zone_fdsu": self.zone_fdsu,
            "geometry": self.geometry,
            "source": self.source,
            "statut": self.statut,
            "qualite": self.qualite,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class CityFactSheet:
    canonical_id: str
    nom: str
    province: str
    zone_fdsu: str
    geometry_type: str | None
    source: str
    quality_flags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_id": self.canonical_id,
            "nom": self.nom,
            "province": self.province,
            "zone_fdsu": self.zone_fdsu,
            "geometry_type": self.geometry_type,
            "source": self.source,
            "quality_flags": list(self.quality_flags),
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class CityQualityReport:
    source_file: str
    generated_at: datetime
    city_count: int
    orphan_city_count: int
    multi_province_conflicts: int
    multi_zone_conflicts: int
    empty_geometry_count: int
    duplicate_count: int
    global_score: float
    duplicate_names: list[str] = field(default_factory=list)
    anomalies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "generated_at": self.generated_at.isoformat(timespec="seconds"),
            "city_count": self.city_count,
            "orphan_city_count": self.orphan_city_count,
            "multi_province_conflicts": self.multi_province_conflicts,
            "multi_zone_conflicts": self.multi_zone_conflicts,
            "empty_geometry_count": self.empty_geometry_count,
            "duplicate_count": self.duplicate_count,
            "duplicate_names": list(self.duplicate_names),
            "anomalies": list(self.anomalies),
            "global_score": self.global_score,
        }


@dataclass(slots=True)
class CityReferentialReport:
    source_file: str
    generated_at: datetime
    city_referential: list[CityCanonicalEntity]
    city_fact_sheets: list[CityFactSheet]
    quality: CityQualityReport

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "generated_at": self.generated_at.isoformat(timespec="seconds"),
            "city_referential": [item.to_dict() for item in self.city_referential],
            "city_fact_sheets": [item.to_dict() for item in self.city_fact_sheets],
            "quality": self.quality.to_dict(),
        }


@dataclass(slots=True)
class CityOfficialRunResult:
    source_path: Path
    report: CityReferentialReport
    referential_json_path: Path
    fact_sheets_json_path: Path
    quality_json_path: Path
    report_markdown_path: Path
    files_report_path: Path
