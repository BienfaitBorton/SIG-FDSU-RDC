"""Spatial Decision Graph v2.0 — composition NSME + Decision (pas de liens inventés).

Produit un graphe décisionnel territorial explicable pour l’Analyse d’Impact Territorial.
Le nom technique interne reste « Spatial Impact / SDG ».
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

ENGINE_VERSION = "sdg-2.1.0"

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
        "relation_types": ["NEAR_FDSU_SITE"],
        "note": "Affiché uniquement si le NSME fournit une relation entre sites",
    },
    "health": {
        "id": "health",
        "label": "Santé",
        "color": "#16a34a",
        "symbol": "health",
        "available": True,
        "relation_types": ["NEAR_HEALTH_FACILITY"],
    },
    "telecom": {
        "id": "telecom",
        "label": "Télécommunications",
        "color": "#06b6d4",
        "symbol": "tower",
        "available": True,
        "relation_types": ["NEAR_FIBER", "NEAR_BACKBONE"],
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
        "available": False,
        "relation_types": ["NEAR_SCHOOL"],
        "note": "Éducation — données non encore intégrées",
    },
    "energy": {
        "id": "energy",
        "label": "Énergie",
        "color": "#ca8a04",
        "symbol": "bolt",
        "available": False,
        "relation_types": [],
        "note": "Énergie — données non encore intégrées",
    },
    "markets": {
        "id": "markets",
        "label": "Marchés / économie",
        "color": "#db2777",
        "symbol": "market",
        "available": False,
        "relation_types": ["NEAR_MARKET"],
        "note": "Marchés / économie — données non encore intégrées",
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
    "NEAR_SCHOOL": {
        "category": "education",
        "label": "Proximité école",
        "color": "#0d9488",
        "weight": 2,
        "dash": "4 4",
        "why": "Une école proche complète le tissu de services publics.",
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
        "label": "Backbone proche",
        "color": "#0891b2",
        "weight": 2,
        "dash": "6 4",
        "why": "Un backbone proche structure le raccordement national.",
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
        "nsme_wired": False,
        "nsme_source": None,
        "search_radius_m": None,
    }

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

    tel_stats = _safe(
        lambda: __import__("api.services.telecom_service", fromlist=["get_statistics"]).get_statistics(),
        {},
    ) or {}
    tel_n = tel_stats.get("total") or tel_stats.get("infrastructure_total") or tel_stats.get("count")
    probes["telecom"] = {
        "referential_exists": bool(tel_n and int(tel_n) > 0) or Path("data/sectoral/telecom").exists(),
        "record_count": tel_n,
        "nsme_wired": True,
        "nsme_source": "NCI infra / fibre labels",
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
        "nsme_source": "demo_ccn.json",
    }

    probes["localities"] = {
        "referential_exists": Path("data/coverage/localities_uncovered.jsonl").exists(),
        "record_count": None,
        "nsme_wired": True,
        "nsme_source": "NCI localities_uncovered",
    }
    probes["population"] = dict(probes["localities"])
    probes["fdsu_sites"] = {
        "referential_exists": True,
        "record_count": None,
        "nsme_wired": False,
        "nsme_source": None,
    }
    probes["admin"] = {"referential_exists": True, "nsme_wired": True, "nsme_source": "NCI / admin derived"}
    probes["needs"] = {"referential_exists": True, "nsme_wired": True, "nsme_source": "CANDIDATE_FOR_MISSION"}
    probes["education"] = {"referential_exists": False, "nsme_wired": False}
    probes["energy"] = {"referential_exists": False, "nsme_wired": False}
    probes["markets"] = {"referential_exists": False, "nsme_wired": False}
    return probes


def _classify_category_emptiness(
    cat_id: str,
    cat: dict[str, Any],
    *,
    count: int,
    nsme_rel_types: set[str],
    matches: list[dict[str, Any]],
    probe: dict[str, Any],
) -> dict[str, Any]:
    """Classe CAS 1–4 Data First pour une catégorie SDG."""
    rel_types = set(cat.get("relation_types") or [])
    produced = bool(rel_types & nsme_rel_types) or count > 0

    if cat_id == "site" or count > 0:
        return {
            "status": "active",
            "maturity": "operational",
            "empty_reason": None,
            "integration_case": None,
            "note": cat.get("note"),
        }

    if not cat.get("available", True):
        return {
            "status": "future",
            "maturity": "integrating",
            "empty_reason": "referential_absent",
            "integration_case": 3,
            "note": cat.get("note")
            or f"{cat.get('label')} — données non encore intégrées (En cours d’intégration).",
        }

    # Catégorie disponible mais count=0
    ref_exists = probe.get("referential_exists")
    nsme_wired = probe.get("nsme_wired", True)
    radius_m = probe.get("search_radius_m")
    radius_km = round(float(radius_m) / 1000, 1) if radius_m else None

    if ref_exists and not nsme_wired:
        return {
            "status": "empty",
            "maturity": "anomaly",
            "empty_reason": "search_not_executed",
            "integration_case": 2,
            "note": (
                f"Anomalie d’intégration — le référentiel « {cat.get('label')} » existe, "
                "mais aucune recherche spatiale NSME n’est câblée pour cette catégorie."
            ),
        }


    if ref_exists and nsme_wired and not produced and matches:
        suffix = f" — {probe.get('record_count')} objets" if probe.get("record_count") else ""
        return {
            "status": "empty",
            "maturity": "partial",
            "empty_reason": "no_relations_found",
            "integration_case": 1,
            "note": (
                f"Aucune relation « {cat.get('label')} » trouvée pour ce site "
                f"(recherche NSME exécutée ; référentiel disponible{suffix})."
            ),
        }

    if ref_exists and nsme_wired and not matches:
        return {
            "status": "empty",
            "maturity": "anomaly",
            "empty_reason": "search_not_executed",
            "integration_case": 2,
            "note": (
                "Anomalie d’intégration — le référentiel existe, mais le NSME n’a renvoyé aucune "
                "correspondance pour ce site (rafraîchissement / mode DB / table d’analyse à vérifier)."
            ),
        }

    if ref_exists and nsme_wired and not produced:
        return {
            "status": "empty",
            "maturity": "partial",
            "empty_reason": "no_relations_found",
            "integration_case": 1,
            "note": f"Aucune relation « {cat.get('label')} » pour ce site après recherche spatiale.",
        }

    return {
        "status": "empty",
        "maturity": "partial",
        "empty_reason": "no_relations_found",
        "integration_case": 1,
        "note": cat.get("note") or f"Aucune relation pour « {cat.get('label')} ».",
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
    }
    if text in mapping:
        return mapping[text]
    if text.startswith("data/") or "." in text and "/" not in text[:20]:
        return text.replace("data/", "").replace("_", " ")
    return text or "NSME"


def _contribution_from_decision(relation_type: str, match: dict[str, Any], case: dict[str, Any] | None) -> dict[str, Any]:
    """Relie une relation NSME à un critère du Decision Engine si disponible — jamais inventé."""
    proxy_pop = match.get("population_impacted")
    style = RELATION_STYLES.get(relation_type) or {}
    base = {
        "status": "unavailable",
        "display": "Preuve contextuelle — contribution directe non calculée",
        "proxy_population": proxy_pop,
        "note": "La contribution au score n’est affichée que lorsqu’un critère décisionnel sourcé existe.",
    }
    if not case:
        if proxy_pop is not None:
            return {
                **base,
                "status": "proxy",
                "display": f"Population concernée : {proxy_pop}",
                "note": "Indicateur populationnel NSME — pas un point de score inventé.",
            }
        return base

    justification = case.get("justification") or case.get("criteria") or []
    if isinstance(justification, dict):
        justification = list(justification.values())
    cat = style.get("category") or _category_for_relation(relation_type)
    keywords = {
        "population": ("population", "couverture", "déficit"),
        "localities": ("localit", "couverture", "déficit"),
        "health": ("santé", "sante", "health"),
        "telecom": ("télécom", "telecom", "fibre", "connect"),
        "roads": ("route", "accessib", "transport"),
        "ccn": ("ccn", "communaut"),
        "admin": ("admin", "contexte"),
        "needs": ("mission", "besoin", "priorit"),
    }.get(cat, ())
    for item in justification:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or item.get("criterion_id") or "").lower()
        if any(k in label for k in keywords):
            return {
                "status": "mapped",
                "display": item.get("contribution_display") or item.get("score_display") or str(item.get("contribution") or "—"),
                "criterion": item.get("label") or item.get("criterion_id"),
                "why": item.get("why") or item.get("description"),
                "proxy_population": proxy_pop,
                "note": "Contribution lue depuis le moteur de décision (critère sourcé).",
            }
    if proxy_pop is not None:
        return {
            **base,
            "status": "proxy",
            "display": f"Population concernée : {proxy_pop}",
            "note": "Indicateur populationnel NSME — pas un point de score inventé.",
        }
    return base


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
    if not matches and needs.get("_meta", {}).get("status") == "not_found":
        return None

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
        style = RELATION_STYLES.get(rel) or {
            "category": "needs",
            "label": rel,
            "color": "#dc2626",
            "weight": 2,
            "dash": "4 4",
            "why": "Relation spatiale issue du moteur NSME.",
        }
        cat = style["category"]
        props = match.get("properties") or {}
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
        category_stats.append(
            {
                **cat,
                "count": count,
                "status": empty_meta["status"],
                "maturity": empty_meta["maturity"],
                "empty_reason": empty_meta.get("empty_reason"),
                "integration_case": empty_meta.get("integration_case"),
                "note": empty_meta.get("note") or cat.get("note"),
                "visible_default": empty_meta["status"] == "active",
                "filterable": empty_meta["status"] == "active" and cat_id != "site",
            }
        )

    why_panel = _build_why_panel(asset, impact, case, matches, edges)
    decision_summary = _build_decision_summary(asset, impact, case, edges, category_stats)
    kpis = _build_kpis(asset, impact, edges, category_stats, case)
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
            }
            for c in category_stats
            if c["id"] != "site"
        ],
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
                if c.get("maturity") == "anomaly"
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


def _build_kpis(asset, impact, edges, categories, case) -> list[dict[str, Any]]:
    impact_body = (impact or {}).get("impact") or impact or {}

    def kpi(kid, label, value, *, unit=None, status="success", note=None):
        if status == "unavailable":
            return {"id": kid, "label": label, "value": None, "display": "Non disponible", "status": status, "note": note}
        if value is None:
            return {"id": kid, "label": label, "value": None, "display": "Non disponible", "status": "unavailable", "note": note}
        return {
            "id": kid,
            "label": label,
            "value": value,
            "display": f"{value}{(' ' + unit) if unit else ''}",
            "status": status,
            "note": note,
        }

    by_cat = {c["id"]: c for c in categories}
    radius = impact_body.get("service_radius_m") or impact_body.get("radius_m")

    def cat_kpi(kid, label, cat_id, *, future_note=None):
        cat = by_cat.get(cat_id) or {}
        status = cat.get("status")
        if status == "future" or cat.get("available") is False:
            return kpi(kid, label, None, status="unavailable", note=future_note or cat.get("note"))
        count = cat.get("count")
        if count is None:
            return kpi(kid, label, None, status="unavailable", note=cat.get("note"))
        # count == 0 → zéro calculé (référentiel intégré, aucune relation pour ce site)
        return kpi(kid, label, count, status="success", note=cat.get("note") if count == 0 else None)

    locs_val = impact_body.get("localities_impacted")
    if locs_val is None:
        locs_val = by_cat.get("localities", {}).get("count")

    return [
        kpi("radius", "Rayon / zone d’influence", radius, unit="m", status="success" if radius is not None else "unavailable"),
        kpi("localities", "Localités concernées", locs_val if locs_val is not None else 0, status="success"),
        kpi("population", "Population concernée", impact_body.get("population_impacted"), status="success" if impact_body.get("population_impacted") is not None else "unavailable"),
        cat_kpi("health", "Établissements de santé", "health"),
        cat_kpi("education", "Écoles", "education", future_note="Éducation — données non encore intégrées"),
        cat_kpi("telecom", "Infrastructures télécom", "telecom"),
        cat_kpi("roads", "Routes principales", "roads"),
        cat_kpi("ccn", "CCN", "ccn"),
        cat_kpi("admin", "Services administratifs", "admin"),
        kpi(
            "data_quality",
            "Qualité des données",
            ((case or {}).get("confidence") or {}).get("label") if isinstance((case or {}).get("confidence"), dict) else None,
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
