"""Executive Situation Room (ESR) v1.0 — composition lecture seule pour la Salle DG.

Agrège les moteurs existants (EDVS cockpit, NCI, NSME, Decision Scenarios, intents,
Transport, NDF) sans inventer de données ni dupliquer de logique métier.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

ENGINE_VERSION = "esr-1.0.0"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe(fn: Callable[[], Any], default: Any = None) -> Any:
    try:
        return fn()
    except Exception:
        return default


def _fmt_int(value: Any) -> str | None:
    if value is None:
        return None
    try:
        return f"{int(value):,}".replace(",", " ")
    except (TypeError, ValueError):
        return str(value)


def build_briefing(cockpit: dict[str, Any] | None = None) -> dict[str, Any]:
    """Résumé exécutif dynamique — uniquement à partir de valeurs sourcées."""
    cockpit = cockpit or _safe(lambda: __import__(
        "api.services.executive_cockpit_service", fromlist=["build_cockpit_payload"]
    ).build_cockpit_payload(), {}) or {}

    kpis = {k.get("id"): k for k in (cockpit.get("kpis") or []) if isinstance(k, dict)}
    rankings = cockpit.get("rankings") or {}
    sites = rankings.get("sites_priority") or []
    nci = (cockpit.get("nci") or {}).get("kpis") or {}
    programs = cockpit.get("programs") or []
    alerts = cockpit.get("alerts") or []
    spatial = (cockpit.get("spatial_matching") or {}).get("statistics") or {}

    provinces_from_sites = {
        str(s.get("province") or s.get("label") or "").split(",")[0].strip()
        for s in sites
        if s.get("label")
    }
    # Compter provinces distinctes uniquement si renseignées ; sinon ne pas inventer
    province_count = len([p for p in provinces_from_sites if p]) if provinces_from_sites else None
    territory_kpi = kpis.get("territoires") or {}
    territory_count = territory_kpi.get("value")

    factors: list[str] = []
    remaining = kpis.get("pop_remaining_nci") or {}
    uncovered = kpis.get("loc_uncovered_nci") or {}
    if remaining.get("value") not in (None, 0) or uncovered.get("value") not in (None, 0):
        factors.append("déficit de couverture")
    if spatial.get("avg_distance_m") is not None or spatial.get("matches_total"):
        factors.append("accessibilité spatiale (NSME)")
    if any((p.get("value") for p in programs if p.get("label", "").startswith("Sites"))):
        factors.append("programmes d’investissement FDSU")
    if kpis.get("ccn_total", {}).get("value"):
        factors.append("ancrage CCN (démonstration)")
    # Services publics / économie uniquement si radar axes confirment
    radar = cockpit.get("radar") or {}
    axes = radar.get("axes") or []
    for axis in axes:
        label = str(axis.get("label") or "").lower()
        status = axis.get("status")
        if status in {"confirmed", "partial", "estimated", "demonstration"}:
            if "santé" in label or "éducation" in label:
                if "services publics" not in factors:
                    factors.append("services publics")
            if "économ" in label and "potentiel économique" not in factors:
                factors.append("potentiel économique")
            if "accessib" in label and "accessibilité" not in factors:
                factors.append("accessibilité")

    high_alerts = [a for a in alerts if str(a.get("level")) in {"high", "critical", "critique"}]
    med_alerts = [a for a in alerts if str(a.get("level")) in {"medium", "attention"}]

    paragraphs: list[str] = []
    if sites:
        site_n = len(sites)
        if territory_count is not None:
            paragraphs.append(
                f"Le SIG-FDSU RDC recommande actuellement de concentrer l’attention sur "
                f"{site_n} site(s) prioritaire(s) parmi { _fmt_int(territory_count) } territoires référencés."
            )
        else:
            paragraphs.append(
                f"Le SIG-FDSU RDC met en avant {site_n} site(s) prioritaire(s) issus du moteur de décision."
            )
    elif territory_count is not None:
        paragraphs.append(
            f"Le référentiel national compte { _fmt_int(territory_count) } territoires. "
            "La priorisation sites n’est pas encore consolidée dans cette session."
        )
    else:
        paragraphs.append(
            "Le briefing national est partiel : certaines sources de priorisation n’ont pas répondu."
        )

    if factors:
        paragraphs.append("Les principaux facteurs observables sont : " + " · ".join(factors) + ".")

    updates: list[str] = []
    if remaining.get("value") is not None:
        updates.append(f"Population restante (NCI) : {_fmt_int(remaining.get('value'))}")
    if uncovered.get("value") is not None:
        updates.append(f"Localités non couvertes : {_fmt_int(uncovered.get('value'))}")
    if spatial.get("matches_total") is not None:
        updates.append(f"Correspondances NSME : {_fmt_int(spatial.get('matches_total'))}")
    if province_count:
        updates.append(f"Empreinte sites prioritaires : {province_count} libellé(s) distinct(s)")

    if high_alerts:
        anomaly = f"{len(high_alerts)} alerte(s) critique(s) détectée(s) — voir le panneau Alertes."
    elif med_alerts:
        anomaly = f"{len(med_alerts)} point(s) d’attention — aucune anomalie critique signalée dans le cockpit."
    else:
        anomaly = "Aucune anomalie critique détectée dans les sources consolidées du cockpit."

    bullets_factors = [{"text": f, "sourced": True} for f in factors]
    bullets_updates = [{"text": u, "sourced": True} for u in updates]

    return {
        "_meta": {
            "version": ENGINE_VERSION,
            "generated_at": _now(),
            "principle": "Texte généré dynamiquement — aucune donnée inventée",
            "sources": cockpit.get("_meta", {}).get("sources") or [],
        },
        "title": "Executive Briefing",
        "headline": paragraphs[0] if paragraphs else "Briefing national",
        "paragraphs": paragraphs,
        "factors": bullets_factors,
        "since_last_update": bullets_updates,
        "anomaly_line": anomaly,
        "narrative": "\n\n".join(paragraphs + ([anomaly] if anomaly else [])),
        "stats_used": {
            "sites_priority_count": len(sites),
            "territories": territory_count,
            "population_remaining": remaining.get("value"),
            "localities_uncovered": uncovered.get("value"),
            "matches_total": spatial.get("matches_total"),
            "alerts_high": len(high_alerts),
            "nci_coverage_ratio": nci.get("coverage_ratio_population") if isinstance(nci, dict) else None,
        },
    }


def build_national_situation(cockpit: dict[str, Any] | None = None) -> dict[str, Any]:
    cockpit = cockpit or _safe(lambda: __import__(
        "api.services.executive_cockpit_service", fromlist=["build_cockpit_payload"]
    ).build_cockpit_payload(), {}) or {}
    kpis_by_id = {k.get("id"): k for k in (cockpit.get("kpis") or [])}

    transport = _safe(lambda: __import__("api.services.transport_service", fromlist=["get_statistics"]).get_statistics(), {}) or {}
    if not transport:
        transport = _safe(
            lambda: __import__("api.services.transport_service", fromlist=["statistics"]).statistics(),
            {},
        ) or {}

    ndf_quality = _safe(
        lambda: __import__("api.services.national_data_fabric_service", fromlist=["compute_quality"]).compute_quality(
            "administrative"
        ),
        {},
    ) or {}

    def card(
        card_id: str,
        label: str,
        value: Any,
        *,
        explain: str,
        source: str,
        hash_route: str,
        detail_key: str | None = None,
        status: str = "success",
        note: str | None = None,
    ) -> dict[str, Any]:
        return {
            "id": card_id,
            "label": label,
            "value": value,
            "value_display": _fmt_int(value) if isinstance(value, (int, float)) else (value if value is not None else "—"),
            "explain": explain,
            "source": source,
            "hash": hash_route,
            "detail_key": detail_key,
            "status": status if value is not None else "unavailable",
            "note": note,
            "why_available": True,
        }

    pop_cov = kpis_by_id.get("pop_covered_nci") or {}
    pop_rem = kpis_by_id.get("pop_remaining_nci") or {}
    sites = (cockpit.get("rankings") or {}).get("sites_priority") or []
    ccn = kpis_by_id.get("ccn_total") or {}
    programs = cockpit.get("programs") or []
    prog_count = sum(1 for p in programs if isinstance(p.get("value"), (int, float)) and p["value"] > 0)
    invest_sites = next((p.get("value") for p in programs if "40" in str(p.get("label"))), None)

    transport_routes = (
        transport.get("routes_total")
        or transport.get("total_routes")
        or (transport.get("kpis") or {}).get("routes_total")
        or (transport.get("statistics") or {}).get("routes_total")
    )

    quality_score = None
    indicators = ndf_quality.get("indicators") or []
    if indicators:
        scores = [i.get("score") for i in indicators if isinstance(i.get("score"), (int, float))]
        if scores:
            quality_score = round(sum(scores) / len(scores), 1)

    cards = [
        card(
            "coverage",
            "Couverture",
            pop_cov.get("value"),
            explain="Population nationale couverte selon le Référentiel National des Besoins (NCI).",
            source="NCI · Coverage Intelligence",
            hash_route="decision-detail/population-non-couverte",
            detail_key="population_uncovered",
            note=f"Restante : {_fmt_int(pop_rem.get('value'))}" if pop_rem.get("value") is not None else None,
        ),
        card(
            "programs",
            "Programmes",
            prog_count,
            explain="Nombre de programmes FDSU avec effectifs confirmés dans le référentiel programmes.",
            source="Programmes FDSU",
            hash_route="decision-view",
        ),
        card(
            "investments",
            "Investissements",
            invest_sites,
            explain="Effectif Sites 40 — proxy d’investissement pilote sourcé (pas un montant budgétaire inventé).",
            source="Programme Sites 40",
            hash_route="decision-detail/sites-prioritaires",
            detail_key="sites_priority",
            note="Montants budgétaires non exposés dans cette version",
        ),
        card(
            "priority_sites",
            "Sites prioritaires",
            len(sites) if sites else None,
            explain="Sites issus du moteur de priorisation FDSU pour le programme national disponible.",
            source="Decision Engine · Priorisation",
            hash_route="decision-detail/sites-prioritaires",
            detail_key="sites_priority",
        ),
        card(
            "ccn",
            "CCN",
            ccn.get("value"),
            explain="Effectif CCN du jeu de démonstration opérationnel — ne pas traiter comme production.",
            source="CCN Operational (DEMO)",
            hash_route="decision-view",
            status="demonstration" if ccn.get("value") is not None else "unavailable",
            note=ccn.get("note"),
        ),
        card(
            "transport",
            "Transport",
            transport_routes,
            explain="Routes principales référencées par Transport & Accessibility Intelligence.",
            source="Transport Intelligence",
            hash_route="territorial-intelligence",
            status="success" if transport_routes is not None else "unavailable",
        ),
        card(
            "data_quality",
            "Qualité des données",
            quality_score,
            explain="Score moyen des indicateurs National Data Fabric pour le référentiel territoires.",
            source="National Data Fabric",
            hash_route="decision-view",
            status="partial" if quality_score is not None else "unavailable",
        ),
    ]

    return {
        "_meta": {"version": ENGINE_VERSION, "generated_at": _now()},
        "title": "Situation nationale",
        "journey_step": "situation",
        "cards": cards,
    }


def build_alerts(cockpit: dict[str, Any] | None = None) -> dict[str, Any]:
    cockpit = cockpit or _safe(lambda: __import__(
        "api.services.executive_cockpit_service", fromlist=["build_cockpit_payload"]
    ).build_cockpit_payload(), {}) or {}

    items: list[dict[str, Any]] = []

    def add(severity: str, title: str, message: str, *, hash_route: str, why: str, category: str):
        items.append(
            {
                "id": f"{category}:{len(items)}",
                "severity": severity,  # critical | attention | info
                "category": category,
                "title": title,
                "message": message,
                "why": why,
                "hash": hash_route,
                "explainable": True,
            }
        )

    # Enrichir depuis cockpit
    for raw in cockpit.get("alerts") or []:
        level = str(raw.get("level") or "low").lower()
        severity = "critical" if level in {"high", "critical"} else ("attention" if level in {"medium", "attention"} else "info")
        add(
            severity,
            str(raw.get("title") or "Alerte"),
            str(raw.get("message") or ""),
            hash_route="decision-view",
            why="Alerte dérivée du cockpit exécutif à partir des sources consolidées.",
            category="cockpit",
        )

    kpis = {k.get("id"): k for k in (cockpit.get("kpis") or [])}
    uncovered = (kpis.get("loc_uncovered_nci") or {}).get("value")
    if isinstance(uncovered, (int, float)) and uncovered > 0:
        add(
            "attention",
            "Territoires / localités sans couverture complète",
            f"{_fmt_int(uncovered)} localités non couvertes selon le NCI.",
            hash_route="decision-detail/population-non-couverte",
            why="Le Référentiel National des Besoins signale un déficit de couverture localités.",
            category="coverage",
        )

    remaining = (kpis.get("pop_remaining_nci") or {}).get("value")
    if isinstance(remaining, (int, float)) and remaining > 0:
        add(
            "attention",
            "Population restante à couvrir",
            f"{_fmt_int(remaining)} personnes dans des localités non couvertes.",
            hash_route="decision-detail/population-non-couverte",
            why="Priorité populationnelle nationale issue du NCI.",
            category="population",
        )

    sites = (cockpit.get("rankings") or {}).get("sites_priority") or []
    critical_sites = [s for s in sites if str(s.get("level") or "").lower() in {"high", "critical", "critique"}]
    if critical_sites:
        add(
            "critical",
            "Investissement prioritaire requis",
            f"{len(critical_sites)} site(s) à priorité élevée / critique dans le top national.",
            hash_route="decision-detail/sites-prioritaires",
            why="Score de priorisation FDSU élevé — ouvrir le Decision Workspace pour justifier.",
            category="investment",
        )

    ndf = _safe(
        lambda: __import__("api.services.national_data_fabric_service", fromlist=["compute_quality"]).compute_quality(
            "administrative"
        ),
        {},
    ) or {}
    scores = [i.get("score") for i in (ndf.get("indicators") or []) if isinstance(i.get("score"), (int, float))]
    if scores and (sum(scores) / len(scores)) < 50:
        add(
            "attention",
            "Qualité des données insuffisante",
            f"Score moyen NDF territoires : {round(sum(scores)/len(scores), 1)}.",
            hash_route="decision-view",
            why="La qualité mesurée par le National Data Fabric est sous le seuil d’attention (50).",
            category="quality",
        )

    # Programmes sans effectif
    missing_prog = [p for p in (cockpit.get("programs") or []) if p.get("status") == "unavailable"]
    if missing_prog:
        add(
            "info",
            "Programme non consolidé",
            f"{len(missing_prog)} programme(s) sans effectif confirmé dans le référentiel.",
            hash_route="decision-view",
            why="Fichier programme absent ou non lisible — pas un blocage opérationnel inventé.",
            category="program",
        )

    by_sev = {"critical": [], "attention": [], "info": []}
    for item in items:
        by_sev.setdefault(item["severity"], []).append(item)

    return {
        "_meta": {"version": ENGINE_VERSION, "generated_at": _now(), "count": len(items)},
        "title": "Alertes nationales",
        "categories": [
            {"id": "critical", "label": "Critique", "count": len(by_sev["critical"])},
            {"id": "attention", "label": "Attention", "count": len(by_sev["attention"])},
            {"id": "info", "label": "Information", "count": len(by_sev["info"])},
        ],
        "items": items,
        "by_severity": by_sev,
    }


def build_questions() -> dict[str, Any]:
    """Questions prédéfinies — architecture prête pour moteurs conversationnels futurs."""
    intents = _safe(
        lambda: __import__("api.services.decision_demo_service", fromlist=["get_decision_intents"]).get_decision_intents(),
        {},
    ) or {}
    scenarios = _safe(
        lambda: __import__("api.services.decision_scenarios_service", fromlist=["list_scenarios"]).list_scenarios(),
        {},
    ) or {}
    scenario_by_id = {s["id"]: s for s in (scenarios.get("scenarios") or [])}

    curated = [
        {
            "id": "why_province_priority",
            "question": "Pourquoi cette province est-elle prioritaire ?",
            "answer_hint": "Ouvre le scénario de justification territoriale et le Twin.",
            "hash": "decision-scenario/territory_priority",
            "scenario_id": "territory_priority",
            "engines": ["territorial_intelligence", "explainable_decision"],
        },
        {
            "id": "where_ccn",
            "question": "Où implanter un nouveau CCN ?",
            "answer_hint": "Lance le scénario d’implantation CCN.",
            "hash": "decision-scenario/ccn_implantation",
            "scenario_id": "ccn_implantation",
            "engines": ["ccn", "territorial_intelligence"],
        },
        {
            "id": "highest_impact",
            "question": "Quels territoires présentent le plus fort impact ?",
            "answer_hint": "Impact spatial / population via scénario d’investissement.",
            "hash": "decision-scenario/investment_impact",
            "scenario_id": "investment_impact",
            "engines": ["nsme", "decision_engine"],
        },
        {
            "id": "best_return",
            "question": "Quels investissements offrent le meilleur retour ?",
            "answer_hint": "Priorisation nationale des sites à financer.",
            "hash": "decision-scenario/invest_priority",
            "scenario_id": "invest_priority",
            "engines": ["fdsu_site_priority", "decision_engine"],
        },
    ]

    # Enrichir depuis intents existants (sans inventer)
    extra = []
    for intent in (intents.get("intents") or [])[:6]:
        sid = intent.get("scenario_id")
        if not sid or any(q["scenario_id"] == sid for q in curated):
            continue
        extra.append(
            {
                "id": intent.get("id"),
                "question": intent.get("title"),
                "answer_hint": intent.get("explanation"),
                "hash": f"decision-scenario/{sid}" if sid else "decision-view",
                "scenario_id": sid,
                "engines": scenario_by_id.get(sid, {}).get("engines") or [],
                "from_intent": True,
            }
        )

    return {
        "_meta": {
            "version": ENGINE_VERSION,
            "generated_at": _now(),
            "conversational_ready": True,
            "mode": "predefined_v1",
            "note": "Les réponses ouvrent les analyses existantes — pas de génération libre inventée.",
        },
        "title": "Posez votre question",
        "placeholder": "Architecture prête pour un moteur conversationnel futur",
        "questions": curated + extra[:4],
    }


def build_scenarios_panel(*, run_limit: int = 0) -> dict[str, Any]:
    """Panneau scénarios — catalogue immédiat ; exécution optionnelle (run_limit) pour ne pas bloquer."""
    catalog = _safe(
        lambda: __import__("api.services.decision_scenarios_service", fromlist=["list_scenarios"]).list_scenarios(),
        {},
    ) or {}
    run = _safe(
        lambda: __import__("api.services.decision_scenarios_service", fromlist=["run_scenario"]).run_scenario,
        None,
    )

    cards = []
    for idx, meta in enumerate((catalog.get("scenarios") or [])[:5]):
        sid = meta["id"]
        result = {}
        if run and idx < max(0, int(run_limit)):
            result = _safe(lambda m=meta: run(m["id"], {}), {}) or {}
        cost = None
        impact = None
        beneficiaries = None
        for key in ("cost", "estimated_cost", "investment"):
            if isinstance(result, dict) and result.get(key) is not None:
                cost = result.get(key)
                break
        kpis = result.get("kpis") if isinstance(result, dict) else None
        if isinstance(kpis, list):
            for k in kpis:
                lab = str(k.get("label") or "").lower()
                if impact is None and ("impact" in lab or "population" in lab):
                    impact = k.get("value")
                if beneficiaries is None and ("bénéfic" in lab or "benef" in lab or "population" in lab):
                    beneficiaries = k.get("value")
        summary = (result or {}).get("executive_summary") if isinstance(result, dict) else None
        cards.append(
            {
                "id": sid,
                "code": meta.get("code"),
                "title": meta.get("title"),
                "question": meta.get("question"),
                "cost": cost,
                "cost_display": _fmt_int(cost) if cost is not None else "Non chiffré dans le scénario",
                "impact": impact,
                "impact_display": (
                    _fmt_int(impact)
                    if impact is not None
                    else (summary[:120] + "…" if summary and len(summary) > 120 else summary)
                    or "Lancer le scénario pour mesurer l’impact"
                ),
                "beneficiaries": beneficiaries,
                "beneficiaries_display": _fmt_int(beneficiaries) if beneficiaries is not None else "Voir à l’exécution",
                "recommendation": summary or meta.get("question"),
                "hash": f"decision-scenario/{sid}",
                "engines": meta.get("engines") or [],
                "status": "ready" if summary else "catalog_ready",
            }
        )

    return {
        "_meta": {"version": ENGINE_VERSION, "generated_at": _now(), "run_limit": run_limit},
        "title": "Simulations stratégiques",
        "scenarios": cards,
    }


def build_executive_actions() -> dict[str, Any]:
    """Actions réelles uniquement — alignées Capability Registry / Zero Decorative Actions."""
    return {
        "_meta": {"version": ENGINE_VERSION, "zero_decorative": True},
        "actions": [
            {
                "id": "prepare_dg_dossier",
                "label": "Préparer un dossier DG",
                "hash": "decision-scenario/dg_dossier",
                "capability": None,
                "available": True,
                "why": "Scénario Decision Scenarios — assemblage dossier DG.",
            },
            {
                "id": "prepare_mission",
                "label": "Préparer une mission",
                "hash": None,
                "capability": "mission_planning",
                "available": False,
                "hide_when_unavailable": True,
                "why": "Workflow mission non branché.",
            },
            {
                "id": "export_analyses",
                "label": "Exporter les analyses",
                "hash": "decision-detail/sites-prioritaires",
                "capability": "export_excel",
                "available": True,
                "why": "Ouvre le workspace où l’export Excel réel est disponible.",
            },
            {
                "id": "open_workspace",
                "label": "Ouvrir Decision Workspace",
                "hash": "decision-detail/sites-prioritaires",
                "capability": None,
                "available": True,
                "why": "Workspace de justification détaillée.",
            },
            {
                "id": "open_twin",
                "label": "Ouvrir Territorial Digital Twin",
                "hash": "territorial-twin/province/Haut-Lomami",
                "capability": None,
                "available": True,
                "why": "Twin provincial de démonstration — sélection TST privilégiée si disponible.",
            },
            {
                "id": "open_sdg",
                "label": "Lancer Analyse d’Impact Territorial",
                "hash": "spatial-impact/site/7?program_code=sites_40",
                "capability": None,
                "available": True,
                "why": "Spatial Decision Graph — site prioritaire de repli si aucune sélection.",
            },
            {
                "id": "present_dg",
                "label": "Présenter au DG",
                "hash": None,
                "action": "start_presentation",
                "capability": None,
                "available": True,
                "why": "Mode présentation ESR guidé.",
            },
        ],
    }


PRESENTATION_STEPS = [
    {"id": "briefing", "label": "Executive Briefing", "selector": "#esr-briefing", "duration_ms": 3500},
    {"id": "situation", "label": "Situation nationale", "selector": "#esr-national", "duration_ms": 3200},
    {"id": "map", "label": "Carte nationale", "selector": "#esr-map", "duration_ms": 3500},
    {"id": "alerts", "label": "Alertes", "selector": "#esr-alerts", "duration_ms": 2800},
    {"id": "priorities", "label": "Priorités", "selector": "#esr-priorities", "duration_ms": 3000},
    {"id": "decisions", "label": "Décisions proposées", "selector": "#esr-scenarios", "duration_ms": 3200},
]


def build_situation_room() -> dict[str, Any]:
    cockpit = _safe(lambda: __import__(
        "api.services.executive_cockpit_service", fromlist=["build_cockpit_payload"]
    ).build_cockpit_payload(), {}) or {}

    briefing = build_briefing(cockpit)
    national = build_national_situation(cockpit)
    alerts = build_alerts(cockpit)
    questions = build_questions()
    scenarios = build_scenarios_panel()
    actions = build_executive_actions()

    # Enrichir KPIs cockpit pour explicabilité / drill-down
    enriched_kpis = []
    detail_map = {
        "pop_covered_nci": ("population_uncovered", "decision-detail/population-non-couverte"),
        "pop_remaining_nci": ("population_uncovered", "decision-detail/population-non-couverte"),
        "loc_covered_nci": ("population_uncovered", "decision-detail/population-non-couverte"),
        "loc_uncovered_nci": ("population_uncovered", "decision-detail/population-non-couverte"),
        "territoires": (None, "salle-pilotage"),
        "ccn_total": (None, "decision-view"),
        "ccn_ops": (None, "decision-view"),
        "kh_domains": (None, "decision-view"),
    }
    for kpi in cockpit.get("kpis") or []:
        kid = kpi.get("id")
        detail_key, route = detail_map.get(kid, (None, "decision-view"))
        enriched = {
            **kpi,
            "detailKey": detail_key,
            "detailRoute": route,
            "explain": kpi.get("note") or "Indicateur consolidé du cockpit exécutif.",
            "why_available": True,
        }
        enriched_kpis.append(enriched)

    return {
        "_meta": {
            "version": ENGINE_VERSION,
            "title": "Executive Situation Room",
            "ui_title": "Salle de Pilotage DG — Situation Room",
            "generated_at": _now(),
            "journey": ["situation", "why", "where", "what", "impact", "decide"],
            "hardcoded_forbidden": True,
            "progressive_loading": True,
        },
        "briefing": briefing,
        "national_situation": national,
        "alerts": alerts,
        "questions": questions,
        "scenarios": scenarios,
        "actions": actions,
        "presentation": {
            "title": "Présenter au DG",
            "steps": PRESENTATION_STEPS,
            "autoplay": True,
        },
        "cockpit": {
            **cockpit,
            "kpis": enriched_kpis,
        },
        "priorities": {
            "sites": (cockpit.get("rankings") or {}).get("sites_priority") or [],
            "recommendations": cockpit.get("recommendations") or [],
        },
    }
