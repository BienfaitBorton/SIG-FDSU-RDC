"""Catalogue extensible des couches cartographiques Télécom FDSU.

Source de vérité pour Smart Map — évite les listes figées comme unique référence.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

# Couches déclaratives — nouveaux opérateurs = nouvelles entrées, sans refonte UI.
LAYER_CATALOG: list[dict[str, Any]] = [
    {
        "layer_key": "telecom_vodacom",
        "label": "Sites Vodacom",
        "source_kind": "TELECOM_DB",
        "operator_code": "VODACOM",
        "geometry_kinds": ["point"],
        "default_on": False,
        "quality_mode": "REFERENTIAL",
        "color": "#e11d48",
        "fillColor": "#fb7185",
        "legend_group": "mno",
    },
    {
        "layer_key": "telecom_orange",
        "label": "Sites Orange",
        "source_kind": "TELECOM_DB",
        "operator_code": "ORANGE",
        "geometry_kinds": ["point"],
        "default_on": False,
        "quality_mode": "REFERENTIAL",
        "color": "#ea580c",
        "fillColor": "#fb923c",
        "legend_group": "mno",
    },
    {
        "layer_key": "telecom_airtel",
        "label": "Sites Airtel",
        "source_kind": "FDSU_MNO_AUDIT",
        "operator_code": "AIRTEL",
        "geometry_kinds": ["point"],
        "default_on": False,
        "quality_mode": "NIRE_QUALITY",
        "color": "#dc2626",
        "fillColor": "#f87171",
        "legend_group": "mno",
        "kpi_excluded": True,
        "note": "Couche FDSU provisoire — hors COUNT telecom.infrastructure",
    },
    {
        "layer_key": "telecom_africell",
        "label": "Sites Africell",
        "source_kind": "FDSU_MNO_AUDIT",
        "operator_code": "AFRICELL",
        "geometry_kinds": ["point"],
        "default_on": False,
        "quality_mode": "NIRE_QUALITY",
        "color": "#16a34a",
        "fillColor": "#4ade80",
        "legend_group": "mno",
        "kpi_excluded": True,
        "note": "Couche FDSU provisoire — hors COUNT telecom.infrastructure",
    },
    {
        "layer_key": "telecom_mno_planned",
        "label": "Sites MNO Planned",
        "source_kind": "FDSU_MNO_AUDIT",
        "operator_code": None,
        "filter": "PLANNED",
        "geometry_kinds": ["point"],
        "default_on": False,
        "quality_mode": "NIRE_QUALITY",
        "color": "#ca8a04",
        "fillColor": "#facc15",
        "legend_group": "mno",
        "kpi_excluded": True,
    },
    {
        "layer_key": "telecom_fiber",
        "label": "Fibre",
        "source_kind": "TELECOM_DB_TYPED",
        "operator_codes": ["FIBER_MW", "FIBERCO", "FTTX"],
        "asset_filter": "FIBER",
        "geometry_kinds": ["point", "line", "polygon"],
        "default_on": False,
        "quality_mode": "REFERENTIAL",
        "color": "#2563eb",
        "fillColor": "#60a5fa",
        "legend_group": "backbone",
    },
    {
        "layer_key": "telecom_microwave",
        "label": "Microwave / MW",
        "source_kind": "TELECOM_DB_TYPED",
        "operator_codes": ["FIBER_MW"],
        "asset_filter": "MICROWAVE",
        "geometry_kinds": ["point", "line", "polygon"],
        "default_on": False,
        "quality_mode": "REFERENTIAL",
        "color": "#7c3aed",
        "fillColor": "#a78bfa",
        "legend_group": "backbone",
    },
    {
        "layer_key": "telecom_fiberco",
        "label": "Fiberco",
        "source_kind": "TELECOM_DB",
        "operator_code": "FIBERCO",
        "geometry_kinds": ["point", "line", "polygon"],
        "default_on": False,
        "quality_mode": "REFERENTIAL",
        "color": "#0891b2",
        "fillColor": "#22d3ee",
        "legend_group": "backbone",
    },
    {
        "layer_key": "telecom_fiber_mw",
        "label": "Fibre / MW (combiné)",
        "source_kind": "TELECOM_DB",
        "operator_code": "FIBER_MW",
        "geometry_kinds": ["point", "line", "polygon"],
        "default_on": False,
        "quality_mode": "REFERENTIAL",
        "color": "#2563eb",
        "fillColor": "#60a5fa",
        "legend_group": "backbone",
        "legacy": True,
    },
    {
        "layer_key": "telecom_fttx",
        "label": "FTTX",
        "source_kind": "TELECOM_DB",
        "operator_code": "FTTX",
        "geometry_kinds": ["point", "line", "polygon"],
        "default_on": False,
        "quality_mode": "REFERENTIAL",
        "color": "#7c3aed",
        "fillColor": "#a78bfa",
        "legend_group": "backbone",
    },
]


def list_layer_catalog() -> list[dict[str, Any]]:
    return deepcopy(LAYER_CATALOG)


def get_layer_definition(layer_key: str) -> dict[str, Any] | None:
    for entry in LAYER_CATALOG:
        if entry["layer_key"] == layer_key:
            return deepcopy(entry)
    return None


def known_layer_keys() -> set[str]:
    return {e["layer_key"] for e in LAYER_CATALOG}


def catalog_payload() -> dict[str, Any]:
    return {
        "layers": list_layer_catalog(),
        "quality_statuses": [
            "VERIFIED",
            "HIGH_CONFIDENCE",
            "PROVISIONAL",
            "NEEDS_REVIEW",
            "CONFLICT",
        ],
        "kpi_note": (
            "Les couches FDSU_MNO_AUDIT sont visibles avec statut NIRE mais "
            "exclues du KPI officiel COUNT(telecom.infrastructure)."
        ),
        "extensible": True,
    }
