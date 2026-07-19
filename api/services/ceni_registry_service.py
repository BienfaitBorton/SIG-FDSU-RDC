"""Lecture fichier du Référentiel National CENI v1.0."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from app.referentials.ceni_official.models import CeniCategory
from app.referentials.ceni_official.service import (
    ANOMALY_PATH,
    BATCH_PATH,
    MAPPABLE_GEOMETRY_STATUSES,
    SENTINEL_COORDINATES_STATUS,
    CeniRegistryService,
    apply_quarantine_contract,
)
from api.services.national_semantic_classification_engine import DEFAULT_RULES_PATH


@lru_cache(maxsize=1)
def registry() -> dict[str, Any]:
    document = CeniRegistryService.load()
    rows = document.get("assets", [])
    batch_id = f"CENI-{str(document.get('_meta', {}).get('source_sha256') or '')[:12]}"
    apply_quarantine_contract(rows, batch_id=batch_id, refresh_duplicates=False)
    statistics = document.setdefault("statistics", {})
    geometry_counts: dict[str, int] = {}
    duplicate_counts: dict[str, int] = {}
    for row in rows:
        geometry = str(row.get("geometry_status") or "unknown")
        geometry_counts[geometry] = geometry_counts.get(geometry, 0) + 1
        duplicate = str((row.get("duplicate") or {}).get("status") or "none")
        duplicate_counts[duplicate] = duplicate_counts.get(duplicate, 0) + 1
    statistics["integrated"] = sum(geometry_counts.get(status, 0) for status in MAPPABLE_GEOMETRY_STATUSES)
    statistics["quarantined"] = geometry_counts.get(SENTINEL_COORDINATES_STATUS, 0)
    statistics["quarantine_by_reason"] = {SENTINEL_COORDINATES_STATUS: statistics["quarantined"]}
    statistics["rejected"] = sum(geometry_counts.get(status, 0) for status in {"invalid", "missing", "outside_country"})
    statistics["geometry_quality"] = geometry_counts
    statistics["duplicates"] = duplicate_counts
    statistics["resolution_candidates"] = sum(bool((row.get("quarantine") or {}).get("resolution_candidate")) for row in rows)
    statistics["quarantined_school_candidates"] = sum(row.get("geometry_status") == SENTINEL_COORDINATES_STATUS and row.get("normalized_category") == "SCHOOL" for row in rows)
    return document


def list_sites(*, q: str | None = None, category: str | None = None, province: str | None = None, territory: str | None = None, quality: str | None = None, limit: int = 100, offset: int = 0) -> dict[str, Any]:
    rows = registry().get("assets", [])
    if q:
        needle = q.casefold()
        rows = [row for row in rows if needle in str(row.get("name") or "").casefold() or needle in row["asset_uid"].casefold()]
    if category:
        rows = [row for row in rows if row.get("normalized_category") == category]
    if province:
        rows = [row for row in rows if row.get("administrative_attachment", {}).get("province") == province]
    if territory:
        rows = [row for row in rows if row.get("administrative_attachment", {}).get("territory") == territory]
    if quality:
        rows = [row for row in rows if row.get("geometry_status") == quality]
    total = len(rows)
    return {"total": total, "offset": offset, "limit": limit, "sites": rows[offset : offset + limit], "source_sha256": registry().get("_meta", {}).get("source_sha256")}


def get_site(asset_uid: str) -> dict[str, Any] | None:
    return next((row for row in registry().get("assets", []) if row.get("asset_uid") == asset_uid or row.get("source_record_id") == asset_uid), None)


def statistics() -> dict[str, Any]:
    return {"_meta": registry().get("_meta", {}), **registry().get("statistics", {}), "contract": registry().get("contract", {})}


def data_quality(limit: int = 500, offset: int = 0) -> dict[str, Any]:
    if not ANOMALY_PATH.exists():
        CeniRegistryService().write(registry())
    doc = json.loads(ANOMALY_PATH.read_text(encoding="utf-8"))
    rows_by_uid = {row.get("asset_uid"): row for row in registry().get("assets", [])}
    anomalies = []
    for anomaly in doc.get("anomalies", [])[offset : offset + limit]:
        row = rows_by_uid.get(anomaly.get("asset_uid"), {})
        anomalies.append({**anomaly, "geometry_status": row.get("geometry_status", anomaly.get("geometry_status")), "quarantine": row.get("quarantine")})
    return {"_meta": doc.get("_meta", {}), "total": doc.get("count", 0), "offset": offset, "limit": limit, "anomalies": anomalies}


def categories() -> dict[str, Any]:
    counts = registry().get("statistics", {}).get("categories", {})
    labels = json.loads(DEFAULT_RULES_PATH.read_text(encoding="utf-8"))["categories_fr"]
    return {"categories": [{"id": item.value, "label_fr": labels[item.value], "count": counts.get(item.value, 0)} for item in CeniCategory]}


def classification_statistics() -> dict[str, Any]:
    return {"_meta": registry().get("_meta", {}), **registry().get("statistics", {}).get("classification", {}), "categories": registry().get("statistics", {}).get("categories", {})}


def classification_rules() -> dict[str, Any]:
    return json.loads(DEFAULT_RULES_PATH.read_text(encoding="utf-8"))


def classification_review(limit: int = 100, offset: int = 0) -> dict[str, Any]:
    rows = [row for row in registry().get("assets", []) if row.get("review_status") == "À vérifier"]
    return {"total": len(rows), "offset": offset, "limit": limit, "sites": rows[offset:offset + limit]}


def site_classification(asset_uid: str) -> dict[str, Any] | None:
    row = get_site(asset_uid)
    if row is None:
        return None
    keys = ("source_name", "normalized_name", "source_category", "normalized_category", "normalized_category_label_fr", "classification_method", "matched_rule_id", "matched_keyword", "classification_confidence", "confidence_label_fr", "classification_justification", "engine_version", "classification_date", "review_status", "raw_properties")
    payload = {key: row.get(key) for key in keys}
    payload["source_name"] = row.get("name")
    payload["normalized_category_code"] = payload.pop("normalized_category")
    payload["confidence"] = payload.pop("classification_confidence")
    payload["justification_fr"] = payload.pop("classification_justification")
    return payload


def map_features(*, category: str | None = None, province: str | None = None, limit: int = 5000) -> dict[str, Any]:
    rows = list_sites(category=category, province=province, limit=limit)["sites"]
    features = [{"type": "Feature", "id": row["asset_uid"], "geometry": {"type": "Point", "coordinates": [row["longitude"], row["latitude"]]}, "properties": {"asset_uid": row["asset_uid"], "name": row["name"], "category": row["normalized_category"], "quality": row["geometry_status"], "province": row["administrative_attachment"].get("province"), "institution": "CENI"}} for row in rows if row.get("geometry_status") in MAPPABLE_GEOMETRY_STATUSES and row.get("longitude") is not None and row.get("latitude") is not None and [float(row["longitude"]), float(row["latitude"])] != [0.0, 0.0]]
    return {"type": "FeatureCollection", "features": features, "returned": len(features), "limit": limit}


def import_batches() -> dict[str, Any]:
    return json.loads(BATCH_PATH.read_text(encoding="utf-8")) if BATCH_PATH.exists() else {"batches": []}


@lru_cache(maxsize=1)
def _mappable_signal_points() -> tuple[dict[str, Any], ...]:
    """Points CENI mappables pour signal décisionnel (≠ sites FDSU)."""
    points: list[dict[str, Any]] = []
    for row in registry().get("assets", []):
        if row.get("geometry_status") not in MAPPABLE_GEOMETRY_STATUSES:
            continue
        lat, lon = row.get("latitude"), row.get("longitude")
        if lat is None or lon is None:
            continue
        try:
            if float(lat) == 0.0 and float(lon) == 0.0:
                continue
        except (TypeError, ValueError):
            continue
        admin = row.get("administrative_attachment") or {}
        points.append(
            {
                "asset_uid": row.get("asset_uid"),
                "name": row.get("name") or row.get("normalized_name"),
                "normalized_name": row.get("normalized_name"),
                "normalized_category": row.get("normalized_category"),
                "latitude": float(lat),
                "longitude": float(lon),
                "province": admin.get("province"),
                "territory": admin.get("territory"),
                "institution": "CENI",
                "asset_domain": "INSTITUTIONAL",
                "signal_role": "administrative_centrality",
            }
        )
    return tuple(points)


def nearest_signals(
    lat: float,
    lon: float,
    *,
    radius_m: float = 15_000,
    limit: int = 15,
    exclude_schools: bool = False,
) -> dict[str, Any]:
    """Sites CENI les plus proches — signal institutionnel, jamais un site FDSU."""
    from api.services.spatial_nearest_utils import nearest_points

    pool = list(_mappable_signal_points())
    if exclude_schools:
        pool = [p for p in pool if p.get("normalized_category") != "SCHOOL"]
    hits = nearest_points(lat, lon, pool, radius_m=radius_m, limit=limit)
    return {
        "data_available": bool(pool),
        "search_executed": True,
        "referential_count": len(pool),
        "radius_m": radius_m,
        "limit": limit,
        "source": "CENI registry file (read-only)",
        "not_fdsu_sites": True,
        "calculation_method": "haversine_bbox_ceni",
        "sites": hits,
        "nearest": hits[0] if hits else None,
        "scoring_weighted": False,
        "note": "Signal disponible — non pondéré dans le scoring actuel",
    }
