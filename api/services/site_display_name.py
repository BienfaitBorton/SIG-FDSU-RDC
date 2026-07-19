"""Résolution centralisée du libellé métier d’un site FDSU.

Règle d’affichage (ordre de priorité) :
1. Village Name / village_name
2. Locality / localite / locality_name
3. name / nom (programmes 40 / 300)
4. autres champs métier non techniques (ex. infra_name NCI)
5. site_name uniquement s’il n’est pas un identifiant technique
6. identifiant technique en dernier recours (site_name / site_code)

L’identifiant technique est toujours conservé séparément (technical_id).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
NCI_UNCOVERED = PROJECT_ROOT / "data" / "coverage" / "localities_uncovered.jsonl"

_NCI_LABEL_CACHE: dict[str, dict[str, Any]] | None = None
_NCI_LABEL_MTIME: float = 0.0

# Identifiants RF / NewSite du programme national 20 476
TECHNICAL_SITE_NAME_RE = re.compile(
    r"(?i)(?:^Part\d+_|\bNewSite\b|\bBC_\d|_C\d+$|^CD\d{3,}|^SITES_\d+_)",
)

# Champs candidats : (source_field_id, clés possibles sur l’objet site / properties)
_DISPLAY_CANDIDATES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("village_name", ("Village Name", "village_name", "village", "Village")),
    ("locality_name", ("locality_name", "locality", "Locality", "localite", "localité", "localite_name")),
    ("name", ("name", "nom")),
    ("infra_name", ("infra_name", "Nom de l'infrastructure de base")),
    ("nearest_site", ("nearest_site", "Nearest Site")),
    ("site_name", ("site_name", "Site Name")),
)


def _as_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def is_technical_site_identifier(value: Any) -> bool:
    text = _as_text(value)
    if not text:
        return False
    if TECHNICAL_SITE_NAME_RE.search(text):
        return True
    # Motifs Part*_…_NewSite_* très fréquents sur le national
    if "NewSite" in text or re.match(r"(?i)^Part\d+_", text):
        return True
    return False


def extract_technical_id(site: dict[str, Any] | None) -> str | None:
    site = site or {}
    for key in ("site_name", "Site Name", "technical_id", "source_id"):
        value = _as_text(site.get(key))
        if value and is_technical_site_identifier(value):
            return value
    return _as_text(site.get("site_code")) or _as_text(site.get("site_id"))


def resolve_site_display_name(site: dict[str, Any] | None) -> dict[str, Any]:
    """Retourne display_name + métadonnées de provenance."""
    site = dict(site or {})
    props = site.get("properties") if isinstance(site.get("properties"), dict) else {}
    bag: dict[str, Any] = {**props, **site}

    technical_id = extract_technical_id(bag)
    chosen: str | None = None
    source_field: str | None = None

    for field_id, keys in _DISPLAY_CANDIDATES:
        for key in keys:
            value = _as_text(bag.get(key))
            if not value:
                continue
            # Ne jamais promouvoir un identifiant technique tant qu’un autre
            # champ métier reste possible plus bas dans la chaîne… sauf si
            # c’est le dernier recours (site_name / nearest_site techniques).
            if is_technical_site_identifier(value):
                continue
            chosen = value
            source_field = field_id if field_id != "name" else ("name" if key in {"name", "nom"} else field_id)
            break
        if chosen:
            break

    if not chosen:
        # Dernier recours : site_name brut, puis code, puis id
        for key in ("site_name", "Site Name", "name", "nom", "site_code"):
            value = _as_text(bag.get(key))
            if value:
                chosen = value
                source_field = "technical_fallback"
                break
        if not chosen:
            chosen = f"Site {bag.get('site_id') or '—'}"
            source_field = "technical_fallback"

    is_fallback = source_field == "technical_fallback" or (
        technical_id is not None and chosen == technical_id
    )

    return {
        "display_name": chosen,
        "technical_id": technical_id,
        "source_field": source_field,
        "is_technical_fallback": bool(is_fallback),
    }


def apply_display_name(site: dict[str, Any] | None) -> dict[str, Any]:
    """Enrichit un dict site avec display_name / technical_id (copie shallow)."""
    site = dict(site or {})
    resolved = resolve_site_display_name(site)
    site["display_name"] = resolved["display_name"]
    site["technical_id"] = resolved["technical_id"]
    site["display_name_source"] = resolved["source_field"]
    site["display_name_is_technical_fallback"] = resolved["is_technical_fallback"]
    # Alias UI fréquent
    if not _as_text(site.get("name")) or is_technical_site_identifier(site.get("name")):
        site["name"] = resolved["display_name"]
    return site


def _nci_label_index() -> dict[str, dict[str, Any]]:
    """Index NCI uncovered : name (souvent = site_name 20476) → champs de libellé."""
    global _NCI_LABEL_CACHE, _NCI_LABEL_MTIME
    try:
        mtime = NCI_UNCOVERED.stat().st_mtime if NCI_UNCOVERED.exists() else 0.0
    except OSError:
        mtime = 0.0
    if _NCI_LABEL_CACHE is not None and _NCI_LABEL_MTIME == mtime:
        return _NCI_LABEL_CACHE

    index: dict[str, dict[str, Any]] = {}
    if NCI_UNCOVERED.exists():
        with NCI_UNCOVERED.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                name = _as_text(row.get("name"))
                if not name or name in index:
                    continue
                index[name] = {
                    "infra_name": _as_text(row.get("infra_name")),
                    "infra_type": _as_text(row.get("infra_type")),
                    "nci_id": row.get("id"),
                    "village_name": _as_text(row.get("village_name") or row.get("Village Name")),
                    "locality_name": _as_text(row.get("locality_name") or row.get("localite")),
                }
    _NCI_LABEL_CACHE = index
    _NCI_LABEL_MTIME = mtime
    return index


def enrich_site_labels(site: dict[str, Any] | None) -> dict[str, Any]:
    """Attache village/locality/infra depuis NCI si absents, puis résout display_name."""
    out = dict(site or {})
    site_name = _as_text(out.get("site_name") or out.get("name"))
    if site_name:
        nci = _nci_label_index().get(site_name)
        if nci:
            if not out.get("village_name") and nci.get("village_name"):
                out["village_name"] = nci["village_name"]
            if not out.get("locality_name") and nci.get("locality_name"):
                out["locality_name"] = nci["locality_name"]
            if not out.get("infra_name") and nci.get("infra_name"):
                out["infra_name"] = nci["infra_name"]
            if not out.get("infra_type") and nci.get("infra_type"):
                out["infra_type"] = nci["infra_type"]
            out["nci_id"] = nci.get("nci_id")
            provenance = out.get("provenance") if isinstance(out.get("provenance"), dict) else {}
            provenance["nci_uncovered"] = True
            if nci.get("infra_name"):
                provenance["label_enrichment"] = "nci.infra_name"
            out["provenance"] = provenance
    return apply_display_name(out)
