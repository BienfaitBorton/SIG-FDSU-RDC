"""Program Lifecycle Engine v1 — six dimensions de statut (Data First / No Black Box).

Sépare strictement :
  A. data_status      — intégration de la donnée dans le SIG
  B. program_status   — état métier du programme
  C. asset_status     — état du site / CCN individuel
  D. worksite_status  — état du chantier
  E. service_status   — service effectivement fourni
  F. impact_status    — nature de l’impact (estimé / projeté / observé)

Aucun statut « opérationnel » n’est inventé. Les totaux inconnus restent null.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ENGINE_VERSION = "ple-1.0.0"
ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "data" / "business" / "program_lifecycle_registry_v1.json"

# ---------------------------------------------------------------------------
# Vocabulaires canoniques
# ---------------------------------------------------------------------------

DATA_STATUS = {
    "integrated": "Données intégrées",
    "partial": "Données partielles",
    "unavailable": "Données indisponibles",
    "error": "Erreur de données",
}

PROGRAM_STATUS = {
    "strategic_planning": "Planification stratégique",
    "national_programming": "Programmation nationale",
    "planned": "Planifié",
    "validated": "Validé",
    "preparation": "En préparation",
    "procurement": "Passation / approvisionnement",
    "deployment_in_progress": "En cours de déploiement",
    "commissioning": "Mise en service",
    "operational": "Opérationnel",
    "suspended": "Suspendu",
    "completed": "Terminé",
    "archived": "Archivé",
}

ASSET_STATUS = {
    "candidate": "Candidat",
    "selected": "Sélectionné",
    "validated": "Validé",
    "studies": "Études",
    "ready_for_deployment": "Prêt au déploiement",
    "deployment_in_progress": "En déploiement",
    "installed": "Installé",
    "testing": "En test",
    "commissioned": "Mis en service",
    "operational": "Opérationnel",
    "suspended": "Suspendu",
    "decommissioned": "Hors service",
    "unknown": "Statut individuel à confirmer",
}

WORKSITE_STATUS = {
    "not_started": "Non démarré",
    "studies": "Études",
    "procurement": "Approvisionnement",
    "civil_works": "Génie civil",
    "equipment_installation": "Installation équipements",
    "integration": "Intégration",
    "technical_testing": "Tests techniques",
    "acceptance": "Réception",
    "completed": "Chantier achevé",
    "unknown": "Chantier non renseigné",
}

SERVICE_STATUS = {
    "not_available": "Service non disponible",
    "pending": "Service en attente",
    "partially_available": "Service partiellement disponible",
    "available": "Service disponible",
    "degraded": "Service dégradé",
    "interrupted": "Service interrompu",
    "unknown": "Service non renseigné",
}

IMPACT_STATUS = {
    "not_measured": "Impact non mesuré",
    "estimated": "Impact estimé",
    "projected": "Impact projeté",
    "observed_partial": "Impact observé partiel",
    "observed": "Impact observé",
    "verified": "Impact vérifié",
}

# Mapping compatibilité (ancien → nouveau), non destructif
LEGACY_PROGRAM_MAP = {
    "planifie": "planned",
    "planned": "planned",
    "en_preparation": "preparation",
    "en_execution": "deployment_in_progress",
    "en_cours": "deployment_in_progress",
    "en_suivi": "commissioning",
    "termine": "completed",
    "active": "deployment_in_progress",  # « active » catalogue ≠ opérationnel physique
    "actif": "deployment_in_progress",
    "paused": "suspended",
    "completed": "completed",
    "defined": "planned",
}

LEGACY_ASSET_MAP = {
    "a qualifier": "unknown",
    "à qualifier": "unknown",
    "planifie": "selected",
    "planifié": "selected",
    "planned": "selected",
    "en execution": "deployment_in_progress",
    "en exécution": "deployment_in_progress",
    "en cours": "deployment_in_progress",
    "deploying": "deployment_in_progress",
    "preparation": "studies",
    "installé": "installed",
    "installe": "installed",
    "installed": "installed",
    "testing": "testing",
    "commissioned": "commissioned",
    "mis en service": "commissioned",
    "operational": "operational",
    "opérationnel": "operational",
    "operationnel": "operational",
    "actif": "unknown",  # « actif » souvent ambigu — ne force pas operational
    "suspended": "suspended",
    "suspendu": "suspended",
}

# SDG / Data First maturity → libellés non ambigus (≠ site opérationnel)
DATA_MATURITY_UI = {
    "operational": "Référentiel intégré",
    "integrated": "Référentiel intégré",
    "partial": "Données partielles",
    "empty": "Aucun objet trouvé",
    "integrating": "En cours d’intégration",
    "integration_pending": "En cours d’intégration",
    "error": "Erreur d’intégration",
    "demonstration": "Démonstration / partiel",
    "anomaly": "Anomalie d’intégration",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().replace("_", " ").replace("-", " ").split())


def _dim(code: str | None, labels: dict[str, str], *, source: str, confidence: str, note: str | None = None) -> dict[str, Any]:
    if not code:
        return {
            "code": None,
            "label": "À consolider",
            "source": source,
            "as_of": None,
            "confidence": confidence,
            "note": note or "Valeur non renseignée — null conservé, pas de faux zéro.",
        }
    return {
        "code": code,
        "label": labels.get(code, code),
        "source": source,
        "as_of": _now(),
        "confidence": confidence,
        "note": note,
    }


def _load_registry() -> dict[str, Any]:
    if not REGISTRY_PATH.exists():
        return {"programs": {}}
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def normalize_program_code(code: str | None) -> str:
    raw = _norm(code).replace(" ", "_")
    aliases = {
        "prog_sites_40": "sites_40",
        "sites40": "sites_40",
        "prog_sites_300": "sites_300",
        "sites300": "sites_300",
        "prog_sites_20476": "sites_20476",
        "sites20476": "sites_20476",
        "prog_ccn": "ccn",
        "ccn_demo": "ccn",
    }
    return aliases.get(raw, raw)


def map_legacy_program_status(raw: Any) -> str | None:
    key = _norm(raw).replace(" ", "_")
    if key in LEGACY_PROGRAM_MAP:
        return LEGACY_PROGRAM_MAP[key]
    compact = key.replace(" ", "")
    for k, v in LEGACY_PROGRAM_MAP.items():
        if k.replace(" ", "") == compact:
            return v
    return None


def map_legacy_asset_status(raw: Any) -> str | None:
    if raw is None or str(raw).strip() == "":
        return None
    key = _norm(raw)
    if key in LEGACY_ASSET_MAP:
        return LEGACY_ASSET_MAP[key]
    for k, v in LEGACY_ASSET_MAP.items():
        if k in key:
            return v
    return "unknown"


def data_maturity_label(code: str | None) -> str:
    """Libellé UI pour maturité d’intégration (jamais « Opérationnel » physique)."""
    if not code:
        return "À consolider"
    return DATA_MATURITY_UI.get(str(code), DATA_MATURITY_UI.get(_norm(code).replace(" ", "_"), str(code)))


def resolve_program_lifecycle(program_code: str | None) -> dict[str, Any]:
    """Contrat programme — six dimensions + progress (null si inconnu)."""
    code = normalize_program_code(program_code)
    reg = _load_registry().get("programs") or {}
    row = reg.get(code)
    if not row:
        return {
            "_meta": {"engine": ENGINE_VERSION, "generated_at": _now()},
            "program_code": code or None,
            "program_status": _dim(None, PROGRAM_STATUS, source="unknown", confidence="low"),
            "data_status": _dim("unavailable", DATA_STATUS, source="unknown", confidence="low"),
            "asset_status": _dim(None, ASSET_STATUS, source="unknown", confidence="low"),
            "worksite_status": _dim(None, WORKSITE_STATUS, source="unknown", confidence="low"),
            "service_status": _dim(None, SERVICE_STATUS, source="unknown", confidence="low"),
            "impact_status": _dim("not_measured", IMPACT_STATUS, source="unknown", confidence="low"),
            "progress": {
                "total": None,
                "planned": None,
                "in_progress": None,
                "installed": None,
                "commissioned": None,
                "operational": None,
            },
            "source": None,
            "notes": ["Programme hors registre institutionnel PLE v1."],
            "known": False,
        }

    return {
        "_meta": {"engine": ENGINE_VERSION, "generated_at": _now(), "registry": str(REGISTRY_PATH.relative_to(ROOT))},
        "program_code": row["program_code"],
        "program_name": row.get("program_name"),
        "phase_label": row.get("phase_label"),
        "program_status": _dim(
            row.get("program_status"),
            PROGRAM_STATUS,
            source=row.get("source") or "registry",
            confidence=row.get("confidence") or "medium",
            note="; ".join(row.get("notes") or []) or None,
        ),
        "data_status": _dim(
            row.get("data_status"),
            DATA_STATUS,
            source=row.get("source") or "registry",
            confidence=row.get("confidence") or "medium",
            note="Qualité d’intégration SIG — distinct de l’avancement physique.",
        ),
        "asset_status": _dim(
            row.get("default_asset_status"),
            ASSET_STATUS,
            source=row.get("source") or "registry",
            confidence="low" if row.get("default_asset_status") is None else "medium",
            note=row.get("default_asset_status_note"),
        ),
        "worksite_status": _dim(
            row.get("default_worksite_status"),
            WORKSITE_STATUS,
            source=row.get("source") or "registry",
            confidence="low",
            note="Détail chantier non consolidé au niveau programme." if row.get("default_worksite_status") is None else None,
        ),
        "service_status": _dim(
            row.get("default_service_status") or "not_available",
            SERVICE_STATUS,
            source=row.get("source") or "registry",
            confidence="medium",
            note="Aucun service considéré disponible sans preuve de mise en service.",
        ),
        "impact_status": _dim(
            row.get("default_impact_status") or "not_measured",
            IMPACT_STATUS,
            source=row.get("source") or "registry",
            confidence=row.get("confidence") or "medium",
        ),
        "progress": {
            "total": row.get("total_target"),
            "planned": row.get("total_target") if row.get("program_status") in {"planned", "strategic_planning", "preparation"} else None,
            "in_progress": None,
            "installed": None,
            "commissioned": None,
            "operational": None,
            "note": "Compteurs physiques individuels non disponibles — null volontaire.",
        },
        "data_class": row.get("data_class"),
        "source": row.get("source"),
        "notes": list(row.get("notes") or []),
        "known": True,
        "compatibility": {
            "legacy_program_status_fdsu": {
                "sites_40": "EN_EXECUTION → deployment_in_progress",
                "sites_300": "PLANIFIE → planned",
                "sites_20476": "PLANIFIE → strategic_planning (registre institutionnel)",
                "ccn": "status=active catalogue → preparation (registre)",
            }
        },
    }


def resolve_asset_lifecycle(
    *,
    program_code: str | None,
    asset_id: str | int | None = None,
    raw_status: Any = None,
    asset_type: str = "FDSU_SITE",
    data_class: str | None = None,
) -> dict[str, Any]:
    """Profil multi-dimensionnel d’un actif."""
    prog = resolve_program_lifecycle(program_code)
    code = prog.get("program_code")

    mapped = map_legacy_asset_status(raw_status)
    asset_note = None
    confidence = "low"

    if asset_type == "CCN" or code == "ccn" or data_class == "demonstration":
        # DEMO : ne jamais promouvoir operational production
        if mapped == "operational":
            mapped = "unknown"
            asset_note = (
                "Statut DEMO « operational » non promu en production — "
                "aucun CCN présenté comme opérationnel sans donnée officielle."
            )
        data_status_code = "partial"
        impact_code = "projected"
        service_code = "not_available"
        worksite_code = None
    else:
        data_status_code = (prog.get("data_status") or {}).get("code") or "partial"
        if mapped in {"commissioned", "operational"}:
            # Preuve individuelle absente dans les référentiels actuels → ne pas valider
            # les mots-clés seuls comme « opérationnel » observé.
            if _norm(raw_status) in {"operational", "opérationnel", "operationnel", "actif"} and code in {
                "sites_40",
                "sites_300",
                "sites_20476",
            }:
                mapped = "unknown"
                asset_note = "Libellé ambigu ou sans preuve de mise en service — statut individuel à confirmer."
                impact_code = (prog.get("impact_status") or {}).get("code") or "estimated"
                service_code = "not_available"
            else:
                impact_code = "observed" if mapped == "operational" else "observed_partial"
                service_code = "available" if mapped == "operational" else "pending"
        elif mapped in {"installed", "testing", "deployment_in_progress"}:
            impact_code = "estimated"
            service_code = "pending"
        elif mapped is None or mapped == "unknown":
            asset_note = (prog.get("asset_status") or {}).get("note") or (
                "Statut individuel en cours de consolidation."
            )
            mapped = None
            impact_code = (prog.get("impact_status") or {}).get("code") or "estimated"
            service_code = "not_available"
        else:
            impact_code = (prog.get("impact_status") or {}).get("code") or "projected"
            service_code = "not_available"
        worksite_code = None
        if mapped == "deployment_in_progress":
            worksite_code = "equipment_installation"
        elif mapped == "studies":
            worksite_code = "studies"
        elif mapped in {"selected", "candidate", "validated"}:
            worksite_code = "not_started"

    # Mode d’impact pour TIE / graphiques
    if impact_code in {"observed", "observed_partial", "verified"}:
        impact_mode = "real"
        impact_badge = "Observé" if impact_code != "observed_partial" else "Observé partiel"
    elif impact_code == "projected":
        impact_mode = "planned"
        impact_badge = "Projeté"
    elif impact_code == "estimated":
        impact_mode = "planned"
        impact_badge = "Estimé"
    else:
        impact_mode = "planned"
        impact_badge = "Non mesuré"

    return {
        "_meta": {"engine": ENGINE_VERSION, "generated_at": _now()},
        "asset_type": asset_type,
        "asset_id": asset_id,
        "program_code": code,
        "raw_status": raw_status,
        "data_status": _dim(data_status_code, DATA_STATUS, source="ple+program", confidence="medium"),
        "program_status": prog.get("program_status"),
        "asset_status": _dim(
            mapped if mapped is not None else None,
            ASSET_STATUS,
            source=f"raw_status:{raw_status!s}" if raw_status else "registry_default",
            confidence=confidence,
            note=asset_note,
        ),
        "worksite_status": _dim(worksite_code, WORKSITE_STATUS, source="derived_or_null", confidence="low"),
        "service_status": _dim(service_code, SERVICE_STATUS, source="ple_rules", confidence="medium"),
        "impact_status": _dim(impact_code, IMPACT_STATUS, source="ple_rules", confidence="medium"),
        "ui_badges": {
            "data": DATA_STATUS.get(data_status_code, "Données"),
            "program": (prog.get("program_status") or {}).get("label"),
            "asset": ASSET_STATUS.get(mapped) if mapped else "Statut individuel à confirmer",
            "impact": IMPACT_STATUS.get(impact_code, impact_badge),
        },
        "impact_accounting": {
            "mode": impact_mode,
            "badge": impact_badge,
            "counts_as_observed_coverage": impact_code in {"observed", "verified"},
            "counts_as_projected_coverage": impact_code in {"estimated", "projected", "observed_partial"},
            "note": (
                "Un site en déploiement / planifié n’entre pas dans la couverture réellement observée."
            ),
        },
        "phase_label": prog.get("phase_label"),
        "notes": list(prog.get("notes") or []),
    }


def build_programs_board() -> dict[str, Any]:
    """Tableau Salle de Pilotage — suivi programmes sans faux zéros."""
    codes = ["sites_40", "sites_300", "sites_20476", "ccn"]
    rows = []
    for code in codes:
        p = resolve_program_lifecycle(code)
        prog = p.get("progress") or {}
        rows.append(
            {
                "program": p.get("program_name") or code,
                "program_code": code,
                "phase": p.get("phase_label"),
                "status": (p.get("program_status") or {}).get("label"),
                "status_code": (p.get("program_status") or {}).get("code"),
                "data_status": (p.get("data_status") or {}).get("label"),
                "total": prog.get("total"),
                "in_progress": prog.get("in_progress"),
                "installed": prog.get("installed"),
                "commissioned": prog.get("commissioned"),
                "operational": prog.get("operational"),
                "display": {
                    "in_progress": prog.get("in_progress") if prog.get("in_progress") is not None else "À consolider",
                    "installed": prog.get("installed") if prog.get("installed") is not None else "À consolider",
                    "commissioned": prog.get("commissioned") if prog.get("commissioned") is not None else "À consolider",
                    "operational": prog.get("operational") if prog.get("operational") is not None else "À consolider",
                },
                "impact_status": (p.get("impact_status") or {}).get("label"),
                "notes": p.get("notes"),
            }
        )
    return {
        "_meta": {"engine": ENGINE_VERSION, "generated_at": _now(), "title": "Suivi des programmes — cycle de vie"},
        "programs": rows,
        "progress_axes": {
            "administrative": "État programmatique (program_status)",
            "physical": "Installés / chantiers — à consolider",
            "commissioning": "Mises en service — à consolider",
            "impact": "Impact estimé / projeté / observé — pas de % inventé",
        },
        "limits": [
            "Pas de pourcentage d’avancement fabriqué à partir de statuts incomplets.",
            "Null / « À consolider » lorsque la preuve manque.",
        ],
    }


def audit_status_matrix() -> dict[str, Any]:
    """Matrice d’audit avant/après des sources de faux « opérationnel »."""
    return {
        "_meta": {"engine": ENGINE_VERSION, "generated_at": _now()},
        "matrix": [
            {
                "screen_or_service": "SDG OFFICIAL_STATUS / maturity",
                "object": "domaine relationnel",
                "status_before": "Opérationnel",
                "source": "spatial_decision_graph_service.OFFICIAL_STATUS",
                "real_meaning": "Référentiel branché / relations trouvées",
                "status_expected": "Référentiel intégré / Analyse disponible",
            },
            {
                "screen_or_service": "Territorial Intelligence field.status",
                "object": "indicateur",
                "status_before": "Opérationnel",
                "source": "territorial_*_service ST_OPERATIONAL",
                "real_meaning": "Donnée disponible",
                "status_expected": "Données intégrées",
            },
            {
                "screen_or_service": "Sites 40 program",
                "object": "programme",
                "status_before": "active / EN_EXECUTION / sites tous opérationnels (risque)",
                "source": "fdsu_programs.json",
                "real_meaning": "Déploiement en cours",
                "status_expected": "deployment_in_progress",
            },
            {
                "screen_or_service": "Sites 300",
                "object": "programme",
                "status_before": "PLANIFIE (OK) / risque de badge opérationnel data",
                "source": "fdsu_programs.json",
                "real_meaning": "Planifié",
                "status_expected": "planned",
            },
            {
                "screen_or_service": "Sites 20 476",
                "object": "programme",
                "status_before": "PLANIFIE",
                "source": "fdsu_programs.json",
                "real_meaning": "Programmation nationale",
                "status_expected": "strategic_planning",
            },
            {
                "screen_or_service": "CCN DEMO",
                "object": "actifs DEMO",
                "status_before": "operational (7) comptés comme ops",
                "source": "demo_ccn.json + ccn_operational_service",
                "real_meaning": "Démonstration",
                "status_expected": "preparation + data_class=demonstration",
            },
            {
                "screen_or_service": "TIE classify_deployment_status",
                "object": "site status text",
                "status_before": "mot « opération » → Réalisé",
                "source": "territorial_impact_engine",
                "real_meaning": "Heuristique trop large",
                "status_expected": "PLE asset_status + impact_accounting",
            },
            {
                "screen_or_service": "program_service sites_in_execution",
                "object": "sites « à qualifier »",
                "status_before": "comptés en exécution",
                "source": "SQL LIKE",
                "real_meaning": "Statut à qualifier",
                "status_expected": "unknown / À consolider",
            },
        ],
    }


def history_contract_template() -> dict[str, Any]:
    """Contrat d’historique non destructif — sans inventer le passé."""
    return {
        "_meta": {
            "engine": ENGINE_VERSION,
            "purpose": "Modèle pour futures transitions — aucune entrée historique inventée",
        },
        "record_shape": {
            "entity_type": "program|asset|worksite|service|impact",
            "entity_id": "...",
            "dimension": "program_status|asset_status|...",
            "previous_code": None,
            "new_code": None,
            "changed_at": None,
            "source": None,
            "actor": "user|system",
            "justification": None,
            "evidence_ref": None,
        },
        "storage_recommendation": "Table PostgreSQL versionnée (pas case_history.json runtime)",
        "records": [],
    }
