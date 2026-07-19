"""Projection métier Éducation, dérivée sans réécriture du référentiel CENI."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from api.services import ceni_registry_service
from app.referentials.ceni_official.service import MAPPABLE_GEOMETRY_STATUSES, SENTINEL_COORDINATES_STATUS

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "data" / "business" / "education_referential_v1.json"


@lru_cache(maxsize=1)
def configuration() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _subtype(row: dict[str, Any]) -> str:
    keyword = str(row.get("matched_keyword") or "").upper()
    rule = str(row.get("matched_rule_id") or "").upper()
    if keyword in {"EP", "ECOLE PRIMAIRE"} or rule == "SCHOOL_EP":
        return "ECOLE_PRIMAIRE"
    if keyword in {"INST", "INSTITUT"} or rule == "SCHOOL_INST":
        return "INSTITUT"
    if keyword in {"CS", "COMPLEXE SCOLAIRE"} or rule == "CS_CONTEXT_SCOLAIRE":
        return "COMPLEXE_SCOLAIRE"
    if keyword == "COLLEGE": return "COLLEGE"
    if keyword == "LYCEE": return "LYCEE"
    if keyword in {"UNIVERSITE", "INSTITUT SUPERIEUR"}: return "ENSEIGNEMENT_SUPERIEUR"
    if keyword == "MATERNELLE": return "MATERNELLE"
    return "AUTRE_ETABLISSEMENT_SCOLAIRE"


def _quality_level(row: dict[str, Any]) -> str:
    if row.get("review_status") == "À vérifier" or row.get("confidence_label_fr") == "Moyenne":
        return "A_VERIFIER"
    return "VALIDE" if row.get("confidence_label_fr") == "Très élevée" else "PROBABLE"


def _project(row: dict[str, Any]) -> dict[str, Any]:
    admin, source = row.get("administrative_attachment") or {}, row.get("source") or {}
    return {
        "education_id": f"EDU-{row.get('asset_uid')}", "source_id": row.get("asset_uid"), "source_system": "CENI",
        "original_name": row.get("name"), "normalized_name": row.get("normalized_name"),
        "business_category": "ETABLISSEMENT_SCOLAIRE", "education_subtype": _subtype(row),
        "latitude": row.get("latitude"), "longitude": row.get("longitude"),
        "province": admin.get("province"), "territory": admin.get("territory"), "collectivity": admin.get("collectivity"),
        "groupement": admin.get("groupement"), "locality": admin.get("locality"),
        "classification_engine": row.get("engine_version"), "matched_rule": row.get("matched_rule_id"),
        "matched_keyword": row.get("matched_keyword"), "confidence": row.get("classification_confidence"),
        "confidence_label": row.get("confidence_label_fr"), "validation_status": _quality_level(row),
        "provenance": {"source": "CENI", "source_file": source.get("file"), "source_sha256": source.get("sha256"), "derived_projection": True, "official_ministry_registry": False},
    }


def statistics() -> dict[str, Any]:
    config = configuration()
    assets = ceni_registry_service.registry().get("assets", [])
    quarantined_school_candidates = sum(row.get("normalized_category") == "SCHOOL" and row.get("geometry_status") == SENTINEL_COORDINATES_STATUS for row in assets)
    return {"_meta": config["_meta"], "sources": config["sources"], "future_source_types": config["future_source_types"], **config["statistics"], "quarantined_school_candidates": quarantined_school_candidates, "quality_rules": config["quality_rules"]}


def list_establishments(*, subtype: str | None = None, quality: str | None = None, province: str | None = None, limit: int = 100, offset: int = 0) -> dict[str, Any]:
    rows = (_project(row) for row in ceni_registry_service.registry().get("assets", []) if row.get("normalized_category") == "SCHOOL" and row.get("geometry_status") in MAPPABLE_GEOMETRY_STATUSES)
    selected = [row for row in rows if (not subtype or row["education_subtype"] == subtype) and (not quality or row["validation_status"] == quality) and (not province or row.get("province") == province)]
    summary = statistics()
    return {"total": len(selected), "classified_total": summary["establishments"], "quarantined_school_candidates": summary["quarantined_school_candidates"], "offset": offset, "limit": limit, "establishments": selected[offset:offset + limit], "_meta": configuration()["_meta"]}


@lru_cache(maxsize=1)
def _mappable_schools() -> tuple[dict[str, Any], ...]:
    """Projection SCHOOL mappable — cache mémoire, lecture seule du registre CENI."""
    rows = []
    for row in ceni_registry_service.registry().get("assets", []):
        if row.get("normalized_category") != "SCHOOL":
            continue
        if row.get("geometry_status") not in MAPPABLE_GEOMETRY_STATUSES:
            continue
        projected = _project(row)
        if projected.get("latitude") is None or projected.get("longitude") is None:
            continue
        rows.append(projected)
    return tuple(rows)


def nearest_establishment(
    lat: float,
    lon: float,
    *,
    radius_m: float = 25_000,
    limit: int = 15,
) -> dict[str, Any]:
    """Établissements éducatifs les plus proches (bbox + Haversine, pas PostGIS)."""
    from api.services.spatial_nearest_utils import nearest_points

    schools = list(_mappable_schools())
    hits = nearest_points(lat, lon, schools, radius_m=radius_m, limit=limit)
    return {
        "data_available": bool(schools),
        "search_executed": True,
        "referential_count": len(schools),
        "radius_m": radius_m,
        "limit": limit,
        "source": "CENI SCHOOL projection (derived)",
        "derived_projection": True,
        "official_ministry_registry": False,
        "calculation_method": "haversine_bbox_education",
        "establishments": hits,
        "nearest": hits[0] if hits else None,
    }
