from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ProvinceSourceRecord:
    name: str
    folder: str
    description: str
    description_values: dict[str, str]
    extended_data: dict[str, str]
    geometry_type: str | None
    geometry: dict[str, Any] | None
    style_url: str | None
    style_inline: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ZoneDefinition:
    code: str
    name: str
    color: str
    provinces: list[str]


@dataclass(slots=True)
class ZonesFDSUConfig:
    country_code: str
    country_name: str
    zones: list[ZoneDefinition]


@dataclass(slots=True)
class ProvinceCanonicalEntity:
    canonical_id: str
    nom: str
    code_officiel: str | None
    niveau: str
    chef_lieu: str | None
    zone_fdsu: str
    source: str
    statut: str
    qualite: float
    geometry: dict[str, Any] | None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_id": self.canonical_id,
            "nom": self.nom,
            "code_officiel": self.code_officiel,
            "niveau": self.niveau,
            "chef_lieu": self.chef_lieu,
            "zone_fdsu": self.zone_fdsu,
            "source": self.source,
            "statut": self.statut,
            "qualite": self.qualite,
            "geometry": self.geometry,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class ProvinceFactSheet:
    canonical_id: str
    nom: str
    zone_fdsu: str
    zone_nom: str
    code_officiel: str | None
    chef_lieu: str | None
    geometry_type: str | None
    source: str
    quality_flags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_id": self.canonical_id,
            "nom": self.nom,
            "zone_fdsu": self.zone_fdsu,
            "zone_nom": self.zone_nom,
            "code_officiel": self.code_officiel,
            "chef_lieu": self.chef_lieu,
            "geometry_type": self.geometry_type,
            "source": self.source,
            "quality_flags": list(self.quality_flags),
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class ProvinceQualityReport:
    source_file: str
    generated_at: datetime
    province_count: int
    provinces_without_geometry: int
    provinces_without_capital: int
    provinces_without_code: int
    duplicates: int
    global_score: float
    duplicate_names: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "generated_at": self.generated_at.isoformat(timespec="seconds"),
            "province_count": self.province_count,
            "provinces_without_geometry": self.provinces_without_geometry,
            "provinces_without_capital": self.provinces_without_capital,
            "provinces_without_code": self.provinces_without_code,
            "duplicates": self.duplicates,
            "duplicate_names": list(self.duplicate_names),
            "global_score": self.global_score,
        }


@dataclass(slots=True)
class ProvinceReferentialReport:
    country: dict[str, str]
    source_file: str
    generated_at: datetime
    province_referential: list[ProvinceCanonicalEntity]
    province_fact_sheets: list[ProvinceFactSheet]
    quality: ProvinceQualityReport

    def to_dict(self) -> dict[str, Any]:
        return {
            "country": dict(self.country),
            "source_file": self.source_file,
            "generated_at": self.generated_at.isoformat(timespec="seconds"),
            "province_referential": [item.to_dict() for item in self.province_referential],
            "province_fact_sheets": [item.to_dict() for item in self.province_fact_sheets],
            "quality": self.quality.to_dict(),
        }


@dataclass(slots=True)
class ProvinceOfficialRunResult:
    source_path: Path
    report: ProvinceReferentialReport
    referential_json_path: Path
    quality_json_path: Path
    fact_sheets_json_path: Path
    report_markdown_path: Path
    files_report_path: Path
