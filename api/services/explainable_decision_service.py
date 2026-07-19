"""Explainable Decision Engine v1 — Dossier de Décision (Decision Case File).

Principe : aucune recommandation sans justification.
Le moteur consomme doctrines, matrices, Knowledge Hub et référentiels —
aucune pondération métier n'est codée en dur ici.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUSINESS_DIR = PROJECT_ROOT / "data" / "business"
DOCTRINES_DIR = BUSINESS_DIR / "doctrines"
CATALOG_PATH = DOCTRINES_DIR / "catalog.json"
ENGINE_META_PATH = BUSINESS_DIR / "decision_engine_meta.json"
MATRIX_PATH = BUSINESS_DIR / "priority_matrix.json"
HISTORY_PATH = PROJECT_ROOT / "data" / "decision" / "case_history.json"
PDF_TEMPLATE_PATH = PROJECT_ROOT / "data" / "decision" / "pdf_templates" / "decision_case_file_v1.json"

CASE_SECTIONS = [
    "summary",
    "asset",
    "score",
    "confidence",
    "doctrine",
    "matrix",
    "criteria",
    "data_used",
    "indicators",
    "impacts",
    "risks",
    "assumptions",
    "sources",
    "justification",
    "traceability",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8")
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        # Fichier concaténé / corrompu : récupérer le premier objet JSON valide
        try:
            data, _end = json.JSONDecoder().raw_decode(raw)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}


def _load_history_payload() -> dict[str, Any]:
    payload = _load_json(HISTORY_PATH)
    if not isinstance(payload, dict):
        return {"_meta": {"title": "Historique des Dossiers de Décision"}, "history": []}
    if "history" not in payload or not isinstance(payload.get("history"), list):
        return {"_meta": payload.get("_meta") or {"title": "Historique des Dossiers de Décision"}, "history": []}
    return payload


def _save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Écriture atomique pour éviter la corruption (JSON concaténé)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def engine_meta() -> dict[str, Any]:
    return _load_json(ENGINE_META_PATH)


def pdf_template() -> dict[str, Any]:
    return _load_json(PDF_TEMPLATE_PATH)


def list_doctrines() -> dict[str, Any]:
    catalog = _load_json(CATALOG_PATH)
    return {
        "_meta": catalog.get("_meta") or {"title": "Catalogue doctrines"},
        "doctrines": catalog.get("doctrines") or [],
    }


def load_doctrine_by_id(doctrine_id: str) -> dict[str, Any] | None:
    needle = str(doctrine_id or "").strip().upper()
    for item in list_doctrines().get("doctrines") or []:
        if str(item.get("id") or "").upper() != needle:
            continue
        path = item.get("path")
        if not path:
            return {
                "_meta": {
                    "doctrine_id": item.get("id"),
                    "title": item.get("label"),
                    "status": item.get("status"),
                    "version": item.get("version"),
                },
                "planned": True,
                "message": "Doctrine planifiée — fichier non encore publié.",
            }
        doctrine = _load_json(PROJECT_ROOT / path)
        return {
            "_meta": {
                **(doctrine.get("_meta") or {}),
                "catalog_status": item.get("status"),
                "catalog_path": path,
            },
            "doctrine": doctrine,
            "matrix": _load_json(MATRIX_PATH) if (doctrine.get("_meta") or {}).get("matrix_ref") or doctrine.get("priority_matrix") else _load_json(MATRIX_PATH),
        }
    return None


def _append_history(entry: dict[str, Any]) -> None:
    """Journalisation best-effort — ne doit jamais faire échouer un dossier."""
    try:
        payload = _load_history_payload()
        history = list(payload.get("history") or [])
        history.insert(0, entry)
        payload = {
            "_meta": {
                "title": "Historique des Dossiers de Décision",
                "updated_at": _now(),
                "count": len(history[:500]),
            },
            "history": history[:500],
        }
        _save_json(HISTORY_PATH, payload)
    except Exception:
        # Historique non bloquant
        return


def get_case_history(case_id: str | None = None, limit: int = 50) -> dict[str, Any]:
    payload = _load_history_payload()
    history = list(payload.get("history") or [])
    if case_id:
        history = [h for h in history if h.get("case_id") == case_id or str(h.get("asset_id")) == str(case_id)]
    return {
        "_meta": {"title": "Traçabilité décisions", "count": len(history[:limit])},
        "history": history[:limit],
    }


def _parse_asset_ref(asset_id: str, asset_type: str | None = None) -> tuple[str, str]:
    raw = str(asset_id or "").strip()
    if ":" in raw:
        prefix, value = raw.split(":", 1)
        return prefix.lower(), value
    if asset_type:
        return asset_type.lower(), raw
    if raw.upper().startswith("CCN") or "CCN" in raw.upper():
        return "ccn", raw
    if raw.upper().startswith("DCF-CCN-"):
        return "ccn", raw[8:]
    if raw.upper().startswith("DCF-SITE-"):
        return "site", raw[9:]
    return "site", raw


def _confidence_level(*, missing: list[str], security: bool, score: float) -> dict[str, Any]:
    if security:
        level, label = "low", "Faible — contrainte sécuritaire"
    elif len(missing) >= 3:
        level, label = "low", "Faible — données manquantes"
    elif missing:
        level, label = "medium", "Moyenne — données partielles"
    elif score >= 70:
        level, label = "high", "Élevée"
    else:
        level, label = "medium", "Moyenne"
    return {"level": level, "label": label, "missing_fields": missing}


def _format_why(template: str, *, score: float, weight_percent: Any, context: str, value: Any = None) -> str:
    text = template or "Score {score}/100 — contribution selon doctrine (poids {weight_percent} %). Contexte : {context}."
    return (
        text.replace("{score}", str(score))
        .replace("{weight_percent}", str(weight_percent))
        .replace("{context}", str(context or "—"))
        .replace("{value}", str(value if value is not None else context or "—"))
    )


def _knowledge_indicators(ids: list[str] | None = None) -> list[dict[str, Any]]:
    from api.services import knowledge_hub_service

    catalog = knowledge_hub_service.list_indicators().get("indicators") or []
    if not ids:
        return [
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "family": item.get("family"),
                "value_status": item.get("value_status"),
                "decision_usage": item.get("decision_usage"),
            }
            for item in catalog[:12]
        ]
    wanted = {str(i).upper() for i in ids}
    return [
        {
            "id": item.get("id"),
            "name": item.get("name"),
            "family": item.get("family"),
            "value_status": item.get("value_status"),
            "decision_usage": item.get("decision_usage"),
        }
        for item in catalog
        if str(item.get("id") or "").upper() in wanted
    ]


def _build_case_shell(
    *,
    case_id: str,
    asset: dict[str, Any],
    score: float,
    priority_level: str,
    priority_label: str,
    doctrine: dict[str, Any],
    matrix: dict[str, Any],
    criteria: list[dict[str, Any]],
    justification: list[dict[str, Any]],
    data_used: dict[str, Any],
    indicators: list[dict[str, Any]] | dict[str, Any],
    impacts: dict[str, Any],
    risks: list[dict[str, Any]],
    assumptions: list[str],
    sources: list[str],
    confidence: dict[str, Any],
    summary: str,
) -> dict[str, Any]:
    meta = engine_meta().get("_meta") or {}
    doctrine_meta = doctrine.get("_meta") or {}
    generated_at = _now()
    case = {
        "case_id": case_id,
        "generated_at": generated_at,
        "engine_version": meta.get("version") or "1.0.0",
        "engine_id": meta.get("engine_id"),
        "summary": {
            "text": summary,
            "recommendation": summary,
            "priority_level": priority_level,
            "priority_label": priority_label,
            "score": score,
        },
        "asset": asset,
        "score": {
            "global": score,
            "priority_level": priority_level,
            "priority_label": priority_label,
            "max": 100,
        },
        "confidence": confidence,
        "doctrine": {
            "id": doctrine_meta.get("doctrine_id"),
            "title": doctrine_meta.get("title"),
            "version": doctrine_meta.get("version"),
            "date": doctrine_meta.get("updated_at"),
            "references": [
                doctrine_meta.get("source_document"),
                doctrine_meta.get("source_table"),
            ],
            "hardcoded_forbidden": doctrine_meta.get("hardcoded_forbidden", True),
        },
        "matrix": {
            "id": (doctrine.get("priority_matrix") or {}).get("id") or (matrix.get("_meta") or {}).get("title") or "Matrice de priorisation des sites FDSU",
            "label": (doctrine.get("priority_matrix") or {}).get("label")
            or (matrix.get("_meta") or {}).get("title")
            or "Matrice de priorisation des sites FDSU",
            "ref": (doctrine.get("priority_matrix") or {}).get("ref") or "data/business/priority_matrix.json",
            "levels": (doctrine.get("priority_matrix") or {}).get("levels") or matrix.get("priority_levels"),
            "source": (matrix.get("_meta") or {}).get("source_documents"),
        },
        "criteria": criteria,
        "data_used": data_used,
        "indicators": indicators,
        "impacts": impacts,
        "risks": risks,
        "assumptions": assumptions,
        "sources": [s for s in sources if s],
        "justification": justification,
        "traceability": {
            "doctrine_id": doctrine_meta.get("doctrine_id"),
            "doctrine_version": doctrine_meta.get("version"),
            "sources": [s for s in sources if s],
            "generated_at": generated_at,
            "engine_version": meta.get("version") or "1.0.0",
            "user": {"id": None, "label": "system", "status": "prepared"},
        },
        "pdf_export": {
            "enabled": False,
            "template_id": "DCF_PDF_TEMPLATE_V1",
            "template_path": "data/decision/pdf_templates/decision_case_file_v1.json",
            "note": "Structure prête — génération PDF non activée.",
        },
        "_meta": {
            "title": "Dossier de Décision FDSU",
            "principle": "Aucune recommandation sans justification.",
            "sections": CASE_SECTIONS,
        },
    }
    _append_history(
        {
            "case_id": case_id,
            "asset_type": asset.get("asset_type"),
            "asset_id": asset.get("id") or asset.get("business_id"),
            "score": score,
            "priority_level": priority_level,
            "doctrine_id": doctrine_meta.get("doctrine_id"),
            "doctrine_version": doctrine_meta.get("version"),
            "engine_version": meta.get("version") or "1.0.0",
            "generated_at": generated_at,
            "user": "system",
            "sources": [s for s in sources if s][:5],
        }
    )
    return case


def build_ccn_case(ccn_id: str) -> dict[str, Any] | None:
    from api.services import ccn_operational_service, knowledge_hub_service

    detail = ccn_operational_service.get_ccn(ccn_id)
    if not detail:
        return None
    ccn = detail["ccn"]
    doctrine = ccn_operational_service.load_doctrine()
    matrix = _load_json(MATRIX_PATH)
    doctrine_meta = doctrine.get("_meta") or {}

    criteria_index = {c.get("id"): c for c in doctrine.get("selection_criteria") or []}
    justification = []
    criteria_out = []
    for item in ccn.get("criteria_details") or []:
        cid = item.get("criterion_id")
        meta_c = criteria_index.get(cid) or {}
        score = float(item.get("score") or 0)
        weight_pct = item.get("weight_percent") or meta_c.get("weight_percent")
        max_contrib = float(weight_pct or 0)
        contribution = float(item.get("contribution") or 0)
        context = ccn.get("host_type") or ccn.get("ccn_type_label") or ccn.get("province")
        why = _format_why(
            meta_c.get("why_template") or "",
            score=score,
            weight_percent=weight_pct,
            context=context,
            value=context,
        )
        block = {
            "criterion_id": cid,
            "label": item.get("label") or meta_c.get("label"),
            "score": score,
            "score_display": f"{score:.0f}/100",
            "weight": item.get("weight"),
            "weight_percent": weight_pct,
            "contribution": contribution,
            "contribution_display": f"{contribution:.1f}/{max_contrib}",
            "why": why,
            "description": meta_c.get("description"),
        }
        justification.append(block)
        criteria_out.append(block)

    flags = set(ccn.get("measurement_flags") or [])
    missing = []
    if not ccn.get("population_served"):
        missing.append("population_served")
    if not ccn.get("site_fdsu_code"):
        missing.append("site_fdsu_code")
    security = bool(ccn.get("security_constraint"))
    confidence = _confidence_level(missing=missing, security=security, score=float(ccn.get("priority_score") or 0))

    impacts = {
        "population_touchee": ccn.get("population_served") or 0,
        "ecoles_concernees": 1 if "MEAS_SCHOOL" in flags else 0,
        "centres_de_sante": 1 if "MEAS_HOSPITAL" in flags else 0,
        "administrations": 1 if "MEAS_ADMIN" in flags else 0,
        "services_numeriques": len(ccn.get("services") or []),
        "note": "Impacts estimés à partir des flags de mesure et attributs CCN (démonstration).",
    }

    risks = []
    if security:
        risks.append({"type": "security", "label": "Contrainte sécuritaire", "severity": "hard"})
    if missing:
        risks.append({"type": "missing_data", "label": "Données manquantes", "fields": missing, "severity": "confidence"})
    if confidence["level"] == "low":
        risks.append({"type": "low_confidence", "label": "Faible confiance", "severity": "flag"})
    for rule in ccn.get("opposability") or []:
        if rule.get("applied"):
            risks.append(
                {
                    "type": "opposability",
                    "label": rule.get("label"),
                    "note": rule.get("note"),
                    "rule_id": rule.get("rule_id"),
                    "severity": "rule",
                }
            )

    indicator_ids = []
    for c in doctrine.get("selection_criteria") or []:
        indicator_ids.extend(c.get("indicator_refs") or [])
    # measurement indicators as business objects
    meas = [
        {"id": m.get("id"), "label": m.get("label"), "category": m.get("category"), "present": m.get("id") in flags}
        for m in doctrine.get("measurement_indicators") or []
    ]
    kh_indicators = _knowledge_indicators(indicator_ids or None)

    # Knowledge Hub domain touch (no direct table reads)
    _ = knowledge_hub_service.get_domain("business_doctrine")

    score = float(ccn.get("priority_score") or 0)
    level = str(ccn.get("priority_level") or "low")
    summary = (
        f"Recommandation CCN « {ccn.get('name')} » — score {score}/100 "
        f"({level}). Doctrine {doctrine_meta.get('title')} v{doctrine_meta.get('version')}."
    )

    case_id = f"DCF-CCN-{ccn.get('id') or ccn_id}"
    return _build_case_shell(
        case_id=case_id,
        asset={
            "asset_type": "CCN",
            "id": ccn.get("id"),
            "business_id": ccn.get("business_id"),
            "name": ccn.get("name"),
            "province": ccn.get("province"),
            "territoire": ccn.get("territoire"),
            "program_code": ccn.get("program_code"),
            "ccn_type": ccn.get("ccn_type"),
            "site_fdsu_code": ccn.get("site_fdsu_code"),
            "status": ccn.get("status"),
        },
        score=score,
        priority_level=level,
        priority_label=level,
        doctrine=doctrine,
        matrix=matrix,
        criteria=criteria_out,
        justification=justification,
        data_used={
            "source": "data/programs/ccn/demo_ccn.json",
            "data_class": "demonstration",
            "fields": {
                "population_served": ccn.get("population_served"),
                "host_type": ccn.get("host_type"),
                "site_fdsu_code": ccn.get("site_fdsu_code"),
                "measurement_flags": list(flags),
                "criteria_scores": ccn.get("criteria_scores") or {},
            },
            "knowledge_hub_domain": "business_doctrine",
        },
        indicators={"measurement": meas, "nif": kh_indicators},
        impacts=impacts,
        risks=risks,
        assumptions=[
            "Les scores critères proviennent du jeu DEMO CCN.",
            "Les pondérations sont lues depuis la doctrine versionnée.",
            "Les impacts sont estimatifs tant que le NIF n'est pas valorisé.",
        ],
        sources=[
            doctrine_meta.get("source_document"),
            "data/business/doctrines/ccn_doctrine_v1.json",
            "data/programs/ccn/demo_ccn.json",
            "data/knowledge/domains.json",
            "data/knowledge/national_indicators.json",
        ],
        confidence=confidence,
        summary=summary,
    )


def build_site_case(site_id: str, program_code: str | None = None) -> dict[str, Any] | None:
    from api.services import knowledge_hub_service, site_entity_resolver

    doctrine_bundle = load_doctrine_by_id("DOCTRINE_SITES_FDSU")
    if not doctrine_bundle or doctrine_bundle.get("planned"):
        return None
    doctrine = doctrine_bundle["doctrine"]
    matrix = doctrine_bundle.get("matrix") or _load_json(MATRIX_PATH)
    doctrine_meta = doctrine.get("_meta") or {}

    resolved = site_entity_resolver.resolve_site(site_id, program_code=program_code, entity_type="site")
    if not resolved or not resolved.get("resolved"):
        return None

    explained = resolved.get("explained") or {}
    site = explained.get("site") or {}
    sid = int(resolved["site_id"])
    criteria_raw = (explained.get("explanation") or {}).get("criteria") or {}
    if isinstance(criteria_raw, dict):
        criteria_pairs = list(criteria_raw.items())
    else:
        criteria_pairs = [(item.get("criterion_id") or item.get("id"), item) for item in (criteria_raw or [])]

    criteria_index = {c.get("id"): c for c in doctrine.get("selection_criteria") or []}
    justification = []
    criteria_out = []
    for key, item in criteria_pairs:
        if not isinstance(item, dict):
            continue
        cid = str(key or item.get("criterion_id") or item.get("id") or "")
        meta_c = criteria_index.get(cid) or {}
        score = float(item.get("score") or 0)
        weight = float(item.get("weight") or meta_c.get("weight") or 0)
        weight_pct = meta_c.get("weight_percent") or round(weight * 100)
        contribution = round(score * weight, 2)
        why = _format_why(
            meta_c.get("why_template") or "",
            score=score,
            weight_percent=weight_pct,
            context=item.get("label") or "",
            value=item.get("label"),
        )
        block = {
            "criterion_id": cid,
            "label": meta_c.get("label") or item.get("label"),
            "score": score,
            "score_display": f"{score:.0f}/100",
            "weight": weight,
            "weight_percent": weight_pct,
            "contribution": contribution,
            "contribution_display": f"{contribution:.1f}/{weight_pct}",
            "why": why,
            "raw_label": item.get("label"),
            "description": meta_c.get("description"),
        }
        justification.append(block)
        criteria_out.append(block)

    missing = []
    if site.get("population") in (None, 0):
        missing.append("population")
    if site.get("distance") is None and not site.get("distance_level"):
        missing.append("distance")
    confidence = _confidence_level(missing=missing, security=False, score=float(site.get("priority_score") or 0))

    impacts = {
        "population_touchee": site.get("population") or 0,
        "ecoles_concernees": None,
        "centres_de_sante": None,
        "marches": None,
        "couverture_reseau": site.get("distance_level") or site.get("distance"),
        "programme": site.get("program_code"),
        "note": "Impacts partiels — indicateurs sectoriels NIF en structure_only.",
    }

    risks = []
    if missing:
        risks.append({"type": "missing_data", "label": "Données manquantes", "fields": missing})
    if confidence["level"] == "low":
        risks.append({"type": "low_confidence", "label": "Faible confiance"})

    indicator_ids = []
    for c in doctrine.get("selection_criteria") or []:
        indicator_ids.extend(c.get("indicator_refs") or [])
    meas = [
        {"id": m.get("id"), "label": m.get("label"), "category": m.get("category")}
        for m in doctrine.get("measurement_indicators") or []
    ]
    kh_indicators = _knowledge_indicators(indicator_ids or None)
    _ = knowledge_hub_service.get_domain("business_doctrine")

    score = float(site.get("priority_score") or 0)
    level = str(site.get("priority_level") or "low")
    label = site.get("priority_level_label") or level
    try:
        from api.services.site_display_name import enrich_site_labels

        site = enrich_site_labels(site)
    except Exception:  # noqa: BLE001
        pass
    display_name = (
        site.get("display_name")
        or site.get("name")
        or site.get("site_name")
        or site.get("site_code")
        or str(sid)
    )
    summary = (
        f"Recommandation Site « {display_name} » — "
        f"score {score}/100 ({label}). Doctrine {doctrine_meta.get('title')} v{doctrine_meta.get('version')}."
    )
    case_id = f"DCF-SITE-{site.get('site_id') or sid}"

    # Enrichissement NCI (besoins territoriaux) — ne remplace pas doctrine/matrice
    nci_context: dict[str, Any] | None = None
    try:
        from api.services import coverage_intelligence_service as nci

        terr = site.get("territoire")
        if terr:
            nci_context = nci.explain_territory_index(str(terr))
            if not nci_context.get("available"):
                nci_context = None
    except Exception:  # noqa: BLE001
        nci_context = None

    if nci_context:
        priority = nci_context.get("priority") or {}
        if isinstance(priority, dict):
            priority_txt = ", ".join(f"{k}: {v}" for k, v in priority.items() if v is not None)
        else:
            priority_txt = str(priority) if priority is not None else "—"
        remaining = ((nci_context.get("population") or {}).get("remaining"))
        summary = (
            f"{summary} Contexte besoins NCI: NDCI={nci_context.get('ndci')}, "
            f"population restante={remaining}, "
            f"priorités={priority_txt}."
        )

    shell = _build_case_shell(
        case_id=case_id,
        asset={
            "asset_type": "SITE",
            "id": site.get("site_id") or sid,
            "site_id": site.get("site_id") or sid,
            "business_id": site.get("site_code"),
            "site_code": site.get("site_code"),
            "name": display_name,
            "site_name": display_name,
            "province": site.get("province"),
            "territoire": site.get("territoire"),
            "program_code": site.get("program_code"),
            "zone": site.get("zone"),
            "latitude": site.get("latitude"),
            "longitude": site.get("longitude"),
            "priority_score": score,
            "priority_level": level,
            "priority_level_label": label,
        },
        score=score,
        priority_level=level,
        priority_label=label,
        doctrine=doctrine,
        matrix=matrix,
        criteria=criteria_out,
        justification=justification,
        data_used={
            "source": f"programme {site.get('program_code')}",
            "resolver": "site_entity_resolver",
            "fields": {
                "population": site.get("population"),
                "distance": site.get("distance"),
                "distance_level": site.get("distance_level"),
                "is_300_planned": site.get("is_300_planned"),
                "province": site.get("province"),
                "territoire": site.get("territoire"),
            },
            "knowledge_hub_domain": "business_doctrine",
            "referentiel": "Référentiel National / programmes FDSU",
            "needs_referentiel": "Référentiel National des Besoins (NCI)",
            "nci": nci_context,
        },
        indicators={"measurement": meas, "nif": kh_indicators},
        impacts=impacts,
        risks=risks,
        assumptions=[
            "Les seuils de priorité sont lus depuis la matrice de priorisation des sites FDSU.",
            "Les pondérations Sites sont lues depuis la doctrine Sites v1.",
            "Les indicateurs NIF restent structure_only tant que non sourcés.",
            "Le contexte NCI (population/priorité/distance/catégorie/infra) complète doctrine et matrice.",
        ],
        sources=[
            doctrine_meta.get("source_document") or "Doctrine Sites FDSU",
            "Matrice de priorisation des sites FDSU",
            "Indicateurs nationaux (Knowledge Hub)",
            "Agrégats de couverture nationale (NCI)",
            "API Couverture nationale",
        ],
        confidence=confidence,
        summary=summary,
    )
    if nci_context:
        shell["needs_intelligence"] = {
            "why": nci_context.get("why"),
            "population": nci_context.get("population"),
            "priority": nci_context.get("priority"),
            "distance_km_avg": nci_context.get("distance_km_avg"),
            "categories": nci_context.get("categories"),
            "infrastructure": nci_context.get("infrastructure"),
            "ndci": nci_context.get("ndci"),
            "doctrine": "DOCTRINE_SITES_FDSU + priority_matrix",
            "confidence_level": nci_context.get("confidence_level"),
        }

    # Preuves spatiales P1 — signaux disponibles, non inventés, scoring inchangé
    shell["telecom_context"] = _build_telecom_case_context(site)
    shell["education_context"] = _build_education_case_context(site)
    shell["ceni_context"] = _build_ceni_case_context(site)
    shell["spatial_evidence"] = {
        "telecom": shell["telecom_context"],
        "education": shell["education_context"],
        "ceni": shell["ceni_context"],
        "health_note": "Santé via NSME NEAREST/NEAR_HEALTH_FACILITY (PostGIS)",
        "scoring_note": (
            "Signaux éducation / CENI / télécom exposés comme preuves. "
            "Critères sectoriels moteur à poids 0 restent non pondérés."
        ),
    }
    if shell["telecom_context"].get("available"):
        shell.setdefault("sources", []).append("Contexte télécom spatial (/api/telecom/spatial-context)")
    if shell["education_context"].get("available"):
        shell.setdefault("sources", []).append("Projection Éducation CENI SCHOOL")
    if shell["ceni_context"].get("available"):
        shell.setdefault("sources", []).append("Signal institutionnel CENI (≠ site FDSU)")

    edu_n = shell["education_context"].get("nearby_count")
    if edu_n is not None and isinstance(shell.get("impacts"), dict):
        shell["impacts"]["ecoles_concernees"] = edu_n
    return shell


def _fmt_km(distance_m: Any) -> str | None:
    from api.services.spatial_nearest_utils import format_km

    return format_km(distance_m if distance_m is not None else None)


def _build_telecom_case_context(site: dict[str, Any]) -> dict[str, Any]:
    lat, lon = site.get("latitude"), site.get("longitude")
    if lat is None or lon is None:
        return {"available": False, "reason": "Coordonnées site absentes"}
    try:
        from api.services import telecom_service

        ctx = telecom_service.spatial_context_around(float(lat), float(lon), radius_m=25_000) or {}
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "reason": str(exc)}

    def _hit(key: str) -> dict[str, Any] | None:
        row = ctx.get(key)
        if not row:
            return None
        return {
            "label": row.get("site_name") or row.get("infra_name") or row.get("line_name") or key,
            "operator_code": row.get("operator_code"),
            "distance_m": row.get("distance_m"),
            "distance_display": _fmt_km(row.get("distance_m")),
            "data_source": row.get("data_source"),
            "nire_quality_status": row.get("nire_quality_status"),
        }

    operators = {
        "vodacom": _hit("NEAREST_MNO_VODACOM"),
        "orange": _hit("NEAREST_MNO_ORANGE"),
        "airtel": _hit("NEAREST_MNO_AIRTEL"),
        "africell": _hit("NEAREST_MNO_AFRICELL"),
    }
    fiber = _hit("NEAREST_FIBER_LINK")
    mw = _hit("NEAREST_MICROWAVE_LINK")
    multi = list(ctx.get("MULTI_OPERATOR_PROXIMITY") or [])
    backhaul = bool(ctx.get("BACKHAUL_CANDIDATE"))
    mutual = bool(ctx.get("MUTUALIZATION_POTENTIAL"))
    colocation = bool(ctx.get("COLOCATION_SIGNAL"))

    summary_parts = []
    if fiber and fiber.get("distance_display"):
        summary_parts.append(f"Fibre la plus proche : {fiber['distance_display']}")
    if mw and mw.get("distance_display"):
        summary_parts.append(f"MW le plus proche : {mw['distance_display']}")
    for code, hit in operators.items():
        if hit and hit.get("distance_display"):
            summary_parts.append(f"{code.capitalize()} : {hit['distance_display']}")
    if mutual:
        summary_parts.append("Potentiel de mutualisation : Oui")
    if backhaul:
        mode = "Fibre" if fiber else ("MW" if mw else "Oui")
        summary_parts.append(f"Backhaul possible : {mode}")

    return {
        "available": bool(ctx.get("search_executed")),
        "search_executed": bool(ctx.get("search_executed")),
        "operators": operators,
        "operators_nearby": multi,
        "fiber": fiber,
        "microwave": mw,
        "distance_to_fiber_m": ctx.get("DISTANCE_TO_FIBER_M"),
        "distance_to_fiber_display": _fmt_km(ctx.get("DISTANCE_TO_FIBER_M")),
        "backhaul_candidate": backhaul,
        "mutualization_potential": mutual,
        "colocation_signal": colocation,
        "summary_lines": summary_parts,
        "scoring_weighted": False,
        "source": "telecom.spatial_context",
    }


def _build_education_case_context(site: dict[str, Any]) -> dict[str, Any]:
    lat, lon = site.get("latitude"), site.get("longitude")
    if lat is None or lon is None:
        return {"available": False, "reason": "Coordonnées site absentes"}
    try:
        from api.services import education_referential_service as edu

        payload = edu.nearest_establishment(float(lat), float(lon), radius_m=25_000, limit=10)
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "reason": str(exc)}
    nearest = payload.get("nearest")
    nearby = list(payload.get("establishments") or [])
    return {
        "available": bool(payload.get("data_available")),
        "search_executed": bool(payload.get("search_executed")),
        "nearby_count": len(nearby),
        "nearest": (
            {
                "name": (nearest or {}).get("normalized_name") or (nearest or {}).get("original_name"),
                "subtype": (nearest or {}).get("education_subtype"),
                "distance_m": (nearest or {}).get("distance_m"),
                "distance_display": _fmt_km((nearest or {}).get("distance_m")),
                "province": (nearest or {}).get("province"),
            }
            if nearest
            else None
        ),
        "derived_projection": True,
        "official_ministry_registry": False,
        "scoring_weighted": False,
        "note": "Signal éducatif disponible — critère moteur education poids 0",
        "source": "CENI SCHOOL projection",
    }


def _build_ceni_case_context(site: dict[str, Any]) -> dict[str, Any]:
    lat, lon = site.get("latitude"), site.get("longitude")
    if lat is None or lon is None:
        return {"available": False, "reason": "Coordonnées site absentes"}
    try:
        from api.services import ceni_registry_service as ceni

        payload = ceni.nearest_signals(
            float(lat), float(lon), radius_m=15_000, limit=10, exclude_schools=True
        )
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "reason": str(exc)}
    nearest = payload.get("nearest")
    nearby = list(payload.get("sites") or [])
    return {
        "available": bool(payload.get("data_available")),
        "search_executed": bool(payload.get("search_executed")),
        "nearby_count": len(nearby),
        "nearest": (
            {
                "name": (nearest or {}).get("name"),
                "category": (nearest or {}).get("normalized_category"),
                "distance_m": (nearest or {}).get("distance_m"),
                "distance_display": _fmt_km((nearest or {}).get("distance_m")),
                "asset_uid": (nearest or {}).get("asset_uid"),
            }
            if nearest
            else None
        ),
        "not_fdsu_sites": True,
        "scoring_weighted": False,
        "note": "Signal disponible — non pondéré dans le scoring actuel",
        "signal_role": "administrative_centrality",
        "source": "CENI registry",
    }


def get_decision_case(asset_id: str, *, asset_type: str | None = None, program_code: str | None = None) -> dict[str, Any] | None:
    kind, value = _parse_asset_ref(asset_id, asset_type)
    if kind == "ccn":
        return build_ccn_case(value)
    return build_site_case(value, program_code=program_code)


def explain_decision(asset_id: str, *, asset_type: str | None = None, program_code: str | None = None) -> dict[str, Any] | None:
    case = get_decision_case(asset_id, asset_type=asset_type, program_code=program_code)
    if not case:
        return None
    return {
        "_meta": {
            "title": "Justification détaillée",
            "case_id": case["case_id"],
            "principle": "Aucune recommandation sans justification.",
            "engine_version": case["engine_version"],
        },
        "summary": case["summary"],
        "asset": case["asset"],
        "score": case["score"],
        "doctrine": case["doctrine"],
        "matrix": {
            "id": case["matrix"].get("id"),
            "ref": case["matrix"].get("ref"),
        },
        "justification": case["justification"],
        "confidence": case["confidence"],
        "needs_intelligence": case.get("needs_intelligence"),
        "risks": case["risks"],
        "impacts": case["impacts"],
        "sources": case.get("sources"),
        "case_ref": f"#decision-case/site/{case['case_id']}",
    }


def get_doctrine_payload(doctrine_id: str) -> dict[str, Any] | None:
    bundle = load_doctrine_by_id(doctrine_id)
    if not bundle:
        return None
    return {
        "_meta": {
            "title": "Doctrine métier FDSU",
            "hardcoded_forbidden": True,
            "engine": (engine_meta().get("_meta") or {}).get("engine_id"),
        },
        **bundle,
        "pdf_template": {
            "enabled": False,
            "path": "data/decision/pdf_templates/decision_case_file_v1.json",
        },
    }
