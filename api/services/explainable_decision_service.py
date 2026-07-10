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
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


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
    payload = _load_json(HISTORY_PATH)
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


def get_case_history(case_id: str | None = None, limit: int = 50) -> dict[str, Any]:
    payload = _load_json(HISTORY_PATH)
    history = list(payload.get("history") or [])
    if case_id:
        history = [h for h in history if h.get("case_id") == case_id or h.get("asset_id") == case_id]
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
            "id": (doctrine.get("priority_matrix") or {}).get("id") or (matrix.get("_meta") or {}).get("title"),
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
    from api.services import fdsu_site_priority_service, knowledge_hub_service

    doctrine_bundle = load_doctrine_by_id("DOCTRINE_SITES_FDSU")
    if not doctrine_bundle or doctrine_bundle.get("planned"):
        return None
    doctrine = doctrine_bundle["doctrine"]
    matrix = doctrine_bundle.get("matrix") or _load_json(MATRIX_PATH)
    doctrine_meta = doctrine.get("_meta") or {}

    try:
        sid = int(re.sub(r"[^\d]", "", str(site_id)) or site_id)
    except ValueError:
        return None

    explained = fdsu_site_priority_service.explain_site(sid, program_code=program_code)
    if not explained:
        return None
    site = explained.get("site") or {}
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
    summary = (
        f"Recommandation Site « {site.get('site_name') or site.get('site_code')} » — "
        f"score {score}/100 ({label}). Doctrine {doctrine_meta.get('title')} v{doctrine_meta.get('version')}."
    )
    case_id = f"DCF-SITE-{site.get('site_id') or sid}"
    return _build_case_shell(
        case_id=case_id,
        asset={
            "asset_type": "SITE",
            "id": site.get("site_id"),
            "business_id": site.get("site_code"),
            "name": site.get("site_name"),
            "province": site.get("province"),
            "territoire": site.get("territoire"),
            "program_code": site.get("program_code"),
            "zone": site.get("zone"),
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
        },
        indicators={"measurement": meas, "nif": kh_indicators},
        impacts=impacts,
        risks=risks,
        assumptions=[
            "Les seuils de priorité sont lus depuis priority_matrix.json.",
            "Les pondérations Sites sont lues depuis la doctrine Sites v1.",
            "Les indicateurs NIF restent structure_only tant que non sourcés.",
        ],
        sources=[
            doctrine_meta.get("source_document"),
            "data/business/doctrines/sites_doctrine_v1.json",
            "data/business/priority_matrix.json",
            "data/knowledge/national_indicators.json",
        ],
        confidence=confidence,
        summary=summary,
    )


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
        "risks": case["risks"],
        "impacts": case["impacts"],
        "case_ref": f"/api/decision/case/{case['case_id']}",
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
