"""Spatial Decision Graph v2.0 — composition NSME + Decision (pas de liens inventés).

Produit un graphe décisionnel territorial explicable pour l’Analyse d’Impact Territorial.
Le nom technique interne reste « Spatial Impact / SDG ».
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

ENGINE_VERSION = "sdg-2.0.0"

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
        "label": "Population",
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
        "color": "#7c3aed",
        "symbol": "hub",
        "available": True,
        "relation_types": ["CONNECTS_CCN"],
    },
    "admin": {
        "id": "admin",
        "label": "Services administratifs",
        "color": "#64748b",
        "symbol": "building",
        "available": True,
        "relation_types": ["NEAR_ADMINISTRATION"],
    },
    "education": {
        "id": "education",
        "label": "Éducation",
        "color": "#0d9488",
        "symbol": "school",
        "available": False,
        "relation_types": ["NEAR_SCHOOL"],
        "note": "Référentiel Éducation non encore intégré",
    },
    "energy": {
        "id": "energy",
        "label": "Énergie",
        "color": "#ca8a04",
        "symbol": "bolt",
        "available": False,
        "relation_types": [],
        "note": "Référentiel Énergie non encore intégré",
    },
    "markets": {
        "id": "markets",
        "label": "Marchés",
        "color": "#db2777",
        "symbol": "market",
        "available": False,
        "relation_types": ["NEAR_MARKET"],
        "note": "Référentiel Marchés non encore intégré",
    },
    "needs": {
        "id": "needs",
        "label": "Besoins critiques",
        "color": "#dc2626",
        "symbol": "alert",
        "available": True,
        "relation_types": [],
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
        "why": "Un établissement de santé à proximité influence l’accessibilité aux services.",
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
        "color": "#7c3aed",
        "weight": 3,
        "dash": None,
        "why": "La relation avec un CCN structure l’ancrage communautaire (Site FDSU ≠ CCN).",
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
        "display": "Non chiffrée dans le score actuel",
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
    if not matches and not needs:
        return None

    impact = _safe(lambda: nsme.get_asset_impact(asset_id), {}) or {}
    case = _safe(lambda: eds.get_decision_case(asset_id, asset_type=asset_type, program_code=program_code), {}) or {}

    asset = needs.get("asset") or (case.get("asset") if case else None)
    if not asset and str(asset_id).isdigit():
        sites = _safe(lambda: nsme.list_fdsu_sites(asset_id=int(asset_id), limit=1), []) or []
        asset = sites[0] if sites else {"site_id": asset_id, "site_name": str(asset_id)}

    asset = asset or {"site_id": asset_id, "site_name": str(asset_id)}
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
            "name": asset.get("site_name") or asset.get("site_code") or str(asset_id),
            "description": "Site FDSU analysé — nœud central du raisonnement territorial.",
            "role": "Point d’intervention proposé",
            "distance_m": 0,
            "state": asset.get("priority_level_label") or asset.get("priority_level") or "priorisé",
            "longitude": a_lon,
            "latitude": a_lat,
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
                "distance_m": match.get("distance_m"),
                "state": match.get("priority_level") or props.get("class_label") or match.get("confidence_level") or "observé",
                "longitude": need_lon,
                "latitude": need_lat,
                "population": match.get("population_impacted"),
                "need_id": match.get("need_id"),
                "relation_type": rel,
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
        edges.append(
            {
                "id": f"edge:{rel}:{match.get('need_id') or idx}",
                "source": center_id,
                "target": node_id,
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
    for cat_id, cat in CATEGORIES.items():
        category_stats.append(
            {
                **cat,
                "count": 1 if cat_id == "site" else counts.get(cat_id, 0),
                "visible_default": cat.get("available", False) and (cat_id == "site" or counts.get(cat_id, 0) > 0 or not cat.get("available")),
            }
        )

    why_panel = _build_why_panel(asset, impact, case, matches, edges)

    return {
        "_meta": {
            "version": ENGINE_VERSION,
            "generated_at": _now(),
            "title_ui": "Analyse d’Impact Territorial",
            "title_technical": "Spatial Decision Graph / Spatial Impact",
            "principle": "Relations exclusivement NSME — aucune arête inventée",
            "asset_id": asset_id,
            "asset_type": asset_type,
        },
        "center": nodes[center_id],
        "nodes": list(nodes.values()),
        "edges": edges,
        "categories": category_stats,
        "presentation_steps": PRESENTATION_STEPS,
        "why_panel": why_panel,
        "impact": impact.get("impact") or needs.get("impact"),
        "coverage_gain": impact.get("coverage_gain"),
        "filters": [
            {"id": c["id"], "label": c["label"], "color": c["color"], "available": c.get("available", True), "count": c.get("count", 0)}
            for c in category_stats
            if c["id"] != "site"
        ],
        "actions": {
            "open_dossier": f"#decision-case/site/{asset_id}",
            "open_twin": f"#territorial-twin/territoire/{asset.get('territoire')}" if asset.get("territoire") else None,
            "open_workspace": "#decision-detail/sites-prioritaires",
            "present": True,
        },
    }


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
