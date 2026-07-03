from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class GroupementCanonicalEntity:
    canonical_id: str
    nom: str
    niveau: str
    collectivite_parent: str
    type_collectivite_parent: str
    territoire: str
    province: str
    zone_fdsu: str
    code_officiel: str | None
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
            "collectivite_parent": self.collectivite_parent,
            "type_collectivite_parent": self.type_collectivite_parent,
            "territoire": self.territoire,
            "province": self.province,
            "zone_fdsu": self.zone_fdsu,
            "code_officiel": self.code_officiel,
            "geometry": self.geometry,
            "source": self.source,
            "statut": self.statut,
            "qualite": self.qualite,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class GroupementFactSheet:
    canonical_id: str
    nom: str
    collectivite_parent: str
    type_collectivite_parent: str
    territoire: str
    province: str
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
            "collectivite_parent": self.collectivite_parent,
            "type_collectivite_parent": self.type_collectivite_parent,
            "territoire": self.territoire,
            "province": self.province,
            "zone_fdsu": self.zone_fdsu,
            "code_officiel": self.code_officiel,
            "geometry_type": self.geometry_type,
            "source": self.source,
            "quality_flags": list(self.quality_flags),
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class GroupementAnomaly:
    entite: str
    type: str
    code: str | None
    province: str
    territoire: str
    collectivite_parent: str
    probleme: str
    cause: str
    statut: str
    suggestion: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "entite": self.entite,
            "type": self.type,
            "code": self.code,
            "province": self.province,
            "territoire": self.territoire,
            "collectivite_parent": self.collectivite_parent,
            "probleme": self.probleme,
            "cause": self.cause,
            "statut": self.statut,
            "suggestion": self.suggestion,
        }


@dataclass(slots=True)
class GroupementQualityReport:
    source_file: str
    generated_at: datetime
    groupement_count: int
    attached_count: int
    orphan_count: int
    missing_territory_count: int
    missing_province_count: int
    missing_zone_count: int
    duplicate_count: int
    invalid_geometry_count: int
    missing_code_count: int
    inconsistency_count: int
    validated_count: int
    global_score: float
    duplicate_keys: list[str] = field(default_factory=list)
    anomalies: list[GroupementAnomaly] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "generated_at": self.generated_at.isoformat(timespec="seconds"),
            "groupement_count": self.groupement_count,
            "attached_count": self.attached_count,
            "orphan_count": self.orphan_count,
            "missing_territory_count": self.missing_territory_count,
            "missing_province_count": self.missing_province_count,
            "missing_zone_count": self.missing_zone_count,
            "duplicate_count": self.duplicate_count,
            "invalid_geometry_count": self.invalid_geometry_count,
            "missing_code_count": self.missing_code_count,
            "inconsistency_count": self.inconsistency_count,
            "validated_count": self.validated_count,
            "duplicate_keys": list(self.duplicate_keys),
            "anomalies": [item.to_dict() for item in self.anomalies],
            "global_score": self.global_score,
        }


@dataclass(slots=True)
class GroupementReferentialReport:
    source_file: str
    generated_at: datetime
    groupement_referential: list[GroupementCanonicalEntity]
    groupement_fact_sheets: list[GroupementFactSheet]
    collectivity_groupement_index: dict[str, Any]
    territory_groupement_index: dict[str, Any]
    province_groupement_index: dict[str, Any]
    quality: GroupementQualityReport

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "generated_at": self.generated_at.isoformat(timespec="seconds"),
            "groupement_referential": [item.to_dict() for item in self.groupement_referential],
            "groupement_fact_sheets": [item.to_dict() for item in self.groupement_fact_sheets],
            "collectivity_groupement_index": self.collectivity_groupement_index,
            "territory_groupement_index": self.territory_groupement_index,
            "province_groupement_index": self.province_groupement_index,
            "quality": self.quality.to_dict(),
        }


@dataclass(slots=True)
class GroupementOfficialRunResult:
    source_path: Path
    report: GroupementReferentialReport
    referential_json_path: Path
    fact_sheets_json_path: Path
    quality_json_path: Path
    report_markdown_path: Path
    files_report_path: Path
    collectivity_index_json_path: Path
    territory_index_json_path: Path
    province_index_json_path: Path
    national_counter_registry_path: Path
