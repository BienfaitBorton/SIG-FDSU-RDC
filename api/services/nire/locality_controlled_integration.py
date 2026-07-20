"""Intégration contrôlée NCI → référentiel national localités.

Règle métier FDSU :
- géométrie exploitable + absente des 26 710 → intégrable ;
- distance seule ≠ doublon / rejet ;
- nom seul ≠ fusion si contexte territorial distinct ;
- identité territoriale prime.

La base KMZ (`locality_referential_official.json`) reste intacte.
Les ajouts NCI sont persistés de façon idempotente dans
`locality_referential_nci_enrichment.json`, fusionnés au chargement national.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from api.services.nire import locality_coverage as lc
from api.services.nire import locality_enrichment_audit as lea
from api.services.nire import locality_preintegration_validation as piv

ENGINE_VERSION = "nire-locality-controlled-integration-1.0.0"
ROOT = lc.ROOT
OFFICIAL_JSON = lc.ADMIN_JSON
ENRICHMENT_JSON = ROOT / "data" / "reports" / "locality_official" / "locality_referential_nci_enrichment.json"
MANIFEST_JSON = ROOT / "data" / "reports" / "locality_official" / "locality_referential_national_manifest.json"
QUALITY_JSON = ROOT / "data" / "reports" / "locality_official" / "locality_quality_report.json"
PRE_STATE_JSON = ROOT / "data" / "cache" / "nire_locality_pre_integration_state_v1.json"
RUN_CACHE_JSON = ROOT / "data" / "cache" / "nire_locality_controlled_integration_v1.json"

CLASSIFICATIONS = (
    "ALREADY_IN_REFERENTIAL",
    "NEW_LOCALITY_WITH_VALID_GEOMETRY",
    "INVALID_GEOMETRY",
    "DUPLICATE_NCI_OBSERVATION",
    "REQUIRES_IDENTITY_REVIEW",
)

# Bornes géographiques plausibles RDC (WGS84)
RDC_LAT_MIN, RDC_LAT_MAX = -13.70, 5.60
RDC_LON_MIN, RDC_LON_MAX = 12.00, 31.80

THRESHOLDS = {
    "same_context_variant_ratio": 0.90,
    "min_name_len": 2,
}


@dataclass
class IntegrationState:
    executed: bool = False
    message: str = ""
    meta: dict[str, Any] = field(default_factory=dict)
    kpis: dict[str, Any] = field(default_factory=dict)
    rows: list[dict[str, Any]] = field(default_factory=list)
    inserted_ids: list[str] = field(default_factory=list)
    performance: dict[str, Any] = field(default_factory=dict)


_STATE = IntegrationState()


def get_state() -> IntegrationState:
    return _STATE


def reset_state() -> None:
    global _STATE
    _STATE = IntegrationState()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def file_sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def geometry_status(lat: Any, lon: Any) -> tuple[str, list[str]]:
    """VALID_GEOMETRY | INVALID_GEOMETRY — bornes RDC, pas (0,0), pas NaN."""
    proofs: list[str] = []
    try:
        if lat is None or lon is None:
            return "INVALID_GEOMETRY", ["NULL_COORDINATE"]
        flat, flon = float(lat), float(lon)
        if math.isnan(flat) or math.isnan(flon) or math.isinf(flat) or math.isinf(flon):
            return "INVALID_GEOMETRY", ["NAN_OR_INF"]
        if flat == 0.0 and flon == 0.0:
            return "INVALID_GEOMETRY", ["ZERO_ZERO_POINT"]
        if not (RDC_LAT_MIN <= flat <= RDC_LAT_MAX and RDC_LON_MIN <= flon <= RDC_LON_MAX):
            return "INVALID_GEOMETRY", ["OUTSIDE_RDC_PLAUSIBLE_BOUNDS"]
        proofs.extend(["NUMERIC_COORDS", "WITHIN_RDC_BOUNDS", "NON_ZERO"])
        return "VALID_GEOMETRY", proofs
    except (TypeError, ValueError):
        return "INVALID_GEOMETRY", ["NON_NUMERIC_COORDS"]


def identity_key(row: dict[str, Any]) -> str:
    return lea.identity_key(row)


def canonical_id_for(row: dict[str, Any]) -> str:
    return lea.future_canonical_id(row)


def _name_ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def save_pre_integration_state(*, admin_count: int) -> dict[str, Any]:
    def _rel(path: Path) -> str:
        try:
            return str(path.relative_to(ROOT)).replace("\\", "/")
        except ValueError:
            return str(path)

    state = {
        "generated_at": _now(),
        "CURRENT_LOCALITIES": admin_count,
        "authoritative_base_file": _rel(OFFICIAL_JSON),
        "enrichment_file": _rel(ENRICHMENT_JSON),
        "base_sha256": file_sha256(OFFICIAL_JSON),
        "enrichment_sha256_before": file_sha256(ENRICHMENT_JSON),
        "note": "Base KMZ non modifiée — ajouts NCI dans enrichment layer",
    }
    PRE_STATE_JSON.parent.mkdir(parents=True, exist_ok=True)
    PRE_STATE_JSON.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return state


def load_enrichment_doc() -> dict[str, Any]:
    if not ENRICHMENT_JSON.exists():
        return {
            "source": "nci_fdsu_controlled_integration",
            "generated_at": None,
            "engine": ENGINE_VERSION,
            "locality_referential": [],
            "by_canonical_id": {},
            "integration_runs": [],
        }
    from api.services import referential_runtime_cache as rrc

    return rrc.load_json_file(ENRICHMENT_JSON, label="locality_referential_nci_enrichment.json")


def load_national_locality_items(*, include_enrichment: bool = True) -> list[dict[str, Any]]:
    """Référentiel national = base officielle (+ enrichissement NCI si présent).

    Si un overlay de liens Groupement→Localité RGC est présent, il est appliqué
    en lecture seule (enrichit le champ groupement sans créer de localité).

    Cache mémoire partagé (mtime) — invalidé si les fichiers sources changent.
    """
    from api.services import referential_runtime_cache as rrc

    try:
        from api.services.nire import groupement_controlled_integration as gci

        links_path = gci.LINKS_JSON
    except Exception:
        links_path = ROOT / "data" / "reports" / "locality_official" / "locality_groupement_links_rgc.json"

    paths = [OFFICIAL_JSON]
    if include_enrichment:
        paths.extend([ENRICHMENT_JSON, links_path])
    signature = (include_enrichment,) + rrc.file_signature(*paths)
    cache_key = "national_locality_items"

    def _build() -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        if OFFICIAL_JSON.exists():
            doc = rrc.load_json_file(OFFICIAL_JSON, label="locality_referential_official.json")
            items.extend(doc.get("locality_referential") or [])
        if include_enrichment and ENRICHMENT_JSON.exists():
            enr = load_enrichment_doc()
            items.extend(enr.get("locality_referential") or [])
        if include_enrichment:
            try:
                from api.services.nire import groupement_controlled_integration as gci

                items = gci.apply_groupement_links_to_localities(items)
            except Exception:
                pass
        return items

    return rrc.get_or_build(cache_key if include_enrichment else f"{cache_key}_base", signature, _build)


def national_locality_count(*, include_enrichment: bool = True) -> int:
    """Compte dynamique — réutilise le cache de fusion (pas de reparse si chaud)."""
    return len(load_national_locality_items(include_enrichment=include_enrichment))


def _admin_from_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalise items JSON officiels/enrichis vers structure admin NIRE."""
    out = []
    for item in items:
        hierarchy = item.get("hierarchy") or item.get("administrative_attachment") or {}
        geom = item.get("geometry") or {}
        coords = geom.get("coordinates") if isinstance(geom, dict) else None
        lon = lat = None
        if isinstance(coords, (list, tuple)) and len(coords) >= 2:
            lon, lat = coords[0], coords[1]
        meta = item.get("metadata") or {}
        ext = meta.get("extended_data") if isinstance(meta, dict) else {}
        if not isinstance(ext, dict):
            ext = {}
        collectivite = (
            item.get("collectivité")
            or item.get("collectivite")
            or hierarchy.get("collectivité")
            or hierarchy.get("collectivite")
            or ext.get("COLLECTIV")
            or item.get("collectivite")
            or ""
        )
        out.append(
            {
                "admin_id": item.get("canonical_id") or item.get("id") or item.get("code"),
                "nom": item.get("nom") or item.get("name"),
                "province": hierarchy.get("province") or item.get("province"),
                "territoire": hierarchy.get("territoire") or hierarchy.get("territory") or item.get("territoire"),
                "collectivite": collectivite,
                "groupement": item.get("groupement") or hierarchy.get("groupement") or "",
                "latitude": lat if lat is not None else item.get("latitude"),
                "longitude": lon if lon is not None else item.get("longitude"),
                "source": item.get("source") or "locality_referential",
                "provenance": item.get("provenance") or item.get("source"),
                "statut": item.get("statut"),
            }
        )
    return out


def build_same_context_index(admin: list[dict[str, Any]]) -> dict[str, Any]:
    by_ctx: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_ctx_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_ctx_adv: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_ctx_compact: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for a in admin:
        prov = lc._norm(a.get("province"))
        terr = lc._norm(a.get("territoire"))
        if not prov or not terr:
            continue
        ctx = f"{prov}|{terr}"
        by_ctx[ctx].append(a)
        nk = lc._norm(a.get("nom"))
        adv = piv.advanced_normalize(a.get("nom"))
        compact = piv.advanced_compact(a.get("nom"))
        if nk:
            by_ctx_name[f"{ctx}|{nk}"].append(a)
        if adv:
            by_ctx_adv[f"{ctx}|{adv}"].append(a)
        if compact:
            by_ctx_compact[f"{ctx}|{compact}"].append(a)
    return {
        "by_ctx": by_ctx,
        "by_ctx_name": by_ctx_name,
        "by_ctx_adv": by_ctx_adv,
        "by_ctx_compact": by_ctx_compact,
    }


def find_existing_representation(
    obs: dict[str, Any],
    indexes: dict[str, Any],
) -> tuple[dict[str, Any] | None, list[str], float]:
    """Même identité territoriale dans le référentiel — jamais nom seul / distance seule."""
    toponym = obs.get("toponym") or lc._nci_toponym(obs)
    nkey = lc._norm(toponym)
    adv = piv.advanced_normalize(toponym)
    compact = piv.advanced_compact(toponym)
    prov = lc._norm(obs.get("province"))
    terr = lc._norm(obs.get("territoire"))
    if not nkey or len(nkey) < THRESHOLDS["min_name_len"] or not prov or not terr:
        return None, ["NAME_OR_CONTEXT_INSUFFICIENT"], 0.0

    ctx = f"{prov}|{terr}"
    # Exact / advanced / compact — O(1)
    for key, bucket, label in (
        (f"{ctx}|{nkey}", indexes["by_ctx_name"], "NORMALIZED_NAME_MATCH_SAME_CONTEXT"),
        (f"{ctx}|{adv}", indexes["by_ctx_adv"], "ADVANCED_NAME_MATCH_SAME_CONTEXT") if adv else (None, None, None),
        (f"{ctx}|{compact}", indexes["by_ctx_compact"], "COMPACT_NAME_MATCH_SAME_CONTEXT") if compact else (None, None, None),
    ):
        if not key:
            continue
        hits = bucket.get(key) or []
        if hits:
            return hits[0], ["SAME_PROVINCE", "SAME_TERRITORY", label, "DISTANCE_NOT_USED"], 1.0

    # Fuzzy limité : même contexte + même initiale + longueur proche
    pool = indexes["by_ctx"].get(ctx) or []
    best = None
    best_score = 0.0
    best_proofs: list[str] = []
    initial = nkey[0]
    for a in pool:
        akey = lc._norm(a.get("nom"))
        if not akey or akey[0] != initial:
            continue
        if abs(len(akey) - len(nkey)) > max(2, int(0.3 * len(nkey))):
            continue
        a_adv = piv.advanced_normalize(a.get("nom"))
        a_compact = piv.advanced_compact(a.get("nom"))
        ratio = max(
            _name_ratio(nkey, akey),
            _name_ratio(adv, a_adv) if adv and a_adv else 0.0,
            _name_ratio(compact, a_compact) if compact and a_compact else 0.0,
        )
        if ratio < THRESHOLDS["same_context_variant_ratio"]:
            if not (adv and a_adv and len(adv) >= 4 and (adv in a_adv or a_adv in adv)):
                continue
            ratio = max(ratio, 0.92)
            proofs = ["SAME_PROVINCE", "SAME_TERRITORY", "PARTIAL_NAME_SAME_CONTEXT"]
        else:
            proofs = ["SAME_PROVINCE", "SAME_TERRITORY", "ORTHOGRAPHIC_VARIANT_SAME_CONTEXT"]
        if ratio > best_score:
            best_score = ratio
            best = a
            best_proofs = proofs

    if best and best_score >= THRESHOLDS["same_context_variant_ratio"]:
        return best, best_proofs + ["DISTANCE_NOT_USED"], best_score
    return None, ["NO_SAME_CONTEXT_MATCH", "DISTANCE_NOT_USED"], 0.0


def build_locality_record(obs: dict[str, Any], *, classification: str) -> dict[str, Any]:
    lat, lon = float(obs["latitude"]), float(obs["longitude"])
    toponym = (
        obs.get("toponym")
        or obs.get("nom")
        or obs.get("nom_source")
        or lc._nci_toponym(obs)
    )
    # Réutiliser l'id déjà intégré — ne jamais régénérer un second id pour la même fiche.
    existing_cid = str(obs.get("canonical_id") or "").strip()
    cid = existing_cid if existing_cid.startswith("RDC-NCI-LOC-") else canonical_id_for(obs)
    coverage_statuses = obs.get("coverage_statuses") or []
    if not coverage_statuses and isinstance(obs.get("metadata"), dict):
        coverage_statuses = list(obs["metadata"].get("coverage_statuses") or [])
    if not coverage_statuses and obs.get("coverage_status"):
        coverage_statuses = [obs.get("coverage_status")]
    return {
        "canonical_id": cid,
        "nom": toponym,
        "nom_source": obs.get("nci_destination") or obs.get("destination") or toponym,
        "nom_normalise": lc._norm(toponym),
        "nom_normalise_avance": piv.advanced_normalize(toponym),
        "niveau": "Localité",
        "type_localite": "Village",
        "province": obs.get("province"),
        "territoire": obs.get("territoire"),
        "collectivité": obs.get("collectivite") or None,
        "groupement": obs.get("groupement") or None,
        "geometry": {"type": "Point", "coordinates": [lon, lat, 0.0]},
        "latitude": lat,
        "longitude": lon,
        "source": "NCI/FDSU",
        "provenance": "nci_fdsu",
        "statut": "nci_integrated",
        "qualité": None,
        "zone_fdsu": obs.get("fdsu_zone"),
        "admin_context_origin": "SOURCE_ADMIN_CONTEXT",
        "spatial_derived_admin_context": None,
        "nire_classification": classification,
        "integration_date": _now(),
        "metadata": {
            "source_observation_ids": obs.get("observation_ids") or [obs.get("nci_id")],
            "coverage_statuses": coverage_statuses,
            "identity_key": obs.get("identity_key") or identity_key(obs),
            "engine": ENGINE_VERSION,
            "proofs": obs.get("proofs") or [],
        },
        "future_profile": {
            "population": obs.get("population"),
            "ecoles": [],
            "centres_de_sante": [],
            "couverture_reseau": None,
            "sites_fdsu": [],
            "activites_economiques": [],
            "energie": None,
            "photos": [],
            "rapports_de_mission": [],
            "indicateurs_caid": {},
        },
    }


def classify_nci_universe(
    *,
    covered_rows: list[dict[str, Any]] | None = None,
    uncovered_rows: list[dict[str, Any]] | None = None,
    base_admin: list[dict[str, Any]] | None = None,
    existing_enrichment_ids: set[str] | None = None,
) -> dict[str, Any]:
    covered = covered_rows if covered_rows is not None else lc._load_jsonl(lc.COVERAGE_DIR / "localities_covered.jsonl")
    uncovered = (
        uncovered_rows if uncovered_rows is not None else lc._load_jsonl(lc.COVERAGE_DIR / "localities_uncovered.jsonl")
    )
    # Base = officiel seul pour décider « déjà dans les 26 710 » ; enrichment ids = déjà intégrés NCI
    if base_admin is None:
        official_items = []
        if OFFICIAL_JSON.exists():
            official_items = json.loads(OFFICIAL_JSON.read_text(encoding="utf-8")).get("locality_referential") or []
        base_admin = _admin_from_items(official_items)

    existing_ids = set(existing_enrichment_ids or [])
    existing_identity_keys: set[str] = set()
    if not existing_ids and ENRICHMENT_JSON.exists():
        for x in load_enrichment_doc().get("locality_referential") or []:
            if x.get("canonical_id"):
                existing_ids.add(str(x.get("canonical_id")))
            meta = x.get("metadata") or {}
            if meta.get("identity_key"):
                existing_identity_keys.add(str(meta.get("identity_key")))
            # fallback identity from fields
            existing_identity_keys.add(
                identity_key(
                    {
                        "toponym": x.get("nom"),
                        "province": x.get("province"),
                        "territoire": x.get("territoire"),
                        "latitude": x.get("latitude"),
                        "longitude": x.get("longitude"),
                    }
                )
            )

    same_ctx_index = build_same_context_index(base_admin)
    admin_by_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for a in base_admin:
        nk = lc._norm(a.get("nom"))
        if nk:
            admin_by_name[nk].append(a)

    # Grouper covered+uncovered par identité
    streams = [("covered", covered), ("uncovered", uncovered)]
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for status, rows in streams:
        for row in rows:
            obs = dict(row)
            obs["coverage_status"] = status
            obs["toponym"] = lc._nci_toponym(obs)
            groups[identity_key(obs)].append(obs)

    results: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    homonym_new = 0
    to_integrate: list[dict[str, Any]] = []

    for ident, rows in groups.items():
        rows_sorted = sorted(
            rows,
            key=lambda x: (0 if x.get("coverage_status") == "uncovered" else 1, str(x.get("id") or "")),
        )
        primary = rows_sorted[0]
        observation_ids = [str(r.get("id")) for r in rows_sorted if r.get("id")]
        coverage_statuses = sorted({str(r.get("coverage_status")) for r in rows_sorted})
        primary = dict(primary)
        primary["observation_ids"] = observation_ids
        primary["coverage_statuses"] = coverage_statuses
        primary["identity_key"] = ident
        primary["nci_id"] = primary.get("id")
        primary["toponym"] = primary.get("toponym") or lc._nci_toponym(primary)

        # Extras = doublons NCI
        for extra in rows_sorted[1:]:
            counts["DUPLICATE_NCI_OBSERVATION"] += 1
            results.append(
                {
                    "nci_id": extra.get("id"),
                    "identity_key": ident,
                    "toponym": lc._nci_toponym(extra),
                    "province": extra.get("province"),
                    "territoire": extra.get("territoire"),
                    "classification": "DUPLICATE_NCI_OBSERVATION",
                    "is_canonical_representative": False,
                    "geometry_status": None,
                    "proofs": ["SAME_NCI_IDENTITY_MULTIPLE_OBSERVATIONS"],
                    "canonical_id": None,
                    "auto_created": False,
                }
            )

        geom_status, geom_proofs = geometry_status(primary.get("latitude"), primary.get("longitude"))
        prov = lc._norm(primary.get("province"))
        terr = lc._norm(primary.get("territoire"))
        nkey = lc._norm(primary.get("toponym"))

        existing, exist_proofs, exist_score = find_existing_representation(primary, same_ctx_index)

        cid = canonical_id_for(primary)
        already_enriched = cid in existing_ids or ident in existing_identity_keys

        if existing or already_enriched:
            classification = "ALREADY_IN_REFERENTIAL"
            proofs = exist_proofs if existing else ["ALREADY_IN_NCI_ENRICHMENT_LAYER"]
            if already_enriched and not existing:
                proofs = ["CANONICAL_ID_ALREADY_INTEGRATED", "DISTANCE_NOT_USED"]
            matched_admin = existing.get("admin_id") if existing else cid
            matched_name = existing.get("nom") if existing else primary.get("toponym")
        elif geom_status == "INVALID_GEOMETRY":
            classification = "INVALID_GEOMETRY"
            proofs = geom_proofs + ["DISTANCE_NOT_USED"]
            matched_admin = matched_name = None
        elif not prov or not terr or not nkey or len(nkey) < THRESHOLDS["min_name_len"]:
            # Doute réel : géométrie OK mais contexte admin insuffisant pour trancher identité
            if geom_status == "VALID_GEOMETRY" and nkey and len(nkey) >= THRESHOLDS["min_name_len"]:
                # Province/territoire manquant mais géométrie OK → nouvelle localité (champs null OK)
                classification = "NEW_LOCALITY_WITH_VALID_GEOMETRY"
                proofs = geom_proofs + ["ABSENT_SAME_CONTEXT", "PARTIAL_ADMIN_CONTEXT_ALLOWED", "DISTANCE_NOT_USED"]
                matched_admin = matched_name = None
            else:
                classification = "REQUIRES_IDENTITY_REVIEW"
                proofs = ["INSUFFICIENT_IDENTITY_FIELDS", "DISTANCE_NOT_USED"]
                matched_admin = matched_name = None
        else:
            classification = "NEW_LOCALITY_WITH_VALID_GEOMETRY"
            proofs = geom_proofs + ["ABSENT_SAME_CONTEXT", "TERRITORIAL_IDENTITY", "DISTANCE_NOT_USED"]
            matched_admin = matched_name = None

        # Homonyme distinct comptabilisé si nouveau + nom existe hors contexte
        if classification == "NEW_LOCALITY_WITH_VALID_GEOMETRY" and nkey:
            name_elsewhere = False
            for a in admin_by_name.get(nkey) or []:
                if lc._norm(a.get("province")) == prov and lc._norm(a.get("territoire")) == terr:
                    continue
                name_elsewhere = True
                break
            if name_elsewhere:
                proofs.append("HOMONYM_DISTINCT_TERRITORIAL_IDENTITY")
                homonym_new += 1

        counts[classification] += 1
        record = {
            "nci_id": primary.get("id"),
            "identity_key": ident,
            "toponym": primary.get("toponym"),
            "province": primary.get("province"),
            "territoire": primary.get("territoire"),
            "latitude": primary.get("latitude"),
            "longitude": primary.get("longitude"),
            "population": primary.get("population"),
            "observation_ids": observation_ids,
            "coverage_statuses": coverage_statuses,
            "classification": classification,
            "is_canonical_representative": True,
            "geometry_status": geom_status,
            "proofs": proofs,
            "score": round(exist_score, 4) if existing else None,
            "matched_admin_id": matched_admin,
            "matched_admin_name": matched_name,
            "canonical_id": cid if classification == "NEW_LOCALITY_WITH_VALID_GEOMETRY" else (cid if already_enriched else None),
            "auto_created": False,
        }
        results.append(record)
        if classification == "NEW_LOCALITY_WITH_VALID_GEOMETRY":
            primary["proofs"] = proofs
            to_integrate.append(primary)

    return {
        "results": results,
        "counts": dict(counts),
        "to_integrate": to_integrate,
        "homonym_new_candidates": homonym_new,
        "unique_identities": len(groups),
        "raw_observations": len(covered) + len(uncovered),
        "covered_rows": len(covered),
        "uncovered_rows": len(uncovered),
    }


def persist_enrichment(
    to_integrate: list[dict[str, Any]],
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Upsert idempotent dans la couche d'enrichissement NCI."""
    doc = load_enrichment_doc()
    by_id: dict[str, dict[str, Any]] = {
        str(x.get("canonical_id")): x for x in (doc.get("locality_referential") or []) if x.get("canonical_id")
    }
    inserted = 0
    skipped = 0
    new_records: list[dict[str, Any]] = []
    for obs in to_integrate:
        # Court-circuit : fiche déjà intégrée (même canonical_id) → no-op.
        existing_cid = str(obs.get("canonical_id") or "").strip()
        if existing_cid and existing_cid in by_id:
            skipped += 1
            continue
        rec = build_locality_record(obs, classification="NEW_LOCALITY_WITH_VALID_GEOMETRY")
        cid = rec["canonical_id"]
        if cid in by_id:
            skipped += 1
            continue
        by_id[cid] = rec
        new_records.append(rec)
        inserted += 1

    if not dry_run:
        if inserted == 0 and ENRICHMENT_JSON.exists():
            return {
                "inserted": 0,
                "skipped_existing": skipped,
                "total_enrichment": len(by_id),
                "new_records_sample": [],
                "dry_run": False,
                "skipped_rewrite": True,
            }
        doc["locality_referential"] = list(by_id.values())
        doc["by_canonical_id"] = {cid: True for cid in by_id}
        doc["generated_at"] = _now()
        doc["engine"] = ENGINE_VERSION
        doc["count"] = len(by_id)
        runs = list(doc.get("integration_runs") or [])
        runs.append(
            {
                "at": _now(),
                "inserted": inserted,
                "skipped_existing": skipped,
                "total_after": len(by_id),
            }
        )
        doc["integration_runs"] = runs[-20:]
        ENRICHMENT_JSON.parent.mkdir(parents=True, exist_ok=True)
        ENRICHMENT_JSON.write_text(
            json.dumps(doc, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        try:
            from api.services import referential_runtime_cache as rrc

            rrc.invalidate_paths(ENRICHMENT_JSON, OFFICIAL_JSON)
        except Exception:
            pass

    return {
        "inserted": inserted,
        "skipped_existing": skipped,
        "total_enrichment": len(by_id),
        "new_records_sample": new_records[:5],
        "dry_run": dry_run,
    }


def update_quality_and_manifest(*, old_count: int, added: int, new_total: int, run_kpis: dict[str, Any]) -> None:
    manifest = {
        "generated_at": _now(),
        "engine": ENGINE_VERSION,
        "OLD_LOCALITIES": old_count,
        "NEW_LOCALITIES_ADDED": added,
        "NEW_TOTAL_LOCALITIES": new_total,
        "base_file": str(OFFICIAL_JSON),
        "enrichment_file": str(ENRICHMENT_JSON),
        "base_sha256": file_sha256(OFFICIAL_JSON),
        "enrichment_sha256": file_sha256(ENRICHMENT_JSON),
        "base_untouched": True,
        "kpis": run_kpis,
    }
    MANIFEST_JSON.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    if QUALITY_JSON.exists():
        try:
            quality = json.loads(QUALITY_JSON.read_text(encoding="utf-8"))
            quality["locality_count"] = new_total
            quality["nci_enrichment_added"] = added
            quality["national_total_dynamic"] = True
            quality["updated_at_integration"] = _now()
            QUALITY_JSON.write_text(json.dumps(quality, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass


def run_controlled_integration(
    *,
    covered_rows: list[dict[str, Any]] | None = None,
    uncovered_rows: list[dict[str, Any]] | None = None,
    apply: bool = True,
    write_cache: bool = True,
) -> IntegrationState:
    started = time.time()
    official_items = []
    if OFFICIAL_JSON.exists():
        official_items = json.loads(OFFICIAL_JSON.read_text(encoding="utf-8")).get("locality_referential") or []
    old_count = len(official_items)
    pre = save_pre_integration_state(admin_count=old_count)

    classified = classify_nci_universe(
        covered_rows=covered_rows,
        uncovered_rows=uncovered_rows,
        base_admin=_admin_from_items(official_items),
    )

    first = {"inserted": 0, "skipped_existing": 0, "total_enrichment": 0}
    second = {"inserted": 0, "skipped_existing": 0, "total_enrichment": 0}
    if apply:
        first = persist_enrichment(classified["to_integrate"], dry_run=False)
        second = persist_enrichment(classified["to_integrate"], dry_run=False)

    enrichment_count = len(load_enrichment_doc().get("locality_referential") or [])
    new_total = old_count + enrichment_count
    added = first.get("inserted", 0) if apply else len(classified["to_integrate"])

    # Post KPIs coverage attachment (analytical)
    dual = sum(
        1
        for r in classified["results"]
        if r.get("is_canonical_representative")
        and set(r.get("coverage_statuses") or []) >= {"covered", "uncovered"}
    )
    covered_attached = sum(
        1
        for r in classified["results"]
        if r.get("classification") in {"ALREADY_IN_REFERENTIAL", "NEW_LOCALITY_WITH_VALID_GEOMETRY"}
        and "covered" in (r.get("coverage_statuses") or [])
    )
    uncovered_attached = sum(
        1
        for r in classified["results"]
        if r.get("classification") in {"ALREADY_IN_REFERENTIAL", "NEW_LOCALITY_WITH_VALID_GEOMETRY"}
        and "uncovered" in (r.get("coverage_statuses") or [])
    )
    pop_attachable = 0
    for r in classified["results"]:
        if r.get("classification") in {"ALREADY_IN_REFERENTIAL", "NEW_LOCALITY_WITH_VALID_GEOMETRY"} and r.get(
            "is_canonical_representative"
        ):
            try:
                pop_attachable += int(r.get("population") or 0)
            except (TypeError, ValueError):
                pass

    # Match rate approx after integration: ALREADY + NEW (now in ref) / unique identities
    matched_like = classified["counts"].get("ALREADY_IN_REFERENTIAL", 0) + classified["counts"].get(
        "NEW_LOCALITY_WITH_VALID_GEOMETRY", 0
    )
    unique = classified["unique_identities"] or 1
    # After integration, NEW become ALREADY — match rate on identities
    post_match_rate = round(matched_like / unique, 4)

    # Observation-level match rate vs raw NCI
    raw = classified["raw_observations"] or 1
    # Count observations belonging to matched/new identities
    matched_idents = {
        r["identity_key"]
        for r in classified["results"]
        if r.get("classification") in {"ALREADY_IN_REFERENTIAL", "NEW_LOCALITY_WITH_VALID_GEOMETRY"}
    }
    obs_matched = sum(
        1
        for r in classified["results"]
        if r.get("identity_key") in matched_idents
    )
    # duplicates share identity — count all obs in those groups from raw via identity
    # results include dups; identity_key match counts all
    post_obs_match_rate = round(
        sum(1 for r in classified["results"] if r.get("identity_key") in matched_idents) / len(classified["results"]),
        4,
    ) if classified["results"] else 0.0

    kpis = {
        "OLD_LOCALITIES": old_count,
        "UNIQUE_NCI_IDENTITIES_ANALYZED": classified["unique_identities"],
        "ALREADY_IN_REFERENTIAL": classified["counts"].get("ALREADY_IN_REFERENTIAL", 0),
        "NEW_LOCALITY_WITH_VALID_GEOMETRY": classified["counts"].get("NEW_LOCALITY_WITH_VALID_GEOMETRY", 0),
        "INVALID_GEOMETRY": classified["counts"].get("INVALID_GEOMETRY", 0),
        "REQUIRES_IDENTITY_REVIEW": classified["counts"].get("REQUIRES_IDENTITY_REVIEW", 0),
        "DUPLICATE_NCI_OBSERVATION": classified["counts"].get("DUPLICATE_NCI_OBSERVATION", 0),
        "HOMONYM_NEW_LOCALITIES_ADDED": classified["homonym_new_candidates"] if apply else classified["homonym_new_candidates"],
        "NEW_LOCALITIES_ADDED": enrichment_count if apply else 0,
        "NEW_TOTAL_LOCALITIES": new_total if apply else old_count,
        "INSERTED_FIRST_RUN": first.get("inserted", 0),
        "INSERTED_SECOND_RUN": second.get("inserted", 0),
        "idempotent": second.get("inserted", 0) == 0,
        "post_identity_match_rate": post_match_rate,
        "post_observation_attach_rate": post_obs_match_rate,
        "covered_identities_attached": covered_attached,
        "uncovered_identities_attached": uncovered_attached,
        "dual_source_identities": dual,
        "population_attachable": pop_attachable,
        "base_file_untouched": True,
        "base_sha256": pre.get("base_sha256"),
        "raw_observations": classified["raw_observations"],
        "by_classification": classified["counts"],
        "apply": apply,
    }

    if apply:
        # Homonym added = among inserted that had HOMONYM proof — approximate from to_integrate
        homonym_added = sum(
            1
            for obs in classified["to_integrate"]
            if any(
                r.get("identity_key") == identity_key(obs)
                and "HOMONYM_DISTINCT_TERRITORIAL_IDENTITY" in (r.get("proofs") or [])
                for r in classified["results"]
                if r.get("is_canonical_representative")
            )
        )
        kpis["HOMONYM_NEW_LOCALITIES_ADDED"] = homonym_added
        update_quality_and_manifest(
            old_count=old_count,
            added=enrichment_count,
            new_total=new_total,
            run_kpis={
                "INSERTED_FIRST_RUN": first.get("inserted", 0),
                "INSERTED_SECOND_RUN": second.get("inserted", 0),
                "idempotent": second.get("inserted", 0) == 0,
            },
        )

    state = IntegrationState(
        executed=True,
        message=(
            "Intégration contrôlée NCI exécutée (couche enrichment idempotente)."
            if apply
            else "Classification NCI exécutée sans écriture."
        ),
        meta={
            "engine": ENGINE_VERSION,
            "generated_at": _now(),
            "pre_integration_state": pre,
            "policy": {
                "distance_never_accepts_or_rejects": True,
                "name_alone_never_merges_across_territories": True,
                "territorial_identity_primary": True,
                "base_kmz_untouched": True,
            },
            "geometry_bounds_rdc": {
                "lat": [RDC_LAT_MIN, RDC_LAT_MAX],
                "lon": [RDC_LON_MIN, RDC_LON_MAX],
            },
        },
        kpis=kpis,
        rows=classified["results"],
        inserted_ids=[canonical_id_for(o) for o in classified["to_integrate"][:50]],
        performance={"elapsed_ms": round((time.time() - started) * 1000, 1)},
    )
    global _STATE
    _STATE = state

    if write_cache:
        RUN_CACHE_JSON.parent.mkdir(parents=True, exist_ok=True)
        RUN_CACHE_JSON.write_text(
            json.dumps(
                {
                    "meta": state.meta,
                    "kpis": state.kpis,
                    "sample_new": [
                        r
                        for r in state.rows
                        if r.get("classification") == "NEW_LOCALITY_WITH_VALID_GEOMETRY"
                    ][:40],
                    "sample_already": [
                        r for r in state.rows if r.get("classification") == "ALREADY_IN_REFERENTIAL"
                    ][:20],
                    "note": "Derived — raw NCI sources immutable — official KMZ base untouched",
                },
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )
    return state


def status_payload() -> dict[str, Any]:
    st = get_state()
    if not st.executed:
        return {"executed": False, "engine": ENGINE_VERSION, "message": "Aucune intégration exécutée"}
    return {
        "executed": True,
        "message": st.message,
        "kpis": st.kpis,
        "meta": st.meta,
        "performance": st.performance,
    }
