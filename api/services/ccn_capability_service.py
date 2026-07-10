"""Fondations Capability 1 — Centres Communautaires Numériques (CCN).

Pas de CRUD. Pas de tables définitives.
Expose le modèle métier, la nomenclature préparatoire et les points
d'extension du Centre de Décision.
"""

from __future__ import annotations

import re
from typing import Any

from api.models.business_entities import (
    CCN_ATTRIBUTE_DOMAINS,
    CCN_CODE_SCHEME,
    CCN_DECISION_EXTENSIONS,
    CCN_RELATIONSHIPS,
    AssetType,
    CcnHostType,
    CcnServiceType,
    RelationshipType,
    assert_site_ccn_distinct,
    build_proposed_ccn_code,
    is_ccn,
    is_site_fdsu,
    parse_proposed_ccn_code,
    validate_proposed_ccn_code,
)

# Activation officielle de FDSU_CCN_* — reste False jusqu'à validation métier
CCN_NOMENCLATURE_OFFICIALLY_ACTIVATED = False

_CCN_CODE_RE = re.compile(
    r"^FDSU_CCN_(?P<zone>[A-Z]{2})_(?P<province>\d{2})_(?P<territoire>\d{3})_(?P<numero>\d{3,5})$",
    re.IGNORECASE,
)


def capability_manifest() -> dict[str, Any]:
    """Manifeste de la capacité CCN (Phase 2 — fondations)."""
    return {
        "_meta": {
            "capability": "CCN",
            "phase": 2,
            "title": "Gestion des Centres Communautaires Numériques",
            "status": "foundations",
            "crud_enabled": False,
            "official_nomenclature_activated": CCN_NOMENCLATURE_OFFICIALLY_ACTIVATED,
            "architecture_doc": "PROJECT_MANAGEMENT/ARCHITECTURE/FDSU_CCN_BUSINESS_MODEL.md",
        },
        "asset_type": AssetType.CCN.value,
        "distinction": {
            "site_fdsu": "Apporte la connectivité",
            "ccn": "Apporte les services numériques à la population",
            "must_remain_distinct": True,
        },
        "attribute_domains": list(CCN_ATTRIBUTE_DOMAINS),
        "host_types": [item.value for item in CcnHostType],
        "service_types": [item.value for item in CcnServiceType],
        "relationships": [
            {
                "code": rel.code,
                "label": rel.label,
                "from_type": rel.from_type.value if hasattr(rel.from_type, "value") else rel.from_type,
                "to_type": rel.to_type.value if hasattr(rel.to_type, "value") else rel.to_type,
            }
            for rel in CCN_RELATIONSHIPS
        ],
        "nomenclature": {
            "scheme": {
                "code": CCN_CODE_SCHEME.code,
                "pattern": CCN_CODE_SCHEME.pattern,
                "example": CCN_CODE_SCHEME.example,
                "is_official": CCN_CODE_SCHEME.is_official,
                "notes": CCN_CODE_SCHEME.notes,
            },
            "ready_for_activation": True,
            "activated": CCN_NOMENCLATURE_OFFICIALLY_ACTIVATED,
        },
        "decision_center_extensions": [
            {
                "code": ext.code,
                "label": ext.label,
                "description": ext.description,
                "ui_ready": ext.ui_ready,
            }
            for ext in CCN_DECISION_EXTENSIONS
        ],
    }


def decision_extension_points() -> list[dict[str, Any]]:
    """Points d'extension Centre de Décision (non branchés UI complète)."""
    return [
        {
            "code": ext.code,
            "label": ext.label,
            "description": ext.description,
            "ui_ready": False,
            "planned_intents": ext.planned_intents,
        }
        for ext in CCN_DECISION_EXTENSIONS
    ]


def prepare_ccn_code(
    *,
    zone: str,
    province_code: str | int,
    territoire_code: str | int,
    numero: str | int,
) -> dict[str, Any]:
    """Prépare un code CCN selon le schéma proposé (non officiel)."""
    code = build_proposed_ccn_code(
        zone=zone,
        province_code=province_code,
        territoire_code=territoire_code,
        numero=numero,
    )
    validation = validate_proposed_ccn_code(code)
    return {
        "business_id": code,
        "is_official": False,
        "nomenclature_activated": CCN_NOMENCLATURE_OFFICIALLY_ACTIVATED,
        "validation": validation,
        "warning": (
            None
            if not CCN_NOMENCLATURE_OFFICIALLY_ACTIVATED
            else None
        )
        or (
            "Schéma préparatoire uniquement — nomenclature CCN non encore officialisée."
            if not CCN_NOMENCLATURE_OFFICIALLY_ACTIVATED
            else None
        ),
    }


def inspect_ccn_code(business_id: str) -> dict[str, Any]:
    parsed = parse_proposed_ccn_code(business_id)
    validation = validate_proposed_ccn_code(business_id)
    return {
        "business_id": business_id,
        "parsed": parsed,
        "validation": validation,
        "is_official_scheme": False,
        "activated": CCN_NOMENCLATURE_OFFICIALLY_ACTIVATED,
        "looks_like_site_fdsu": bool(
            str(business_id or "").upper().startswith("FDSU_")
            and not str(business_id or "").upper().startswith("FDSU_CCN_")
        ),
    }


def assert_not_confused_with_site(asset_type_a: str, asset_type_b: str) -> dict[str, Any]:
    distinct = assert_site_ccn_distinct(asset_type_a, asset_type_b)
    return {
        "left": asset_type_a,
        "right": asset_type_b,
        "site_ccn_pair": distinct,
        "ok": distinct or (
            not is_site_fdsu(asset_type_a) and not is_ccn(asset_type_a)
        ),
        "rule": "Un Site FDSU et un CCN ne doivent jamais être confondus.",
    }


def relationship_catalog() -> list[dict[str, Any]]:
    return [
        {
            "code": item.code,
            "relationship_type": item.relationship_type.value,
            "label": item.label,
            "from_type": item.from_type if isinstance(item.from_type, str) else item.from_type.value,
            "to_type": item.to_type if isinstance(item.to_type, str) else item.to_type.value,
        }
        for item in CCN_RELATIONSHIPS
    ]


def required_connectivity_link() -> str:
    return RelationshipType.FEEDS_CONNECTIVITY.value
