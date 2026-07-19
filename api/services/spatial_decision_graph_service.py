"""Spatial Decision Graph v2.0 — composition NSME + Decision (pas de liens inventés).

Produit un graphe décisionnel territorial explicable pour l’Analyse d’Impact Territorial.
Le nom technique interne reste « Spatial Impact / SDG ».
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

ENGINE_VERSION = "sdg-2.2.0"

# Statuts officiels utilisateur (Data First + No Black Box)
# « operational » = maturité d’intégration référentiel — PAS site/service physiquement opérationnel.
OFFICIAL_STATUS = {
    "operational": {"label": "Référentiel intégré", "code": "operational", "dimension": "data_status"},
    "empty": {"label": "Aucun objet trouvé", "code": "empty", "dimension": "data_status"},
    "integrating": {"label": "En cours d’intégration", "code": "integration_pending", "dimension": "data_status"},
    "error": {"label": "Erreur d’intégration", "code": "error", "dimension": "data_status"},
    "partial": {"label": "Données partielles", "code": "partial", "dimension": "data_status"},
    "demonstration": {"label": "Démonstration / partiel", "code": "demonstration", "dimension": "data_status"},
}

# Catégories UI — certaines futures restent disponibles=False
CATEGORIES: dict[str, dict[str, Any]] = {
    "site": {
        "id": "site",
        "label": "Site étudié",
        "color": "#f59e0b",
        "symbol": "star",
        "available": True,
        "relation_types": [],
    },
    "population": {
        "id": "population",
        "label": "Population / localités",
        "color": "#2563eb",
        "symbol": "people",
        "available": True,
        "relation_types": ["IMPACTS_POPULATION"],
    },
    "localities": {
        "id": "localities",
        "label": "Localités",
        "color": "#3b82f6",
        "symbol": "place",
        "available": True,
        "relation_types": ["SERVES_LOCALITY"],
    },
    "fdsu_sites": {
        "id": "fdsu_sites",
        "label": "Sites FDSU",
        "color": "#b45309",
        "symbol": "site",
        "available": True,
        "relation_types": [
            "NEAR_FDSU_SITE",
            "SAME_PROGRAM",
            "COMPLEMENTS_FDSU_SITE",
            "OVERLAPPING_SERVICE_AREA",
        ],
    },
    "health": {
        "id": "health",
        "label": "Santé",
        "color": "#16a34a",
        "symbol": "health",
        "available": True,
        "relation_types": ["NEAR_HEALTH_FACILITY", "NEAREST_HEALTH_FACILITY", "WITHIN_HEALTH_SERVICE_AREA"],
    },
    "telecom": {
        "id": "telecom",
        "label": "Télécommunications",
        "color": "#06b6d4",
        "symbol": "tower",
        "available": True,
        "relation_types": [
            "NEAR_FIBER",
            "NEAR_BACKBONE",
            "NEAREST_TELECOM_INFRA",
            "NEAREST_FIBER_LINE",
            "NEAREST_MNO_VODACOM",
            "NEAREST_MNO_ORANGE",
            "NEAREST_MNO_AIRTEL",
            "NEAREST_MNO_AFRICELL",
            "NEAREST_FIBER_LINK",
            "NEAREST_MICROWAVE_LINK",
            "MUTUALIZATION_POTENTIAL",
        ],
    },
    "roads": {
        "id": "roads",
        "label": "Routes",
        "color": "#ea580c",
        "symbol": "road",
        "available": True,
        "relation_types": ["NEAR_MAIN_ROAD", "ROAD_ACCESSIBILITY", "WITHIN_ROAD_CORRIDOR"],
    },
    "ccn": {
        "id": "ccn",
        "label": "CCN",
        "color": "#14b8a6",
        "symbol": "hub",
        "available": True,
        "relation_types": ["CONNECTS_CCN", "NEAR_CCN"],
    },
    "admin": {
        "id": "admin",
        "label": "Services administratifs",
        "color": "#64748b",
        "symbol": "building",
        "available": True,
        "relation_types": ["NEAR_ADMINISTRATION", "SAME_ADMINISTRATIVE_AREA"],
    },
    "education": {
        "id": "education",
        "label": "Éducation",
        "color": "#7c3aed",
        "symbol": "school",
        "available": True,
        "relation_types": ["NEAR_SCHOOL", "NEAREST_SCHOOL"],
        "note": "Projection CENI SCHOOL — pas de registre ministériel officiel.",
    },
    "ceni": {
        "id": "ceni",
        "label": "Signal CENI",
        "color": "#475569",
        "symbol": "building",
        "available": True,
        "relation_types": ["NEAREST_CENI_SIGNAL", "NEAR_CENI_SITE"],
        "note": "Signal institutionnel CENI (≠ sites FDSU) — non pondéré dans le scoring.",
    },
    "energy": {
        "id": "energy",
        "label": "Énergie",
        "color": "#ca8a04",
        "symbol": "bolt",
        "available": False,
        "relation_types": [],
        "note": "Énergie — référentiel non encore importé.",
    },
    "markets": {
        "id": "markets",
        "label": "Marchés / économie",
        "color": "#db2777",
        "symbol": "market",
        "available": False,
        "relation_types": ["NEAR_MARKET"],
        "note": "Marchés / économie — référentiel non encore importé.",
    },
    "needs": {
        "id": "needs",
        "label": "Besoins prioritaires",
        "color": "#dc2626",
        "symbol": "alert",
        "available": True,
        "relation_types": ["CANDIDATE_FOR_MISSION", "COVERAGE_NEED", "PRIORITY_NEED"],
    },
}

RELATION_STYLES: dict[str, dict[str, Any]] = {
    "SERVES_LOCALITY": {
        "category": "localities",
        "label": "Localité desservie",
        "color": "#3b82f6",
        "weight": 3,
        "dash": None,
        "why": "Cette localité non couverte se trouve dans le rayon de service du site.",
    },
    "IMPACTS_POPULATION": {
        "category": "population",
        "label": "Impact populationnel",
        "color": "#2563eb",
        "weight": 2,
        "dash": "4 4",
        "why": "Relation d’impact sur la population concernée par l’intervention.",
    },
    "NEAR_FDSU_SITE": {
        "category": "fdsu_sites",
        "label": "Site FDSU voisin",
        "color": "#b45309",
        "weight": 2,
        "dash": "4 4",
        "why": "Un autre site FDSU à proximité peut coordonner ou compléter l’intervention.",
    },
    "SAME_PROGRAM": {
        "category": "fdsu_sites",
        "label": "Même programme FDSU",
        "color": "#92400e",
        "weight": 2,
        "dash": "6 3",
        "why": "Ce site appartient au même programme FDSU que le site étudié.",
    },
    "COMPLEMENTS_FDSU_SITE": {
        "category": "fdsu_sites",
        "label": "Complémentarité de sites",
        "color": "#a16207",
        "weight": 2,
        "dash": "4 4",
        "why": "Les deux sites du même programme peuvent se compléter dans le territoire.",
    },
    "OVERLAPPING_SERVICE_AREA": {
        "category": "fdsu_sites",
        "label": "Zones de service qui se chevauchent",
        "color": "#b45309",
        "weight": 1,
        "dash": "2 4",
        "why": "Les rayons de service des deux sites se chevauchent — risque de redondance ou opportunité de coordination.",
    },
    "CANDIDATE_FOR_MISSION": {
        "category": "needs",
        "label": "Besoin critique / mission",
        "color": "#dc2626",
        "weight": 3,
        "dash": "6 3",
        "why": "Ce besoin justifie une mission prioritaire autour du site.",
    },
    "NEAR_HEALTH_FACILITY": {
        "category": "health",
        "label": "Proximité santé",
        "color": "#16a34a",
        "weight": 2,
        "dash": None,
        "why": "Un établissement de santé du référentiel national se trouve dans le rayon de proximité configuré.",
    },
    "NEAREST_HEALTH_FACILITY": {
        "category": "health",
        "label": "Établissement de santé le plus proche",
        "color": "#15803d",
        "weight": 3,
        "dash": None,
        "why": "Établissement de santé le plus proche du site — accessibilité sanitaire de référence.",
    },
    "WITHIN_HEALTH_SERVICE_AREA": {
        "category": "health",
        "label": "Dans la zone de service santé",
        "color": "#22c55e",
        "weight": 2,
        "dash": "4 4",
        "why": "Le site se trouve dans la zone de service sanitaire configurée autour de l’établissement.",
    },
    "NEAR_SCHOOL": {
        "category": "education",
        "label": "Proximité école",
        "color": "#7c3aed",
        "weight": 2,
        "dash": "4 4",
        "why": "Un établissement éducatif (projection CENI SCHOOL) se trouve dans le rayon de proximité.",
    },
    "NEAREST_SCHOOL": {
        "category": "education",
        "label": "Établissement éducatif le plus proche",
        "color": "#6d28d9",
        "weight": 3,
        "dash": None,
        "why": "Établissement éducatif le plus proche du site — signal social (non pondéré si critère moteur à poids 0).",
    },
    "NEAREST_CENI_SIGNAL": {
        "category": "ceni",
        "label": "Signal CENI le plus proche",
        "color": "#475569",
        "weight": 2,
        "dash": None,
        "why": "Site institutionnel CENI le plus proche — présence administrative / humaine (≠ site FDSU).",
    },
    "NEAR_CENI_SITE": {
        "category": "ceni",
        "label": "Proximité site CENI",
        "color": "#64748b",
        "weight": 1,
        "dash": "4 4",
        "why": "Un site CENI se trouve dans le rayon de proximité — signal de centralité locale.",
    },
    "NEAREST_MNO_VODACOM": {
        "category": "telecom",
        "label": "Vodacom le plus proche",
        "color": "#e11d48",
        "weight": 2,
        "dash": None,
        "why": "Site Vodacom le plus proche du site FDSU étudié.",
    },
    "NEAREST_MNO_ORANGE": {
        "category": "telecom",
        "label": "Orange le plus proche",
        "color": "#f97316",
        "weight": 2,
        "dash": None,
        "why": "Site Orange le plus proche du site FDSU étudié.",
    },
    "NEAREST_MNO_AIRTEL": {
        "category": "telecom",
        "label": "Airtel le plus proche",
        "color": "#ef4444",
        "weight": 2,
        "dash": None,
        "why": "Site Airtel le plus proche (référentiel FDSU MNO / NIRE).",
    },
    "NEAREST_MNO_AFRICELL": {
        "category": "telecom",
        "label": "Africell le plus proche",
        "color": "#a855f7",
        "weight": 2,
        "dash": None,
        "why": "Site Africell le plus proche (référentiel FDSU MNO / NIRE).",
    },
    "NEAREST_FIBER_LINK": {
        "category": "telecom",
        "label": "Fibre la plus proche",
        "color": "#0891b2",
        "weight": 3,
        "dash": None,
        "why": "Tronçon fibre le plus proche — candidat backhaul.",
    },
    "NEAREST_MICROWAVE_LINK": {
        "category": "telecom",
        "label": "MW le plus proche",
        "color": "#0e7490",
        "weight": 2,
        "dash": "4 4",
        "why": "Lien micro-ondes le plus proche — alternative backhaul.",
    },
    "MUTUALIZATION_POTENTIAL": {
        "category": "telecom",
        "label": "Potentiel de mutualisation",
        "color": "#155e75",
        "weight": 2,
        "dash": "6 3",
        "why": "Plusieurs opérateurs et/ou backhaul proches — opportunité de mutualisation.",
    },
    "NEAR_MARKET": {
        "category": "markets",
        "label": "Proximité marché",
        "color": "#db2777",
        "weight": 2,
        "dash": "4 4",
        "why": "Un marché proche indique une activité économique locale.",
    },
    "NEAR_ADMINISTRATION": {
        "category": "admin",
        "label": "Proximité administrative",
        "color": "#64748b",
        "weight": 2,
        "dash": "4 4",
        "why": "Un service administratif proche facilite le déploiement et le suivi.",
    },
    "NEAR_FIBER": {
        "category": "telecom",
        "label": "Fibre proche",
        "color": "#06b6d4",
        "weight": 2,
        "dash": None,
        "why": "La fibre à proximité améliore le potentiel de connectivité.",
    },
    "NEAR_BACKBONE": {
        "category": "telecom",
        "label": "Infrastructure télécom proche",
        "color": "#0891b2",
        "weight": 2,
        "dash": "6 4",
        "why": "Une infrastructure télécom proche structure le potentiel de couverture.",
    },
    "NEAREST_TELECOM_INFRA": {
        "category": "telecom",
        "label": "Infrastructure télécom la plus proche",
        "color": "#0e7490",
        "weight": 3,
        "dash": None,
        "why": "Infrastructure télécom la plus proche du site — référence de couverture pour la décision.",
    },
    "NEAREST_FIBER_LINE": {
        "category": "telecom",
        "label": "Tronçon fibre le plus proche",
        "color": "#155e75",
        "weight": 2,
        "dash": "4 4",
        "why": "Tronçon / ligne réseau fibre le plus proche — distinct des nœuds FTTX.",
    },
    "NEAR_MAIN_ROAD": {
        "category": "roads",
        "label": "Route principale",
        "color": "#ea580c",
        "weight": 3,
        "dash": None,
        "why": "La route principale la plus proche conditionne l’accessibilité terrain.",
    },
    "ROAD_ACCESSIBILITY": {
        "category": "roads",
        "label": "Accessibilité routière",
        "color": "#c2410c",
        "weight": 2,
        "dash": "4 4",
        "why": "Le score d’accessibilité routière explique la facilité d’intervention.",
    },
    "WITHIN_ROAD_CORRIDOR": {
        "category": "roads",
        "label": "Corridor routier",
        "color": "#f97316",
        "weight": 2,
        "dash": "2 4",
        "why": "Le site se trouve dans un corridor routier opérationnel.",
    },
    "CONNECTS_CCN": {
        "category": "ccn",
        "label": "Lien CCN",
        "color": "#14b8a6",
        "weight": 3,
        "dash": None,
        "why": "La relation avec un CCN structure l’ancrage communautaire (Site FDSU ≠ CCN).",
    },
    "NEAR_CCN": {
        "category": "ccn",
        "label": "Proximité CCN",
        "color": "#14b8a6",
        "weight": 2,
        "dash": "4 4",
        "why": "Un CCN à proximité ancre l’intervention dans le tissu communautaire numérique.",
    },
    "SAME_ADMINISTRATIVE_AREA": {
        "category": "admin",
        "label": "Même territoire administratif",
        "color": "#64748b",
        "weight": 2,
        "dash": "2 4",
        "why": "Le site et l’entité partagent le même découpage administratif.",
    },
    "COVERAGE_NEED": {
        "category": "needs",
        "label": "Besoin de couverture",
        "color": "#dc2626",
        "weight": 3,
        "dash": "6 3",
        "why": "Un besoin de couverture non satisfait motive l’intervention.",
    },
    "PRIORITY_NEED": {
        "category": "needs",
        "label": "Besoin prioritaire",
        "color": "#dc2626",
        "weight": 3,
        "dash": "6 3",
        "why": "Ce besoin prioritaire contribue directement au raisonnement décisionnel.",
    },
}

PRESENTATION_STEPS = [
    {"id": "site", "label": "Site sélectionné", "categories": ["site"]},
    {"id": "population", "label": "Population concernée", "categories": ["population", "localities", "needs"]},
    {"id": "health", "label": "Services de santé", "categories": ["health"]},
    {"id": "telecom", "label": "Télécommunications", "categories": ["telecom"]},
    {"id": "roads", "label": "Routes et accessibilité", "categories": ["roads"]},
    {"id": "ccn", "label": "Ancrage CCN", "categories": ["ccn", "admin", "fdsu_sites"]},
    {"id": "recommendation", "label": "Recommandation", "categories": ["*"]},
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _probe_referential_availability(lon: float | None, lat: float | None) -> dict[str, dict[str, Any]]:
    """Sonde les référentiels déjà présents (sans inventer de relations)."""
    from pathlib import Path

    probes: dict[str, dict[str, Any]] = {}

    health_stats = _safe(
        lambda: __import__("api.services.health_service", fromlist=["get_statistics"]).get_statistics(),
        {},
    ) or {}
    health_count = health_stats.get("total_facilities")
    if not health_count:
        hf = Path("data/health/facilities/health_facilities.json")
        if hf.exists():
            try:
                import json

                raw = json.loads(hf.read_text(encoding="utf-8"))
                if isinstance(raw, dict) and "features" in raw:
                    health_count = len(raw["features"])
                elif isinstance(raw, dict) and "facilities" in raw:
                    health_count = len(raw["facilities"])
                elif isinstance(raw, list):
                    health_count = len(raw)
            except Exception:
                health_count = None
    probes["health"] = {
        "referential_exists": bool(health_count and int(health_count) > 0),
        "record_count": health_count,
        "nsme_wired": True,
        "nsme_source": "health.health_facilities",
        "search_radius_m": None,
    }
    try:
        from api.services.spatial_matching_service import get_rules

        radii = (get_rules().get("service_radii_m") or {})
        probes["health"]["search_radius_m"] = radii.get("health_proximity") or 5000
        probes["health"]["nearest_max_m"] = radii.get("health_nearest_max") or 25000
    except Exception:
        probes["health"]["search_radius_m"] = 5000
        probes["health"]["nearest_max_m"] = 25000

    route_stats = _safe(
        lambda: __import__("api.services.transport_service", fromlist=["get_statistics"]).get_statistics(),
        {},
    ) or {}
    route_n = route_stats.get("routes_total") or route_stats.get("total") or route_stats.get("count")
    if not route_n:
        gj = Path("data/sectoral/transport/processed/routes_principales.geojson")
        if gj.exists():
            try:
                import json

                route_n = len(json.loads(gj.read_text(encoding="utf-8")).get("features") or [])
            except Exception:
                route_n = None
    probes["roads"] = {
        "referential_exists": bool(route_n and int(route_n) > 0),
        "record_count": route_n,
        "nsme_wired": True,
        "nsme_source": "transport.routes PostGIS",
    }

    ccn_path = Path("data/programs/ccn/demo_ccn.json")
    ccn_n = None
    if ccn_path.exists():
        try:
            import json

            payload = json.loads(ccn_path.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                ccn_n = len(payload)
            elif isinstance(payload, dict):
                ccn_n = len(payload.get("ccn") or payload.get("items") or payload.get("features") or [])
        except Exception:
            ccn_n = None
    probes["ccn"] = {
        "referential_exists": bool(ccn_n and ccn_n > 0),
        "record_count": ccn_n,
        "nsme_wired": True,
        "nsme_source": "demo_ccn.json (démonstration)",
        "demonstration": True,
    }

    tel_stats = _safe(
        lambda: __import__("api.services.telecom_service", fromlist=["get_statistics"]).get_statistics(),
        {},
    ) or {}
    tel_n = (
        tel_stats.get("infrastructure_count")
        or tel_stats.get("total_objects")
        or tel_stats.get("total")
        or tel_stats.get("count")
    )
    line_n = tel_stats.get("network_line_count")
    probes["telecom"] = {
        "referential_exists": bool(tel_n and int(tel_n) > 0) or Path("data/sectoral/telecom").exists(),
        "record_count": tel_n,
        "network_line_count": line_n,
        "nsme_wired": True,
        "nsme_source": "telecom.infrastructure + telecom.network_lines",
        "search_radius_m": None,
        "demonstration": False,
    }
    try:
        from api.services.spatial_matching_service import get_rules

        radii = get_rules().get("service_radii_m") or {}
        probes["telecom"]["search_radius_m"] = radii.get("telecom_proximity") or 25000
        probes["telecom"]["fiber_radius_m"] = radii.get("fiber_connection") or 5000
        probes["roads"]["search_radius_m"] = radii.get("nearest_main_road") or 50000
        probes["roads"]["corridor_m"] = radii.get("road_corridor") or 2000
        probes["fdsu_sites"] = {
            "referential_exists": True,
            "record_count": None,
            "nsme_wired": True,
            "nsme_source": "programs.fdsu_sites",
            "search_radius_m": radii.get("fdsu_site_proximity") or 25000,
        }
        probes["ccn"]["search_radius_m"] = radii.get("ccn_community_impact") or 10000
        probes["ccn"]["demonstration"] = True
        probes["ccn"]["nsme_source"] = "demo_ccn.json (démonstration)"
    except Exception:
        probes["telecom"]["search_radius_m"] = 25000
        probes["fdsu_sites"] = {
            "referential_exists": True,
            "record_count": None,
            "nsme_wired": True,
            "nsme_source": "programs.fdsu_sites",
            "search_radius_m": 25000,
        }

    probes["localities"] = {
        "referential_exists": Path("data/coverage/localities_uncovered.jsonl").exists(),
        "record_count": None,
        "nsme_wired": True,
        "nsme_source": "NCI localities_uncovered",
    }
    probes["population"] = dict(probes["localities"])
    if "fdsu_sites" not in probes:
        probes["fdsu_sites"] = {
            "referential_exists": True,
            "record_count": None,
            "nsme_wired": True,
            "nsme_source": "programs.fdsu_sites",
            "search_radius_m": 25000,
        }
    probes["admin"] = {"referential_exists": True, "nsme_wired": True, "nsme_source": "NCI / admin derived"}
    probes["needs"] = {"referential_exists": True, "nsme_wired": True, "nsme_source": "CANDIDATE_FOR_MISSION"}

    edu_stats = _safe(
        lambda: __import__(
            "api.services.education_referential_service", fromlist=["statistics"]
        ).statistics(),
        {},
    ) or {}
    edu_n = edu_stats.get("establishments") or edu_stats.get("classified_total")
    probes["education"] = {
        "referential_exists": bool(edu_n and int(edu_n) > 0),
        "record_count": edu_n,
        "nsme_wired": True,
        "nsme_source": "CENI SCHOOL projection (education_referential)",
        "derived_projection": True,
        "official_ministry_registry": False,
        "search_radius_m": None,
        "scoring_weighted": False,
    }
    try:
        from api.services.spatial_matching_service import get_rules

        radii = get_rules().get("service_radii_m") or {}
        probes["education"]["search_radius_m"] = radii.get("school_proximity") or 3000
        probes["education"]["nearest_max_m"] = radii.get("school_nearest_max") or 25000
    except Exception:
        probes["education"]["search_radius_m"] = 3000

    ceni_stats = _safe(
        lambda: __import__("api.services.ceni_registry_service", fromlist=["statistics"]).statistics(),
        {},
    ) or {}
    ceni_n = ceni_stats.get("integrated") or ceni_stats.get("total_raw")
    probes["ceni"] = {
        "referential_exists": bool(ceni_n and int(ceni_n) > 0),
        "record_count": ceni_n,
        "nsme_wired": True,
        "nsme_source": "CENI registry file (institutional signal)",
        "not_fdsu_sites": True,
        "scoring_weighted": False,
        "search_radius_m": None,
        "note": "Signal disponible — non pondéré dans le scoring actuel",
    }
    try:
        from api.services.spatial_matching_service import get_rules

        radii = get_rules().get("service_radii_m") or {}
        probes["ceni"]["search_radius_m"] = radii.get("ceni_proximity") or 5000
        probes["ceni"]["nearest_max_m"] = radii.get("ceni_nearest_max") or 15000
    except Exception:
        probes["ceni"]["search_radius_m"] = 5000

    probes["energy"] = {"referential_exists": False, "nsme_wired": False}
    probes["markets"] = {"referential_exists": False, "nsme_wired": False}
    return probes


def _km(radius_m: Any) -> float | None:
    if radius_m is None:
        return None
    try:
        return round(float(radius_m) / 1000.0, 1)
    except (TypeError, ValueError):
        return None


def _nearest_from_matches(matches: list[dict[str, Any]], relation_types: set[str]) -> dict[str, Any] | None:
    candidates = [m for m in matches if str(m.get("relation_type") or "") in relation_types]
    if not candidates:
        return None
    candidates.sort(key=lambda m: float(m.get("distance_m") or 1e12))
    m = candidates[0]
    props = m.get("properties") or {}
    name = (
        props.get("infra_label")
        or props.get("facility_name")
        or props.get("site_name")
        or props.get("road_name")
        or props.get("ccn_name")
        or props.get("line_name")
        or m.get("need_id")
    )
    return {
        "name": name,
        "type": props.get("infra_type") or props.get("facility_type_name") or props.get("road_type") or props.get("line_type") or props.get("class_label"),
        "operator": props.get("operator_name") or props.get("operator_code"),
        "distance_m": m.get("distance_m"),
        "distance_km": round(float(m["distance_m"]) / 1000.0, 1) if m.get("distance_m") is not None else None,
        "outside_search_radius": bool(props.get("outside_search_radius")),
        "object_kind": props.get("object_kind"),
        "relation_type": m.get("relation_type"),
        "source": m.get("source_need"),
    }


def _classify_category_emptiness(
    cat_id: str,
    cat: dict[str, Any],
    *,
    count: int,
    nsme_rel_types: set[str],
    matches: list[dict[str, Any]],
    probe: dict[str, Any],
) -> dict[str, Any]:
    """Classe les domaines selon le modèle officiel des statuts (Data First)."""
    rel_types = set(cat.get("relation_types") or [])
    graph_rel_types = rel_types  # relations métier affichables
    produced = bool(graph_rel_types & nsme_rel_types) or count > 0
    search_markers = {
        "fdsu_sites": {"FDSU_SEARCH_EXECUTED"},
        "telecom": {
            "TELECOM_SEARCH_EXECUTED",
            "NEAREST_TELECOM_INFRA",
            "NEAREST_FIBER_LINE",
            "NEAR_FIBER",
            "NEAR_BACKBONE",
            "NEAREST_MNO_VODACOM",
            "NEAREST_MNO_ORANGE",
            "NEAREST_MNO_AIRTEL",
            "NEAREST_MNO_AFRICELL",
            "NEAREST_FIBER_LINK",
            "NEAREST_MICROWAVE_LINK",
            "MUTUALIZATION_POTENTIAL",
        },
        "ccn": {"CCN_SEARCH_EXECUTED", "NEAR_CCN", "CONNECTS_CCN"},
        "health": {"NEAR_HEALTH_FACILITY", "NEAREST_HEALTH_FACILITY", "WITHIN_HEALTH_SERVICE_AREA"},
        "education": {"NEAR_SCHOOL", "NEAREST_SCHOOL", "EDUCATION_SEARCH_EXECUTED"},
        "ceni": {"NEAREST_CENI_SIGNAL", "NEAR_CENI_SITE", "CENI_SEARCH_EXECUTED"},
        "roads": {"NEAR_MAIN_ROAD", "ROAD_ACCESSIBILITY", "WITHIN_ROAD_CORRIDOR"},
    }
    search_executed = bool(nsme_rel_types & search_markers.get(cat_id, graph_rel_types)) or bool(
        any(
            (m.get("properties") or {}).get("search_executed")
            and str(m.get("category") or "") == cat_id
            for m in matches
        )
    )
    # Si des matches du domaine existent (même hors rayon), la recherche a eu lieu
    domain_matches = [
        m
        for m in matches
        if str(m.get("relation_type") or "") in (graph_rel_types | search_markers.get(cat_id, set()))
        or str(m.get("category") or "") == cat_id
    ]
    if domain_matches:
        search_executed = True

    # Admin / besoins : dérivés des localités NCI — si localités cherchées, la recherche domaine est considérée exécutée
    if cat_id in {"admin", "needs", "markets"}:
        locality_searched = any(
            str(m.get("relation_type") or "") in {"SERVES_LOCALITY", "IMPACTS_POPULATION", "CANDIDATE_FOR_MISSION"}
            or str(m.get("calculation_method") or "") == "derived_from_nci_infra"
            for m in matches
        )
        if locality_searched:
            search_executed = True
        if cat_id == "markets" and not cat.get("available", True):
            pass  # futur : laisser integrating
        elif cat_id == "admin" and not produced and locality_searched:
            # pas d'infra admin dans les localités matchées → aucun objet trouvé, pas une erreur
            search_executed = True
        elif cat_id == "needs" and not produced and locality_searched:
            search_executed = True

    nearest = None
    if cat_id == "telecom":
        nearest = _nearest_from_matches(
            matches,
            {
                "NEAREST_TELECOM_INFRA",
                "NEAR_FIBER",
                "NEAR_BACKBONE",
                "NEAREST_FIBER_LINE",
                "NEAREST_FIBER_LINK",
                "NEAREST_MICROWAVE_LINK",
                "NEAREST_MNO_VODACOM",
                "NEAREST_MNO_ORANGE",
                "NEAREST_MNO_AIRTEL",
                "NEAREST_MNO_AFRICELL",
            },
        )
    elif cat_id == "roads":
        nearest = _nearest_from_matches(matches, {"NEAR_MAIN_ROAD", "ROAD_ACCESSIBILITY", "WITHIN_ROAD_CORRIDOR"})
    elif cat_id == "health":
        nearest = _nearest_from_matches(
            matches, {"NEAREST_HEALTH_FACILITY", "NEAR_HEALTH_FACILITY", "WITHIN_HEALTH_SERVICE_AREA"}
        )
    elif cat_id == "education":
        nearest = _nearest_from_matches(matches, {"NEAREST_SCHOOL", "NEAR_SCHOOL"})
    elif cat_id == "ceni":
        nearest = _nearest_from_matches(matches, {"NEAREST_CENI_SIGNAL", "NEAR_CENI_SITE"})
    elif cat_id == "fdsu_sites":
        nearest = _nearest_from_matches(
            matches, {"NEAR_FDSU_SITE", "SAME_PROGRAM", "COMPLEMENTS_FDSU_SITE", "OVERLAPPING_SERVICE_AREA"}
        )
    elif cat_id == "ccn":
        nearest = _nearest_from_matches(matches, {"NEAR_CCN", "CONNECTS_CCN"})

    radius_m = probe.get("search_radius_m")
    radius_km = _km(radius_m)
    ref_count = probe.get("record_count")
    ref_exists = probe.get("referential_exists")
    nsme_wired = probe.get("nsme_wired", True)

    def _impact(msg: str) -> str:
        return msg

    if cat_id == "site" or count > 0:
        note = cat.get("note")
        if cat_id == "telecom" and nearest and nearest.get("outside_search_radius"):
            # relations hors rayon seules → traité plus bas ; ici count>0 peut être nearest-only
            pass
        return {
            "status": "active",
            "maturity": "operational",
            "empty_reason": None,
            "integration_case": None,
            "note": note,
            "search_executed": True,
            "nearest_context": nearest,
            "business_impact": None,
            "official_status": "operational",
        }

    if not cat.get("available", True):
        return {
            "status": "future",
            "maturity": "integrating",
            "empty_reason": "referential_absent",
            "integration_case": 3,
            "note": cat.get("note") or f"{cat.get('label')} — référentiel non encore importé.",
            "search_executed": False,
            "nearest_context": None,
            "business_impact": "Ce domaine ne peut pas encore influencer la décision.",
            "official_status": "integration_pending",
        }

    if probe.get("demonstration") and cat_id == "ccn":
        note = (
            "Aucun CCN du jeu DEMO trouvé dans ce territoire."
            if search_executed and not produced
            else cat.get("note")
        )
        if produced:
            note = "CCN issu du jeu de démonstration — référentiel production non encore intégré."
        return {
            "status": "empty" if not produced else "active",
            "maturity": "demonstration" if not produced else "partial",
            "empty_reason": None if produced else "no_relations_found",
            "integration_case": 3,
            "note": note or "Jeu CCN de démonstration — couverture partielle.",
            "search_executed": search_executed,
            "nearest_context": nearest,
            "business_impact": "Les CCN DEMO ne doivent pas être traités comme un référentiel production.",
            "official_status": "demonstration",
            "reference_available": True,
            "relation_count": count,
        }

    if ref_exists and not nsme_wired:
        return {
            "status": "empty",
            "maturity": "partial",
            "empty_reason": "search_not_wired",
            "integration_case": 2,
            "note": (
                f"Le référentiel « {cat.get('label')} » existe"
                + (f" ({ref_count} objets)" if ref_count else "")
                + ", mais la recherche spatiale n’est pas encore branchée pour ce domaine."
            ),
            "search_executed": False,
            "nearest_context": None,
            "business_impact": "Ce domaine ne peut pas encore être exploité dans la décision.",
            "official_status": "partial",
        }

    if ref_exists and nsme_wired and search_executed and not produced:
        # Aucun objet trouvé dans le rayon — statut métier clair
        if cat_id == "fdsu_sites":
            note = (
                f"Aucun autre site FDSU trouvé dans le rayon analysé"
                f"{f' ({radius_km} km)' if radius_km is not None else ''}."
            )
            impact = "Pas de coordination immédiate avec un autre site FDSU dans ce rayon."
        elif cat_id == "telecom":
            bits = [
                f"Aucune infrastructure trouvée dans un rayon de {radius_km} km."
                if radius_km is not None
                else "Aucune infrastructure trouvée dans le rayon analysé."
            ]
            if ref_count:
                bits.append(f"Référentiel analysé : {int(ref_count):,} infrastructures.".replace(",", " "))
            if nearest:
                nearest_label = nearest.get("name") or "Infrastructure"
                op = f" ({nearest.get('operator')})" if nearest.get("operator") else ""
                dist = f" — {nearest.get('distance_km')} km" if nearest.get("distance_km") is not None else ""
                bits.append(f"Infrastructure la plus proche : {nearest_label}{op}{dist}.")
            note = " ".join(bits)
            impact = "Le raccordement nécessitera probablement une extension de couverture ou une solution alternative."
        elif cat_id == "roads":
            radius_txt = f" ({radius_km} km)" if radius_km is not None else ""
            bits = [f"Aucune route trouvée dans le rayon analysé{radius_txt}."]
            if ref_count:
                bits.append(f"Référentiel : {int(ref_count):,} objets.".replace(",", " "))
            if nearest:
                bits.append(
                    f"Route la plus proche : {nearest.get('name') or 'Route'}"
                    + (f" — {nearest.get('distance_km')} km" if nearest.get("distance_km") is not None else "")
                    + "."
                )
            note = " ".join(bits)
            impact = "L’accessibilité terrain doit être vérifiée avant déploiement."
        elif cat_id == "health":
            if radius_km is not None:
                note = (
                    "Recherche exécutée sur le référentiel Santé : aucun établissement trouvé "
                    f"dans le rayon de {radius_km} km."
                )
            else:
                note = "Recherche exécutée : aucun établissement de santé trouvé dans le rayon."
            if nearest:
                dist_txt = ""
                if nearest.get("distance_km") is not None:
                    dist_txt = f" — {nearest.get('distance_km')} km"
                note += f" Établissement le plus proche : {nearest.get('name')}{dist_txt}."
            impact = "L’offre de santé locale n’est pas documentée dans le rayon de service."
        else:
            suffix = f" ({ref_count} objets)" if ref_count else ""
            radius_txt = f" dans un rayon de {radius_km} km" if radius_km is not None else ""
            note = (
                f"Aucun objet « {cat.get('label')} » trouvé{radius_txt} "
                f"après recherche spatiale ; référentiel disponible{suffix}."
            )
            impact = f"Le domaine « {cat.get('label')} » n’apporte pas de relation utile pour ce site."
        return {
            "status": "empty",
            "maturity": "empty",
            "empty_reason": "no_relations_found",
            "integration_case": 1,
            "note": note,
            "search_executed": True,
            "nearest_context": nearest,
            "business_impact": _impact(impact),
            "official_status": "empty",
            "reference_available": True,
            "relation_count": 0,
            "radius_m": radius_m,
        }

    if ref_exists and nsme_wired and not search_executed and not domain_matches:
        return {
            "status": "empty",
            "maturity": "error",
            "empty_reason": "search_failed",
            "integration_case": 2,
            "note": (
                f"Erreur d’intégration — le référentiel « {cat.get('label')} » existe, "
                "mais la recherche spatiale n’a pas pu être exécutée pour ce site."
            ),
            "search_executed": False,
            "nearest_context": None,
            "business_impact": "Impossible d’exploiter ce domaine tant que l’erreur technique n’est pas corrigée.",
            "official_status": "error",
        }

    if ref_exists and nsme_wired and not produced:
        return {
            "status": "empty",
            "maturity": "empty",
            "empty_reason": "no_relations_found",
            "integration_case": 1,
            "note": f"Aucun objet « {cat.get('label')} » trouvé après recherche spatiale.",
            "search_executed": search_executed,
            "nearest_context": nearest,
            "business_impact": None,
            "official_status": "empty",
        }

    return {
        "status": "empty",
        "maturity": "partial",
        "empty_reason": "no_relations_found",
        "integration_case": 1,
        "note": cat.get("note") or f"Aucune relation pour « {cat.get('label')} ».",
        "search_executed": search_executed,
        "nearest_context": nearest,
        "business_impact": None,
        "official_status": "partial",
    }


def _safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def _category_for_relation(relation_type: str) -> str:
    style = RELATION_STYLES.get(relation_type) or {}
    if style.get("category"):
        return style["category"]
    for cat_id, cat in CATEGORIES.items():
        if relation_type in (cat.get("relation_types") or []):
            return cat_id
    return "needs"


def _human_source(raw: Any) -> str:
    text = str(raw or "").strip()
    mapping = {
        "programs.fdsu_sites": "Sites FDSU",
        "data/coverage/localities_uncovered.jsonl": "Localités non couvertes (NCI)",
        "analysis.asset_need_matches": "Correspondances spatiales NSME",
        "transport.routes": "Routes principales",
        "postgis_nearest_road": "Analyse PostGIS — route la plus proche",
        "health.health_facilities": "Référentiel Santé (health.health_facilities)",
        "postgis_nearest_health": "Analyse PostGIS — établissement de santé",
    }
    if text in mapping:
        return mapping[text]
    if text.startswith("data/") or "." in text and "/" not in text[:20]:
        return text.replace("data/", "").replace("_", " ")
    return text or "NSME"


def _classify_contribution_type(
    *,
    status: str,
    category: str,
    criterion: str | None,
    display: str | None,
    relation_type: str | None = None,
) -> str:
    """Classification explicable — aucun point inventé.

    Types : direct | indirect | contextual_evidence | not_applicable | pending_rule
    """
    cat = (category or "").lower()
    rel = (relation_type or "").lower()
    disp = str(display or "")
    # Points numériques réellement lus depuis un critère sourcé
    if status == "mapped" and criterion:
        if any(ch.isdigit() for ch in disp) or "/" in disp:
            return "direct"
        return "indirect"
    if status == "proxy" or cat in {"population", "localities", "needs"}:
        return "indirect"
    if cat == "ccn" or "ccn" in rel:
        return "pending_rule"
    if cat in {"fdsu_sites", "admin"}:
        return "contextual_evidence"
    if cat in {"health", "education", "telecom", "roads"}:
        return "contextual_evidence"
    if status == "unavailable":
        return "contextual_evidence"
    return "not_applicable"


def _contribution_explanation(contrib_type: str, category: str, criterion: str | None = None) -> str:
    cat = (category or "").lower()
    if contrib_type == "direct" and criterion:
        return f"Cette relation attribue des points au critère « {criterion} » selon la règle officielle appliquée."
    if contrib_type == "indirect":
        if cat in {"population", "localities", "needs"}:
            return "Cette localité ou population alimente indirectement les critères démographie et couverture."
        if criterion:
            return f"Cette relation alimente le critère agrégé « {criterion} », sans points isolés propres."
        return "Cette relation alimente des critères agrégés du score, sans attribution de points isolés."
    if contrib_type == "pending_rule":
        return "Moteur CCN / DEMO — aucune pondération inventée ; en attente de règle officielle sourcée."
    if contrib_type == "not_applicable":
        return "Cette relation n’entre pas dans le scoring ; elle est affichée à titre de contexte territorial."
    if cat == "health":
        return "Cet établissement confirme la présence d’un service public essentiel (preuve contextuelle)."
    if cat in {"telecom", "roads"}:
        return "Cette infrastructure éclaire la faisabilité territoriale (preuve contextuelle), sans points inventés."
    if cat == "fdsu_sites":
        return "Site FDSU voisin — preuve de coordination / contexte programme, sans points attribués."
    return "Cette relation aide à comprendre la décision sans être pondérée directement dans le score."


def _contribution_from_decision(relation_type: str, match: dict[str, Any], case: dict[str, Any] | None) -> dict[str, Any]:
    """Relie une relation NSME à un critère du Decision Engine si disponible — jamais inventé."""
    proxy_pop = match.get("population_impacted")
    style = RELATION_STYLES.get(relation_type) or {}
    cat = style.get("category") or _category_for_relation(relation_type)
    base = {
        "status": "unavailable",
        "display": "Preuve contextuelle",
        "proxy_population": proxy_pop,
        "note": "Aucun point isolé n’est affiché sans critère décisionnel sourcé.",
        "contribution_type": "contextual_evidence",
        "role_label": "Preuve contextuelle",
        "explanation": _contribution_explanation("contextual_evidence", cat),
        "fed_criteria": [],
    }
    if not case:
        if proxy_pop is not None:
            ctype = "indirect"
            out = {
                **base,
                "status": "proxy",
                "display": f"Population concernée : {proxy_pop}",
                "note": "Indicateur populationnel NSME — pas un point de score inventé.",
                "contribution_type": ctype,
                "role_label": "Contribution indirecte",
                "explanation": _contribution_explanation(ctype, cat),
                "fed_criteria": ["population", "couverture"],
            }
            return out
        return base

    justification = case.get("justification") or case.get("criteria") or []
    if isinstance(justification, dict):
        justification = list(justification.values())
    keywords = {
        "population": ("population", "couverture", "déficit"),
        "localities": ("localit", "couverture", "déficit"),
        "health": ("santé", "sante", "health", "social"),
        "telecom": ("télécom", "telecom", "fibre", "connect", "couverture", "déficit"),
        "roads": ("route", "accessib", "transport", "faisabil"),
        "ccn": ("ccn", "communaut"),
        "admin": ("admin", "contexte"),
        "needs": ("mission", "besoin", "priorit"),
        "fdsu_sites": ("site", "chevauche", "coord"),
    }.get(cat, ())
    for item in justification:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or item.get("criterion_id") or "").lower()
        if any(k in label for k in keywords):
            criterion = item.get("label") or item.get("criterion_id")
            display = item.get("contribution_display") or item.get("score_display") or str(item.get("contribution") or "—")
            ctype = _classify_contribution_type(
                status="mapped",
                category=cat,
                criterion=str(criterion) if criterion else None,
                display=str(display),
                relation_type=relation_type,
            )
            points = item.get("points") or item.get("score") or item.get("contribution")
            maximum = item.get("max_points") or item.get("maximum") or item.get("max")
            source_doc = item.get("source") or item.get("source_document") or item.get("matrix_version")
            return {
                "status": "mapped",
                "display": display,
                "criterion": criterion,
                "why": item.get("why") or item.get("description"),
                "proxy_population": proxy_pop,
                "note": "Contribution lue depuis le moteur de décision (critère sourcé).",
                "contribution_type": ctype,
                "role_label": {
                    "direct": "Contribution directe",
                    "indirect": "Contribution indirecte",
                    "contextual_evidence": "Preuve contextuelle",
                    "not_applicable": "Non applicable",
                    "pending_rule": "En attente de règle officielle",
                }.get(ctype, "Preuve contextuelle"),
                "explanation": _contribution_explanation(ctype, cat, str(criterion) if criterion else None),
                "points": points if ctype == "direct" else None,
                "maximum": maximum if ctype == "direct" else None,
                "weight": item.get("weight") or item.get("ponderation"),
                "source_document": source_doc,
                "matrix_version": item.get("matrix_version") or item.get("matrix"),
                "rule": item.get("rule") or item.get("rule_id"),
                "fed_criteria": [criterion] if criterion else [],
            }
    if proxy_pop is not None:
        ctype = "indirect"
        return {
            **base,
            "status": "proxy",
            "display": f"Population concernée : {proxy_pop}",
            "note": "Indicateur populationnel NSME — pas un point de score inventé.",
            "contribution_type": ctype,
            "role_label": "Contribution indirecte",
            "explanation": _contribution_explanation(ctype, cat),
            "fed_criteria": ["population", "couverture"],
        }
    # Domaines sans critère mappé : preuve contextuelle (jamais « non calculée »)
    ctype = _classify_contribution_type(
        status="unavailable",
        category=cat,
        criterion=None,
        display=None,
        relation_type=relation_type,
    )
    return {
        **base,
        "contribution_type": ctype,
        "role_label": {
            "direct": "Contribution directe",
            "indirect": "Contribution indirecte",
            "contextual_evidence": "Preuve contextuelle",
            "not_applicable": "Non applicable",
            "pending_rule": "En attente de règle officielle",
        }.get(ctype, "Preuve contextuelle"),
        "explanation": _contribution_explanation(ctype, cat),
        "display": {
            "indirect": "Contribution indirecte",
            "pending_rule": "En attente de règle officielle",
            "not_applicable": "Non applicable",
        }.get(ctype, "Preuve contextuelle"),
    }


def _road_endpoint(match: dict[str, Any], asset_lon: float | None, asset_lat: float | None) -> tuple[float, float] | None:
    """Enrichit la géométrie d’affichage d’une relation route déjà produite par le NSME."""
    props = match.get("properties") or {}
    if props.get("need_lon") is not None and props.get("need_lat") is not None:
        return float(props["need_lon"]), float(props["need_lat"])
    if asset_lon is None or asset_lat is None:
        return None
    road = _safe(
        lambda: __import__("api.services.transport_service", fromlist=["nearest_road"]).nearest_road(
            float(asset_lon), float(asset_lat)
        ),
        None,
    )
    if not road:
        return None
    # Point d’accroche : centroid approximatif via géométrie si fournie
    geom = road.get("geometry") or {}
    coords = geom.get("coordinates") if isinstance(geom, dict) else None
    if isinstance(coords, list) and coords:
        # LineString → premier point
        first = coords[0]
        if isinstance(first, (list, tuple)) and len(first) >= 2:
            return float(first[0]), float(first[1])
    return None


def build_graph(asset_type: str, asset_id: str, *, program_code: str | None = None) -> dict[str, Any] | None:
    from api.services import spatial_matching_service as nsme
    from api.services import explainable_decision_service as eds

    needs = _safe(lambda: nsme.get_asset_needs(asset_id, asset_type="fdsu_site" if asset_type in {"site", "fdsu_site"} else asset_type, limit=200), {}) or {}
    matches = list(needs.get("matches") or [])
    # Filtrer les anciennes relations Santé dérivées NCI (non PostGIS) — source unique = health.health_facilities
    matches = [
        m
        for m in matches
        if not (
            str(m.get("relation_type") or "")
            in {"NEAR_HEALTH_FACILITY", "NEAREST_HEALTH_FACILITY", "WITHIN_HEALTH_SERVICE_AREA"}
            and str(m.get("calculation_method") or "") == "derived_from_nci_infra"
        )
    ]

    from api.services import sdg_coverage_service as coverage

    # Si NSME not_found strict (aucun site résolu) → fiche explicative, pas un graphe fictif
    if not matches and needs.get("_meta", {}).get("status") == "not_found" and not needs.get("asset"):
        assessed = coverage.assess_asset(asset_id, program_code=program_code, run_matching=False)
        return {
            "_meta": {
                "engine": "spatial-decision-graph-v2.1",
                "generated_at": _now(),
                "status": "impossible",
                "classification": "C",
                "asset_id": asset_id,
                "asset_type": asset_type,
                "program_code": program_code,
                "data_first": True,
            },
            "nodes": [],
            "edges": [],
            "categories": [],
            "filters": [],
            "kpis": [],
            "decision_summary": {
                "title": "Analyse spatiale indisponible",
                "message": (assessed.get("explainability") or {}).get("message"),
            },
            "explainability": assessed.get("explainability"),
            "coverage_diagnosis": assessed.get("diagnosis"),
            "ui": {
                "badge": "Analyse impossible",
                "show_partial_graph": False,
            },
        }

    impact = _safe(lambda: nsme.get_asset_impact(asset_id), {}) or {}
    case = _safe(lambda: eds.get_decision_case(asset_id, asset_type=asset_type, program_code=program_code), {}) or {}

    asset = needs.get("asset") or (case.get("asset") if case else None)
    if not asset and str(asset_id).isdigit():
        sites = _safe(lambda: nsme.list_fdsu_sites(asset_id=int(asset_id), limit=1), []) or []
        asset = sites[0] if sites else {"site_id": asset_id, "site_name": str(asset_id)}

    asset = dict(asset or {"site_id": asset_id, "site_name": str(asset_id)})

    # Nom métier prioritaire (dossier / résolveur) — évite les codes techniques NSME (Part2_…)
    case_asset = (case or {}).get("asset") or {}
    for key in (
        "site_name",
        "name",
        "site_code",
        "program_code",
        "territoire",
        "province",
        "priority_level",
        "priority_level_label",
    ):
        if case_asset.get(key) not in (None, ""):
            asset[key] = case_asset[key]
    try:
        from api.services.site_entity_resolver import resolve_site

        resolved = resolve_site(asset_id, program_code=program_code, entity_type=asset_type)
        if resolved and resolved.get("resolved"):
            if resolved.get("site_name"):
                asset["site_name"] = resolved["site_name"]
            for key in ("site_code", "program_code", "territoire", "province", "priority_level", "priority_level_label"):
                if resolved.get(key) not in (None, ""):
                    asset.setdefault(key, resolved[key])
            if resolved.get("longitude") is not None and asset.get("longitude") is None:
                asset["longitude"] = resolved["longitude"]
                asset["latitude"] = resolved.get("latitude")
    except Exception:
        pass

    if program_code and not asset.get("program_code"):
        asset["program_code"] = program_code

    a_lon = asset.get("longitude")
    a_lat = asset.get("latitude")
    # fallback from first match props
    if a_lon is None:
        for m in matches:
            props = m.get("properties") or {}
            if props.get("asset_lon") is not None:
                a_lon, a_lat = props.get("asset_lon"), props.get("asset_lat")
                break

    center_id = f"site:{asset.get('site_id') or asset.get('id') or asset_id}"
    nodes: dict[str, dict[str, Any]] = {
        center_id: {
            "id": center_id,
            "kind": "site",
            "category": "site",
            "name": asset.get("site_name") or asset.get("name") or asset.get("site_code") or str(asset_id),
            "description": "Site FDSU analysé — nœud central du raisonnement territorial.",
            "role": "Point d’intervention proposé",
            "type_label": "Site FDSU",
            "referential": "Programmes FDSU / Master Registry",
            "distance_m": 0,
            "state": asset.get("priority_level_label") or asset.get("priority_level") or "priorisé",
            "longitude": a_lon,
            "latitude": a_lat,
            "source_label": "Sites FDSU · Decision Engine",
            "maturity": "operational",
            "confidence": ((case or {}).get("confidence") or {}).get("label")
            if isinstance((case or {}).get("confidence"), dict)
            else None,
            "program_code": asset.get("program_code") or program_code,
            "territoire": asset.get("territoire"),
            "province": asset.get("province"),
            "actions": {
                "open_dossier": f"#decision-case/site/{asset_id}",
                "open_twin": f"#territorial-twin/territoire/{asset.get('territoire')}" if asset.get("territoire") else None,
                "analyze": f"#decision-detail/sites-prioritaires",
                "open_workspace": f"#decision-detail/sites-prioritaires",
            },
        }
    }
    edges: list[dict[str, Any]] = []
    counts: dict[str, int] = {k: 0 for k in CATEGORIES}

    for idx, match in enumerate(matches):
        rel = str(match.get("relation_type") or "")
        if not rel:
            continue
        props = match.get("properties") or {}
        if props.get("suppress_graph_edge"):
            continue
        if rel.endswith("_SEARCH_EXECUTED"):
            continue
        style = RELATION_STYLES.get(rel) or {
            "category": "needs",
            "label": rel,
            "color": "#dc2626",
            "weight": 2,
            "dash": "4 4",
            "why": "Relation spatiale issue du moteur de correspondance spatiale.",
        }
        cat = style["category"]
        need_lon = props.get("need_lon")
        need_lat = props.get("need_lat")
        if (need_lon is None or need_lat is None) and cat == "roads":
            ep = _road_endpoint(match, a_lon, a_lat)
            if ep:
                need_lon, need_lat = ep

        node_id = f"{cat}:{match.get('need_id') or idx}"
        name = (
            props.get("locality_name")
            or props.get("infra_label")
            or props.get("road_name")
            or props.get("ccn_name")
            or props.get("site_name")
            or props.get("line_name")
            or match.get("need_id")
            or style["label"]
        )
        if node_id not in nodes:
            nodes[node_id] = {
                "id": node_id,
                "kind": "related",
                "category": cat,
                "name": name,
                "description": style.get("why"),
                "role": style.get("label"),
                "type_label": style.get("label"),
                "referential": _human_source(match.get("source_need") or match.get("source_asset") or match.get("calculation_method")),
                "distance_m": match.get("distance_m"),
                "state": match.get("priority_level") or props.get("class_label") or match.get("confidence_level") or "observé",
                "longitude": need_lon,
                "latitude": need_lat,
                "population": match.get("population_impacted"),
                "need_id": match.get("need_id"),
                "relation_type": rel,
                "source_label": _human_source(match.get("source_need") or match.get("source_asset") or match.get("calculation_method")),
                "confidence": match.get("confidence_level"),
                "maturity": "operational",
                "why": style.get("why"),
                "actions": {
                    "open_twin": f"#territorial-twin/territoire/{match.get('territoire') or asset.get('territoire')}"
                    if (match.get("territoire") or asset.get("territoire"))
                    else None,
                    "open_dossier": f"#decision-case/site/{asset_id}",
                    "analyze": f"#decision-detail/sites-prioritaires",
                    "open_workspace": f"#decision-detail/sites-prioritaires",
                },
            }
            counts[cat] = counts.get(cat, 0) + 1

        contribution = _contribution_from_decision(rel, match, case if case else None)
        origin_name = nodes[center_id]["name"]
        edges.append(
            {
                "id": f"edge:{rel}:{match.get('need_id') or idx}",
                "relation_id": f"edge:{rel}:{match.get('need_id') or idx}",
                "source": center_id,
                "target": node_id,
                "source_entity": {"id": center_id, "name": origin_name, "kind": "site"},
                "target_entity": {"id": node_id, "name": name, "kind": "related", "category": cat},
                "origin_label": origin_name,
                "target_label": name,
                "relation_type": rel,
                "category": cat,
                "label": style.get("label"),
                "color": style.get("color"),
                "weight": style.get("weight"),
                "dash": style.get("dash"),
                "distance_m": match.get("distance_m"),
                "confidence": match.get("confidence_level"),
                "source_label": _human_source(match.get("source_need") or match.get("source_asset") or match.get("calculation_method")),
                "why": style.get("why"),
                "explanation": style.get("why"),
                "contribution": contribution,
                "geometry": (
                    {
                        "type": "LineString",
                        "coordinates": [[a_lon, a_lat], [need_lon, need_lat]],
                    }
                    if a_lon is not None and a_lat is not None and need_lon is not None and need_lat is not None
                    else None
                ),
                "nsme_trace": {
                    "relation_type": rel,
                    "need_id": match.get("need_id"),
                    "calculation_method": match.get("calculation_method"),
                    "source_asset": match.get("source_asset"),
                    "source_need": match.get("source_need"),
                },
            }
        )

    # Marquer besoins critiques (priorité High)
    for node in nodes.values():
        if node.get("category") in {"population", "localities"} and str(node.get("state") or "").lower() in {"high", "critique", "critical"}:
            node["category_badge"] = "needs"
            counts["needs"] = counts.get("needs", 0) + 1

    category_stats = []
    referential_probes = _probe_referential_availability(a_lon, a_lat)
    nsme_rel_types = {str(m.get("relation_type") or "") for m in matches}
    domain_statuses: list[dict[str, Any]] = []
    for cat_id, cat in CATEGORIES.items():
        count = 1 if cat_id == "site" else counts.get(cat_id, 0)
        empty_meta = _classify_category_emptiness(
            cat_id,
            cat,
            count=count,
            nsme_rel_types=nsme_rel_types,
            matches=matches,
            probe=referential_probes.get(cat_id) or {},
        )
        # Télécom / santé : nearest hors rayon ≠ opérationnel dans le rayon
        if cat_id in {"telecom", "health"} and count > 0:
            in_radius_rels = {
                "telecom": {"NEAR_FIBER", "NEAR_BACKBONE"},
                "health": {"NEAR_HEALTH_FACILITY", "WITHIN_HEALTH_SERVICE_AREA"},
            }[cat_id]
            has_in_radius = any(str(m.get("relation_type") or "") in in_radius_rels for m in matches)
            only_outside = not has_in_radius and any(
                (m.get("properties") or {}).get("outside_search_radius")
                or str(m.get("relation_type") or "") in {"NEAREST_TELECOM_INFRA", "NEAREST_FIBER_LINE", "NEAREST_HEALTH_FACILITY"}
                for m in matches
            )
            if only_outside:
                empty_meta = _classify_category_emptiness(
                    cat_id,
                    cat,
                    count=0,
                    nsme_rel_types=nsme_rel_types,
                    matches=matches,
                    probe=referential_probes.get(cat_id) or {},
                )
                empty_meta["maturity"] = "empty"
                empty_meta["official_status"] = "empty"
                empty_meta["status"] = "empty"
                count = 0  # KPI / filtre : 0 dans le rayon ; nearest_context porte le hors rayon
        category_stats.append(
            {
                **cat,
                "count": count,
                "status": empty_meta["status"],
                "maturity": empty_meta["maturity"],
                "empty_reason": empty_meta.get("empty_reason"),
                "integration_case": empty_meta.get("integration_case"),
                "note": empty_meta.get("note") or cat.get("note"),
                "search_executed": empty_meta.get("search_executed"),
                "nearest_context": empty_meta.get("nearest_context"),
                "business_impact": empty_meta.get("business_impact"),
                "official_status": empty_meta.get("official_status") or empty_meta.get("maturity"),
                "visible_default": empty_meta["status"] == "active",
                "filterable": empty_meta["status"] == "active" and cat_id != "site",
            }
        )
        if cat_id != "site":
            probe = referential_probes.get(cat_id) or {}
            domain_statuses.append(
                {
                    "domain": cat_id,
                    "status": empty_meta.get("official_status") or empty_meta.get("maturity"),
                    "reference_available": bool(probe.get("referential_exists") if "referential_exists" in probe else cat.get("available", True)),
                    "search_executed": bool(empty_meta.get("search_executed")),
                    "relation_count": count if cat_id != "site" else 1,
                    "nearest_context": empty_meta.get("nearest_context"),
                    "radius": {
                        "value_m": probe.get("search_radius_m"),
                        "value_km": _km(probe.get("search_radius_m")),
                        "fiber_m": probe.get("fiber_radius_m"),
                        "rule": probe.get("nsme_source"),
                    },
                    "source": probe.get("nsme_source") or cat.get("note"),
                    "confidence": "élevée" if empty_meta.get("maturity") == "operational" else (
                        "moyenne" if empty_meta.get("search_executed") else "à confirmer"
                    ),
                    "message": empty_meta.get("note"),
                    "business_impact": empty_meta.get("business_impact"),
                }
            )

    # Santé / télécom : nearest hors rayon déjà traité dans la classification ci-dessus

    why_panel = _build_why_panel(asset, impact, case, matches, edges)
    decision_summary = _build_decision_summary(asset, impact, case, edges, category_stats)
    kpis = _build_kpis(asset, impact, edges, category_stats, case, referential_probes=referential_probes)
    missing = [
        {
            "category": c["id"],
            "label": c["label"],
            "reason": c.get("note") or (
                "Aucune relation NSME pour ce site"
                if c.get("status") == "empty"
                else "Référentiel non encore intégré"
            ),
            "status": c.get("status"),
        }
        for c in category_stats
        if c["id"] != "site" and c.get("status") in {"empty", "future"}
    ]

    # Enrichir nœuds / arêtes pour panneau détail
    for edge in edges:
        contrib = edge.get("contribution") or {}
        edge["score_contribution"] = {
            "status": contrib.get("status") or "unavailable",
            "display": contrib.get("display"),
            "criterion": contrib.get("criterion"),
            "note": contrib.get("note"),
            "contribution_type": contrib.get("contribution_type") or "contextual_evidence",
            "role_label": contrib.get("role_label") or "Preuve contextuelle",
            "explanation": contrib.get("explanation"),
            "points": contrib.get("points"),
            "maximum": contrib.get("maximum"),
            "weight": contrib.get("weight"),
            "source_document": contrib.get("source_document"),
            "matrix_version": contrib.get("matrix_version"),
            "rule": contrib.get("rule"),
            "fed_criteria": contrib.get("fed_criteria") or [],
        }
        edge["availability_status"] = "success" if edge.get("geometry") else "partial"
        edge["source_date"] = None
        if edge.get("nsme_trace", {}).get("source_need") or edge.get("source_label"):
            edge["detail"] = {
                "relation_type": edge.get("relation_type"),
                "category": edge.get("category"),
                "distance_m": edge.get("distance_m"),
                "population": next(
                    (n.get("population") for n in nodes.values() if n.get("id") == edge.get("target")),
                    None,
                ),
                "confidence": edge.get("confidence"),
                "source": edge.get("source_label"),
                "method": (edge.get("nsme_trace") or {}).get("calculation_method"),
                "why": edge.get("why"),
                "score_contribution": edge["score_contribution"],
            }

    diagnosis = coverage.diagnose_site(
        asset,
        matches=matches,
        radius_m=_safe(
            lambda: __import__("api.services.spatial_matching_service", fromlist=["_radius_for_asset"])._radius_for_asset(
                "fdsu_site"
            ),
            15000,
        ),
        nsme_found=needs.get("_meta", {}).get("status") != "not_found" or bool(matches),
        source=(needs.get("_meta") or {}).get("mode"),
    )
    explain_card = coverage.build_explainability_card(site=asset, diagnosis=diagnosis, case=case)

    return {
        "_meta": {
            "version": ENGINE_VERSION,
            "generated_at": _now(),
            "title_ui": "Analyse d’Impact Territorial",
            "title_technical": "Spatial Decision Graph / Spatial Impact",
            "principle": "Relations exclusivement NSME — aucune arête inventée",
            "asset_id": asset_id,
            "asset_type": asset_type,
            "status": "success" if edges else "partial",
            "classification": diagnosis.get("classification"),
            "renderer": "spatial-decision-graph-v2.1",
        },
        "center": nodes[center_id],
        "nodes": list(nodes.values()),
        "edges": edges,
        "categories": category_stats,
        "presentation_steps": PRESENTATION_STEPS,
        "why_panel": why_panel,
        "decision_summary": decision_summary,
        "kpis": kpis,
        "missing_data": missing,
        "impact": impact.get("impact") or needs.get("impact"),
        "coverage_gain": impact.get("coverage_gain"),
        "explainability": explain_card,
        "coverage_diagnosis": diagnosis,
        "ui": {
            "badge": diagnosis.get("classification_label"),
            "show_partial_graph": diagnosis.get("classification") in {"A", "B"},
        },
        "filters": [
            {
                "id": c["id"],
                "label": c["label"],
                "color": c["color"],
                "symbol": c.get("symbol"),
                "available": c.get("available", True),
                "count": c.get("count", 0),
                "status": c.get("status"),
                "maturity": c.get("maturity"),
                "empty_reason": c.get("empty_reason"),
                "integration_case": c.get("integration_case"),
                "note": c.get("note"),
                "search_executed": c.get("search_executed"),
                "nearest_context": c.get("nearest_context"),
                "business_impact": c.get("business_impact"),
                "official_status": c.get("official_status"),
            }
            for c in category_stats
            if c["id"] != "site"
        ],
        "domain_statuses": domain_statuses,
        "radii": {
            "principal_m": ((impact or {}).get("service_area") or {}).get("service_radius_m")
            or _safe(lambda: __import__("api.services.spatial_matching_service", fromlist=["_radius_for_asset"])._radius_for_asset("fdsu_site"), 15000),
            "by_domain_m": {
                "health": (referential_probes.get("health") or {}).get("search_radius_m"),
                "roads": (referential_probes.get("roads") or {}).get("search_radius_m"),
                "telecom": (referential_probes.get("telecom") or {}).get("search_radius_m"),
                "fiber": (referential_probes.get("telecom") or {}).get("fiber_radius_m"),
                "ccn": (referential_probes.get("ccn") or {}).get("search_radius_m"),
                "fdsu_sites": (referential_probes.get("fdsu_sites") or {}).get("search_radius_m"),
            },
            "source": "spatial_matching_rules.json",
        },
        "data_first": {
            "policy": "DATA_FIRST_INTEGRATION_POLICY",
            "motto": "Chaque décision doit exploiter toutes les connaissances actuellement disponibles, tout en indiquant explicitement les connaissances encore manquantes.",
            "anomalies": [
                {
                    "category": c["id"],
                    "maturity": c.get("maturity"),
                    "empty_reason": c.get("empty_reason"),
                    "note": c.get("note"),
                }
                for c in category_stats
                if c.get("maturity") == "error"
            ],
        },
        "actions": {
            "open_dossier": f"#decision-case/site/{asset_id}",
            "open_twin": f"#territorial-twin/territoire/{asset.get('territoire')}" if asset.get("territoire") else None,
            "open_workspace": "#decision-detail/sites-prioritaires",
            "present": True,
        },
        "counts": {
            "nodes": len(nodes),
            "edges": len(edges),
            "categories_active": sum(1 for c in category_stats if c.get("status") == "active" and c["id"] != "site"),
        },
    }


def _build_decision_summary(asset, impact, case, edges, categories) -> dict[str, Any]:
    name = asset.get("site_name") or asset.get("site_code") or "ce site"
    impact_body = (impact or {}).get("impact") or impact or {}
    factors = []
    locs = impact_body.get("localities_impacted")
    pop = impact_body.get("population_impacted")
    loc_edges = sum(1 for e in edges if e.get("category") == "localities")
    if locs:
        factors.append(f"{locs} localité(s) non couverte(s) dans le rayon de service")
    elif loc_edges:
        factors.append(f"{loc_edges} localité(s) reliée(s) via le NSME")
    if pop:
        factors.append(f"population concernée estimée à {pop}")
    # Facteurs issus des catégories actives réellement peuplées (hors site / besoins)
    for c in categories:
        if c.get("status") != "active" or c["id"] in {"site", "needs", "localities", "population"}:
            continue
        if not c.get("count"):
            continue
        lab = str(c.get("label") or c["id"]).lower()
        if lab not in " ".join(factors).lower():
            factors.append(f"{c['count']} relation(s) « {c['label']} »")
        if len(factors) >= 3:
            break
    score = (case or {}).get("score") or {}
    score_val = score.get("global") if isinstance(score, dict) else score
    prio = None
    if isinstance(score, dict):
        prio = score.get("priority_label") or score.get("priority_level")
    prio = prio or asset.get("priority_level_label") or asset.get("priority_level")

    if factors:
        text = (
            f"Le moteur recommande une attention prioritaire pour « {name} » "
            f"principalement en raison de {', '.join(factors[:3])}. "
            "Les relations ci-dessous exposent les infrastructures, besoins et populations réellement sourcés."
        )
        status = "success"
    else:
        text = (
            f"Analyse d’impact territorial pour « {name} » — "
            "les correspondances spatiales disponibles sont affichées ; certains référentiels restent partiels."
        )
        status = "partial"

    return {
        "text": text,
        "factors": factors,
        "priority": prio,
        "score": score_val,
        "confidence": ((case or {}).get("confidence") or {}).get("label")
        if isinstance((case or {}).get("confidence"), dict)
        else ((case or {}).get("confidence") or impact_body.get("confidence_level")),
        "status": status,
        "sources": ["NSME", "Decision Engine", "NCI"],
    }


def _build_kpis(asset, impact, edges, categories, case, referential_probes=None) -> list[dict[str, Any]]:
    impact_body = (impact or {}).get("impact") or impact or {}
    service_area = (impact or {}).get("service_area") or {}
    probes = referential_probes or {}

    def kpi(kid, label, value, *, unit=None, status="success", note=None, detail=None):
        if status == "unavailable":
            return {
                "id": kid,
                "label": label,
                "value": None,
                "display": "Non disponible",
                "status": status,
                "note": note,
                "detail": detail,
            }
        if value is None:
            return {
                "id": kid,
                "label": label,
                "value": None,
                "display": "Non disponible",
                "status": "unavailable",
                "note": note,
                "detail": detail,
            }
        return {
            "id": kid,
            "label": label,
            "value": value,
            "display": f"{value}{(' ' + unit) if unit else ''}",
            "status": status,
            "note": note,
            "detail": detail,
        }

    by_cat = {c["id"]: c for c in categories}
    radius = (
        service_area.get("service_radius_m")
        or impact_body.get("service_radius_m")
        or impact_body.get("radius_m")
    )
    if radius is None:
        try:
            from api.services.spatial_matching_service import _radius_for_asset

            radius = _radius_for_asset("fdsu_site")
        except Exception:
            radius = 15000

    radius_detail = {
        "principal_m": radius,
        "principal_km": _km(radius),
        "by_domain_km": {
            "santé": _km((probes.get("health") or {}).get("search_radius_m") or 5000),
            "routes": _km((probes.get("roads") or {}).get("search_radius_m") or 50000),
            "télécom": _km((probes.get("telecom") or {}).get("search_radius_m") or 25000),
            "fibre": _km((probes.get("telecom") or {}).get("fiber_radius_m") or 5000),
        },
        "rule": "configurable_buffer",
        "source": "spatial_matching_rules.json",
    }
    radius_note = (
        f"Rayon principal : {_km(radius)} km · "
        f"Santé : {radius_detail['by_domain_km']['santé']} km · "
        f"Routes : {radius_detail['by_domain_km']['routes']} km · "
        f"Télécom : {radius_detail['by_domain_km']['télécom']} km"
    )

    def cat_kpi(kid, label, cat_id, *, future_note=None):
        cat = by_cat.get(cat_id) or {}
        status = cat.get("status")
        if status == "future" or cat.get("available") is False:
            return kpi(kid, label, None, status="unavailable", note=future_note or cat.get("note"))
        count = cat.get("count")
        if count is None:
            return kpi(kid, label, None, status="unavailable", note=cat.get("note"))
        note = cat.get("note") if count == 0 or cat.get("maturity") in {"empty", "partial", "demonstration"} else None
        nearest = cat.get("nearest_context")
        detail = {
            "maturity": cat.get("maturity"),
            "nearest_context": nearest,
            "business_impact": cat.get("business_impact"),
            "search_executed": cat.get("search_executed"),
        }
        display_status = "success"
        if cat.get("maturity") == "demonstration":
            display_status = "partial"
        elif count == 0 and cat.get("maturity") == "empty":
            display_status = "empty"
        return kpi(kid, label, count, status=display_status, note=note, detail=detail)

    locs_val = impact_body.get("localities_impacted")
    if locs_val is None:
        locs_val = by_cat.get("localities", {}).get("count")

    return [
        kpi(
            "radius",
            "Rayon / zone d’influence",
            radius,
            unit="m",
            status="success",
            note=radius_note,
            detail=radius_detail,
        ),
        kpi("localities", "Localités concernées", locs_val if locs_val is not None else 0, status="success"),
        kpi(
            "population",
            "Population concernée",
            impact_body.get("population_impacted"),
            status="success" if impact_body.get("population_impacted") is not None else "unavailable",
        ),
        cat_kpi("health", "Établissements de santé", "health"),
        cat_kpi(
            "education",
            "Écoles",
            "education",
            future_note="Projection CENI SCHOOL — registre ministériel non officiel",
        ),
        cat_kpi(
            "ceni",
            "Signal CENI",
            "ceni",
            future_note="Signal institutionnel — non pondéré dans le scoring",
        ),
        cat_kpi("telecom", "Infrastructures télécom", "telecom"),
        cat_kpi("roads", "Routes principales", "roads"),
        cat_kpi("ccn", "CCN", "ccn"),
        cat_kpi("admin", "Services administratifs", "admin"),
        kpi(
            "data_quality",
            "Qualité des données",
            ((case or {}).get("confidence") or {}).get("label")
            if isinstance((case or {}).get("confidence"), dict)
            else None,
            status="partial",
        ),
    ]


def _build_why_panel(asset, impact, case, matches, edges) -> dict[str, Any]:
    impact_body = (impact or {}).get("impact") or impact or {}
    blocks = []

    def block(title: str, score: Any, justification: str, source: str, status: str = "success"):
        blocks.append(
            {
                "title": title,
                "score": score if score not in (None, "") else "—",
                "justification": justification,
                "source": source,
                "status": status,
            }
        )

    pop = impact_body.get("population_impacted")
    locs = impact_body.get("localities_impacted")
    block(
        "Population",
        f"{pop if pop is not None else '—'} pers. / {locs if locs is not None else '—'} localités",
        "Population et localités reliées au site via les correspondances NSME SERVES_LOCALITY.",
        "NSME · NCI",
        "success" if pop is not None else "partial",
    )

    road_edges = [e for e in edges if e.get("category") == "roads"]
    if road_edges:
        acc = next((e for e in road_edges if e.get("relation_type") == "ROAD_ACCESSIBILITY"), road_edges[0])
        block(
            "Accessibilité",
            acc.get("contribution", {}).get("display") or f"{acc.get('distance_m')} m",
            acc.get("why") or "Accessibilité routière issue du moteur Transport / NSME.",
            acc.get("source_label") or "Transport · NSME",
        )
    else:
        block("Accessibilité", "—", "Aucune relation routière NSME disponible pour ce site.", "Transport · NSME", "unavailable")

    health_n = sum(1 for e in edges if e.get("category") == "health")
    block(
        "Santé",
        f"{health_n} relation(s)",
        "Proximités santé dérivées des correspondances NSME lorsque l’infrastructure est renseignée.",
        "NSME · Santé",
        "success" if health_n else "unavailable",
    )

    telecom_n = sum(1 for e in edges if e.get("category") == "telecom")
    block(
        "Télécommunications",
        f"{telecom_n} relation(s)",
        "Fibre / backbone proches lorsqu’ils sont présents dans les matches NSME.",
        "NSME · Télécom",
        "success" if telecom_n else "unavailable",
    )

    block(
        "Services",
        f"{sum(1 for e in edges if e.get('category') in {'admin', 'ccn', 'education', 'markets'})} relation(s)",
        "Services administratifs, CCN et services futurs lorsqu’ils sont sourcés.",
        "NSME",
        "partial",
    )

    score = (case or {}).get("score") or {}
    score_val = score.get("global") if isinstance(score, dict) else score
    prio = score.get("priority_label") if isinstance(score, dict) else None
    block(
        "Priorité",
        f"{score_val if score_val is not None else '—'} · {prio or '—'}",
        ((case or {}).get("summary") or {}).get("text")
        if isinstance((case or {}).get("summary"), dict)
        else ((case or {}).get("summary") or "Priorité issue du moteur de décision lorsque disponible."),
        "Decision Engine",
        "success" if score_val is not None else "partial",
    )

    block(
        "Investissements",
        asset.get("program_code") or "—",
        "Programme FDSU associé au site — suivi d’investissement via le dossier de décision.",
        "Programmes FDSU",
        "partial",
    )

    return {
        "title": "Pourquoi ce site ?",
        "subtitle": asset.get("site_name") or asset.get("site_code"),
        "blocks": blocks,
    }


def build_presentation(asset_type: str, asset_id: str, *, program_code: str | None = None) -> dict[str, Any] | None:
    graph = build_graph(asset_type, asset_id, program_code=program_code)
    if not graph:
        return None
    steps = []
    for step in PRESENTATION_STEPS:
        cats = set(step["categories"])
        if "*" in cats:
            node_ids = [n["id"] for n in graph["nodes"]]
            edge_ids = [e["id"] for e in graph["edges"]]
        else:
            node_ids = [n["id"] for n in graph["nodes"] if n.get("category") in cats or n.get("kind") == "site" and "site" in cats]
            edge_ids = [e["id"] for e in graph["edges"] if e.get("category") in cats]
        narrative = {
            "site": "Voici le site proposé à l’arbitrage.",
            "population": "Ces populations et localités expliquent pourquoi une intervention est pertinente.",
            "health": "Les services de santé à proximité complètent le diagnostic territorial.",
            "telecom": "Les infrastructures télécom proches conditionnent le potentiel de connectivité.",
            "roads": "L’accessibilité routière détermine la faisabilité opérationnelle.",
            "ccn": "L’ancrage CCN et administratif situe le site dans le tissu institutionnel.",
            "recommendation": "Synthèse : les relations visibles justifient la priorité et les bénéfices attendus.",
        }.get(step["id"], step["label"])
        steps.append(
            {
                **step,
                "narrative": narrative,
                "reveal_nodes": node_ids,
                "reveal_edges": edge_ids,
                "duration_ms": 2200 if step["id"] != "recommendation" else 2800,
            }
        )
    return {
        "_meta": graph["_meta"],
        "graph": graph,
        "steps": steps,
        "autoplay": True,
    }
