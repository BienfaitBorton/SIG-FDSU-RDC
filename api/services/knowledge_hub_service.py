"""FDSU Knowledge Hub — connaissance métier consolidée (sans calcul de recommandation).

Distinct du Référentiel National (identité des actifs) et du moteur décisionnel.
Répond à : « Que sait-on de ce territoire ou de cet actif ? »
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_DIR = PROJECT_ROOT / "data" / "knowledge"
DOMAINS_PATH = KNOWLEDGE_DIR / "domains.json"
INDICATORS_PATH = KNOWLEDGE_DIR / "national_indicators.json"
DOCTRINE_CATALOG_PATH = PROJECT_ROOT / "data" / "business" / "doctrines" / "catalog.json"

INTEGRATION_POINTS: dict[str, dict[str, str]] = {
    "master_registry": {
        "component": "Référentiel National des Actifs",
        "role": "Identité des actifs ; le Hub enrichit la connaissance associée",
        "api_hint": "/api/master",
    },
    "prioritization": {
        "component": "Moteur de priorisation nationale",
        "role": "Consomme indicateurs / critères documentés (NIF + matrices)",
        "api_hint": "/api/decision/sites/priorities",
    },
    "ccn": {
        "component": "Capability CCN",
        "role": "Module opérationnel CCN + doctrine métier versionnée",
        "api_hint": "/api/ccn",
    },
    "territorial_intelligence": {
        "component": "Territorial Intelligence Explorer",
        "role": "Profil territorial consolidé et recommandations explicables",
        "api_hint": "/api/territorial-intelligence",
    },
    "coverage_intelligence": {
        "component": "National Coverage Intelligence",
        "role": "Référentiel National des Besoins — population, localités, NDCI",
        "api_hint": "/api/coverage",
    },
    "executive_cockpit": {
        "component": "Salle de Pilotage DG / EDVS",
        "role": "KPI et graphiques exécutifs nationaux",
        "api_hint": "/api/executive/cockpit",
    },
    "edvs": {
        "component": "Executive Data Visualization System",
        "role": "Visualisations exécutives alimentées par NCI",
        "api_hint": "/api/coverage/edvs",
    },
    "decision_engine": {
        "component": "Explainable Decision Engine",
        "role": "Recommandations enrichies par besoins NCI",
        "api_hint": "/api/decision",
    },
    "geocoding": {
        "component": "Géocodage Intelligent FDSU",
        "role": "Qualité de localisation → connaissance territoriale",
        "api_hint": "/api/geocoding",
    },
    "telecom": {
        "component": "Référentiel Télécommunications",
        "role": "Alimente le domaine connectivité",
        "api_hint": "/api/telecom",
    },
    "health": {
        "component": "Référentiel Santé",
        "role": "Alimente le domaine services publics (santé)",
        "api_hint": "/api/health",
    },
    "cartography": {
        "component": "Cartographie / SIG",
        "role": "Visualisation des couches liées aux domaines",
        "api_hint": "/map/layers/{layer}",
    },
    "decision_center": {
        "component": "Centre de Décision",
        "role": "Lit la connaissance ; ne la calcule pas dans le Hub",
        "api_hint": "/api/decision",
    },
    "reference": {
        "component": "National Reference Framework",
        "role": "Référentiels sectoriels",
        "api_hint": "/api/reference",
    },
    "programs": {
        "component": "Programmes FDSU",
        "role": "Sites, vagues, programmes",
        "api_hint": "/api/programs",
    },
}


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def list_domains() -> dict[str, Any]:
    payload = _load_json(DOMAINS_PATH)
    domains = list(payload.get("domains") or [])
    return {
        "_meta": {
            **(payload.get("_meta") or {}),
            "title": "FDSU Knowledge Hub — Domaines",
            "count": len(domains),
            "hub_role": "Que sait-on de ce territoire ou de cet actif ?",
        },
        "domains": domains,
    }


def get_domain(domain_id: str) -> dict[str, Any] | None:
    needle = str(domain_id or "").strip().lower()
    for domain in list_domains().get("domains") or []:
        if str(domain.get("id") or "").lower() == needle:
            integrations = []
            for target in domain.get("integration_targets") or []:
                point = INTEGRATION_POINTS.get(target)
                if point:
                    integrations.append({"target": target, **point})
                else:
                    integrations.append({"target": target, "role": "point d'extension prévu"})
            payload: dict[str, Any] = {
                "domain": domain,
                "integrations": integrations,
                "_meta": {
                    "computes_recommendations": False,
                    "note": "Knowledge Hub structure la connaissance ; pas de recommandation ici.",
                },
            }
            if needle == "business_doctrine":
                catalog = _load_json(DOCTRINE_CATALOG_PATH)
                payload["doctrine_catalog"] = catalog.get("doctrines") or []
                payload["_meta"]["doctrine_catalog_path"] = "data/business/doctrines/catalog.json"
                payload["_meta"]["active_doctrine_api"] = "/api/ccn/doctrine"
            if needle == "national_coverage":
                try:
                    from api.services import coverage_intelligence_service as nci

                    payload["coverage"] = nci.knowledge_domain_payload()
                    payload["_meta"]["api"] = "/api/coverage"
                    payload["_meta"]["heritage"] = "Référentiel National des Besoins"
                except Exception as exc:  # noqa: BLE001
                    payload["_meta"]["coverage_error"] = str(exc)
            return payload
    return None


def list_indicators(
    *,
    family: str | None = None,
    domain_id: str | None = None,
) -> dict[str, Any]:
    payload = _load_json(INDICATORS_PATH)
    indicators = list(payload.get("indicators") or [])
    if family:
        fam = family.strip().lower()
        indicators = [item for item in indicators if str(item.get("family") or "").lower() == fam]
    if domain_id:
        dom = domain_id.strip().lower()
        indicators = [item for item in indicators if str(item.get("domain_id") or "").lower() == dom]
    families = sorted({str(item.get("family")) for item in (payload.get("indicators") or []) if item.get("family")})
    return {
        "_meta": {
            **(payload.get("_meta") or {}),
            "title": "National Indicators Framework",
            "count": len(indicators),
            "families": families,
            "values_included": False,
        },
        "indicators": indicators,
    }


def get_indicator(indicator_id: str) -> dict[str, Any] | None:
    needle = str(indicator_id or "").strip().upper()
    for item in list_indicators().get("indicators") or []:
        if str(item.get("id") or "").upper() == needle:
            domain = get_domain(str(item.get("domain_id") or ""))
            return {
                "indicator": item,
                "domain": (domain or {}).get("domain"),
                "_meta": {
                    "value_status": item.get("value_status"),
                    "computes_recommendations": False,
                },
            }
    return None


def integration_points() -> dict[str, Any]:
    return {
        "_meta": {
            "title": "Points de connexion Knowledge Hub",
            "note": "Préparation d'intégration — services existants non modifiés.",
        },
        "points": [
            {"target": key, **value}
            for key, value in INTEGRATION_POINTS.items()
        ],
    }


def hub_manifest() -> dict[str, Any]:
    domains = list_domains()
    indicators = list_indicators()
    return {
        "_meta": {
            "title": "FDSU Knowledge Hub",
            "architecture_doc": "PROJECT_MANAGEMENT/ARCHITECTURE/FDSU_KNOWLEDGE_HUB.md",
            "distinct_from": {
                "master_registry": "Identité des actifs",
                "decision_engine": "Décisions et recommandations",
                "knowledge_cnct": "Centre de connaissances historique (/knowledge)",
            },
            "computes_recommendations": False,
            "territorial_intelligence_engine": "v1_explorer",
        },
        "domains_count": domains["_meta"]["count"],
        "indicators_count": indicators["_meta"]["count"],
        "integration_points": list(INTEGRATION_POINTS.keys()),
    }
