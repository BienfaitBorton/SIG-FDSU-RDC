"""Centre de Décision FDSU — KPI explicables, questions métier et mode démonstration."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from psycopg2.extras import RealDictCursor

from api.config import connect_db
from api.services import decision_engine_service, health_service, program_service

PENDING = "Données en cours d'intégration"
NOT_CALCULATED = "Donnée non encore calculée — nécessite référentiel Population / CCN / Budget."
STATUS_TO_FILL = "Statuts opérationnels à renseigner"

STRATEGIC_SOURCES = [
    "data/strategic/strategie_fdsu_ccn_2026_2030.docx",
    "data/strategic/matrice_priorisation_300_sites.xlsx",
    "data/business/priority_matrix.json",
    "data/business/kpi_catalog.json",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _explained(
    *,
    key: str,
    label: str,
    value: Any,
    definition: str,
    source_table: str,
    calculation_method: str,
    recommended_action: str,
    available: bool = True,
    limitations: str | None = None,
    display: str | None = None,
    unit: str | None = None,
    source_label: str | None = None,
    confidence: str = "medium",
) -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "value": value,
        "display": display if display is not None else (None if available else PENDING),
        "available": available,
        "definition": definition,
        "source_table": source_table,
        "source_label": source_label or source_table,
        "calculation_method": calculation_method,
        "last_updated": _now(),
        "limitations": limitations,
        "recommended_action": recommended_action,
        "unit": unit,
        "confidence": confidence if available else "low",
        "trend": "flat",
        "technical": {
            "source_table": source_table,
            "calculation_method": calculation_method,
        },
        "strategic_references": STRATEGIC_SOURCES,
    }


def _safe_count(cur, query: str, params: tuple[Any, ...] | None = None) -> int:
    try:
        cur.execute("SAVEPOINT demo_count")
        cur.execute(query, params or ())
        row = cur.fetchone()
        cur.execute("RELEASE SAVEPOINT demo_count")
        if row is None:
            return 0
        if isinstance(row, dict):
            return int(next(iter(row.values())))
        return int(row[0])
    except Exception:
        try:
            cur.execute("ROLLBACK TO SAVEPOINT demo_count")
        except Exception:
            pass
        return 0


def build_explainable_kpis() -> dict[str, dict[str, Any]]:
    national = decision_engine_service.get_national_panel_payload()
    synthesis = national.get("synthesis") or {}
    scores = national.get("decision_summary") or {}
    health_stats = health_service.get_statistics()

    sites_fdsu = synthesis.get("sites_fdsu")
    sites_priority = synthesis.get("sites_priority")
    sites_critical = synthesis.get("sites_critical")
    sites_high = synthesis.get("sites_high")
    health_total = int(health_stats.get("total_facilities") or 0)

    kpis = {
        "sites_fdsu": _explained(
            key="sites_fdsu",
            label="Sites FDSU",
            value=sites_fdsu,
            definition="Nombre total de sites enregistrés dans les programmes FDSU (Sites 40 + Sites 300).",
            source_table="programs.fdsu_sites",
            calculation_method="COUNT(*) FROM programs.fdsu_sites (= Sites 40 + Sites 300).",
            recommended_action="Voir les sites",
        ),
        "sites_priority": _explained(
            key="sites_priority",
            label="Sites prioritaires",
            value=sites_priority,
            definition="Sites avec niveau de priorité critique ou élevée selon le moteur de décision FDSU.",
            source_table="decision.fdsu_site_scores",
            calculation_method="critical + high (aligné sur data/business/priority_matrix.json).",
            recommended_action="Voir les sites prioritaires",
        ),
        "sites_critical": _explained(
            key="sites_critical",
            label="Sites critiques",
            value=sites_critical,
            definition="Sites nécessitant une intervention immédiate (déficit majeur / fort impact social).",
            source_table="decision.fdsu_site_scores",
            calculation_method="COUNT WHERE priority_level = 'critical'.",
            recommended_action="Analyser les sites critiques",
        ),
        "sites_high": _explained(
            key="sites_high",
            label="Sites à priorité élevée",
            value=sites_high,
            definition="Sites à déployer en priorité dans la séquence nationale.",
            source_table="decision.fdsu_site_scores",
            calculation_method="COUNT WHERE priority_level = 'high'.",
            recommended_action="Voir le classement",
        ),
        "sites_40": _explained(
            key="sites_40",
            label="Sites 40",
            value=(national.get("kpis") or {}).get("sites_40", {}).get("value"),
            definition="Sites du programme pilote Sites 40 en exécution.",
            source_table="programs.fdsu_sites + programs.fdsu_programs",
            calculation_method="COUNT WHERE program_code = 'PROG_SITES_40'.",
            recommended_action="Suivre les 40 sites pilotes",
        ),
        "sites_300": _explained(
            key="sites_300",
            label="Sites 300",
            value=(national.get("kpis") or {}).get("sites_300", {}).get("value"),
            definition="Sites du programme Sites 300 planifiés, cadrés par la matrice de priorisation.",
            source_table="programs.fdsu_sites + programs.fdsu_programs",
            calculation_method="COUNT WHERE program_code = 'PROG_SITES_300'.",
            recommended_action="Suivre les 300 sites planifiés",
            limitations="Scores matrice xlsx non encore recalculés site par site (fdsu_score souvent null).",
        ),
        "sites_scored": _explained(
            key="sites_scored",
            label="Sites scorés",
            value=scores.get("total"),
            definition="Sites ayant un score de priorité calculé par le moteur de décision.",
            source_table="decision.fdsu_site_scores",
            calculation_method="COUNT(*) FROM decision.fdsu_site_scores.",
            recommended_action="Ouvrir la priorisation",
        ),
        "referentials_active": _explained(
            key="referentials_active",
            label="Référentiels actifs",
            value=synthesis.get("referentials_active"),
            definition="Référentiels sectoriels au statut actif dans le National Reference Framework.",
            source_table="reference.reference_catalog",
            calculation_method="COUNT WHERE status = 'active'.",
            recommended_action="Voir les référentiels",
        ),
        "referentials_planned": _explained(
            key="referentials_planned",
            label="Référentiels planifiés",
            value=synthesis.get("referentials_planned"),
            definition="Référentiels sectoriels encore planifiés (non opérationnels).",
            source_table="reference.reference_catalog",
            calculation_method="COUNT WHERE status = 'planned'.",
            recommended_action="Analyser la qualité des données",
        ),
        "referentials_in_progress": _explained(
            key="referentials_in_progress",
            label="Référentiels en cours",
            value=(national.get("kpis") or {}).get("referentials_in_progress", {}).get("value"),
            definition="Référentiels en cours d'intégration ou de consolidation.",
            source_table="reference.reference_catalog",
            calculation_method="COUNT WHERE status = 'in_progress'.",
            recommended_action="Voir le catalogue sectoriel",
        ),
        "telecom_objects": _explained(
            key="telecom_objects",
            label="Objets télécoms",
            value=(national.get("kpis") or {}).get("telecom_objects", {}).get("value"),
            definition="Infrastructures ponctuelles du référentiel télécom national.",
            source_table="telecom.infrastructure",
            calculation_method="COUNT(*) FROM telecom.infrastructure.",
            recommended_action="Voir la carte télécom",
        ),
        "provinces": _explained(
            key="provinces",
            label="Provinces",
            value=(national.get("kpis") or {}).get("provinces", {}).get("value"),
            definition="Provinces du référentiel administratif RDC.",
            source_table="provinces",
            calculation_method="COUNT(*) FROM provinces.",
            recommended_action="Voir la carte nationale",
        ),
        "territoires": _explained(
            key="territoires",
            label="Territoires",
            value=(national.get("kpis") or {}).get("territoires", {}).get("value"),
            definition="Territoires administratifs du référentiel territorial.",
            source_table="territoires",
            calculation_method="COUNT(*) FROM territoires.",
            recommended_action="Voir la carte nationale",
        ),
        "localites": _explained(
            key="localites",
            label="Localités",
            value=(national.get("kpis") or {}).get("localites", {}).get("value"),
            definition="Localités / villages du référentiel territorial.",
            source_table="localites",
            calculation_method="COUNT(*) FROM localites.",
            recommended_action="Explorer le territoire",
        ),
        "health_facilities": _explained(
            key="health_facilities",
            label="Référentiel Santé",
            value=health_total,
            definition="Établissements sanitaires importés depuis le KMZ national ESS.",
            source_table="health.health_facilities",
            calculation_method="COUNT(*) FROM health.health_facilities (source KMZ RDC_ESS_Santé).",
            recommended_action="Voir la carte Santé",
        ),
        "population_covered": _explained(
            key="population_covered",
            label="Population couverte",
            value=None,
            available=False,
            display=NOT_CALCULATED,
            definition="Population bénéficiant d'un accès effectif au service universel.",
            source_table="référentiel Population (non intégré)",
            calculation_method="Non calculable tant que le référentiel Population n'est pas branché.",
            recommended_action="Intégrer le référentiel Population",
            limitations=NOT_CALCULATED,
        ),
        "population_uncovered": _explained(
            key="population_uncovered",
            label="Population non couverte",
            value=None,
            available=False,
            display=NOT_CALCULATED,
            definition="Population hors couverture effective FDSU/CCN.",
            source_table="référentiel Population (non intégré)",
            calculation_method="Non calculable sans Population + couverture.",
            recommended_action="Intégrer le référentiel Population",
            limitations=NOT_CALCULATED,
        ),
        "planned_ccn": _explained(
            key="planned_ccn",
            label="CCN planifiés",
            value=None,
            available=False,
            display=NOT_CALCULATED,
            definition="Centres Communautaires Numériques planifiés selon la stratégie FDSU–CCN 2026–2030.",
            source_table="programme CCN / budget (non intégré)",
            calculation_method="Non calculable sans inventaire CCN opérationnel.",
            recommended_action="Planifier les CCN",
            limitations=NOT_CALCULATED,
        ),
        "estimated_investment": _explained(
            key="estimated_investment",
            label="Investissement estimé",
            value=None,
            available=False,
            display=NOT_CALCULATED,
            definition="Estimation budgétaire des investissements FDSU prioritaires.",
            source_table="référentiel Budget (non intégré)",
            calculation_method="Non calculable sans référentiel Budget / coûts unitaires.",
            recommended_action="Préparer un rapport de décision",
            limitations=NOT_CALCULATED,
        ),
    }
    # Enrichissement labels métier depuis le catalogue Decision Detail (pas de SQL au DG)
    try:
        from api.services import decision_kpi_detail_service

        for key, kpi in kpis.items():
            cfg = decision_kpi_detail_service.get_kpi_config(key)
            if not cfg:
                continue
            kpi["source_label"] = cfg.get("source_label") or kpi.get("source_label")
            kpi["confidence"] = cfg.get("confidence") or kpi.get("confidence") or "medium"
            kpi["objective"] = cfg.get("executive_objective")
    except Exception:  # noqa: BLE001
        pass
    return kpis


def get_explain_kpi_payload(kpi_key: str | None = None) -> dict[str, Any]:
    kpis = build_explainable_kpis()
    if kpi_key:
        item = kpis.get(kpi_key)
        if not item:
            return {"error": "KPI introuvable", "available_keys": list(kpis.keys())}
        return {"kpi": item, "_meta": {"title": "Explication KPI FDSU", "strategic_references": STRATEGIC_SOURCES}}
    return {
        "_meta": {
            "title": "Catalogue KPI explicables — Centre de Décision FDSU",
            "strategic_references": STRATEGIC_SOURCES,
            "count": len(kpis),
        },
        "kpis": kpis,
    }


def get_decision_intents() -> dict[str, Any]:
    return {
        "_meta": {
            "title": "Que voulez-vous décider aujourd’hui ?",
            "strategic_references": STRATEGIC_SOURCES,
        },
        "intents": [
            {
                "id": "prioritize_funding",
                "title": "Prioriser les sites à financer",
                "explanation": "Identifier les sites critiques et élevés à financer en priorité selon la matrice FDSU.",
                "data_used": ["decision.fdsu_site_scores", "programs.fdsu_sites", "priority_matrix.json"],
                "primary_action": "Analyser",
                "target_tab": "simulations",
                "scenario_id": "invest_priority",
            },
            {
                "id": "follow_sites_40",
                "title": "Suivre les 40 sites pilotes",
                "explanation": "Suivre l’avancement opérationnel du programme Sites 40 en exécution.",
                "data_used": ["programs.fdsu_sites (PROG_SITES_40)"],
                "primary_action": "Voir la carte",
                "target_tab": "vue-nationale",
                "scenario_id": "follow_projects",
            },
            {
                "id": "follow_sites_300",
                "title": "Suivre les 300 sites planifiés",
                "explanation": "Suivre la préparation des 300 sites cadrés par la matrice de priorisation.",
                "data_used": ["programs.fdsu_sites (PROG_SITES_300)", "matrice_priorisation_300_sites.xlsx"],
                "primary_action": "Analyser",
                "target_tab": "vue-nationale",
                "scenario_id": "follow_projects",
            },
            {
                "id": "white_zones",
                "title": "Identifier les zones blanches",
                "explanation": "Croiser sites FDSU et infrastructures télécom pour repérer les déficits de couverture.",
                "data_used": ["telecom.infrastructure", "analysis.spatial_relations"],
                "primary_action": "Voir la carte",
                "target_tab": "vue-nationale",
                "scenario_id": "social_infra",
            },
            {
                "id": "plan_ccn",
                "title": "Planifier les CCN",
                "explanation": "Préparer le déploiement des Centres Communautaires Numériques (stratégie 2026–2030).",
                "data_used": ["strategie_fdsu_ccn_2026_2030.docx", "ccn_model.json", "doctrine CCN"],
                "primary_action": "Analyser",
                "target_tab": "simulations",
                "scenario_id": "ccn_implantation",
            },
            {
                "id": "social_infra",
                "title": "Voir les infrastructures sociales à connecter",
                "explanation": "Localiser les établissements sanitaires et leur proximité aux sites FDSU.",
                "data_used": ["health.health_facilities", "analysis.spatial_relations"],
                "primary_action": "Voir la carte",
                "target_tab": "referentiels-sectoriels",
                "scenario_id": "social_infra",
            },
            {
                "id": "decision_report",
                "title": "Préparer un rapport de décision",
                "explanation": "Assembler automatiquement un dossier de décision justifié pour le DG.",
                "data_used": ["explainable_decision", "decision_case", "pdf_template"],
                "primary_action": "Préparer",
                "target_tab": "simulations",
                "scenario_id": "dg_dossier",
            },
            {
                "id": "territory_why",
                "title": "Pourquoi ce territoire est-il prioritaire ?",
                "explanation": "Comprendre la justification territoriale (profil, doctrines, recommandations).",
                "data_used": ["territorial_intelligence", "Master Registry"],
                "primary_action": "Analyser",
                "target_tab": "simulations",
                "scenario_id": "territory_priority",
            },
            {
                "id": "investment_impact",
                "title": "Quel sera l’impact de cet investissement ?",
                "explanation": "Estimer l’impact populationnel et spatial d’un site prioritaire (NSME).",
                "data_used": ["spatial_matching", "decision_case"],
                "primary_action": "Mesurer",
                "target_tab": "simulations",
                "scenario_id": "investment_impact",
            },
            {
                "id": "data_quality",
                "title": "Analyser la qualité des données",
                "explanation": "Contrôler complétude, géolocalisation et types manquants des référentiels.",
                "data_used": ["reference.reference_quality_indicators", "health.health_quality_dashboard"],
                "primary_action": "Analyser",
                "target_tab": "referentiels-sectoriels",
                "scenario_id": "social_infra",
            },
        ],
    }


def get_demo_scenarios() -> dict[str, Any]:
    """Scénarios superviseur — réponses explicables sans payload massif."""
    scores = decision_engine_service.get_scores_summary()
    followup = program_service.get_sites_followup()
    health_stats = health_service.get_statistics()
    health_total = int(health_stats.get("total_facilities") or 0)
    sites_priority = int(scores.get("critical", 0)) + int(scores.get("high", 0))
    sites_fdsu = int(followup.get("sites_40", {}).get("total") or 0) + int(
        followup.get("sites_300", {}).get("total") or 0
    )

    sites_40_total = followup.get("sites_40", {}).get("total")
    sites_300_total = followup.get("sites_300", {}).get("total")
    status_40 = followup.get("sites_40", {}).get("status_message") or STATUS_TO_FILL
    status_300 = followup.get("sites_300", {}).get("status_message") or STATUS_TO_FILL

    def _kpi_lite(key: str, label: str, value: Any, source: str, available: bool = True, display: str | None = None) -> dict[str, Any]:
        return {
            "key": key,
            "label": label,
            "value": value,
            "display": display,
            "available": available,
            "source_table": source,
            "definition": label,
            "calculation_method": "Agrégat Centre de Décision",
            "last_updated": _now(),
            "limitations": None if available else NOT_CALCULATED,
            "recommended_action": "Voir le détail",
        }

    scenarios = [
        {
            "id": "invest_priority",
            "title": "Où investir en priorité ?",
            "business_question": "Quels sites FDSU financer en premier selon la matrice de priorisation ?",
            "synthetic_answer": (
                f"{scores.get('critical', 0)} sites critiques et {scores.get('high', 0)} sites à priorité élevée "
                f"sur {scores.get('total', 0)} sites scorés."
            ),
            "data_used": [
                "decision.fdsu_site_scores",
                "data/business/priority_matrix.json",
                "data/strategic/matrice_priorisation_300_sites.xlsx",
            ],
            "map_focus": "priorisation",
            "table_focus": "critical_high_sites",
            "recommendation": (
                "Concentrer le prochain cycle de financement sur les sites critiques, "
                "puis enchaîner sur les sites à priorité élevée alignés Sites 40 / Sites 300."
            ),
            "limitations": (
                "La matrice Excel est référencée via les extraits JSON ; "
                "les scores site-par-site de la matrice native ne sont pas tous rechargés."
            ),
            "kpis": {
                "critical": _kpi_lite("sites_critical", "Sites critiques", scores.get("critical"), "decision.fdsu_site_scores"),
                "high": _kpi_lite("sites_high", "Sites à priorité élevée", scores.get("high"), "decision.fdsu_site_scores"),
                "priority": _kpi_lite(
                    "sites_priority",
                    "Sites prioritaires",
                    sites_priority,
                    "decision.fdsu_site_scores",
                ),
            },
            "actions": [
                {"label": "Voir la carte des sites prioritaires", "target_tab": "priorisation"},
                {"label": "Exporter la liste", "action": "export-priority"},
            ],
        },
        {
            "id": "social_infra",
            "title": "Où connecter les infrastructures sociales ?",
            "business_question": "Quelles infrastructures sociales (santé) connecter en priorité autour des sites FDSU ?",
            "synthetic_answer": (
                f"{health_total} établissements sanitaires importés ; "
                f"proximité HGR/CS disponible pour les sites FDSU analysés."
            ),
            "data_used": [
                "health.health_facilities",
                "analysis.spatial_relations (nearest_hgr, nearest_health_center)",
                "strategie_fdsu_ccn_2026_2030.docx",
            ],
            "map_focus": "referentiels-sectoriels",
            "table_focus": "health_facilities",
            "recommendation": (
                "Prioriser la connectivité des HGR et centres de santé proches des sites FDSU "
                "dans les zones de déficit réseau."
            ),
            "limitations": (
                "Les « zones de déficit réseau » restent une lecture spatiale indicative ; "
                "pas de polygone officiel de zone blanche national."
            ),
            "kpis": {
                "health_facilities": _kpi_lite(
                    "health_facilities",
                    "Référentiel Santé",
                    health_total,
                    "health.health_facilities",
                ),
                "sites_fdsu": _kpi_lite(
                    "sites_fdsu",
                    "Sites FDSU",
                    sites_fdsu,
                    "programs.fdsu_sites",
                ),
            },
            "actions": [
                {"label": "Ouvrir la carte Santé", "target_tab": "referentiels-sectoriels"},
                {"label": "Voir proximité santé", "action": "health-proximity"},
            ],
        },
        {
            "id": "follow_projects",
            "title": "Comment suivre les projets FDSU ?",
            "business_question": "Quel est l’état d’avancement des programmes Sites 40, Sites 300 et CCN ?",
            "synthetic_answer": (
                f"Sites 40 : {sites_40_total} sites — {status_40}. "
                f"Sites 300 : {sites_300_total} sites — {status_300}."
            ),
            "data_used": [
                "programs.fdsu_sites",
                "programs.fdsu_programs",
                "strategie_fdsu_ccn_2026_2030.docx",
            ],
            "map_focus": "vue-nationale",
            "table_focus": "program_followup",
            "recommendation": (
                "Renseigner les statuts opérationnels détaillés (installé, bloqué, opérationnel) "
                "puis activer le suivi en direct des projets."
            ),
            "limitations": followup.get("global_limitations"),
            "followup": {
                "sites_40": {
                    "metrics": {"total_sites": sites_40_total},
                    "status_message": status_40,
                    "source_table": "programs.fdsu_sites",
                },
                "sites_300": {
                    "metrics": {"total": sites_300_total},
                    "status_message": status_300,
                    "source_table": "programs.fdsu_sites",
                },
                "ccn": {
                    "display": PENDING,
                    "source_table": "programme CCN (non intégré opérationnellement)",
                },
            },
            "kpis": {
                "sites_40": _kpi_lite("sites_40", "Sites 40", sites_40_total, "programs.fdsu_sites"),
                "sites_300": _kpi_lite("sites_300", "Sites 300", sites_300_total, "programs.fdsu_sites"),
                "planned_ccn": _kpi_lite(
                    "planned_ccn",
                    "CCN planifiés",
                    None,
                    "programme CCN",
                    available=False,
                    display=NOT_CALCULATED,
                ),
            },
            "actions": [
                {"label": "Voir le suivi opérationnel", "target_tab": "vue-nationale"},
                {"label": "Ouvrir Sites 40 sur la carte", "action": "map-sites-40"},
            ],
        },
    ]
    return {
        "_meta": {
            "title": "Mode démonstration — Centre de Décision FDSU",
            "scenario_count": len(scenarios),
            "strategic_references": STRATEGIC_SOURCES,
        },
        "scenarios": scenarios,
    }
