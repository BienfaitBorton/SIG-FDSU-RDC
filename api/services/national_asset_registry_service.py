"""National FDSU Asset Registry v1 — vue métier fédérée, Data First.

Le registre ne copie ni ne corrige les sources officielles. Il construit des
identités stables et explicables au-dessus des référentiels existants.
"""

from __future__ import annotations

import uuid
from collections import Counter
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

from api.services import (
    ccn_operational_service,
    fdsu_sites_import_service,
    program_lifecycle_engine,
    territorial_impact_engine,
)

REGISTRY_VERSION = "nfar-1.0.0"
NAMESPACE = uuid.UUID("9178c4cc-a8ef-4c79-8876-2cfa2781c343")
PROGRAMS = ("sites_40", "sites_300", "sites_20476")

ASSET_TYPE_CATALOG = (
    ("FDSU_SITE", "Sites FDSU", "integrated"),
    ("CCN", "Centres communautaires numériques", "partial"),
    ("TELECOM", "Télécommunications", "federated"),
    ("HEALTH", "Santé", "federated"),
    ("EDUCATION", "Éducation", "unavailable"),
    ("ENERGY", "Énergie", "unavailable"),
    ("ROAD", "Routes", "federated"),
    ("PUBLIC_SERVICE", "Services publics", "unavailable"),
    ("POPULATION", "Population", "federated"),
    ("LOCALITY", "Localités", "federated"),
    ("ECONOMIC_CORRIDOR", "Corridors économiques", "unavailable"),
    ("PRIORITY_ZONE", "Zones prioritaires", "unavailable"),
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_uuid(source: str, business_code: str) -> str:
    return str(uuid.uuid5(NAMESPACE, f"{source}:{business_code}"))


def _site_code(program: str, row: dict[str, Any], index: int) -> str:
    return str(
        row.get("site_code")
        or row.get("business_id")
        or row.get("code")
        or f"{program.upper()}_{index + 1:05d}"
    )


def _source_meta(program: str, payload: dict[str, Any]) -> dict[str, Any]:
    meta = payload.get("_meta") or {}
    source = meta.get("source_csv") or meta.get("source_kmz") or meta.get("source_matrix")
    return {
        "id": program,
        "path": source,
        "version": meta.get("schema_version") or "source-current",
        "integrated_at": meta.get("imported_at"),
        "producer": "FDSU RDC",
        "confidence": "high" if source else "medium",
    }


def _territory(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "zone_fdsu": row.get("zone") or row.get("zone_fdsu"),
        "province": row.get("province"),
        "territoire": row.get("territoire"),
        "secteur": row.get("secteur"),
        "chefferie": row.get("chefferie"),
        "collectivite": row.get("collectivite"),
        "groupement": row.get("groupement"),
        "localite": row.get("localite"),
        "village": row.get("village"),
    }


def _site_asset(program: str, row: dict[str, Any], index: int, payload: dict[str, Any]) -> dict[str, Any]:
    code = _site_code(program, row, index)
    source = _source_meta(program, payload)
    lat, lon = row.get("latitude"), row.get("longitude")
    population = row.get("population")
    return {
        "uuid": _stable_uuid(program, code),
        "business_code": code,
        "program": program,
        "asset_type": "FDSU_SITE",
        "asset_subtype": row.get("phase") or (payload.get("_meta") or {}).get("phase"),
        "name": row.get("site_name") or row.get("name") or code,
        "source": source,
        "version": source["version"],
        "integrated_at": source["integrated_at"],
        "author": source["producer"],
        "confidence": source["confidence"],
        "data_status": "integrated" if lat is not None and lon is not None else "partial",
        "territory": _territory(row),
        "location": {"latitude": lat, "longitude": lon, "altitude": row.get("altitude")},
        "population": {
            "total": population,
            "covered": None,
            "uncovered": None,
            "households": None,
            "localities_covered": None,
            "localities_uncovered": None,
            "source": source["path"] if population is not None else None,
            "as_of": source["integrated_at"],
            "confidence": source["confidence"] if population is not None else "unknown",
        },
        "fdsu_decision": {
            "priority": row.get("priority_status") or row.get("priority_level"),
            "class": row.get("priority_class") or row.get("classification"),
            "score": row.get("fdsu_score") or row.get("priority_score"),
            "criteria": row.get("criteria"),
            "justification": row.get("justification"),
            "engine_reference": "Decision Engine / matrice officielle",
        },
        "ccn_readiness": {
            "candidate": None,
            "reason": None,
            "proposed_type": None,
            "expected_services": None,
            "score": None,
            "justification": None,
            "status": "structure_prepared_no_ccn_engine",
        },
        "raw_reference": {"program": program, "index": index, "site_id": row.get("site_id")},
    }


@lru_cache(maxsize=3)
def _program_payload(program: str) -> dict[str, Any]:
    return fdsu_sites_import_service.load_program_sites(program)


def _program_assets(program: str) -> list[dict[str, Any]]:
    payload = _program_payload(program)
    return [_site_asset(program, row, index, payload) for index, row in enumerate(payload.get("sites") or [])]


def _ccn_assets() -> list[dict[str, Any]]:
    payload = ccn_operational_service.list_ccn(limit=10000)
    rows = payload.get("items") or payload.get("ccn") or []
    assets = []
    for index, row in enumerate(rows):
        code = str(row.get("ccn_id") or row.get("id") or f"CCN-{index + 1:05d}")
        assets.append({
            "uuid": _stable_uuid("ccn", code), "business_code": code, "program": "ccn",
            "asset_type": "CCN", "asset_subtype": row.get("type"), "name": row.get("name") or row.get("nom") or code,
            "source": {"id": "ccn", "path": "data/programs/ccn/demo_ccn.json", "version": "demo-current", "integrated_at": None, "producer": "FDSU RDC", "confidence": "low"},
            "version": "demo-current", "integrated_at": None, "author": "FDSU RDC", "confidence": "low",
            "data_status": "demonstration", "territory": _territory(row),
            "location": {"latitude": row.get("latitude"), "longitude": row.get("longitude"), "altitude": row.get("altitude")},
            "population": {"total": None, "covered": None, "uncovered": None, "households": None, "localities_covered": None, "localities_uncovered": None, "source": None, "as_of": None, "confidence": "unknown"},
            "fdsu_decision": {"priority": None, "class": None, "score": None, "criteria": None, "justification": None, "engine_reference": None},
            "ccn_readiness": {"candidate": True, "reason": "Actif issu du registre CCN de démonstration", "proposed_type": row.get("type"), "expected_services": row.get("services"), "score": row.get("priority_score"), "justification": row.get("justification"), "status": "demonstration_to_validate"},
            "raw_reference": {"program": "ccn", "index": index},
        })
    return assets


@lru_cache(maxsize=1)
def _all_assets() -> list[dict[str, Any]]:
    assets: list[dict[str, Any]] = []
    for program in PROGRAMS:
        assets.extend(_program_assets(program))
    assets.extend(_ccn_assets())
    return assets


def list_assets(*, program: str | None = None, asset_type: str | None = None, province: str | None = None, q: str | None = None, limit: int = 100, offset: int = 0) -> dict[str, Any]:
    items = _all_assets()
    if program: items = [a for a in items if a["program"] == program]
    if asset_type: items = [a for a in items if a["asset_type"] == asset_type.upper()]
    if province: items = [a for a in items if str(a["territory"].get("province") or "").lower() == province.lower()]
    if q:
        needle = q.lower()
        items = [a for a in items if needle in a["business_code"].lower() or needle in a["name"].lower()]
    total = len(items)
    return {"_meta": {"registry": REGISTRY_VERSION, "total": total, "count": len(items[offset:offset + limit]), "offset": offset, "limit": limit}, "assets": items[offset:offset + limit]}


def get_asset(asset_id: str) -> dict[str, Any] | None:
    needle = str(asset_id)
    for asset in _all_assets():
        if asset["uuid"] == needle or asset["business_code"] == needle:
            return asset
    return None


def relationships(asset_id: str) -> dict[str, Any] | None:
    asset = get_asset(asset_id)
    if not asset: return None
    relations = []
    territory = asset["territory"]
    for key in ("zone_fdsu", "province", "territoire", "collectivite", "groupement", "localite", "village"):
        if territory.get(key):
            relations.append({"type": "LOCATED_IN", "target_type": key.upper(), "target_label": territory[key], "source": asset["source"], "explanation": f"Rattachement {key} fourni par la source de l’actif."})
    return {"asset_uuid": asset["uuid"], "relationships": relations, "count": len(relations), "note": "Relations limitées aux liens réellement documentés ; le NSME reste le moteur des proximités calculées."}


def population(asset_id: str) -> dict[str, Any] | None:
    asset = get_asset(asset_id)
    return None if not asset else {"asset_uuid": asset["uuid"], "population": asset["population"], "explainability": explainability(asset_id, field="population")}


def lifecycle(asset_id: str) -> dict[str, Any] | None:
    asset = get_asset(asset_id)
    if not asset: return None
    return program_lifecycle_engine.resolve_asset_lifecycle(program_code=asset["program"], asset_id=asset["business_code"], raw_status=asset.get("data_status"), asset_type=asset["asset_type"])


def impact(asset_id: str) -> dict[str, Any] | None:
    asset = get_asset(asset_id)
    if not asset: return None
    if asset["asset_type"] != "FDSU_SITE": return {"asset_uuid": asset["uuid"], "status": "not_available", "reason": "Impact non calculé pour ce type d’actif."}
    result = territorial_impact_engine.build_site_impact_profile(asset["raw_reference"].get("site_id") or asset["business_code"], program_code=asset["program"])
    return result or {"asset_uuid": asset["uuid"], "status": "not_available", "reason": "Aucun profil d’impact calculable depuis les données disponibles."}


def explainability(asset_id: str, field: str | None = None) -> dict[str, Any] | None:
    asset = get_asset(asset_id)
    if not asset: return None
    return {"asset_uuid": asset["uuid"], "field": field, "why": "Valeur fédérée depuis le référentiel source sans transformation métier.", "source": asset["source"], "engine": "National FDSU Asset Registry", "official_document": asset["source"].get("path"), "rule": "Data First — conserver null lorsqu’une valeur n’est pas documentée.", "calculation": None, "generated_at": _now()}


def statistics() -> dict[str, Any]:
    assets = _all_assets()
    by_type = Counter(a["asset_type"] for a in assets)
    by_program = Counter(a["program"] for a in assets)
    by_province = Counter(a["territory"].get("province") or "Non renseignée" for a in assets)
    documented_population = sum(1 for a in assets if a["population"].get("total") is not None)
    geolocated = sum(1 for a in assets if a["location"].get("latitude") is not None and a["location"].get("longitude") is not None)
    return {"_meta": {"registry": REGISTRY_VERSION, "generated_at": _now()}, "total_assets": len(assets), "by_type": dict(by_type), "by_program": dict(by_program), "by_province": dict(by_province), "data_quality": {"geolocated": geolocated, "geolocation_rate": round(geolocated * 100 / len(assets), 2) if assets else None}, "population": {"assets_documented": documented_population, "assets_remaining": len(assets) - documented_population, "coverage_national": None}, "asset_types": [{"code": code, "label": label, "status": status, "count": by_type.get(code) if status != "unavailable" else None} for code, label, status in ASSET_TYPE_CATALOG]}


def manifest() -> dict[str, Any]:
    return {"name": "National FDSU Asset Registry", "version": REGISTRY_VERSION, "principles": ["Data First", "No Black Box", "No invented data", "Federation without source duplication"], "programs": list(PROGRAMS) + ["ccn"], "asset_types": [{"code": c, "label": l, "status": s} for c, l, s in ASSET_TYPE_CATALOG]}
