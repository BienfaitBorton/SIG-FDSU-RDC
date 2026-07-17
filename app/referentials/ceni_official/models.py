from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class CeniCategory(StrEnum):
    CENI_SITE = "CENI_SITE"
    VOTING_CENTER = "VOTING_CENTER"
    REGISTRATION_CENTER = "REGISTRATION_CENTER"
    PUBLIC_BUILDING = "PUBLIC_BUILDING"
    SCHOOL = "SCHOOL"
    HEALTH_FACILITY = "HEALTH_FACILITY"
    ADMINISTRATIVE_BUILDING = "ADMINISTRATIVE_BUILDING"
    RELIGIOUS_BUILDING = "RELIGIOUS_BUILDING"
    MARKET = "MARKET"
    ENERGY = "ENERGY"
    TELECOM = "TELECOM"
    ROAD = "ROAD"
    OTHER = "OTHER"
    UNCLASSIFIED = "UNCLASSIFIED"


@dataclass(slots=True)
class CeniAsset:
    asset_uid: str
    source_record_id: str
    name: str
    source_category: str | None
    normalized_category: str
    classification_justification: str
    classification_confidence: float
    longitude: float | None
    latitude: float | None
    geometry_status: str
    administrative_attachment: dict[str, Any]
    source: dict[str, Any]
    raw_properties: dict[str, Any]
    aliases: list[str] = field(default_factory=list)
    fingerprint: str = ""
    legacy_ids: list[str] = field(default_factory=list)
    duplicate: dict[str, Any] = field(default_factory=dict)
    asset_domain: str = "INSTITUTIONAL"
    institution: str = "CENI"
    asset_type: str = "CENI_SITE"
    normalized_name: str = ""
    normalized_category_label_fr: str = ""
    classification_method: str = ""
    matched_rule_id: str | None = None
    matched_keyword: str | None = None
    confidence_label_fr: str = ""
    engine_version: str = ""
    classification_date: str = ""
    review_status: str = "Non revu"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
