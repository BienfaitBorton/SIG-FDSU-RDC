"""Classification dérivée non destructive des actifs Fibre / MW / Fiberco.

Conserve les types originaux ; ne mute jamais les sources KMZ.
"""
from __future__ import annotations

from typing import Any

ASSET_TYPES = (
    "FIBER_LINK",
    "MICROWAVE_LINK",
    "NETWORK_NODE",
    "POP",
    "TECHNICAL_SITE",
    "COVERAGE_OR_SERVICE_AREA",
    "OTHER",
)


def _blob(row: dict[str, Any]) -> str:
    props = row.get("properties") or {}
    parts = [
        row.get("infra_type"),
        row.get("line_type"),
        row.get("polygon_type"),
        row.get("technology"),
        row.get("infra_name"),
        row.get("line_name"),
        row.get("polygon_name"),
        props.get("name"),
        props.get("folder"),
        props.get("styleUrl"),
        props.get("description"),
        str(props),
    ]
    return " ".join(str(p or "") for p in parts).lower()


def classify_telecom_asset(row: dict[str, Any], *, geometry_kind: str) -> dict[str, Any]:
    """Retourne derived_asset_type + original_type sans altérer la ligne source."""
    original = (
        row.get("line_type")
        or row.get("infra_type")
        or row.get("polygon_type")
        or row.get("technology")
        or "unknown"
    )
    text = _blob(row)
    derived = "OTHER"

    if geometry_kind == "polygon" or "coverage" in text or "footprint" in text or "service" in text:
        derived = "COVERAGE_OR_SERVICE_AREA"
    elif geometry_kind == "line":
        if any(tok in text for tok in ("microwave", "micro-onde", "micro onde", " mw", "mw ", "radio link")):
            derived = "MICROWAVE_LINK"
        elif any(tok in text for tok in ("fiber", "fibre", "fttx", "ftth", "optic")):
            derived = "FIBER_LINK"
        elif "mw" in text and "fiber" not in text and "fibre" not in text:
            derived = "MICROWAVE_LINK"
        else:
            # FIBER_MW seed defaults to fiber_mw — prefer fibre unless MW explicit
            if "fiber_mw" in text or "fiber/mw" in text:
                derived = "FIBER_LINK"
            else:
                derived = "FIBER_LINK"
    else:  # point
        if any(tok in text for tok in ("pop", "point of presence")):
            derived = "POP"
        elif any(tok in text for tok in ("node", "noeud", "nœud", "technical", "site")):
            derived = "NETWORK_NODE"
        elif any(tok in text for tok in ("microwave", " mw", "mw ")):
            derived = "TECHNICAL_SITE"
        else:
            derived = "NETWORK_NODE"

    return {
        "derived_asset_type": derived,
        "original_type": original,
        "geometry_kind": geometry_kind,
    }


def is_fiber_asset(row: dict[str, Any], *, geometry_kind: str) -> bool:
    return classify_telecom_asset(row, geometry_kind=geometry_kind)["derived_asset_type"] in {
        "FIBER_LINK",
        "POP",
        "NETWORK_NODE",
        "COVERAGE_OR_SERVICE_AREA",
    } and "microwave" not in _blob(row) and " mw" not in f" {_blob(row)} "


def is_microwave_asset(row: dict[str, Any], *, geometry_kind: str) -> bool:
    typed = classify_telecom_asset(row, geometry_kind=geometry_kind)["derived_asset_type"]
    text = _blob(row)
    return typed == "MICROWAVE_LINK" or any(
        tok in text for tok in ("microwave", "micro-onde", "micro onde", " mw", "/mw", "mw/")
    )
