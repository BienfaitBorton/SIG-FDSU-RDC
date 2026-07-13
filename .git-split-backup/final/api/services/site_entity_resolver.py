"""Résolveur centralisé d’entité Site FDSU.

Toutes les vues (Decision Case, DXL, SDG, ESR) doivent passer par ce module
pour interpréter (entity_type, entity_id, program_code) — aucun module ne doit
réinterpréter « 29 » isolément.
"""

from __future__ import annotations

import re
from typing import Any


def normalize_site_id(raw: Any) -> int | None:
    if raw is None:
        return None
    if isinstance(raw, int):
        return raw
    text = str(raw).strip()
    if not text:
        return None
    # DCF-SITE-29 / site:29 / SITES_40_00029
    if ":" in text:
        text = text.split(":", 1)[-1]
    digits = re.sub(r"[^\d]", "", text)
    if not digits:
        return None
    # Prefer trailing significant id for codes like SITES_40_00029
    try:
        return int(digits.lstrip("0") or "0") if len(digits) > 6 else int(digits)
    except ValueError:
        return None


def resolve_site(
    entity_id: Any,
    *,
    program_code: str | None = None,
    entity_type: str | None = "site",
) -> dict[str, Any] | None:
    """Retourne l’identité canonique du site + score sourcé, ou None."""
    kind = str(entity_type or "site").lower().strip()
    if kind not in {"site", "fdsu_site", "sites"}:
        return None

    sid = normalize_site_id(entity_id)
    if sid is None:
        return None

    from api.services import fdsu_site_priority_service

    explained = fdsu_site_priority_service.explain_site(sid, program_code=program_code)
    if not explained:
        # Repli : chercher sans forcer le programme
        if program_code:
            explained = fdsu_site_priority_service.explain_site(sid, program_code=None)
    if not explained:
        return {
            "resolved": False,
            "site_id": sid,
            "entity_type": "site",
            "program_code": program_code,
            "site_name": None,
            "site_code": None,
            "message": f"Site {sid} introuvable dans les programmes / scores disponibles.",
        }

    site = explained.get("site") or {}
    return {
        "resolved": True,
        "entity_type": "site",
        "site_id": int(site.get("site_id") or sid),
        "site_name": site.get("site_name") or site.get("name"),
        "site_code": site.get("site_code") or site.get("business_id"),
        "program_code": site.get("program_code") or program_code,
        "province": site.get("province"),
        "territoire": site.get("territoire"),
        "zone": site.get("zone"),
        "latitude": site.get("latitude"),
        "longitude": site.get("longitude"),
        "population": site.get("population"),
        "priority_score": site.get("priority_score"),
        "priority_level": site.get("priority_level"),
        "priority_level_label": site.get("priority_level_label"),
        "distance": site.get("distance"),
        "distance_level": site.get("distance_level"),
        "is_300_planned": site.get("is_300_planned"),
        "explained": explained,
        "source": "fdsu_site_priority_service.explain_site",
    }
