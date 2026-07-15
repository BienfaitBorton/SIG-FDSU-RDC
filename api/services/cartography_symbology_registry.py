"""Registre unique de symbologie cartographique — carte et légende partagent la même config."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

REGISTRY_PATH = Path(__file__).resolve().parents[2] / "data" / "cartography" / "symbology_registry_v1.json"


@lru_cache(maxsize=1)
def load_symbology_registry() -> dict[str, Any]:
    if not REGISTRY_PATH.exists():
        return {"_meta": {"version": "fallback"}, "domains": []}
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def list_domains() -> list[dict[str, Any]]:
    return list(load_symbology_registry().get("domains") or [])


def get_domain(kind: str) -> dict[str, Any] | None:
    key = str(kind or "").strip()
    for domain in list_domains():
        if domain.get("domain") == key:
            return domain
    return None


def style_for(kind: str) -> dict[str, Any]:
    """Style Leaflet-compatible dérivé du registre (jamais une couleur hardcodée séparée)."""
    domain = get_domain(kind) or {}
    return {
        "domain": domain.get("domain") or kind,
        "label": domain.get("label") or kind,
        "geometry_type": domain.get("geometry_type") or "point",
        "color": domain.get("color") or "#64748b",
        "fillColor": domain.get("fill_color") or domain.get("color") or "#94a3b8",
        "fillOpacity": domain.get("fill_opacity", 0.8),
        "radius": domain.get("radius", 5),
        "weight": domain.get("weight", 2),
        "opacity": domain.get("opacity", 0.9),
        "icon": domain.get("icon") or "circle",
        "line_style": domain.get("line_style"),
        "layer_order": domain.get("layer_order", 100),
        "legend_class": domain.get("legend_class") or "",
    }


def build_legend_items(
    layer_counts: dict[str, Any] | None,
    *,
    only_visible: bool = True,
) -> list[dict[str, Any]]:
    """Légende dynamique : uniquement les couches présentes (count > 0) si only_visible."""
    counts = {str(k): int(v) for k, v in (layer_counts or {}).items() if not str(k).startswith("_")}
    items: list[dict[str, Any]] = []
    for domain in sorted(list_domains(), key=lambda d: int(d.get("layer_order") or 100)):
        kind = str(domain.get("domain") or "")
        count = counts.get(kind, 0)
        if only_visible and count <= 0:
            continue
        style = style_for(kind)
        items.append(
            {
                "kind": kind,
                "domain": kind,
                "label": domain.get("label") or kind,
                "count": count,
                "visible": count > 0,
                "geometry_type": style["geometry_type"],
                "color": style["color"],
                "fill_color": style["fillColor"],
                "icon": style["icon"],
                "line_style": style["line_style"],
                "legend_class": style["legend_class"],
                "layer_order": style["layer_order"],
            }
        )
    return items


def registry_payload() -> dict[str, Any]:
    reg = load_symbology_registry()
    return {
        "_meta": reg.get("_meta") or {},
        "domains": [style_for(d["domain"]) for d in list_domains() if d.get("domain")],
    }
