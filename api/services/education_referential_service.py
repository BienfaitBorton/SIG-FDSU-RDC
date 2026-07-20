"""Projection métier Éducation, dérivée sans réécriture du référentiel CENI.

Perf Phase 2D :
- projection SCHOOL mappable mise en cache (mémoire + fichier slim) ;
- invalidation par signature mtime/size du registre CENI ;
- build one-shot thread-safe ;
- nearest reste bbox + Haversine (résultats métier inchangés).
"""

from __future__ import annotations

import json
import threading
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

from api.services import ceni_registry_service
from api.services import referential_runtime_cache as rrc
from app.referentials.ceni_official.service import (
    MAPPABLE_GEOMETRY_STATUSES,
    REGISTRY_PATH,
    SENTINEL_COORDINATES_STATUS,
)

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "data" / "business" / "education_referential_v1.json"
PROJECTION_CACHE_PATH = ROOT / "data" / "cache" / "education_mappable_schools_v1.json"

_SCHOOLS_LOCK = threading.RLock()
_SCHOOLS_MEM: tuple[dict[str, Any], ...] | None = None
_SCHOOLS_SIG: tuple[Any, ...] | None = None
_SCHOOLS_STATS: dict[str, Any] = {
    "BUILDS": 0,
    "MEM_HITS": 0,
    "DISK_HITS": 0,
    "LAST_BUILD_MS": 0.0,
    "LAST_DISK_LOAD_MS": 0.0,
}


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
    if keyword == "COLLEGE":
        return "COLLEGE"
    if keyword == "LYCEE":
        return "LYCEE"
    if keyword in {"UNIVERSITE", "INSTITUT SUPERIEUR"}:
        return "ENSEIGNEMENT_SUPERIEUR"
    if keyword == "MATERNELLE":
        return "MATERNELLE"
    return "AUTRE_ETABLISSEMENT_SCOLAIRE"


def _quality_level(row: dict[str, Any]) -> str:
    if row.get("review_status") == "À vérifier" or row.get("confidence_label_fr") == "Moyenne":
        return "A_VERIFIER"
    return "VALIDE" if row.get("confidence_label_fr") == "Très élevée" else "PROBABLE"


def _project(row: dict[str, Any]) -> dict[str, Any]:
    admin, source = row.get("administrative_attachment") or {}, row.get("source") or {}
    return {
        "education_id": f"EDU-{row.get('asset_uid')}",
        "source_id": row.get("asset_uid"),
        "source_system": "CENI",
        "original_name": row.get("name"),
        "normalized_name": row.get("normalized_name"),
        "business_category": "ETABLISSEMENT_SCOLAIRE",
        "education_subtype": _subtype(row),
        "latitude": row.get("latitude"),
        "longitude": row.get("longitude"),
        "province": admin.get("province"),
        "territory": admin.get("territory"),
        "collectivity": admin.get("collectivity"),
        "groupement": admin.get("groupement"),
        "locality": admin.get("locality"),
        "classification_engine": row.get("engine_version"),
        "matched_rule": row.get("matched_rule_id"),
        "matched_keyword": row.get("matched_keyword"),
        "confidence": row.get("classification_confidence"),
        "confidence_label": row.get("confidence_label_fr"),
        "validation_status": _quality_level(row),
        "provenance": {
            "source": "CENI",
            "source_file": source.get("file"),
            "source_sha256": source.get("sha256"),
            "derived_projection": True,
            "official_ministry_registry": False,
        },
    }


def statistics() -> dict[str, Any]:
    config = configuration()
    assets = ceni_registry_service.registry().get("assets", [])
    quarantined_school_candidates = sum(
        row.get("normalized_category") == "SCHOOL" and row.get("geometry_status") == SENTINEL_COORDINATES_STATUS
        for row in assets
    )
    return {
        "_meta": config["_meta"],
        "sources": config["sources"],
        "future_source_types": config["future_source_types"],
        **config["statistics"],
        "quarantined_school_candidates": quarantined_school_candidates,
        "quality_rules": config["quality_rules"],
    }


def list_establishments(
    *,
    subtype: str | None = None,
    quality: str | None = None,
    province: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    rows = (
        _project(row)
        for row in ceni_registry_service.registry().get("assets", [])
        if row.get("normalized_category") == "SCHOOL" and row.get("geometry_status") in MAPPABLE_GEOMETRY_STATUSES
    )
    selected = [
        row
        for row in rows
        if (not subtype or row["education_subtype"] == subtype)
        and (not quality or row["validation_status"] == quality)
        and (not province or row.get("province") == province)
    ]
    summary = statistics()
    return {
        "total": len(selected),
        "classified_total": summary["establishments"],
        "quarantined_school_candidates": summary["quarantined_school_candidates"],
        "offset": offset,
        "limit": limit,
        "establishments": selected[offset : offset + limit],
        "_meta": configuration()["_meta"],
    }


def education_cache_stats() -> dict[str, Any]:
    with _SCHOOLS_LOCK:
        return {
            **_SCHOOLS_STATS,
            "mem_loaded": _SCHOOLS_MEM is not None,
            "mem_count": len(_SCHOOLS_MEM or ()),
            "projection_path": str(PROJECTION_CACHE_PATH),
            "projection_exists": PROJECTION_CACHE_PATH.exists(),
        }


def clear_education_caches(*, clear_disk: bool = False) -> None:
    """Tests / invalidation explicite — n'efface pas le disque par défaut."""
    global _SCHOOLS_MEM, _SCHOOLS_SIG
    with _SCHOOLS_LOCK:
        _SCHOOLS_MEM = None
        _SCHOOLS_SIG = None
        for k in list(_SCHOOLS_STATS):
            if isinstance(_SCHOOLS_STATS[k], (int, float)):
                _SCHOOLS_STATS[k] = 0 if isinstance(_SCHOOLS_STATS[k], int) else 0.0
        if clear_disk and PROJECTION_CACHE_PATH.exists():
            try:
                PROJECTION_CACHE_PATH.unlink()
            except OSError:
                pass
    configuration.cache_clear()


def _registry_signature() -> tuple[Any, ...]:
    return rrc.file_signature(REGISTRY_PATH)


def _sig_as_list(sig: tuple[Any, ...]) -> list[Any]:
    # JSON-serializable form of file_signature tuples
    out: list[Any] = []
    for item in sig:
        if isinstance(item, tuple):
            out.append(list(item))
        else:
            out.append(item)
    return out


def _sig_from_meta(meta_sig: Any) -> tuple[Any, ...] | None:
    if not isinstance(meta_sig, list):
        return None
    converted: list[Any] = []
    for item in meta_sig:
        if isinstance(item, list):
            converted.append(tuple(item))
        else:
            converted.append(item)
    return tuple(converted)


def _build_schools_from_ceni() -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
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


def _try_load_disk_projection(sig: tuple[Any, ...]) -> tuple[dict[str, Any], ...] | None:
    if not PROJECTION_CACHE_PATH.exists():
        return None
    try:
        t0 = time.perf_counter()
        # Lecture directe (hors rrc JSON partagé) — payload dédié projection
        doc = json.loads(PROJECTION_CACHE_PATH.read_text(encoding="utf-8"))
        load_ms = (time.perf_counter() - t0) * 1000.0
        meta = doc.get("_meta") or {}
        disk_sig = _sig_from_meta(meta.get("signature"))
        if disk_sig != sig:
            return None
        establishments = doc.get("establishments")
        if not isinstance(establishments, list):
            return None
        _SCHOOLS_STATS["DISK_HITS"] += 1
        _SCHOOLS_STATS["LAST_DISK_LOAD_MS"] = round(load_ms, 1)
        return tuple(establishments)
    except Exception:
        return None


def _persist_disk_projection(sig: tuple[Any, ...], rows: tuple[dict[str, Any], ...]) -> None:
    try:
        PROJECTION_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "_meta": {
                "engine": "education-mappable-projection-v1",
                "source_registry": str(REGISTRY_PATH),
                "signature": _sig_as_list(sig),
                "count": len(rows),
                "derived_projection": True,
                "official_ministry_registry": False,
            },
            "establishments": list(rows),
        }
        tmp = PROJECTION_CACHE_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        tmp.replace(PROJECTION_CACHE_PATH)
    except Exception:
        pass


def _mappable_schools() -> tuple[dict[str, Any], ...]:
    """Projection SCHOOL mappable — cache mémoire + slim disque, invalidation mtime/size CENI."""
    global _SCHOOLS_MEM, _SCHOOLS_SIG

    sig = _registry_signature()
    with _SCHOOLS_LOCK:
        if _SCHOOLS_MEM is not None and _SCHOOLS_SIG == sig:
            _SCHOOLS_STATS["MEM_HITS"] += 1
            return _SCHOOLS_MEM

        disk = _try_load_disk_projection(sig)
        if disk is not None:
            _SCHOOLS_MEM = disk
            _SCHOOLS_SIG = sig
            return _SCHOOLS_MEM

        t0 = time.perf_counter()
        rows = _build_schools_from_ceni()
        build_ms = (time.perf_counter() - t0) * 1000.0
        _SCHOOLS_MEM = rows
        _SCHOOLS_SIG = sig
        _SCHOOLS_STATS["BUILDS"] += 1
        _SCHOOLS_STATS["LAST_BUILD_MS"] = round(build_ms, 1)
        _persist_disk_projection(sig, rows)
        return _SCHOOLS_MEM


def nearest_establishment(
    lat: float,
    lon: float,
    *,
    radius_m: float = 25_000,
    limit: int = 15,
) -> dict[str, Any]:
    """Établissements éducatifs les plus proches (bbox + Haversine, pas PostGIS)."""
    from api.services.spatial_nearest_utils import nearest_points

    schools = _mappable_schools()
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
