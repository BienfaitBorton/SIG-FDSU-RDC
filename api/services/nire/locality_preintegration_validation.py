"""Validation d'identité pré-intégration (lecture seule).

Requalifie les candidates HIGH_CONFIDENCE et les homonymes avant toute intégration.
La distance à une autre localité n'est ni une preuve de nouveauté ni un motif de rejet.
"""

from __future__ import annotations

import json
import re
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any

from api.services.nire import locality_coverage as lc
from api.services.nire import locality_enrichment_audit as lea

ENGINE_VERSION = "nire-locality-preintegration-1.0.0"
CACHE_PATH = lc.ROOT / "data" / "cache" / "nire_locality_preintegration_v1.json"

FINAL_CLASSES = (
    "READY_FOR_INTEGRATION",
    "REQUIRES_HUMAN_REVIEW",
    "EXISTING_LOCALITY_VARIANT",
    "DUPLICATE_NCI_OBSERVATION",
    "HOMONYM_DISTINCT_CONFIRMED",
)

HOMONYM_CLASSES = (
    "HOMONYM_ALREADY_IN_REFERENTIAL",
    "HOMONYM_NEW_LOCALITY_READY",
    "HOMONYM_REQUIRES_REVIEW",
)

THRESHOLDS = {
    "deep_variant_ratio": 0.90,
    "bbox_padding_deg": 0.30,
    "min_territory_admin_for_bbox": 3,
    "min_name_len": 3,
}

_SUFFIXES = (
    "village",
    "cite",
    "camp",
    "localite",
    "quartier",
    "groupement",
    "mission",
    "centre",
    "ext",
    "new",
    "site",
)


@dataclass
class PreintegrationState:
    executed: bool = False
    message: str = ""
    meta: dict[str, Any] = field(default_factory=dict)
    kpis: dict[str, Any] = field(default_factory=dict)
    rows: list[dict[str, Any]] = field(default_factory=list)
    homonym_rows: list[dict[str, Any]] = field(default_factory=list)
    integration_plan: dict[str, Any] = field(default_factory=dict)
    simulation: dict[str, Any] = field(default_factory=dict)
    propagation: dict[str, Any] = field(default_factory=dict)
    performance: dict[str, Any] = field(default_factory=dict)


_STATE = PreintegrationState()


def get_state() -> PreintegrationState:
    return _STATE


def reset_state() -> None:
    global _STATE
    _STATE = PreintegrationState()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def advanced_normalize(name: str | None) -> str:
    """Normalisation avancée pour variantes orthographiques / suffixes source."""
    base = lc._norm(name)
    if not base:
        return ""
    # Retirer codes techniques type part2_23453_...
    base = re.sub(r"\bpart\d+\b", " ", base)
    base = re.sub(r"\b\d{4,}\b", " ", base)
    tokens = [t for t in base.split() if t and t not in _SUFFIXES]
    compact = " ".join(tokens).strip()
    # Forme compacte sans espaces (comparaison secondaire)
    return compact


def advanced_compact(name: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", advanced_normalize(name))


def _name_ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _is_technical_toponym(toponym: str) -> bool:
    n = (toponym or "").strip()
    if not n:
        return True
    if n.count("_") >= 2:
        return True
    if re.fullmatch(r"[0-9_\-]+", n):
        return True
    letters = sum(1 for c in n if c.isalpha())
    return letters < 3


def _bbox(points: list[tuple[float, float]], pad: float) -> tuple[float, float, float, float] | None:
    if not points:
        return None
    lats = [p[0] for p in points]
    lons = [p[1] for p in points]
    return (min(lats) - pad, max(lats) + pad, min(lons) - pad, max(lons) + pad)


def _in_bbox(lat: float, lon: float, bbox: tuple[float, float, float, float] | None) -> bool:
    if not bbox:
        return False
    min_lat, max_lat, min_lon, max_lon = bbox
    return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon


def _build_admin_indexes(admin: list[dict[str, Any]]) -> dict[str, Any]:
    by_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_adv: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_prov_terr: dict[str, list[dict[str, Any]]] = defaultdict(list)
    prov_pts: dict[str, list[tuple[float, float]]] = defaultdict(list)
    terr_pts: dict[str, list[tuple[float, float]]] = defaultdict(list)

    for a in admin:
        nk = lc._norm(a.get("nom"))
        adv = advanced_normalize(a.get("nom"))
        prov = lc._norm(a.get("province"))
        terr = lc._norm(a.get("territoire"))
        if nk:
            by_name[nk].append(a)
        if adv:
            by_adv[adv].append(a)
            by_adv[advanced_compact(a.get("nom"))].append(a)
        if prov and terr:
            by_prov_terr[f"{prov}|{terr}"].append(a)
        try:
            lat, lon = float(a["latitude"]), float(a["longitude"])
        except (TypeError, ValueError, KeyError):
            continue
        if prov:
            prov_pts[prov].append((lat, lon))
        if prov and terr:
            terr_pts[f"{prov}|{terr}"].append((lat, lon))

    pad = THRESHOLDS["bbox_padding_deg"]
    return {
        "by_name": by_name,
        "by_adv": by_adv,
        "by_prov_terr": by_prov_terr,
        "province_bboxes": {k: _bbox(v, pad) for k, v in prov_pts.items()},
        "territory_bboxes": {
            k: _bbox(v, pad)
            for k, v in terr_pts.items()
            if len(v) >= THRESHOLDS["min_territory_admin_for_bbox"]
        },
        "territory_point_counts": {k: len(v) for k, v in terr_pts.items()},
    }


def find_deep_variant(
    obs: dict[str, Any],
    indexes: dict[str, Any],
) -> tuple[dict[str, Any] | None, list[str], float]:
    """Variante existante dans le MÊME contexte province+territoire (pas fusion nom seul)."""
    toponym = obs.get("toponym") or lc._nci_toponym(obs)
    nkey = lc._norm(toponym)
    adv = advanced_normalize(toponym)
    compact = advanced_compact(toponym)
    prov = lc._norm(obs.get("province"))
    terr = lc._norm(obs.get("territoire"))
    if not nkey or not prov or not terr:
        return None, [], 0.0

    pool = list(indexes["by_prov_terr"].get(f"{prov}|{terr}") or [])
    best = None
    best_score = 0.0
    best_proofs: list[str] = []

    for a in pool:
        akey = lc._norm(a.get("nom"))
        a_adv = advanced_normalize(a.get("nom"))
        a_compact = advanced_compact(a.get("nom"))
        proofs: list[str] = ["SAME_PROVINCE", "SAME_TERRITORY"]
        score = 0.0
        if akey == nkey or a_adv == adv or (compact and compact == a_compact):
            score = 1.0
            proofs.append("ADVANCED_NAME_EXACT")
        else:
            ratio = max(_name_ratio(nkey, akey), _name_ratio(adv, a_adv), _name_ratio(compact, a_compact))
            if ratio >= THRESHOLDS["deep_variant_ratio"]:
                score = ratio
                proofs.append("ADVANCED_NAME_FUZZY")
            elif adv and a_adv and (adv in a_adv or a_adv in adv) and min(len(adv), len(a_adv)) >= 4:
                score = 0.92
                proofs.append("ADVANCED_NAME_PARTIAL")
        if score > best_score:
            best_score = score
            best = a
            best_proofs = proofs

    if best and best_score >= THRESHOLDS["deep_variant_ratio"]:
        return best, best_proofs, best_score
    return None, [], 0.0


def territorial_coherence(
    obs: dict[str, Any],
    indexes: dict[str, Any],
    *,
    require_territory_bbox: bool = False,
) -> tuple[bool, list[str]]:
    """Cohérence avec limites admin disponibles — pas de règle de distance inter-localités."""
    proofs: list[str] = []
    prov = lc._norm(obs.get("province"))
    terr = lc._norm(obs.get("territoire"))
    try:
        lat, lon = float(obs["latitude"]), float(obs["longitude"])
    except (TypeError, ValueError, KeyError):
        return False, ["INVALID_COORDINATES"]

    if not lea._valid_coords(obs):
        return False, ["INVALID_COORDINATES"]

    prov_bbox = indexes["province_bboxes"].get(prov)
    if prov_bbox and _in_bbox(lat, lon, prov_bbox):
        proofs.append("GEOMETRY_IN_PROVINCE_BBOX")
    elif prov_bbox:
        proofs.append("GEOMETRY_OUTSIDE_PROVINCE_BBOX")
        return False, proofs
    else:
        proofs.append("PROVINCE_BBOX_UNAVAILABLE")
        if require_territory_bbox:
            return False, proofs

    terr_key = f"{prov}|{terr}"
    terr_bbox = indexes["territory_bboxes"].get(terr_key)
    if terr_bbox:
        if _in_bbox(lat, lon, terr_bbox):
            proofs.append("GEOMETRY_IN_TERRITORY_BBOX")
        else:
            proofs.append("GEOMETRY_OUTSIDE_TERRITORY_BBOX")
            return False, proofs
    else:
        proofs.append("TERRITORY_BBOX_UNAVAILABLE_OR_SPARSE")
        if require_territory_bbox:
            return False, proofs

    return True, proofs


def classify_ready_candidate(
    obs: dict[str, Any],
    *,
    is_duplicate_extra: bool,
    indexes: dict[str, Any],
) -> dict[str, Any]:
    """Requalification d'une ancienne HIGH_CONFIDENCE (identité territoriale)."""
    if is_duplicate_extra:
        return {
            "final_class": "DUPLICATE_NCI_OBSERVATION",
            "confidence": "high",
            "score": 1.0,
            "proofs": ["SAME_CANONICAL_IDENTITY_MULTIPLE_OBSERVATIONS"],
            "reason": "duplicate_nci_observation",
            "candidate_admin_id": None,
            "candidate_admin_name": None,
        }

    toponym = obs.get("toponym") or lc._nci_toponym(obs)
    nkey = lc._norm(toponym)
    prov = lc._norm(obs.get("province"))
    terr = lc._norm(obs.get("territoire"))
    proofs: list[str] = []

    if not lea._exploitable_name(toponym) or len(nkey) < THRESHOLDS["min_name_len"]:
        return {
            "final_class": "REQUIRES_HUMAN_REVIEW",
            "confidence": "low",
            "score": 0.2,
            "proofs": ["NAME_NOT_EXPLOITABLE"],
            "reason": "insufficient_name",
            "candidate_admin_id": None,
            "candidate_admin_name": None,
        }

    if _is_technical_toponym(toponym):
        return {
            "final_class": "REQUIRES_HUMAN_REVIEW",
            "confidence": "low",
            "score": 0.25,
            "proofs": ["TECHNICAL_OR_CODE_LIKE_TOPONYM"],
            "reason": "technical_toponym",
            "candidate_admin_id": None,
            "candidate_admin_name": None,
        }

    variant, v_proofs, v_score = find_deep_variant(obs, indexes)
    if variant:
        return {
            "final_class": "EXISTING_LOCALITY_VARIANT",
            "confidence": "high",
            "score": round(v_score, 4),
            "proofs": v_proofs,
            "reason": "advanced_normalization_match_same_context",
            "candidate_admin_id": variant.get("admin_id"),
            "candidate_admin_name": variant.get("nom"),
        }

    # Homonyme exact ailleurs (pas dans ce contexte) — identité distincte possible
    same_elsewhere = []
    for a in indexes["by_name"].get(nkey) or []:
        a_prov = lc._norm(a.get("province"))
        a_terr = lc._norm(a.get("territoire"))
        if a_prov == prov and a_terr == terr:
            continue
        same_elsewhere.append(a)

    if not lea._valid_coords(obs) or not prov or not terr:
        return {
            "final_class": "REQUIRES_HUMAN_REVIEW",
            "confidence": "low",
            "score": 0.3,
            "proofs": ["MISSING_TERRITORIAL_FIELDS"],
            "reason": "insufficient_territorial_identity",
            "candidate_admin_id": None,
            "candidate_admin_name": None,
        }

    # READY exige bbox territoire (identité territoriale forte) — pas la distance à une localité
    geo_ok, geo_proofs = territorial_coherence(obs, indexes, require_territory_bbox=True)
    proofs.extend(geo_proofs)
    proofs.extend(["EXPLOITABLE_NAME", "VALID_COORDINATES", "PROVINCE_IDENTIFIED", "TERRITORY_IDENTIFIED"])
    proofs.append("NO_ADVANCED_VARIANT_SAME_CONTEXT")
    proofs.append("DISTANCE_NOT_USED_AS_IDENTITY_RULE")

    collectivite = obs.get("collectivite") or obs.get("collectivité")
    groupement = obs.get("groupement")
    if collectivite:
        proofs.append("COLLECTIVITE_PRESENT")
    if groupement:
        proofs.append("GROUPEMENT_PRESENT")

    if same_elsewhere:
        if geo_ok:
            return {
                "final_class": "HOMONYM_DISTINCT_CONFIRMED",
                "confidence": "high",
                "score": 0.8,
                "proofs": proofs + ["HOMONYM_NAME_ELSEWHERE", "DISTINCT_TERRITORIAL_CONTEXT"],
                "reason": "homonym_distinct_territorial_identity",
                "candidate_admin_id": same_elsewhere[0].get("admin_id"),
                "candidate_admin_name": same_elsewhere[0].get("nom"),
            }
        return {
            "final_class": "REQUIRES_HUMAN_REVIEW",
            "confidence": "medium",
            "score": 0.5,
            "proofs": proofs + ["HOMONYM_NAME_ELSEWHERE", "GEO_CONTEXT_WEAK"],
            "reason": "homonym_needs_review",
            "candidate_admin_id": same_elsewhere[0].get("admin_id"),
            "candidate_admin_name": same_elsewhere[0].get("nom"),
        }

    if geo_ok:
        return {
            "final_class": "READY_FOR_INTEGRATION",
            "confidence": "high",
            "score": 0.88,
            "proofs": proofs + ["TERRITORIAL_IDENTITY_STRONG"],
            "reason": "ready_territorial_identity",
            "candidate_admin_id": None,
            "candidate_admin_name": None,
        }

    return {
        "final_class": "REQUIRES_HUMAN_REVIEW",
        "confidence": "medium",
        "score": 0.55,
        "proofs": proofs + ["GEO_ADMIN_COHERENCE_WEAK"],
        "reason": "plausible_but_insufficient_context",
        "candidate_admin_id": None,
        "candidate_admin_name": None,
    }


def classify_homonym(
    obs: dict[str, Any],
    *,
    indexes: dict[str, Any],
) -> dict[str, Any]:
    """Sous-classification des HOMONYM_DIFFERENT_LOCALITY."""
    toponym = obs.get("toponym") or lc._nci_toponym(obs)
    nkey = lc._norm(toponym)
    prov = lc._norm(obs.get("province"))
    terr = lc._norm(obs.get("territoire"))

    # Déjà dans le référentiel au même contexte ?
    same_context = [
        a
        for a in indexes["by_name"].get(nkey) or []
        if lc._norm(a.get("province")) == prov and lc._norm(a.get("territoire")) == terr
    ]
    if same_context:
        return {
            "homonym_class": "HOMONYM_ALREADY_IN_REFERENTIAL",
            "confidence": "high",
            "score": 1.0,
            "proofs": ["EXACT_NAME_SAME_PROVINCE_TERRITORY"],
            "reason": "already_in_referential_same_context",
            "candidate_admin_id": same_context[0].get("admin_id"),
            "candidate_admin_name": same_context[0].get("nom"),
        }

    variant, v_proofs, v_score = find_deep_variant(obs, indexes)
    if variant:
        return {
            "homonym_class": "HOMONYM_ALREADY_IN_REFERENTIAL",
            "confidence": "high",
            "score": round(v_score, 4),
            "proofs": v_proofs + ["ADVANCED_VARIANT_SAME_CONTEXT"],
            "reason": "variant_of_existing_in_same_context",
            "candidate_admin_id": variant.get("admin_id"),
            "candidate_admin_name": variant.get("nom"),
        }

    geo_ok, geo_proofs = territorial_coherence(obs, indexes, require_territory_bbox=True)
    proofs = geo_proofs + ["HOMONYM_NAME_EXISTS_ELSEWHERE", "DISTANCE_NOT_USED_AS_IDENTITY_RULE"]

    if (
        lea._exploitable_name(toponym)
        and not _is_technical_toponym(toponym)
        and lea._valid_coords(obs)
        and prov
        and terr
        and geo_ok
    ):
        return {
            "homonym_class": "HOMONYM_NEW_LOCALITY_READY",
            "confidence": "high",
            "score": 0.82,
            "proofs": proofs + ["DISTINCT_TERRITORIAL_IDENTITY", "ABSENT_SAME_CONTEXT"],
            "reason": "homonym_is_new_locality_in_this_context",
            "candidate_admin_id": None,
            "candidate_admin_name": None,
        }

    return {
        "homonym_class": "HOMONYM_REQUIRES_REVIEW",
        "confidence": "medium",
        "score": 0.5,
        "proofs": proofs + ["INSUFFICIENT_OR_AMBIGUOUS_CONTEXT"],
        "reason": "homonym_needs_human_review",
        "candidate_admin_id": None,
        "candidate_admin_name": None,
    }


def build_integration_record(obs: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    return {
        "canonical_id": lea.future_canonical_id(obs),
        "nom_canonique": obs.get("toponym") or lc._nci_toponym(obs),
        "nom_source": obs.get("nci_destination") or obs.get("destination") or obs.get("toponym"),
        "nom_normalise": lc._norm(obs.get("toponym")),
        "nom_normalise_avance": advanced_normalize(obs.get("toponym")),
        "latitude": obs.get("latitude"),
        "longitude": obs.get("longitude"),
        "province": obs.get("province"),
        "territoire": obs.get("territoire"),
        "collectivite": obs.get("collectivite"),
        "groupement": obs.get("groupement"),
        "source": "nci_fdsu",
        "source_observation_ids": obs.get("observation_ids") or [obs.get("nci_id")],
        "coverage_statuses": obs.get("coverage_statuses") or [obs.get("coverage_status")],
        "nire_classification": decision.get("final_class") or decision.get("homonym_class"),
        "score": decision.get("score"),
        "confidence": decision.get("confidence"),
        "proofs": decision.get("proofs"),
        "integration_date": None,
        "applied": False,
        "idempotency_key": lea.future_canonical_id(obs),
    }


def describe_propagation() -> dict[str, Any]:
    return {
        "mode": "post_validation_idempotent",
        "steps": [
            "1. Intégrer READY (+ HOMONYM_NEW_LOCALITY_READY validés) dans Master Registry / référentiel national",
            "2. Attacher hiérarchie administrative (province → territoire → collectivité/groupement)",
            "3. Exposer points Smart Map (couche localités enrichies)",
            "4. NIRE : statut matched / pending → canonical_id stable",
            "5. NSME / SDG : relations sites↔localités sans rescoring automatique",
            "6. Intelligence Territoriale / couverture-population : rattacher observations NCI à l'identité",
            "7. Centre de Décision : consommer localités enrichies sans inventer de scores",
        ],
        "invariants": [
            "idempotency_key empêche la double création",
            "observations covered/uncovered restent liées, jamais fusionnées en identité",
            "aucune propagation avant validation humaine du lot READY",
        ],
    }


def run_preintegration_validation(
    *,
    enrichment_rows: list[dict[str, Any]] | None = None,
    coverage_rows: list[dict[str, Any]] | None = None,
    admin_rows: list[dict[str, Any]] | None = None,
    run_upstream_if_needed: bool = True,
    write_cache: bool = False,
) -> PreintegrationState:
    started = time.time()
    admin = admin_rows if admin_rows is not None else lc._load_admin_localities()
    indexes = _build_admin_indexes(admin)

    if enrichment_rows is None:
        if run_upstream_if_needed:
            if lea.get_state().executed and lea.get_state().rows:
                enrichment_rows = lea.get_state().rows
            else:
                en = lea.run_enrichment_audit(
                    coverage_rows=coverage_rows,
                    admin_rows=admin,
                    run_coverage_if_needed=coverage_rows is None,
                    write_cache=False,
                )
                enrichment_rows = en.rows
        else:
            enrichment_rows = []

    hc_rows = [
        r
        for r in enrichment_rows
        if r.get("enrichment_class") == "NEW_LOCALITY_CANDIDATE_HIGH_CONFIDENCE"
    ]
    homonym_rows_in = [
        r
        for r in enrichment_rows
        if r.get("enrichment_class") == "HOMONYM_DIFFERENT_LOCALITY"
        and r.get("is_canonical_representative", True)
    ]

    # Grouper HC par identity_key
    hc_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in hc_rows:
        hc_groups[r.get("identity_key") or lea.identity_key(r)].append(r)

    final_rows: list[dict[str, Any]] = []
    final_counts: Counter[str] = Counter()
    ready_records: list[dict[str, Any]] = []
    pop_ready = 0
    pop_review = 0

    for ident, rows in hc_groups.items():
        rows_sorted = sorted(
            rows,
            key=lambda x: (0 if x.get("is_canonical_representative") else 1, str(x.get("nci_id"))),
        )
        has_rep = any(r.get("is_canonical_representative") for r in rows_sorted)
        for idx, obs in enumerate(rows_sorted):
            if has_rep:
                is_extra = not bool(obs.get("is_canonical_representative"))
            else:
                is_extra = idx > 0

            decision = classify_ready_candidate(obs, is_duplicate_extra=is_extra, indexes=indexes)
            record = {
                **{k: obs.get(k) for k in (
                    "nci_id", "identity_key", "toponym", "province", "territoire",
                    "latitude", "longitude", "population", "coverage_statuses",
                    "observation_ids", "dual_source_observation", "enrichment_class",
                    "nci_destination", "destination", "collectivite", "groupement",
                    "coverage_status",
                )},
                "is_canonical_representative": not is_extra,
                "final_class": decision["final_class"],
                "confidence": decision["confidence"],
                "score": decision["score"],
                "proofs": decision["proofs"],
                "reason": decision["reason"],
                "candidate_admin_id": decision["candidate_admin_id"],
                "candidate_admin_name": decision["candidate_admin_name"],
                "auto_created": False,
                "referential_modified": False,
            }
            final_rows.append(record)

    final_counts = Counter()
    pop_ready = 0
    pop_review = 0
    for r in final_rows:
        if r["final_class"] == "DUPLICATE_NCI_OBSERVATION":
            final_counts["DUPLICATE_NCI_OBSERVATION"] += 1
        elif r.get("is_canonical_representative"):
            final_counts[r["final_class"]] += 1
            try:
                pop = int(r.get("population") or 0)
            except (TypeError, ValueError):
                pop = 0
            if r["final_class"] in {"READY_FOR_INTEGRATION", "HOMONYM_DISTINCT_CONFIRMED"}:
                pop_ready += pop
            elif r["final_class"] == "REQUIRES_HUMAN_REVIEW":
                pop_review += pop

    # Homonymes
    homonym_out: list[dict[str, Any]] = []
    homonym_counts: Counter[str] = Counter()
    for obs in homonym_rows_in:
        decision = classify_homonym(obs, indexes=indexes)
        hc = decision["homonym_class"]
        homonym_counts[hc] += 1
        row = {
            **{k: obs.get(k) for k in (
                "nci_id", "identity_key", "toponym", "province", "territoire",
                "latitude", "longitude", "population", "enrichment_class",
            )},
            "homonym_class": hc,
            "confidence": decision["confidence"],
            "score": decision["score"],
            "proofs": decision["proofs"],
            "reason": decision["reason"],
            "candidate_admin_id": decision["candidate_admin_id"],
            "candidate_admin_name": decision["candidate_admin_name"],
            "auto_created": False,
        }
        homonym_out.append(row)
        if hc == "HOMONYM_NEW_LOCALITY_READY":
            try:
                pop_ready += int(obs.get("population") or 0)
            except (TypeError, ValueError):
                pass

    ready_n = final_counts.get("READY_FOR_INTEGRATION", 0)
    homonym_ready_n = homonym_counts.get("HOMONYM_NEW_LOCALITY_READY", 0)
    # READY_FOR_INTEGRATION final pour plan = READY + homonymes new ready (proposition contrôlée)
    ready_for_integration_total = ready_n  # strict: seules ex-HC requalifiées READY
    # Option documentée : homonymes ready séparés, non auto-fusionnés dans X sans validation

    for r in final_rows:
        if r.get("is_canonical_representative") and r.get("final_class") == "READY_FOR_INTEGRATION":
            ready_records.append(build_integration_record(r, {"final_class": r["final_class"], **r}))

    # Simulation
    current_localities = len(admin)
    projected = current_localities + ready_for_integration_total
    # Match rate: current matched from enrichment upstream coverage if available
    cov_state = lc.get_state()
    nci_obs = int((cov_state.kpis or {}).get("nci_observations") or 0)
    match_now = float((cov_state.kpis or {}).get("match_rate_confident_or_probable") or 0.1289)
    matched_now = int(round(match_now * nci_obs)) if nci_obs else 0

    # Observations rattachables = toutes obs des identités READY
    ready_keys = {
        r["identity_key"]
        for r in final_rows
        if r.get("is_canonical_representative") and r.get("final_class") == "READY_FOR_INTEGRATION"
    }
    ready_obs = [r for r in final_rows if r.get("identity_key") in ready_keys]
    # Aussi compter depuis enrichment toutes obs de ces identités
    en_ready_obs = [r for r in enrichment_rows if r.get("identity_key") in ready_keys]
    attachable_obs = len(en_ready_obs) if en_ready_obs else len(ready_obs)

    covered_attachable = sum(
        1 for r in en_ready_obs if "covered" in (r.get("coverage_statuses") or []) or r.get("coverage_status") == "covered"
    )
    # coverage_statuses on enrichment rows
    if not covered_attachable:
        covered_attachable = sum(
            1
            for r in enrichment_rows
            if r.get("identity_key") in ready_keys
            and (
                r.get("coverage_status") == "covered"
                or "covered" in (r.get("coverage_statuses") or [])
            )
        )
    uncovered_attachable = sum(
        1
        for r in enrichment_rows
        if r.get("identity_key") in ready_keys
        and (
            r.get("coverage_status") == "uncovered"
            or "uncovered" in (r.get("coverage_statuses") or [])
        )
    )

    potential_match_rate = (
        round((matched_now + attachable_obs) / nci_obs, 4) if nci_obs else None
    )
    gap_now = max(0, (nci_obs or 0) - matched_now)
    gap_after = max(0, gap_now - attachable_obs)

    simulation = {
        "CURRENT_LOCALITIES": current_localities,
        "HIGH_CONFIDENCE_initial": len({r.get("identity_key") for r in hc_rows if r.get("is_canonical_representative", True)}),
        "READY_FOR_INTEGRATION": ready_for_integration_total,
        "HOMONYM_NEW_LOCALITY_READY": homonym_ready_n,
        "PROJECTED_LOCALITIES": projected,
        "PROJECTED_IF_HOMONYM_READY_INCLUDED": current_localities + ready_for_integration_total + homonym_ready_n,
        "current_match_rate": match_now,
        "potential_match_rate_after_ready": potential_match_rate,
        "nci_observations_attachable": attachable_obs,
        "covered_observations_attachable": covered_attachable,
        "uncovered_observations_attachable": uncovered_attachable,
        "population_attachable_ready": pop_ready,
        "population_remaining_review": pop_review,
        "gap_unmatched_now_approx": gap_now,
        "gap_after_ready_approx": gap_after,
        "gap_reduction_obs": attachable_obs,
        "remaining_human_review": final_counts.get("REQUIRES_HUMAN_REVIEW", 0)
        + homonym_counts.get("HOMONYM_REQUIRES_REVIEW", 0),
        "applied": False,
        "note": "Simulation only — referential and KPIs not updated",
    }

    # Fix HIGH_CONFIDENCE_initial count: use unique identities from HC
    hc_identities = {
        r.get("identity_key")
        for r in hc_rows
        if r.get("is_canonical_representative") is not False
    }
    # Prefer counting unique identity keys among HC
    hc_identities = {
        r.get("identity_key")
        for r in enrichment_rows
        if r.get("enrichment_class") == "NEW_LOCALITY_CANDIDATE_HIGH_CONFIDENCE"
        and r.get("is_canonical_representative", True)
    }
    simulation["HIGH_CONFIDENCE_initial"] = len(hc_identities)

    integration_plan = {
        "mode": "idempotent_controlled",
        "auto_execute": False,
        "eligible_count": ready_for_integration_total,
        "homonym_ready_separate_count": homonym_ready_n,
        "required_fields": [
            "canonical_id",
            "nom_canonique",
            "nom_source",
            "coordinates",
            "province",
            "territoire",
            "collectivite_or_groupement_if_available",
            "source_nci_fdsu",
            "nire_classification",
            "score_confidence",
            "proofs",
            "integration_date",
        ],
        "coverage_policy": "coverage remains observation linked to locality identity",
        "sample_records": ready_records[:10],
        "steps": [
            "1. Freeze lot READY_FOR_INTEGRATION",
            "2. Human spot-check sample",
            "3. Upsert by idempotency_key into locality referential",
            "4. Link NCI observations without dropping covered/uncovered",
            "5. Propagate modules (see propagation)",
        ],
    }

    kpis = {
        "CURRENT_LOCALITIES": current_localities,
        "HIGH_CONFIDENCE_initial": simulation["HIGH_CONFIDENCE_initial"],
        "READY_FOR_INTEGRATION": ready_for_integration_total,
        "REQUIRES_HUMAN_REVIEW": final_counts.get("REQUIRES_HUMAN_REVIEW", 0),
        "EXISTING_LOCALITY_VARIANT_recovered": final_counts.get("EXISTING_LOCALITY_VARIANT", 0),
        "DUPLICATE_NCI_OBSERVATION_recovered": final_counts.get("DUPLICATE_NCI_OBSERVATION", 0),
        "HOMONYM_DISTINCT_CONFIRMED": final_counts.get("HOMONYM_DISTINCT_CONFIRMED", 0),
        "HOMONYM_ALREADY_IN_REFERENTIAL": homonym_counts.get("HOMONYM_ALREADY_IN_REFERENTIAL", 0),
        "HOMONYM_NEW_LOCALITY_READY": homonym_ready_n,
        "HOMONYM_REQUIRES_REVIEW": homonym_counts.get("HOMONYM_REQUIRES_REVIEW", 0),
        "PROJECTED_LOCALITIES": projected,
        "by_final_class": {c: final_counts.get(c, 0) for c in FINAL_CLASSES},
        "by_homonym_class": {c: homonym_counts.get(c, 0) for c in HOMONYM_CLASSES},
        "distance_rule_removed": True,
        "referential_not_modified": True,
        "auto_creation_disabled": True,
        "sources_immutable": True,
    }

    state = PreintegrationState(
        executed=True,
        message=(
            "Validation pré-intégration exécutée (lecture seule) — "
            "aucune intégration référentiel."
        ),
        meta={
            "engine": ENGINE_VERSION,
            "generated_at": _now(),
            "thresholds": THRESHOLDS,
            "final_classes": list(FINAL_CLASSES),
            "homonym_classes": list(HOMONYM_CLASSES),
            "policy": {
                "distance_never_creates_or_rejects": True,
                "proximity_is_match_signal_only": True,
                "no_merge_on_name_alone": True,
            },
        },
        kpis=kpis,
        rows=final_rows,
        homonym_rows=homonym_out,
        integration_plan=integration_plan,
        simulation=simulation,
        propagation=describe_propagation(),
        performance={"elapsed_ms": round((time.time() - started) * 1000, 1)},
    )

    global _STATE
    _STATE = state

    if write_cache:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(
            json.dumps(
                {
                    "meta": state.meta,
                    "kpis": state.kpis,
                    "simulation": state.simulation,
                    "integration_plan": {
                        k: v for k, v in state.integration_plan.items() if k != "sample_records"
                    },
                    "propagation": state.propagation,
                    "sample_ready": [
                        r for r in state.rows
                        if r.get("final_class") == "READY_FOR_INTEGRATION" and r.get("is_canonical_representative")
                    ][:40],
                    "sample_homonym": state.homonym_rows[:40],
                    "note": "Derived cache — sources immutable — referential not modified",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    return state


def status_payload() -> dict[str, Any]:
    st = get_state()
    if not st.executed:
        return {
            "executed": False,
            "message": "Aucune validation pré-intégration — POST /api/nire/locality-preintegration/run",
            "engine": ENGINE_VERSION,
        }
    return {
        "executed": True,
        "message": st.message,
        "meta": st.meta,
        "kpis": st.kpis,
        "simulation": st.simulation,
        "performance": st.performance,
        "referential_not_modified": True,
    }


def summary_payload() -> dict[str, Any]:
    st = get_state()
    if not st.executed:
        return status_payload()
    return {
        "executed": True,
        "kpis": st.kpis,
        "simulation": st.simulation,
        "integration_plan": st.integration_plan,
        "propagation": st.propagation,
        "meta": st.meta,
    }
