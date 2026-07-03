from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class CollectivityCanonicalEntity:
    canonical_id: str
    nom: str
    niveau: str
    type_collectivite: str
    province: str
    territoire: str
    zone_fdsu: str
    geometry: dict[str, Any] | None
    code_officiel: str | None
    source: str
    statut: str
    qualite: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_id": self.canonical_id,
            "nom": self.nom,
            "niveau": self.niveau,
            "type_collectivite": self.type_collectivite,
            "province": self.province,
            "territoire": self.territoire,
            "zone_fdsu": self.zone_fdsu,
            "geometry": self.geometry,
            "code_officiel": self.code_officiel,
            "source": self.source,
            "statut": self.statut,
            "qualite": self.qualite,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class CollectivityFactSheet:
    canonical_id: str
    nom: str
    type_collectivite: str
    province: str
    territoire: str
    zone_fdsu: str
    code_officiel: str | None
    geometry_type: str | None
    source: str
    quality_flags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_id": self.canonical_id,
            "nom": self.nom,
            "type_collectivite": self.type_collectivite,
            "province": self.province,
            "territoire": self.territoire,
            "zone_fdsu": self.zone_fdsu,
            "code_officiel": self.code_officiel,
            "geometry_type": self.geometry_type,
            "source": self.source,
            "quality_flags": list(self.quality_flags),
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class CollectivityAnomaly:
    entite: str
    type: str
    province: str
    probleme: str
    cause: str
    statut: str
    suggestion: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "entite": self.entite,
            "type": self.type,
            "province": self.province,
            "probleme": self.probleme,
            "cause": self.cause,
            "statut": self.statut,
            "suggestion": self.suggestion,
        }


@dataclass(slots=True)
class CollectivityQualityReport:
    source_file: str
    generated_at: datetime
    collectivity_count: int
    secteur_count: int
    chefferie_count: int
    missing_territory_count: int
    missing_province_count: int
    missing_zone_count: int
    invalid_geometry_count: int
    duplicate_count: int
    unknown_type_count: int
    global_score: float
    duplicate_keys: list[str] = field(default_factory=list)
    anomalies: list[CollectivityAnomaly] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "generated_at": self.generated_at.isoformat(timespec="seconds"),
            "collectivity_count": self.collectivity_count,
            "secteur_count": self.secteur_count,
            "chefferie_count": self.chefferie_count,
            "missing_territory_count": self.missing_territory_count,
            "missing_province_count": self.missing_province_count,
            "missing_zone_count": self.missing_zone_count,
            "invalid_geometry_count": self.invalid_geometry_count,
            "duplicate_count": self.duplicate_count,
            "unknown_type_count": self.unknown_type_count,
            "duplicate_keys": list(self.duplicate_keys),
            "anomalies": [item.to_dict() for item in self.anomalies],
            "global_score": self.global_score,
        }


@dataclass(slots=True)
class CollectivityReferentialReport:
    source_file: str
    generated_at: datetime
    collectivity_referential: list[CollectivityCanonicalEntity]
    collectivity_fact_sheets: list[CollectivityFactSheet]
    territory_collectivity_index: dict[str, Any]
    province_collectivity_index: dict[str, Any]
    quality: CollectivityQualityReport

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "generated_at": self.generated_at.isoformat(timespec="seconds"),
            "collectivity_referential": [item.to_dict() for item in self.collectivity_referential],
            "collectivity_fact_sheets": [item.to_dict() for item in self.collectivity_fact_sheets],
            "territory_collectivity_index": self.territory_collectivity_index,
            "province_collectivity_index": self.province_collectivity_index,
            "quality": self.quality.to_dict(),
        }


@dataclass(slots=True)
class CollectivityOfficialRunResult:
    source_path: Path
    report: CollectivityReferentialReport
    referential_json_path: Path
    fact_sheets_json_path: Path
    quality_json_path: Path
    report_markdown_path: Path
    files_report_path: Path
    territory_index_json_path: Path
    province_index_json_path: Path
    national_counter_registry_path: Path
