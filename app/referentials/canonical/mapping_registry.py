from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .canonical_schema import SourceKey

TransformFn = Callable[[Any], Any]


@dataclass(slots=True, frozen=True)
class FieldMapping:
    """Maps one canonical field from one or many source fields."""

    canonical_field: str
    source_fields: tuple[str, ...]
    required: bool = False
    default: Any = None
    transform: TransformFn | None = None
    description: str = ""

    def extract(self, source_record: dict[str, Any]) -> Any:
        value = self.default
        for key in self.source_fields:
            if key in source_record and source_record[key] not in (None, ""):
                value = source_record[key]
                break
        if self.transform:
            return self.transform(value)
        return value


@dataclass(slots=True)
class SourceMappingProfile:
    """Declarative mapping profile from one source into canonical payload."""

    source: SourceKey
    version: str = "1.0"
    field_mappings: tuple[FieldMapping, ...] = ()
    constants: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_canonical_payload(self, source_record: dict[str, Any]) -> dict[str, Any]:
        payload = dict(self.constants)
        for mapping in self.field_mappings:
            payload[mapping.canonical_field] = mapping.extract(source_record)
        return payload


class MappingRegistry:
    """Registry for all source-to-canonical mapping profiles."""

    def __init__(self) -> None:
        self._profiles: dict[SourceKey, SourceMappingProfile] = {}

    def register(self, profile: SourceMappingProfile) -> None:
        self._profiles[profile.source] = profile

    def get(self, source: SourceKey) -> SourceMappingProfile:
        if source not in self._profiles:
            raise KeyError(f"No mapping profile registered for source '{source.value}'.")
        return self._profiles[source]

    def has(self, source: SourceKey) -> bool:
        return source in self._profiles

    def list_profiles(self) -> list[SourceMappingProfile]:
        return list(self._profiles.values())


def _uppercase(value: Any) -> Any:
    if value is None:
        return None
    return str(value).strip().upper()


def _trim(value: Any) -> Any:
    if value is None:
        return None
    return str(value).strip()


def build_default_mapping_registry() -> MappingRegistry:
    """Build default profile declarations for current planned official sources."""

    registry = MappingRegistry()

    shared = (
        FieldMapping("name", ("name", "nom", "adm_name", "libelle"), required=True, transform=_trim),
        FieldMapping("level", ("level", "niveau", "admin_level", "shapelevel", "adm_level"), transform=_trim),
        FieldMapping("code", ("code", "pcode", "adm_code", "code_entite"), transform=_uppercase),
        FieldMapping("parent_code", ("parent_code", "code_parent", "adm_parent_code"), transform=_uppercase),
    )

    registry.register(
        SourceMappingProfile(
            source=SourceKey.HDX,
            field_mappings=shared
            + (
                FieldMapping("province_code", ("adm1_pcode",)),
                FieldMapping("territoire_code", ("adm2_pcode",)),
                FieldMapping("groupement_code", ("adm3_pcode",)),
            ),
            metadata={"status": "declarative_only", "connected": False},
        )
    )

    registry.register(
        SourceMappingProfile(
            source=SourceKey.CENI,
            field_mappings=shared
            + (
                FieldMapping("province_code", ("code_province", "province_code"), transform=_uppercase),
                FieldMapping("territoire_code", ("code_territoire", "territoire_code"), transform=_uppercase),
            ),
            metadata={"status": "declarative_only", "connected": False},
        )
    )

    registry.register(
        SourceMappingProfile(
            source=SourceKey.CAID,
            field_mappings=shared,
            metadata={"status": "declarative_only", "connected": False},
        )
    )

    registry.register(
        SourceMappingProfile(
            source=SourceKey.KMZ,
            field_mappings=shared
            + (
                FieldMapping("geometry_name", ("geometry_name", "placemark_name"), transform=_trim),
                FieldMapping("geometry_type", ("geometry_type", "shape_type"), transform=_trim),
            ),
            metadata={"status": "declarative_only", "connected": False},
        )
    )

    registry.register(
        SourceMappingProfile(
            source=SourceKey.EXCEL_FDSU,
            field_mappings=shared
            + (
                FieldMapping("province_name", ("province", "nom_province"), transform=_trim),
                FieldMapping("territoire_name", ("territoire", "nom_territoire"), transform=_trim),
            ),
            metadata={"status": "declarative_only", "connected": False},
        )
    )

    return registry
