"""Canonical referential layer for SIG-FDSU."""

from .canonical_entity import (
    CanonicalAdministrativeEntity,
    CanonicalCodeSet,
    CanonicalSourceReference,
)
from .canonical_mapper import CanonicalMapper
from .canonical_schema import CanonicalLevel, CanonicalStatus, SourceKey, parse_level
from .mapping_registry import (
    FieldMapping,
    MappingRegistry,
    SourceMappingProfile,
    build_default_mapping_registry,
)
from .source_registry import (
    SourceDefinition,
    SourceRegistry,
    build_default_source_registry,
)

__all__ = [
    "CanonicalAdministrativeEntity",
    "CanonicalCodeSet",
    "CanonicalSourceReference",
    "CanonicalMapper",
    "CanonicalLevel",
    "CanonicalStatus",
    "SourceKey",
    "parse_level",
    "FieldMapping",
    "MappingRegistry",
    "SourceMappingProfile",
    "build_default_mapping_registry",
    "SourceDefinition",
    "SourceRegistry",
    "build_default_source_registry",
]
