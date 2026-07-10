"""Module opérationnel CCN v1 — lecture doctrine versionnée + données démo.

Les pondérations et règles viennent de data/business/doctrines/ccn_doctrine_v1.json.
Aucune pondération métier n'est codée en dur ici.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCTRINE_PATH = PROJECT_ROOT / "data" / "business" / "doctrines" / "ccn_doctrine_v1.json"
TYPES_PATH = PROJECT_ROOT / "data" / "business" / "ccn_types.json"
DEMO_PATH = PROJECT_ROOT / "data" / "programs" / "ccn" / "demo_ccn.json"

STATUS_BUCKETS = {
    "planned": "planifies",
    "preparation": "preparation",
    "deploying": "deploiement",
    "operational": "operationnels",
    "suspended": "suspendus",
    "maintenance": "maintenance",
    "archived": "archives",
}


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_doctrine() -> dict[str, Any]:
    return _load_json(DOCTRINE_PATH)


def load_ccn_types() -> dict[str, Any]:
    return _load_json(TYPES_PATH)


def _raw_demo_records() -> list[dict[str, Any]]:
    payload = _load_json(DEMO_PATH)
    return list(payload.get("ccn") or [])


def _type_index() -> dict[str, dict[str, Any]]:
    payload = load_ccn_types()
    return {str(item.get("code")): item for item in payload.get("types") or []}


def _priority_level(score: float, doctrine: dict[str, Any]) -> str:
    levels = (doctrine.get("priority_matrix") or {}).get("levels") or []
    for level in levels:
        if float(level.get("min_score", 0)) <= score <= float(level.get("max_score", 100)):
            return str(level.get("id") or "low")
    return "low"


def compute_priority_score(record: dict[str, Any], doctrine: dict[str, Any] | None = None) -> dict[str, Any]:
    """Score CCN à partir des critères/pondérations de la doctrine (non hardcodés)."""
    doctrine = doctrine or load_doctrine()
    criteria = doctrine.get("selection_criteria") or []
    scores = record.get("criteria_scores") or {}
    details = []
    total = 0.0
    weight_sum = 0.0
    for criterion in criteria:
        cid = criterion.get("id")
        weight = float(criterion.get("weight") or 0)
        raw = float(scores.get(cid, 0))
        contribution = raw * weight
        total += contribution
        weight_sum += weight
        details.append(
            {
                "criterion_id": cid,
                "label": criterion.get("label"),
                "weight": weight,
                "weight_percent": criterion.get("weight_percent"),
                "score": raw,
                "contribution": round(contribution, 2),
            }
        )
    # Normalisation de sécurité si la doctrine évolue
    priority_score = round(total / weight_sum, 1) if weight_sum else 0.0
    level = _priority_level(priority_score, doctrine)

    opposability = []
    for rule in doctrine.get("opposability_rules") or []:
        applied = False
        note = None
        rid = rule.get("id")
        if rid == "RULE_CONNECTIVITY_SITES_FIRST" and record.get("site_fdsu_code"):
            applied = True
            note = "CCN lié à un Site FDSU — règle connectivité appliquée."
        if rid == "RULE_SECURITY_CONSTRAINTS" and record.get("security_constraint"):
            applied = True
            note = "Contrainte sécuritaire signalée — arbitrage manuel requis."
        if rid == "RULE_SERVICE_UNIVERSAL_FIRST":
            suf = float((record.get("criteria_scores") or {}).get("CRIT_SERVICE_UNIVERSAL_FIRST") or 0)
            if suf >= 80:
                applied = True
                note = "Score Service Universal First élevé."
        if rid == "RULE_HIGHER_PRIORITY_WINS":
            applied = True
            note = f"Niveau retenu: {level}."
        opposability.append(
            {
                "rule_id": rid,
                "label": rule.get("label"),
                "applied": applied,
                "note": note,
                "version": rule.get("version"),
            }
        )

    return {
        "priority_score": priority_score,
        "priority_level": level,
        "criteria_details": details,
        "opposability": opposability,
        "doctrine_version": (doctrine.get("_meta") or {}).get("version"),
        "doctrine_id": (doctrine.get("_meta") or {}).get("doctrine_id"),
    }


def _enrich(record: dict[str, Any], doctrine: dict[str, Any] | None = None) -> dict[str, Any]:
    doctrine = doctrine or load_doctrine()
    item = deepcopy(record)
    type_meta = _type_index().get(str(item.get("ccn_type") or ""), {})
    scoring = compute_priority_score(item, doctrine)
    item.update(
        {
            "demo": True,
            "data_class": "demonstration",
            "asset_type": "CCN",
            "ccn_type_label": type_meta.get("label") or item.get("ccn_type"),
            "ccn_type_short": type_meta.get("short_label") or item.get("ccn_type"),
            **scoring,
            "sections": {
                "identification": {
                    "business_id": item.get("business_id"),
                    "name": item.get("name"),
                    "ccn_type": item.get("ccn_type"),
                    "status": item.get("status"),
                    "program_code": item.get("program_code"),
                },
                "localisation": {
                    "province": item.get("province"),
                    "territoire": item.get("territoire"),
                    "zone": item.get("zone"),
                    "latitude": item.get("latitude"),
                    "longitude": item.get("longitude"),
                    "host_type": item.get("host_type"),
                },
                "connectivite": {
                    "site_fdsu_code": item.get("site_fdsu_code"),
                    "site_fdsu_name": item.get("site_fdsu_name"),
                },
                "equipements": item.get("equipment") or [],
                "services": item.get("services") or [],
                "exploitation": {"manager": item.get("manager")},
                "maintenance": {"status": item.get("maintenance_status")},
                "population": {"population_served": item.get("population_served")},
                "indicateurs": {
                    "measurement_flags": item.get("measurement_flags") or [],
                    "priority_score": scoring["priority_score"],
                    "priority_level": scoring["priority_level"],
                },
                "impact": {
                    "population_served": item.get("population_served"),
                    "services_count": len(item.get("services") or []),
                },
                "historique": [
                    {
                        "event": "demo_seed",
                        "note": "Enregistrement de démonstration — non production",
                    }
                ],
            },
        }
    )
    return item


def ensure_demo_export() -> Path:
    return DEMO_PATH


def list_ccn(
    *,
    province: str | None = None,
    territoire: str | None = None,
    zone: str | None = None,
    program_code: str | None = None,
    status: str | None = None,
    ccn_type: str | None = None,
    limit: int = 500,
) -> dict[str, Any]:
    doctrine = load_doctrine()
    items = [_enrich(item, doctrine) for item in _raw_demo_records()]
    if province:
        items = [i for i in items if str(i.get("province") or "").lower() == province.lower()]
    if territoire:
        items = [i for i in items if str(i.get("territoire") or "").lower() == territoire.lower()]
    if zone:
        items = [i for i in items if str(i.get("zone") or "").upper() == zone.upper()]
    if program_code:
        items = [i for i in items if str(i.get("program_code") or "") == program_code]
    if status:
        items = [i for i in items if str(i.get("status") or "") == status]
    if ccn_type:
        items = [i for i in items if str(i.get("ccn_type") or "").upper() == ccn_type.upper()]
    items.sort(key=lambda i: (-float(i.get("priority_score") or 0), str(i.get("name") or "")))
    page = items[:limit]
    return {
        "_meta": {
            "title": "Centres Communautaires Numériques",
            "data_class": "demonstration",
            "count": len(page),
            "total": len(items),
            "doctrine_version": (doctrine.get("_meta") or {}).get("version"),
        },
        "ccn": page,
    }


def get_ccn(ccn_id: str) -> dict[str, Any] | None:
    needle = str(ccn_id or "").strip()
    for item in _raw_demo_records():
        if item.get("id") == needle or item.get("business_id") == needle:
            return {"ccn": _enrich(item), "data_class": "demonstration"}
    return None


def statistics() -> dict[str, Any]:
    doctrine = load_doctrine()
    items = [_enrich(item, doctrine) for item in _raw_demo_records()]
    by_status = {key: 0 for key in STATUS_BUCKETS.values()}
    by_province: dict[str, int] = {}
    linked_sites = set()
    population = 0
    for item in items:
        bucket = STATUS_BUCKETS.get(str(item.get("status") or ""), "autres")
        by_status[bucket] = by_status.get(bucket, 0) + 1
        prov = item.get("province") or "Non renseignée"
        by_province[prov] = by_province.get(prov, 0) + 1
        population += int(item.get("population_served") or 0)
        if item.get("site_fdsu_code"):
            linked_sites.add(item["site_fdsu_code"])
    return {
        "_meta": {
            "title": "Statistiques CCN",
            "data_class": "demonstration",
            "doctrine_version": (doctrine.get("_meta") or {}).get("version"),
        },
        "kpis": {
            "total": len(items),
            "planifies": by_status.get("planifies", 0),
            "preparation": by_status.get("preparation", 0),
            "deploiement": by_status.get("deploiement", 0),
            "operationnels": by_status.get("operationnels", 0),
            "population_desservie": population,
            "sites_fdsu_associes": len(linked_sites),
        },
        "by_status": by_status,
        "by_province": dict(sorted(by_province.items(), key=lambda x: (-x[1], x[0]))),
    }


def map_payload(
    *,
    province: str | None = None,
    territoire: str | None = None,
    zone: str | None = None,
    program_code: str | None = None,
    status: str | None = None,
    ccn_type: str | None = None,
) -> dict[str, Any]:
    listed = list_ccn(
        province=province,
        territoire=territoire,
        zone=zone,
        program_code=program_code,
        status=status,
        ccn_type=ccn_type,
        limit=500,
    )
    features = []
    links = []
    for item in listed["ccn"]:
        if item.get("latitude") is None or item.get("longitude") is None:
            continue
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [item["longitude"], item["latitude"]],
                },
                "properties": {
                    "kind": "ccn",
                    "id": item["id"],
                    "business_id": item["business_id"],
                    "name": item["name"],
                    "status": item["status"],
                    "ccn_type": item["ccn_type"],
                    "priority_score": item["priority_score"],
                    "province": item["province"],
                    "site_fdsu_code": item.get("site_fdsu_code"),
                },
            }
        )
        # Point site associé (légèrement décalé si pas de géométrie site réelle en démo)
        if item.get("site_fdsu_code"):
            site_lon = float(item["longitude"]) + 0.08
            site_lat = float(item["latitude"]) + 0.05
            features.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [site_lon, site_lat]},
                    "properties": {
                        "kind": "site_fdsu",
                        "code": item["site_fdsu_code"],
                        "name": item.get("site_fdsu_name"),
                        "linked_ccn": item["id"],
                    },
                }
            )
            links.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [item["longitude"], item["latitude"]],
                            [site_lon, site_lat],
                        ],
                    },
                    "properties": {
                        "kind": "site_ccn_link",
                        "ccn_id": item["id"],
                        "site_fdsu_code": item["site_fdsu_code"],
                    },
                }
            )
    return {
        "_meta": {
            "title": "Carte CCN",
            "data_class": "demonstration",
            "feature_count": len(features) + len(links),
        },
        "geojson": {
            "type": "FeatureCollection",
            "features": features + links,
        },
    }


def doctrine_payload() -> dict[str, Any]:
    doctrine = load_doctrine()
    types = load_ccn_types()
    return {
        "_meta": {
            "title": "Doctrine métier CCN FDSU",
            "version": (doctrine.get("_meta") or {}).get("version"),
            "source_document": (doctrine.get("_meta") or {}).get("source_document"),
            "hardcoded_forbidden": True,
        },
        "doctrine": doctrine,
        "ccn_types": types,
    }
