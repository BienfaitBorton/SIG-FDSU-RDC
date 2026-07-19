"""Intégration contrôlée RGC → référentiel national groupements (+ liens localités).

Règles :
- base historique `groupement_referential_official.json` intacte ;
- nouveaux groupements dans `groupement_referential_rgc_enrichment.json` ;
- enrichissements d'identité (codes / géométries alternatives) dans crosswalk ;
- liens Groupement→Localité confirmés dans overlay localités (sans créer de localité) ;
- candidats localités RGC (Localite_p) audités, non intégrés en masse ;
- égalité analytique après intégration (provenance = métadonnée) ;
- idempotence : second run = 0 inserts.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from api.services.nire import locality_controlled_integration as lci
from api.services.nire import rgc_groupements_localities_audit as rgc

ENGINE_VERSION = "nire-groupement-rgc-controlled-integration-1.0.0"
ROOT = Path(__file__).resolve().parents[3]

OFFICIAL_JSON = ROOT / "data" / "reports" / "groupement_official" / "groupement_referential_official.json"
ENRICHMENT_JSON = ROOT / "data" / "reports" / "groupement_official" / "groupement_referential_rgc_enrichment.json"
CROSSWALK_JSON = ROOT / "data" / "reports" / "groupement_official" / "groupement_rgc_crosswalk.json"
MANIFEST_JSON = ROOT / "data" / "reports" / "groupement_official" / "groupement_referential_national_manifest.json"
LINKS_JSON = ROOT / "data" / "reports" / "locality_official" / "locality_groupement_links_rgc.json"
CANDIDATES_AUDIT_JSON = ROOT / "data" / "reports" / "locality_official" / "locality_rgc_candidates_audit_v1.json"
REGISTRY_JSON = ROOT / "data" / "reports" / "national_counter_registry.json"
RUN_CACHE_JSON = ROOT / "data" / "cache" / "nire_groupement_rgc_controlled_integration_v1.json"
AMBIGUOUS_LINKS_JSON = ROOT / "data" / "reports" / "locality_official" / "locality_groupement_links_rgc_ambiguous.json"

RGC_MILLESIME = "2010-09-22"
REFERENCE_TARGET_INDICATIVE = 6053


@dataclass
class IntegrationState:
    executed: bool = False
    message: str = ""
    meta: dict[str, Any] = field(default_factory=dict)
    kpis: dict[str, Any] = field(default_factory=dict)
    groupements: dict[str, Any] = field(default_factory=dict)
    links: dict[str, Any] = field(default_factory=dict)
    candidates: dict[str, Any] = field(default_factory=dict)
    idempotence: dict[str, Any] = field(default_factory=dict)
    performance: dict[str, Any] = field(default_factory=dict)


_STATE = IntegrationState()


def get_state() -> IntegrationState:
    return _STATE


def reset_state() -> None:
    global _STATE
    _STATE = IntegrationState()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _token(value: Any) -> str:
    text = _norm(value).upper().replace(" ", "_")
    return re.sub(r"[^A-Z0-9_]+", "", text) or "INCONNU"


def _filled(value: Any) -> bool:
    if value is None:
        return False
    s = str(value).strip()
    return bool(s) and s.lower() not in {"none", "null", "nan", "0", "0.0"}


def file_sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_official_groupements() -> list[dict[str, Any]]:
    if not OFFICIAL_JSON.exists():
        return []
    return list(json.loads(OFFICIAL_JSON.read_text(encoding="utf-8")).get("groupement_referential") or [])


def load_enrichment_doc() -> dict[str, Any]:
    if not ENRICHMENT_JSON.exists():
        return {
            "source": "rgc_controlled_integration",
            "original_producer": "Référentiel Géographique Commun (RGC RDC)",
            "millesime": RGC_MILLESIME,
            "generated_at": None,
            "engine": ENGINE_VERSION,
            "groupement_referential": [],
            "by_canonical_id": {},
            "integration_runs": [],
        }
    return json.loads(ENRICHMENT_JSON.read_text(encoding="utf-8"))


def load_crosswalk_doc() -> dict[str, Any]:
    if not CROSSWALK_JSON.exists():
        return {
            "source": "rgc_controlled_integration",
            "generated_at": None,
            "engine": ENGINE_VERSION,
            "mappings": [],
            "by_fdsu_id": {},
            "integration_runs": [],
        }
    return json.loads(CROSSWALK_JSON.read_text(encoding="utf-8"))


def load_links_doc() -> dict[str, Any]:
    if not LINKS_JSON.exists():
        return {
            "source": "rgc_controlled_integration",
            "generated_at": None,
            "engine": ENGINE_VERSION,
            "links_by_locality_canonical_id": {},
            "integration_runs": [],
        }
    return json.loads(LINKS_JSON.read_text(encoding="utf-8"))


def load_national_groupement_items(*, include_enrichment: bool = True) -> list[dict[str, Any]]:
    """Référentiel unifié = historique (+ enrichissement RGC) + enrichissements identity crosswalk."""
    items: list[dict[str, Any]] = []
    official = load_official_groupements()
    crosswalk = load_crosswalk_doc() if include_enrichment else {}
    by_fdsu = crosswalk.get("by_fdsu_id") or {}

    for item in official:
        row = dict(item)
        if include_enrichment:
            cid = str(row.get("canonical_id") or "")
            enrich = by_fdsu.get(cid)
            if enrich:
                row = _merge_historical_enrichment(row, enrich)
        items.append(row)

    if include_enrichment:
        enr = load_enrichment_doc()
        items.extend(enr.get("groupement_referential") or [])
    return items


def national_groupement_counts(*, include_enrichment: bool = True) -> dict[str, int]:
    historical = len(load_official_groupements())
    enrichment = len(load_enrichment_doc().get("groupement_referential") or []) if include_enrichment else 0
    return {
        "historical_count": historical,
        "enrichment_count": enrichment,
        "total_count": historical + enrichment if include_enrichment else historical,
    }


def national_groupement_count(*, include_enrichment: bool = True) -> int:
    return national_groupement_counts(include_enrichment=include_enrichment)["total_count"]


def _merge_historical_enrichment(row: dict[str, Any], enrich: dict[str, Any]) -> dict[str, Any]:
    """Enrichit identité historique sans écraser géométrie valide."""
    out = dict(row)
    meta = dict(out.get("metadata") or {})
    ext = dict(meta.get("extended_data") or {})
    if enrich.get("rgc_groupment_code") and not _filled(ext.get("CODE_GRPT")):
        ext["CODE_GRPT"] = enrich["rgc_groupment_code"]
    if enrich.get("rgc_pcode") and not _filled(ext.get("PCODE")):
        ext["PCODE"] = enrich["rgc_pcode"]
    meta["extended_data"] = ext
    meta["rgc_crosswalk"] = {
        "rgc_groupment_code": enrich.get("rgc_groupment_code"),
        "rgc_pcode": enrich.get("rgc_pcode"),
        "classification": enrich.get("classification"),
        "geometry_role_rgc": "REPRESENTATIVE_POINT",
        "geometry_provenance_rgc": "RGC",
        "geometry_source_date": RGC_MILLESIME,
    }
    alt = enrich.get("alternative_geometry")
    if alt and out.get("geometry"):
        meta["alternative_geometries"] = list(meta.get("alternative_geometries") or []) + [alt]
    elif alt and not out.get("geometry"):
        out["geometry"] = alt.get("geometry")
        out["geometry_role"] = "REPRESENTATIVE_POINT"
        out["geometry_provenance"] = "RGC"
    out["metadata"] = meta
    return out


def apply_groupement_links_to_localities(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Applique l'overlay de liens RGC sur les localités fusionnées (sans créer d'entité)."""
    links = load_links_doc().get("links_by_locality_canonical_id") or {}
    if not links:
        return items
    out = []
    for item in items:
        cid = str(item.get("canonical_id") or "")
        link = links.get(cid)
        if not link:
            out.append(item)
            continue
        row = dict(item)
        if not _filled(row.get("groupement")) and _filled(link.get("groupement")):
            row["groupement"] = link["groupement"]
        meta = dict(row.get("metadata") or {})
        meta["rgc_groupement_link"] = link
        row["metadata"] = meta
        out.append(row)
    return out


def canonical_id_for_rgc(r: dict[str, Any]) -> str:
    parent = _token(r.get("secteur_chefferie") or "COLLECTIVITE_INCONNUE")
    name = _token(r.get("source_name") or "SANS_NOM")
    code = r.get("rgc_groupment_code") or "SANS_CODE"
    base = f"RDC-RGC-GRPT-{parent}-{name}-{code}"
    # Stabilise collisions d'identité via hash court de la clé audit
    ik = r.get("identity_key") or f"{_norm(r.get('source_name'))}|{_norm(r.get('territoire'))}|{_norm(r.get('secteur_chefferie'))}|{code}"
    digest = hashlib.sha1(ik.encode("utf-8")).hexdigest()[:8].upper()
    return f"{base}-{digest}"


def build_groupement_record(r: dict[str, Any], *, classification: str) -> dict[str, Any]:
    rp = r.get("representative_point") or {}
    lat, lon = rp.get("lat"), rp.get("lon")
    cid = canonical_id_for_rgc(r)
    origine = None
    origins = r.get("origine_points") or []
    for o in origins:
        if _filled(o):
            origine = o
            break
    return {
        "canonical_id": cid,
        "nom": r.get("source_name"),
        "niveau": "Groupement",
        "collectivite_parent": r.get("secteur_chefferie"),
        "type_collectivite_parent": None,
        "territoire": r.get("territoire"),
        "province": None,
        "zone_fdsu": "INCONNU",
        "code_officiel": r.get("rgc_groupment_code"),
        "geometry": {
            "type": "Point",
            "coordinates": [float(lon), float(lat), 0.0],
        },
        "geometry_role": "REPRESENTATIVE_POINT",
        "geometry_provenance": "RGC",
        "geometry_source_date": RGC_MILLESIME,
        "geometry_origin": origine,
        "source": "RGC",
        "provenance": "rgc",
        "statut": "rgc_integrated",
        "qualite": None,
        "nire_classification": classification,
        "integration_date": _now(),
        "metadata": {
            "engine": ENGINE_VERSION,
            "identity_key": r.get("identity_key"),
            "rgc_groupment_code": r.get("rgc_groupment_code"),
            "rgc_pcode": r.get("rgc_pcode_sample"),
            "locality_count_source": r.get("locality_count"),
            "extended_data": {
                "CODE_GRPT": r.get("rgc_groupment_code"),
                "PCODE": r.get("rgc_pcode_sample"),
                "TERRITOIRE": r.get("territoire"),
                "COLLECTIV": r.get("secteur_chefferie"),
                "ORIGINE": origine,
                "NOM_RGC": r.get("source_name"),
            },
            "note": (
                "Point représentatif RGC (chef-lieu ou localité du groupement). "
                "Ce n'est PAS une frontière administrative officielle."
            ),
        },
    }


def _load_rgc_inventory() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Charge Localite / Localite_p et dérive inventaire groupements."""
    localite = rgc.load_shapefile_rows(rgc.LOCALITE_SHP_DIR / "Localite")
    localite_p = (
        rgc.load_shapefile_rows(rgc.LOCALITE_SHP_DIR / "Localite_p")
        if (rgc.LOCALITE_SHP_DIR / "Localite_p.shp").exists()
        else []
    )
    source = localite_p if localite_p else localite
    inventory = rgc.derive_rgc_groupements_from_localities(source)
    return localite, localite_p, inventory


def persist_enrichment(records: list[dict[str, Any]], *, dry_run: bool = False) -> dict[str, Any]:
    doc = load_enrichment_doc()
    by_id: dict[str, dict[str, Any]] = {
        str(x.get("canonical_id")): x for x in (doc.get("groupement_referential") or []) if x.get("canonical_id")
    }
    # Also index by identity to prevent orthographic re-inserts
    identity_keys = {
        str((x.get("metadata") or {}).get("identity_key"))
        for x in by_id.values()
        if (x.get("metadata") or {}).get("identity_key")
    }
    inserted = 0
    skipped = 0
    new_records: list[dict[str, Any]] = []
    for rec in records:
        cid = str(rec.get("canonical_id"))
        ik = str((rec.get("metadata") or {}).get("identity_key") or "")
        if cid in by_id or (ik and ik in identity_keys):
            skipped += 1
            continue
        by_id[cid] = rec
        if ik:
            identity_keys.add(ik)
        new_records.append(rec)
        inserted += 1

    if not dry_run:
        if inserted == 0 and ENRICHMENT_JSON.exists():
            return {
                "inserted": 0,
                "skipped_existing": skipped,
                "total_enrichment": len(by_id),
                "new_records_sample": [],
                "skipped_rewrite": True,
            }
        doc["groupement_referential"] = list(by_id.values())
        doc["by_canonical_id"] = {cid: True for cid in by_id}
        doc["generated_at"] = _now()
        doc["engine"] = ENGINE_VERSION
        doc["count"] = len(by_id)
        doc["millesime"] = RGC_MILLESIME
        runs = list(doc.get("integration_runs") or [])
        runs.append({"at": _now(), "inserted": inserted, "skipped_existing": skipped, "total_after": len(by_id)})
        doc["integration_runs"] = runs[-20:]
        ENRICHMENT_JSON.parent.mkdir(parents=True, exist_ok=True)
        ENRICHMENT_JSON.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    return {
        "inserted": inserted,
        "skipped_existing": skipped,
        "total_enrichment": len(by_id),
        "new_records_sample": [
            {"canonical_id": r.get("canonical_id"), "nom": r.get("nom"), "territoire": r.get("territoire")}
            for r in new_records[:8]
        ],
    }


def persist_crosswalk(mappings: list[dict[str, Any]], *, dry_run: bool = False) -> dict[str, Any]:
    doc = load_crosswalk_doc()
    by_fdsu: dict[str, dict[str, Any]] = dict(doc.get("by_fdsu_id") or {})
    inserted = 0
    skipped = 0
    for m in mappings:
        fid = str(m.get("fdsu_groupment_id") or "")
        if not fid:
            continue
        existing = by_fdsu.get(fid)
        if existing and existing.get("rgc_groupment_code") == m.get("rgc_groupment_code"):
            skipped += 1
            continue
        if existing:
            # merge non-destructively
            merged = dict(existing)
            for k, v in m.items():
                if v and not merged.get(k):
                    merged[k] = v
            by_fdsu[fid] = merged
            skipped += 1  # not a new identity
            continue
        by_fdsu[fid] = m
        inserted += 1

    if not dry_run:
        if inserted == 0 and CROSSWALK_JSON.exists():
            return {"inserted": inserted, "skipped_existing": skipped, "total_mappings": len(by_fdsu), "skipped_rewrite": True}
        doc["by_fdsu_id"] = by_fdsu
        doc["mappings"] = list(by_fdsu.values())
        doc["generated_at"] = _now()
        doc["engine"] = ENGINE_VERSION
        doc["count"] = len(by_fdsu)
        runs = list(doc.get("integration_runs") or [])
        runs.append({"at": _now(), "inserted": inserted, "skipped_existing": skipped, "total_after": len(by_fdsu)})
        doc["integration_runs"] = runs[-20:]
        CROSSWALK_JSON.parent.mkdir(parents=True, exist_ok=True)
        CROSSWALK_JSON.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"inserted": inserted, "skipped_existing": skipped, "total_mappings": len(by_fdsu)}


def collect_link_candidates(
    rgc_rows: list[dict[str, Any]],
    fdsu_localities: list[dict[str, Any]],
) -> dict[str, Any]:
    """Prépare liens auto (NEW + CROSS_SOURCE_CONFIRMED) et ambiguës (revue)."""
    by_pcode: dict[str, dict[str, Any]] = {}
    by_name_terr: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for loc in fdsu_localities:
        md = (loc.get("metadata") or {}).get("extended_data") or {}
        p = md.get("PCODE") or loc.get("pcode")
        if _filled(p):
            by_pcode[str(p).split(".")[0]] = loc
        by_name_terr[f"{_norm(loc.get('nom'))}|{_norm(loc.get('territoire'))}"].append(loc)

    auto: dict[str, dict[str, Any]] = {}
    ambiguous: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()

    for r in rgc_rows:
        if not _filled(r.get("GROUPEMENT")) and not _filled(r.get("CODE_GRPT")):
            continue
        pkey = str(int(float(r["PCODE"]))) if _filled(r.get("PCODE")) else None
        loc = by_pcode.get(pkey) if pkey else None
        match_mode = "pcode" if loc else None
        if loc is None:
            hits = by_name_terr.get(f"{_norm(r.get('NOM1'))}|{_norm(r.get('TERRITOIRE'))}") or []
            if len(hits) > 1:
                counts["AMBIGUOUS_MULTI_HIT"] += 1
                ambiguous.append(
                    {
                        "reason": "MULTI_NAME_TERRITORY_HIT",
                        "nom1": r.get("NOM1"),
                        "territoire": r.get("TERRITOIRE"),
                        "groupement_rgc": r.get("GROUPEMENT"),
                        "hits": len(hits),
                    }
                )
                continue
            if len(hits) == 1:
                loc = hits[0]
                match_mode = "name_territory"
        if loc is None:
            continue

        lid = str(loc.get("canonical_id") or "")
        if not lid or lid in auto:
            continue

        rgc_g = str(r.get("GROUPEMENT") or "").strip()
        existing = loc.get("groupement")
        if _filled(existing):
            if _norm(existing) == _norm(rgc_g):
                status = "CROSS_SOURCE_CONFIRMED"
                counts["CROSS_SOURCE_CONFIRMED"] += 1
            else:
                counts["AMBIGUOUS_CONFLICT"] += 1
                ambiguous.append(
                    {
                        "reason": "EXISTING_GROUPMENT_CONFLICT",
                        "locality_canonical_id": lid,
                        "locality_name": loc.get("nom"),
                        "existing_groupement": existing,
                        "groupement_rgc": rgc_g,
                    }
                )
                continue
        else:
            if not _filled(rgc_g):
                continue
            status = "NEW_FROM_RGC"
            counts["NEW_FROM_RGC"] += 1

        auto[lid] = {
            "locality_canonical_id": lid,
            "locality_name": loc.get("nom"),
            "territoire": loc.get("territoire") or r.get("TERRITOIRE"),
            "groupement": rgc_g if _filled(rgc_g) else existing,
            "groupement_code_rgc": str(int(float(r["CODE_GRPT"]))) if _filled(r.get("CODE_GRPT")) else None,
            "rgc_pcode": pkey,
            "link_status": status,
            "match_mode": match_mode,
            "provenance": "RGC",
            "geometry_role_note": "ADMINISTRATIVE_MEMBERSHIP via attribut RGC — pas proximité spatiale",
            "millesime": RGC_MILLESIME,
            "engine": ENGINE_VERSION,
        }

    return {
        "auto_links": auto,
        "ambiguous": ambiguous,
        "counts": dict(counts),
        "NEW_CONFIRMED_OR_NEW_LINKS": len(auto),
        "NEW_FROM_RGC": counts.get("NEW_FROM_RGC", 0),
        "CROSS_SOURCE_CONFIRMED": counts.get("CROSS_SOURCE_CONFIRMED", 0),
        "AMBIGUOUS": len(ambiguous),
    }


def persist_links(auto_links: dict[str, dict[str, Any]], *, dry_run: bool = False) -> dict[str, Any]:
    doc = load_links_doc()
    by_id: dict[str, dict[str, Any]] = dict(doc.get("links_by_locality_canonical_id") or {})
    inserted = 0
    skipped = 0
    for lid, link in auto_links.items():
        existing = by_id.get(lid)
        if existing and existing.get("groupement") == link.get("groupement") and existing.get("link_status") == link.get(
            "link_status"
        ):
            skipped += 1
            continue
        if existing:
            skipped += 1
            continue
        by_id[lid] = link
        inserted += 1

    if not dry_run:
        if inserted == 0 and LINKS_JSON.exists():
            return {"inserted": 0, "skipped_existing": skipped, "total_links": len(by_id), "skipped_rewrite": True}
        doc["links_by_locality_canonical_id"] = by_id
        doc["generated_at"] = _now()
        doc["engine"] = ENGINE_VERSION
        doc["count"] = len(by_id)
        runs = list(doc.get("integration_runs") or [])
        runs.append({"at": _now(), "inserted": inserted, "skipped_existing": skipped, "total_after": len(by_id)})
        doc["integration_runs"] = runs[-20:]
        LINKS_JSON.parent.mkdir(parents=True, exist_ok=True)
        LINKS_JSON.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    return {"inserted": inserted, "skipped_existing": skipped, "total_links": len(by_id)}


def audit_rgc_locality_candidates(localite_p: list[dict[str, Any]], fdsu_localities: list[dict[str, Any]]) -> dict[str, Any]:
    """Audit approfondi des candidats Localite_p sans intégration."""
    match = rgc.match_localities(localite_p, fdsu_localities)
    samples = {
        "NEW_WITH_VALID_GEOMETRY": match.get("samples_new") or [],
    }
    payload = {
        "generated_at": _now(),
        "engine": ENGINE_VERSION,
        "audit_only": True,
        "no_integration": True,
        "RGC_LOCALITY_CANDIDATES_ANALYZED": match.get("RGC_ROWS_SCANNED"),
        "ALREADY_IN_47130": match.get("ALREADY_IN_LOCALITY_REFERENTIAL"),
        "EXISTING_VARIANTS": match.get("EXISTING_LOCALITY_VARIANT"),
        "NEW_WITH_VALID_GEOMETRY": match.get("NEW_RGC_LOCALITY_WITH_VALID_GEOMETRY"),
        "NEW_VILLAGE_WITH_VALID_GEOMETRY": match.get("NEW_RGC_VILLAGE_WITH_VALID_GEOMETRY"),
        "AMBIGUOUS": match.get("AMBIGUOUS_RGC_LOCALITY"),
        "HOMONYM_DISTINCT": match.get("HOMONYM_DISTINCT_RGC_LOCALITY"),
        "DUPLICATES": match.get("DUPLICATE_RGC_LOCALITY"),
        "classification_counts": match.get("classification_counts"),
        "samples": samples,
        "recommendation": (
            "Intégration future candidate-par-candidate après revue NIRE d'identité. "
            "Millésime RGC ~2010 — ne pas intégrer en masse sans validation. "
            "Toute entité absente des 47 130, géolocalisée et distincte peut combler le gap."
        ),
    }
    CANDIDATES_AUDIT_JSON.parent.mkdir(parents=True, exist_ok=True)
    CANDIDATES_AUDIT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def _link_coverage_stats(fdsu_localities: list[dict[str, Any]]) -> dict[str, Any]:
    """Couverture après application overlay (simulation sur copie)."""
    total = len(fdsu_localities)
    before = sum(1 for loc in fdsu_localities if _filled(loc.get("groupement")))
    enriched = apply_groupement_links_to_localities(fdsu_localities)
    after = sum(1 for loc in enriched if _filled(loc.get("groupement")))
    return {
        "LOCALITIES_WITH_GROUPMENT_BEFORE": before,
        "LOCALITIES_WITH_GROUPMENT_AFTER": after,
        "LOCALITIES_WITHOUT_GROUPMENT_AFTER": max(0, total - after),
        "GROUPMENT_LINK_COVERAGE_RATE_BEFORE": round(before / total, 4) if total else 0,
        "GROUPMENT_LINK_COVERAGE_RATE_AFTER": round(after / total, 4) if total else 0,
        "TOTAL_LOCALITIES": total,
    }


def update_registry_and_manifest(*, counts: dict[str, int], run_kpis: dict[str, Any]) -> None:
    hist = counts["historical_count"]
    enr = counts["enrichment_count"]
    total = counts["total_count"]
    gap = max(0, REFERENCE_TARGET_INDICATIVE - total)
    coverage = round(100.0 * total / REFERENCE_TARGET_INDICATIVE, 2) if REFERENCE_TARGET_INDICATIVE else 0

    manifest = {
        "generated_at": _now(),
        "engine": ENGINE_VERSION,
        "OLD_GROUPMENTS": hist,
        "NEW_GROUPMENTS_ADDED": enr,
        "NEW_TOTAL_GROUPMENTS": total,
        "base_file": str(OFFICIAL_JSON.relative_to(ROOT)).replace("\\", "/"),
        "enrichment_file": str(ENRICHMENT_JSON.relative_to(ROOT)).replace("\\", "/"),
        "base_sha256": file_sha256(OFFICIAL_JSON),
        "enrichment_sha256": file_sha256(ENRICHMENT_JSON),
        "base_untouched": True,
        "analytical_equality": True,
        "geometry_role_rgc": "REPRESENTATIVE_POINT",
        "millesime_rgc": RGC_MILLESIME,
        "kpis": run_kpis,
    }
    MANIFEST_JSON.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_JSON.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    if REGISTRY_JSON.exists():
        try:
            reg = json.loads(REGISTRY_JSON.read_text(encoding="utf-8"))
            counters = reg.setdefault("registre_national_des_compteurs", {})
            g = counters.setdefault("groupements", {})
            g["attendu_officiel"] = REFERENCE_TARGET_INDICATIVE
            g["trouve"] = total
            g["nombre"] = total
            g["historique_kmz"] = hist
            g["enrichissement_rgc"] = enr
            g["couverture"] = f"{coverage}%"
            g["statut"] = "enrichi"
            g["validation"] = "non publié"
            g["comparaison_reference"] = (
                f"Référentiel enrichi = historique KMZ {hist} + RGC {enr}"
            )
            g["provenance"] = {
                "historique": "Groupements.kmz → groupement_referential_official.json",
                "enrichissement": "RGC → groupement_referential_rgc_enrichment.json",
                "fusion": "dynamique au chargement",
                "geometry_role_rgc": "REPRESENTATIVE_POINT",
                "millesime_rgc": RGC_MILLESIME,
            }
            g["recommandation"] = (
                "Enrichissement RGC contrôlé — points représentatifs, pas frontières officielles. "
                f"Gap résiduel indicatif vs {REFERENCE_TARGET_INDICATIVE}: {gap}."
            )
            reg["source_groupements"] = "Groupements.kmz + RGC enrichment"
            reg["generated_at_groupement_rgc_integration"] = _now()
            REGISTRY_JSON.write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass


def run_controlled_integration(*, apply: bool = True, write_cache: bool = True) -> IntegrationState:
    started = time.time()
    reset_state()
    st = get_state()
    st.meta = {
        "engine": ENGINE_VERSION,
        "generated_at": _now(),
        "apply": apply,
        "analytical_equality": True,
        "no_raw_source_modification": True,
        "locality_candidates_not_integrated": True,
        "millesime_rgc": RGC_MILLESIME,
    }

    if not rgc.LOCALITE_ZIP.exists():
        st.message = "Localite.zip RGC absent — acquisition requise."
        st.executed = False
        return st

    print("[grp-rgc] load shapefiles…", flush=True)
    localite, localite_p, inventory = _load_rgc_inventory()
    official = load_official_groupements()
    old_count = len(official)

    print(f"[grp-rgc] match groupements (rgc={len(inventory)}, fdsu={old_count})…", flush=True)
    match = rgc.match_groupements(official, inventory)

    # Build records for NEW only
    # Rebuild classification per inventory item via match classified samples + full pass
    classified_new = match.get("classified_new_sample") or []
    # Full NEW set: re-derive from match by scanning inventory with same logic
    new_records: list[dict[str, Any]] = []
    crosswalk_mappings: list[dict[str, Any]] = []

    # Index match results by re-running classification row-level via match_groupements classified list
    # Use inventory + match classification by re-calling internal logic:
    fdsu_by_code: dict[str, dict[str, Any]] = {}
    fdsu_by_key: dict[str, dict[str, Any]] = {}
    for g in official:
        md = (g.get("metadata") or {}).get("extended_data") or {}
        code = md.get("CODE_GRPT") or g.get("code_officiel")
        if _filled(code):
            try:
                fdsu_by_code[str(int(float(code)))] = g
            except (TypeError, ValueError):
                fdsu_by_code[str(code)] = g
        key = "|".join([_norm(g.get("nom")), _norm(g.get("territoire")), _norm(g.get("collectivite_parent"))])
        fdsu_by_key[key] = g

    names_to_terrs: dict[str, set[str]] = defaultdict(set)
    by_name_terr: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for g in official:
        nn = _norm(g.get("nom"))
        nt = _norm(g.get("territoire"))
        names_to_terrs[nn].add(nt)
        by_name_terr[f"{nn}|{nt}"].append(g)

    already = variants = ambiguous = new_valid = homonym = 0
    for r in inventory:
        code = r.get("rgc_groupment_code")
        name = r.get("normalized_name")
        terr = _norm(r.get("territoire"))
        coll = _norm(r.get("secteur_chefferie"))
        key = f"{name}|{terr}|{coll}"
        fdsu_hit = None
        cls = None

        if code and str(code) in fdsu_by_code:
            cls = "ALREADY_IN_GROUPMENT_REFERENTIAL"
            fdsu_hit = fdsu_by_code[str(code)]
            already += 1
        elif key in fdsu_by_key:
            cls = "ALREADY_IN_GROUPMENT_REFERENTIAL"
            fdsu_hit = fdsu_by_key[key]
            already += 1
        else:
            cands = by_name_terr.get(f"{name}|{terr}") or []
            if cands:
                # variant / ambiguous — enrich, don't insert
                from difflib import SequenceMatcher

                best = max(
                    (SequenceMatcher(None, coll, _norm(c.get("collectivite_parent"))).ratio(), c) for c in cands
                )
                if best[0] >= 0.85:
                    cls = "EXISTING_GROUPMENT_VARIANT"
                    fdsu_hit = best[1]
                    variants += 1
                else:
                    cls = "AMBIGUOUS_RGC_GROUPMENT"
                    ambiguous += 1
            elif r.get("has_valid_geometry"):
                other = names_to_terrs.get(name) or set()
                if name and other and terr not in other:
                    homonym += 1
                cls = "NEW_RGC_GROUPMENT_WITH_VALID_GEOMETRY"
                new_valid += 1
                new_records.append(build_groupement_record(r, classification=cls))
            else:
                cls = "AMBIGUOUS_RGC_GROUPMENT"
                ambiguous += 1

        if fdsu_hit and cls in {"ALREADY_IN_GROUPMENT_REFERENTIAL", "EXISTING_GROUPMENT_VARIANT"}:
            rp = r.get("representative_point") or {}
            alt = None
            if rp.get("lat") is not None and rp.get("lon") is not None:
                alt = {
                    "geometry": {
                        "type": "Point",
                        "coordinates": [float(rp["lon"]), float(rp["lat"]), 0.0],
                    },
                    "geometry_role": "REPRESENTATIVE_POINT",
                    "geometry_provenance": "RGC",
                    "geometry_source_date": RGC_MILLESIME,
                }
            crosswalk_mappings.append(
                {
                    "fdsu_groupment_id": fdsu_hit.get("canonical_id"),
                    "rgc_groupment_code": code,
                    "rgc_pcode": r.get("rgc_pcode_sample"),
                    "classification": cls,
                    "rgc_name": r.get("source_name"),
                    "alternative_geometry": alt,
                }
            )

    print(f"[grp-rgc] NEW candidates={len(new_records)} crosswalk={len(crosswalk_mappings)}", flush=True)

    # Localities + links (sans intégrer les 3814 candidats Localite_p)
    print("[grp-rgc] load localities + prepare links…", flush=True)
    # Base fusion sans overlay liens (mesures BEFORE dynamiques)
    base_loc = []
    if lci.OFFICIAL_JSON.exists():
        base_loc.extend(json.loads(lci.OFFICIAL_JSON.read_text(encoding="utf-8")).get("locality_referential") or [])
    if lci.ENRICHMENT_JSON.exists():
        base_loc.extend(lci.load_enrichment_doc().get("locality_referential") or [])
    before_with = sum(1 for loc in base_loc if _filled(loc.get("groupement")))

    link_prep = collect_link_candidates(localite_p or localite, base_loc)

    first_g = {"inserted": 0, "skipped_existing": 0, "total_enrichment": 0}
    second_g = {"inserted": 0, "skipped_existing": 0, "total_enrichment": 0}
    first_x = {"inserted": 0, "skipped_existing": 0}
    second_x = {"inserted": 0, "skipped_existing": 0}
    first_l = {"inserted": 0, "skipped_existing": 0, "total_links": 0}
    second_l = {"inserted": 0, "skipped_existing": 0, "total_links": 0}

    if apply:
        print("[grp-rgc] persist first run…", flush=True)
        first_g = persist_enrichment(new_records, dry_run=False)
        first_x = persist_crosswalk(crosswalk_mappings, dry_run=False)
        first_l = persist_links(link_prep["auto_links"], dry_run=False)

        print("[grp-rgc] persist second run (idempotence)…", flush=True)
        second_g = persist_enrichment(new_records, dry_run=False)
        second_x = persist_crosswalk(crosswalk_mappings, dry_run=False)
        second_l = persist_links(link_prep["auto_links"], dry_run=False)

        AMBIGUOUS_LINKS_JSON.parent.mkdir(parents=True, exist_ok=True)
        AMBIGUOUS_LINKS_JSON.write_text(
            json.dumps(
                {
                    "generated_at": _now(),
                    "engine": ENGINE_VERSION,
                    "count": len(link_prep["ambiguous"]),
                    "items": link_prep["ambiguous"][:500],
                    "note": "Revue NIRE — non intégrés automatiquement",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    counts = national_groupement_counts(include_enrichment=True)
    coverage = _link_coverage_stats(base_loc)

    print("[grp-rgc] audit locality candidates (no integrate)…", flush=True)
    candidates = audit_rgc_locality_candidates(localite_p or localite, base_loc)

    run_kpis = {
        "OLD_GROUPMENTS": old_count,
        "RGC_GROUPMENTS_ANALYZED": len(inventory),
        "ALREADY_IN_REFERENTIAL": already,
        "EXISTING_VARIANTS": variants,
        "NEW_GROUPMENTS_INSERTED": first_g.get("inserted", 0),
        "HOMONYM_DISTINCT_INSERTED": homonym,  # subset of NEW
        "AMBIGUOUS_NOT_INSERTED": ambiguous,
        "NEW_TOTAL_GROUPMENTS": counts["total_count"],
        "historical_count": counts["historical_count"],
        "enrichment_count": counts["enrichment_count"],
        "total_count": counts["total_count"],
        **{k: coverage[k] for k in coverage},
        "NEW_CONFIRMED_GROUPMENT_LINKS": link_prep.get("NEW_FROM_RGC", 0),
        "CONFIRMED_GROUPMENT_LINKS_INSERTED": first_l.get("inserted", 0),
        "CROSS_SOURCE_CONFIRMED_RECORDED": link_prep.get("CROSS_SOURCE_CONFIRMED", 0),
        "AMBIGUOUS_GROUPMENT_LINKS_NOT_INSERTED": link_prep.get("AMBIGUOUS", 0),
        "GROUPMENTS_INSERTED_FIRST_RUN": first_g.get("inserted", 0),
        "GROUPMENTS_INSERTED_SECOND_RUN": second_g.get("inserted", 0),
        "LINKS_INSERTED_FIRST_RUN": first_l.get("inserted", 0),
        "LINKS_INSERTED_SECOND_RUN": second_l.get("inserted", 0),
        "CROSSWALK_INSERTED_FIRST_RUN": first_x.get("inserted", 0),
        "CROSSWALK_INSERTED_SECOND_RUN": second_x.get("inserted", 0),
    }

    if apply:
        update_registry_and_manifest(counts=counts, run_kpis=run_kpis)

    st.groupements = {
        "match_audit_kpis": {
            k: match.get(k)
            for k in (
                "NEW_RGC_GROUPMENT_WITH_VALID_GEOMETRY",
                "ALREADY_IN_GROUPMENT_REFERENTIAL",
                "EXISTING_GROUPMENT_VARIANT",
                "AMBIGUOUS_RGC_GROUPMENT",
                "HOMONYM_DISTINCT_RGC_GROUPMENT",
            )
        },
        "classified_new_sample": classified_new[:10],
        "inserted_sample": first_g.get("new_records_sample"),
    }
    st.links = {**link_prep.get("counts", {}), **coverage, "persist": first_l}
    st.candidates = {
        k: candidates.get(k)
        for k in (
            "RGC_LOCALITY_CANDIDATES_ANALYZED",
            "ALREADY_IN_47130",
            "EXISTING_VARIANTS",
            "NEW_WITH_VALID_GEOMETRY",
            "AMBIGUOUS",
            "HOMONYM_DISTINCT",
            "DUPLICATES",
            "recommendation",
        )
    }
    st.idempotence = {
        "GROUPMENTS_INSERTED_FIRST_RUN": first_g.get("inserted", 0),
        "GROUPMENTS_INSERTED_SECOND_RUN": second_g.get("inserted", 0),
        "LINKS_INSERTED_FIRST_RUN": first_l.get("inserted", 0),
        "LINKS_INSERTED_SECOND_RUN": second_l.get("inserted", 0),
        "ok": second_g.get("inserted", 0) == 0 and second_l.get("inserted", 0) == 0,
    }
    st.kpis = run_kpis
    st.performance = {"elapsed_s": round(time.time() - started, 2)}
    st.executed = True
    st.message = (
        f"Intégration RGC groupements: +{first_g.get('inserted', 0)} "
        f"(total={counts['total_count']}); liens +{first_l.get('inserted', 0)}; "
        f"candidats localités audités sans intégration."
    )

    if write_cache:
        RUN_CACHE_JSON.parent.mkdir(parents=True, exist_ok=True)
        RUN_CACHE_JSON.write_text(
            json.dumps(
                {
                    "meta": st.meta,
                    "kpis": st.kpis,
                    "groupements": st.groupements,
                    "links": st.links,
                    "candidates": st.candidates,
                    "idempotence": st.idempotence,
                    "performance": st.performance,
                    "message": st.message,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    print(f"[grp-rgc] done in {st.performance['elapsed_s']}s — {st.message}", flush=True)
    return st


def status_payload() -> dict[str, Any]:
    counts = national_groupement_counts(include_enrichment=True)
    return {
        "engine": ENGINE_VERSION,
        "executed": _STATE.executed,
        "message": _STATE.message,
        "counts": counts,
        "kpis": _STATE.kpis,
        "idempotence": _STATE.idempotence,
        "enrichment_exists": ENRICHMENT_JSON.exists(),
        "links_exists": LINKS_JSON.exists(),
        "base_sha256": file_sha256(OFFICIAL_JSON),
        "enrichment_sha256": file_sha256(ENRICHMENT_JSON),
        "raw_localite_sha256": file_sha256(rgc.LOCALITE_ZIP),
    }
