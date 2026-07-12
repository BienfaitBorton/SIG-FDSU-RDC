"""Decision Scenarios Engine v1.2 — orchestration métier sans logique dupliquée.

Chaque scénario compose des moteurs déjà livrés :
Decision Engine, Explainable Decision, NSME, TI, CCN, Knowledge Hub (via dossiers).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from api.services import (
    ccn_capability_service,
    ccn_operational_service,
    decision_demo_service,
    decision_engine_service,
    explainable_decision_service,
    fdsu_site_priority_service,
    spatial_matching_service,
    territorial_intelligence_service,
)

ENGINE_VERSION = "decision-scenarios-1.2.0"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _link(label: str, href: str, kind: str = "api") -> dict[str, str]:
    return {"label": label, "href": href, "kind": kind}


def _action(action_id: str, label: str, *, route: str | None = None, hash_route: str | None = None) -> dict[str, Any]:
    return {
        "id": action_id,
        "label": label,
        "route": route,
        "hash": hash_route,
    }


def _kpi(label: str, value: Any, *, color: str = "blue", note: str | None = None) -> dict[str, Any]:
    return {"label": label, "value": value, "color": color, "note": note}


def _safe(fn: Callable[[], Any], default: Any = None) -> Any:
    try:
        return fn()
    except Exception:
        return default


def _top_site(program_code: str = "sites_40", limit: int = 5) -> dict[str, Any] | None:
    payload = _safe(lambda: fdsu_site_priority_service.top_priorities(program_code, limit=limit), {}) or {}
    sites = payload.get("sites") or []
    return sites[0] if sites else None


def _site_id(site: dict[str, Any] | None) -> str | None:
    if not site:
        return None
    for key in ("site_id", "id", "site_code", "code"):
        if site.get(key) is not None:
            return str(site[key])
    return None


def _first_territory_id() -> str | None:
    # Démo TI connue, sinon premier territoire Master Registry
    demo = "TERRITOIRE-05-002"
    profile = _safe(lambda: territorial_intelligence_service.build_territorial_profile(demo))
    if profile:
        return demo
    listed = _safe(lambda: territorial_intelligence_service.list_territories(limit=5), {}) or {}
    items = listed.get("items") or listed.get("territories") or []
    if items:
        return items[0].get("territory_id")
    return None


# ——— Catalog ———

SCENARIO_CATALOG: list[dict[str, Any]] = [
    {
        "id": "invest_priority",
        "code": "A",
        "title": "Où investir en priorité ?",
        "question": "Quels sites FDSU financer en premier selon la matrice de priorisation ?",
        "audience": ["DG", "partenaires", "équipes opérationnelles"],
        "engines": ["decision_engine", "fdsu_site_priority", "explain_kpi"],
    },
    {
        "id": "ccn_implantation",
        "code": "B",
        "title": "Où implanter un nouveau CCN ?",
        "question": "Où préparer l’implantation d’un Centre Communautaire Numérique ?",
        "audience": ["DG", "partenaires"],
        "engines": ["ccn_doctrine", "ccn_extensions", "territorial_intelligence"],
    },
    {
        "id": "territory_priority",
        "code": "C",
        "title": "Pourquoi ce territoire est-il prioritaire ?",
        "question": "Quelles justifications rendent ce territoire prioritaire pour le FDSU ?",
        "audience": ["DG", "équipes territoriales"],
        "engines": ["territorial_intelligence", "explainable_decision"],
    },
    {
        "id": "investment_impact",
        "code": "D",
        "title": "Quel sera l’impact de cet investissement ?",
        "question": "Quel impact populationnel et spatial attendre d’un investissement sur un site prioritaire ?",
        "audience": ["DG", "partenaires"],
        "engines": ["spatial_matching", "explainable_decision"],
    },
    {
        "id": "dg_dossier",
        "code": "E",
        "title": "Préparer un dossier de décision pour le DG",
        "question": "Assembler automatiquement un dossier de décision complet et justifié ?",
        "audience": ["DG"],
        "engines": ["explainable_decision", "decision_case", "pdf_template"],
    },
]


def list_scenarios() -> dict[str, Any]:
    return {
        "_meta": {
            "title": "Scénarios décisionnels FDSU",
            "version": ENGINE_VERSION,
            "count": len(SCENARIO_CATALOG),
            "computed_at": _now(),
        },
        "scenarios": SCENARIO_CATALOG,
    }


def get_scenario(scenario_id: str) -> dict[str, Any] | None:
    needle = str(scenario_id or "").strip().lower()
    for item in SCENARIO_CATALOG:
        if item["id"] == needle or item["code"].lower() == needle:
            return item
    return None


# ——— Runners (orchestration only) ———

def _run_invest_priority(context: dict[str, Any]) -> dict[str, Any]:
    program = context.get("program_code") or "sites_40"
    national = _safe(decision_engine_service.get_national_panel_payload, {}) or {}
    synthesis = national.get("synthesis") or {}
    top = _safe(lambda: fdsu_site_priority_service.top_priorities(program, limit=10), {}) or {}
    sites = top.get("sites") or []
    explain = _safe(lambda: decision_demo_service.get_explain_kpi_payload("sites_priority"), {}) or {}
    kpi = (explain.get("kpi") or {}) if isinstance(explain, dict) else {}

    recommendations = []
    for site in sites[:5]:
        sid = _site_id(site)
        recommendations.append(
            {
                "title": site.get("site_name") or site.get("name") or f"Site {sid}",
                "detail": (
                    f"Priorité {site.get('priority_level_label') or site.get('priority_level') or '—'} "
                    f"— score {site.get('priority_score', '—')}"
                ),
                "asset_id": sid,
                "hash": f"decision-case/site/{sid}" if sid else None,
            }
        )

    categories = [str(s.get("priority_level") or "n/d") for s in sites[:8]]
    values = [float(s.get("priority_score") or 0) for s in sites[:8]]

    return {
        "executive_summary": (
            f"Sur le programme {program}, {len(sites)} sites figurent parmi les priorités nationales. "
            f"Synthèse : {synthesis.get('sites_priority', '—')} sites prioritaires, "
            f"{synthesis.get('sites_critical', '—')} critiques (panneau national)."
        ),
        "data_used": [
            _link("Scores sites FDSU", "/api/decision/site-scores"),
            _link("Top priorités", f"/api/decision/sites/top-priorities?program_code={program}"),
            _link("Panneau national", "/api/decision/national-panel"),
            _link("KPI sites prioritaires", "/api/decision/explain-kpi?kpi_key=sites_priority"),
            _link("Matrice de priorisation", "data/business/priority_matrix.json", "file"),
            _link("Accessibilité transport", "/api/transport/formula"),
            _link("Qualité routes", "/api/transport/quality"),
        ],
        "analysis": {
            "program_code": program,
            "top_count": len(sites),
            "summary": top.get("summary"),
            "kpi_definition": kpi.get("definition"),
        },
        "kpis": [
            _kpi("Sites prioritaires", synthesis.get("sites_priority"), color="orange"),
            _kpi("Sites critiques", synthesis.get("sites_critical"), color="red"),
            _kpi("Sites FDSU", synthesis.get("sites_fdsu"), color="blue"),
            _kpi("Top listés", len(sites), color="green", note=program),
        ],
        "charts": {
            "stacked": {
                "title": "Scores des sites prioritaires",
                "categories": [s.get("site_name") or s.get("site_code") or str(_site_id(s)) for s in sites[:8]],
                "series": [{"label": "Score", "color": "orange", "values": values or [0]}],
            }
        },
        "map": {
            "label": "Carte priorisation",
            "hash": "decision-view",
            "tab": "priorisation",
            "hint": "Ouvrir l’onglet Priorisation pour la carte synchronisée des sites scorés.",
        },
        "justification": {
            "why": kpi.get("calculation_method") or "Score multicritère issu du moteur de décision FDSU.",
            "confidence": kpi.get("confidence") or "medium",
            "doctrine": "DOCTRINE_SITES_FDSU",
            "limitations": kpi.get("limitations"),
        },
        "recommendations": recommendations or [
            {"title": "Aucune priorité calculée", "detail": "Vérifier le recalcul des scores sites.", "hash": "decision-view"}
        ],
        "actions": [
            _action("open_priorisation", "Ouvrir la priorisation", hash_route="decision-view"),
            _action("open_detail", "Analyse détaillée des sites prioritaires", hash_route="decision-detail/sites-prioritaires"),
            _action("open_workspace", "Espace d’analyse", hash_route="decision-workspace/sites-prioritaires"),
        ],
        "visualizations": ["kpi_strip", "stacked_bar", "priority_map", "recommendation_list"],
    }


def _run_ccn_implantation(context: dict[str, Any]) -> dict[str, Any]:
    doctrine = _safe(ccn_operational_service.doctrine_payload, {}) or {}
    extensions_raw = _safe(ccn_capability_service.decision_extension_points, []) or []
    extensions = extensions_raw if isinstance(extensions_raw, list) else (
        extensions_raw.get("extensions") or extensions_raw.get("points") or []
    )
    territory_id = context.get("territory_id") or _first_territory_id()
    reco = (
        _safe(lambda: territorial_intelligence_service.build_recommendations(territory_id), {})
        if territory_id
        else {}
    ) or {}

    items = reco.get("recommendations") or reco.get("items") or []
    recommendations = []
    for item in items[:5]:
        if isinstance(item, dict):
            recommendations.append(
                {
                    "title": item.get("title") or item.get("label") or "Recommandation CCN",
                    "detail": item.get("detail") or item.get("rationale") or item.get("summary") or "",
                    "hash": f"territorial-intelligence/{territory_id}" if territory_id else "ccn",
                }
            )
    if not recommendations:
        recommendations.append(
            {
                "title": "Consulter la doctrine CCN et les extensions décisionnelles",
                "detail": "Les points d’extension CCN guidant l’implantation sont disponibles ; l’UI simulation reste progressive.",
                "hash": "ccn",
            }
        )

    return {
        "executive_summary": (
            "L’implantation d’un CCN s’appuie sur la doctrine CCN–FDSU et les recommandations territoriales. "
            f"Territoire de référence : {territory_id or 'non sélectionné'}."
        ),
        "data_used": [
            _link("Doctrine CCN", "/api/ccn/doctrine"),
            _link("Extensions décisionnelles CCN", "/api/ccn/decision-extensions"),
            _link("Recommandations territoriales", f"/api/territorial-intelligence/territories/{territory_id}/recommendations")
            if territory_id
            else _link("Intelligence territoriale", "/api/territorial-intelligence/territories"),
            _link("Stratégie FDSU–CCN 2026–2030", "data/strategic/strategie_fdsu_ccn_2026_2030.docx", "file"),
        ],
        "analysis": {
            "territory_id": territory_id,
            "doctrine_id": (doctrine.get("doctrine") or {}).get("id") or doctrine.get("id") or "DOCTRINE_CCN_FDSU",
            "extensions": extensions,
        },
        "kpis": [
            _kpi("Territoire analysé", territory_id or "—", color="purple"),
            _kpi("Recommandations", len(items), color="orange"),
            _kpi("Extensions CCN", len(extensions), color="blue"),
        ],
        "charts": {
            "gauge": {
                "title": "Maturité décisionnelle CCN",
                "value": 55 if items else 35,
                "subtitle": "Basé sur disponibilité doctrine + recommandations TI",
                "color": "purple",
            }
        },
        "map": {
            "label": "Carte CCN / territoire",
            "hash": f"territorial-intelligence/{territory_id}" if territory_id else "ccn",
            "hint": "Carte synchronisée dans Intelligence territoriale ou module CCN.",
        },
        "justification": {
            "why": "Doctrine CCN versionnée + profil territorial Master Registry / Knowledge Hub — aucune pondération inventée ici.",
            "confidence": "medium",
            "doctrine": "DOCTRINE_CCN_FDSU",
        },
        "recommendations": recommendations,
        "actions": [
            _action("open_ccn", "Ouvrir les CCN", hash_route="ccn"),
            _action("open_ti", "Profil territorial", hash_route=f"territorial-intelligence/{territory_id}" if territory_id else "territorial-intelligence"),
            _action("open_extensions", "Voir extensions CCN", hash_route="decision-view"),
        ],
        "visualizations": ["kpi_strip", "gauge", "territory_map", "recommendation_list"],
    }


def _run_territory_priority(context: dict[str, Any]) -> dict[str, Any]:
    territory_id = context.get("territory_id") or _first_territory_id()
    if not territory_id:
        return {
            "executive_summary": "Aucun territoire disponible pour l’analyse.",
            "data_used": [],
            "analysis": {},
            "kpis": [],
            "charts": {},
            "map": {"hash": "territorial-intelligence"},
            "justification": {"why": "Référentiel territorial indisponible.", "confidence": "low"},
            "recommendations": [],
            "actions": [_action("open_ti", "Intelligence territoriale", hash_route="territorial-intelligence")],
            "visualizations": [],
            "status": "unavailable",
        }

    profile = _safe(lambda: territorial_intelligence_service.build_territorial_profile(territory_id), {}) or {}
    explain = _safe(lambda: territorial_intelligence_service.explain_territory(territory_id), {}) or {}
    reco = _safe(lambda: territorial_intelligence_service.build_recommendations(territory_id), {}) or {}
    p = profile.get("profile") or profile
    name = p.get("territory_name") or p.get("name") or territory_id

    recommendations = []
    for item in (reco.get("recommendations") or reco.get("items") or [])[:5]:
        if isinstance(item, dict):
            recommendations.append(
                {
                    "title": item.get("title") or item.get("label") or "Action territoriale",
                    "detail": item.get("detail") or item.get("rationale") or "",
                    "hash": f"territorial-intelligence/{territory_id}",
                }
            )

    why = (
        (explain.get("explanation") or {}).get("answer")
        if isinstance(explain.get("explanation"), dict)
        else explain.get("summary") or explain.get("why")
    )

    conf = str(p.get("confidence_level") or "").lower()
    conf_pct = 75 if conf == "high" else 55 if conf == "medium" else 35 if conf else 0
    charts = {}
    if conf_pct:
        charts["gauge"] = {
            "title": "Confiance du profil",
            "value": conf_pct,
            "subtitle": f"Niveau déclaré : {p.get('confidence_level') or '—'}",
            "color": "green" if conf_pct >= 70 else "orange",
        }

    return {
        "executive_summary": (
            f"{name} : priorité territoriale évaluée via Intelligence territoriale "
            f"(qualité {p.get('data_quality') or '—'}, confiance {p.get('confidence_level') or '—'})."
        ),
        "data_used": [
            _link("Profil territorial", f"/api/territorial-intelligence/territories/{territory_id}"),
            _link("Justification", f"/api/territorial-intelligence/territories/{territory_id}/explain"),
            _link("Recommandations", f"/api/territorial-intelligence/territories/{territory_id}/recommendations"),
            _link("Carte territoire", f"/api/territorial-intelligence/territories/{territory_id}/map"),
        ],
        "analysis": {
            "territory_id": territory_id,
            "territory_name": name,
            "profile_sections": list((p.get("sections") or {}).keys()) if isinstance(p.get("sections"), dict) else [],
            "explain": explain,
        },
        "kpis": [
            _kpi("Territoire", name, color="blue"),
            _kpi("Qualité données", p.get("data_quality") or "—", color="yellow"),
            _kpi("Confiance", p.get("confidence_level") or "—", color="green"),
            _kpi("Recommandations", len(reco.get("recommendations") or reco.get("items") or []), color="orange"),
        ],
        "charts": charts,
        "map": {
            "label": "Carte du territoire",
            "hash": f"territorial-intelligence/{territory_id}",
            "hint": "Carte et couches synchronisées dans Intelligence territoriale.",
        },
        "justification": {
            "why": why or "Justification produite par le moteur d’intelligence territoriale (doctrines sites/CCN).",
            "confidence": p.get("confidence_level") or "medium",
            "raw": explain,
        },
        "recommendations": recommendations
        or [{"title": "Ouvrir le profil complet", "detail": name, "hash": f"territorial-intelligence/{territory_id}"}],
        "actions": [
            _action("open_ti", "Ouvrir le profil", hash_route=f"territorial-intelligence/{territory_id}"),
            _action("open_detail", "KPI territoires", hash_route="decision-detail/territoires"),
        ],
        "visualizations": ["kpi_strip", "gauge", "territory_map", "recommendation_list"],
    }


def _run_investment_impact(context: dict[str, Any]) -> dict[str, Any]:
    asset_id = context.get("asset_id") or context.get("site_id")
    program = context.get("program_code") or "sites_40"
    site = None
    if not asset_id:
        site = _top_site(program)
        asset_id = _site_id(site)

    impact = _safe(lambda: spatial_matching_service.get_asset_impact(asset_id), {}) if asset_id else {}
    impact = impact or {}
    explain = _safe(lambda: spatial_matching_service.explain_match(asset_id), {}) if asset_id else {}
    explain = explain or {}
    case = (
        _safe(lambda: explainable_decision_service.get_decision_case(str(asset_id), asset_type="site", program_code=program), {})
        if asset_id
        else {}
    ) or {}
    access = None
    if asset_id and str(asset_id).isdigit():
        access = _safe(
            lambda: __import__("api.services.transport_service", fromlist=["site_accessibility"]).site_accessibility(
                site_id=int(asset_id)
            ),
            {},
        )

    imp = impact.get("impact") or impact
    pop = imp.get("population_impacted")
    locs = imp.get("localities_impacted")
    acc = (access or {}).get("accessibility") or {}
    road = (access or {}).get("nearest_road") or {}

    return {
        "executive_summary": (
            f"Impact estimé pour l’actif {asset_id or '—'} : "
            f"{locs if locs is not None else '—'} localités, "
            f"population {pop if pop is not None else 'non disponible'} "
            f"(moteur spatial NSME — aucune valeur inventée). "
            f"Accessibilité : {acc.get('display') or 'Données insuffisantes'}"
            f"{(' — ' + str(road.get('nom'))) if road.get('nom') else ''}."
        ),
        "data_used": [
            _link("Impact NSME", f"/api/spatial-matching/assets/{asset_id}/impact") if asset_id else _link("NSME", "/api/spatial-matching/statistics"),
            _link("Explication spatiale", f"/api/spatial-matching/assets/{asset_id}/explain") if asset_id else _link("Règles NSME", "/api/spatial-matching/rules"),
            _link("Dossier de décision", f"/api/decision/case/{asset_id}") if asset_id else _link("Explainable engine", "/api/decision/pdf-template"),
            _link("Accessibilité", f"/api/transport/accessibility?site_id={asset_id}") if asset_id else _link("Transport", "/api/transport/statistics"),
        ],
        "analysis": {
            "asset_id": asset_id,
            "program_code": program,
            "site": site,
            "impact": imp,
            "spatial_explain": explain,
            "accessibility": access,
            "access_level": acc.get("class_label"),
            "nearest_road_distance_m": road.get("distance_m"),
            "constraints": [
                c
                for c in [
                    "Distance route élevée" if (road.get("distance_m") or 0) > 5000 else None,
                    "Score accessibilité faible" if (acc.get("score") or 100) < 40 else None,
                ]
                if c
            ],
        },
        "kpis": [
            _kpi("Actif", asset_id or "—", color="blue"),
            _kpi("Localités impactées", locs if locs is not None else "—", color="orange"),
            _kpi("Population", pop if pop is not None else "n/d", color="green", note=imp.get("population_status")),
            _kpi("Statut impact", imp.get("population_status") or imp.get("status") or "—", color="yellow"),
        ],
        "charts": {
            "waterfall": {
                "title": "Contribution à l’impact",
                "steps": [
                    {"label": "Localités", "value": int(locs or 0), "color": "orange"},
                    {"label": "Population (proxy)", "value": int(float(pop or 0)) if pop is not None else 0, "color": "green"},
                ],
            }
        },
        "map": {
            "label": "Impact spatial",
            "hash": f"spatial-impact/site/{asset_id}" if asset_id else "decision-view",
            "hint": "Vue Spatial Impact (DXL) synchronisée avec besoins et localités.",
        },
        "justification": {
            "why": explain.get("summary")
            or (explain.get("explanation") if isinstance(explain.get("explanation"), str) else None)
            or "Correspondance spatiale NSME (rayon de service + localités non couvertes).",
            "confidence": explain.get("confidence_level") or "medium",
            "case_summary": (case.get("summary") or {}).get("headline") if isinstance(case.get("summary"), dict) else case.get("summary"),
        },
        "recommendations": [
            {
                "title": "Ouvrir l’impact spatial détaillé",
                "detail": f"Actif {asset_id}",
                "hash": f"spatial-impact/site/{asset_id}" if asset_id else None,
            },
            {
                "title": "Ouvrir le dossier de décision",
                "detail": "Justification complète pour arbitrage",
                "hash": f"decision-case/site/{asset_id}?program_code={program}" if asset_id else None,
            },
        ],
        "actions": [
            _action("open_impact", "Impact spatial", hash_route=f"spatial-impact/site/{asset_id}" if asset_id else "decision-view"),
            _action("open_case", "Dossier de décision", hash_route=f"decision-case/site/{asset_id}?program_code={program}" if asset_id else "decision-view"),
        ],
        "visualizations": ["kpi_strip", "waterfall", "impact_map", "recommendation_list"],
    }


def _run_dg_dossier(context: dict[str, Any]) -> dict[str, Any]:
    program = context.get("program_code") or "sites_40"
    asset_id = context.get("asset_id") or context.get("site_id")
    site = None
    if not asset_id:
        site = _top_site(program)
        asset_id = _site_id(site)

    case = (
        _safe(
            lambda: explainable_decision_service.get_decision_case(
                str(asset_id), asset_type="site", program_code=program
            ),
            {},
        )
        if asset_id
        else {}
    ) or {}
    explained = (
        _safe(
            lambda: explainable_decision_service.explain_decision(
                str(asset_id), asset_type="site", program_code=program
            ),
            {},
        )
        if asset_id
        else {}
    ) or {}
    template = _safe(explainable_decision_service.pdf_template, {}) or {}
    access = None
    if asset_id and str(asset_id).isdigit():
        access = _safe(
            lambda: __import__("api.services.transport_service", fromlist=["site_accessibility"]).site_accessibility(
                site_id=int(asset_id)
            ),
            {},
        )
    acc = (access or {}).get("accessibility") or {}
    road = (access or {}).get("nearest_road") or {}

    summary = case.get("summary") or {}
    headline = summary.get("headline") if isinstance(summary, dict) else summary

    return {
        "executive_summary": (
            headline
            or f"Dossier de décision prêt pour l’actif {asset_id or '—'} — "
            "assemblage automatique via Explainable Decision Engine (aucune recommandation sans justification)."
            f" Accessibilité : {acc.get('display') or 'Données insuffisantes'}."
        ),
        "data_used": [
            _link("Dossier de décision", f"/api/decision/case/{asset_id}") if asset_id else _link("PDF template", "/api/decision/pdf-template"),
            _link("Justification", f"/api/decision/explain/{asset_id}") if asset_id else _link("Doctrines", "/api/decision/doctrine/DOCTRINE_SITES_FDSU"),
            _link("Modèle PDF DG", "/api/decision/pdf-template"),
            _link("Historique des cas", "/api/decision/case-history"),
            _link("Transport / accessibilité", f"/api/transport/accessibility?site_id={asset_id}") if asset_id else _link("Transport", "/api/transport/panel"),
        ],
        "analysis": {
            "asset_id": asset_id,
            "program_code": program,
            "case_sections": list(case.keys()),
            "template_id": template.get("id") or template.get("_meta", {}).get("id"),
            "site": site,
            "accessibility": access,
            "nearest_road": road.get("nom"),
            "nearest_road_distance_m": road.get("distance_m"),
            "access_level": acc.get("class_label"),
            "access_constraints": [
                c
                for c in [
                    "Éloignement routier" if (road.get("distance_m") or 0) > 5000 else None,
                    "Accès difficile" if (acc.get("score") or 100) < 40 else None,
                ]
                if c
            ],
        },
        "kpis": [
            _kpi("Actif", asset_id or "—", color="blue"),
            _kpi("Confiance", (case.get("confidence") or explained.get("confidence") or "—"), color="green"),
            _kpi("Score", (case.get("score") or {}).get("value") if isinstance(case.get("score"), dict) else case.get("score") or "—", color="orange"),
            _kpi("Accessibilité", acc.get("display") or "Données insuffisantes", color="purple"),
        ],
        "charts": {
            "treemap": {
                "title": "Composition du dossier",
                "items": [
                    {"label": "Synthèse", "value": 1, "color": "blue"},
                    {"label": "Score", "value": 1 if case.get("score") else 0, "color": "orange"},
                    {"label": "Justification", "value": 1 if case.get("justification") or explained else 0, "color": "green"},
                    {"label": "Impacts", "value": 1 if case.get("impacts") else 0, "color": "yellow"},
                    {"label": "Risques", "value": 1 if case.get("risks") else 0, "color": "red"},
                ],
            }
        },
        "map": {
            "label": "Localisation de l’actif",
            "hash": f"decision-case/site/{asset_id}?program_code={program}" if asset_id else "decision-view",
            "hint": "Le dossier DXL affiche la carte et le contexte territorial.",
        },
        "justification": {
            "why": (explained.get("why") or (case.get("justification") or {}).get("why") if isinstance(case.get("justification"), dict) else None)
            or "Dossier généré par Explainable Decision Engine à partir doctrines + matrices + données.",
            "confidence": case.get("confidence") or explained.get("confidence") or "medium",
            "traceability": case.get("traceability") or explained.get("traceability"),
        },
        "recommendations": [
            {
                "title": "Ouvrir le dossier de décision (DXL)",
                "detail": "Présentation DG — résumé, justification, impacts, actions",
                "hash": f"decision-case/site/{asset_id}?program_code={program}" if asset_id else None,
            },
            {
                "title": "Préparer export PDF",
                "detail": template.get("title") or "Modèle decision_case_file_v1",
                "hash": f"decision-case/site/{asset_id}?program_code={program}" if asset_id else None,
            },
        ],
        "actions": [
            _action("open_case", "Ouvrir le dossier DG", hash_route=f"decision-case/site/{asset_id}?program_code={program}" if asset_id else "decision-view"),
            _action("open_impact", "Voir l’impact", hash_route=f"spatial-impact/site/{asset_id}" if asset_id else "decision-view"),
            _action("prepare_mission", "Préparer une mission", hash_route=f"decision-case/site/{asset_id}?program_code={program}" if asset_id else "decision-view"),
        ],
        "visualizations": ["kpi_strip", "treemap", "case_map", "recommendation_list"],
        "mission_workflow": {
            "status": "ready_for_review",
            "steps": [
                "Valider le dossier de décision",
                "Partager avec le comité de pilotage",
                "Créer la mission terrain (API /missions — branchement progressif)",
            ],
        },
    }


RUNNERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "invest_priority": _run_invest_priority,
    "ccn_implantation": _run_ccn_implantation,
    "territory_priority": _run_territory_priority,
    "investment_impact": _run_investment_impact,
    "dg_dossier": _run_dg_dossier,
}


def run_scenario(scenario_id: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    meta = get_scenario(scenario_id)
    if not meta:
        return {"error": "Scénario introuvable", "available": [s["id"] for s in SCENARIO_CATALOG]}
    ctx = dict(context or {})
    runner = RUNNERS[meta["id"]]
    body = runner(ctx)
    return {
        "_meta": {
            "version": ENGINE_VERSION,
            "scenario_id": meta["id"],
            "computed_at": _now(),
            "context": ctx,
        },
        "scenario": meta,
        "question": meta["question"],
        "title": meta["title"],
        **body,
    }
