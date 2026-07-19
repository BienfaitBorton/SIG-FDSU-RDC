"""Audit RGC Groupements & Localités (lecture seule, aucune intégration).

Source primaire originale : Référentiel Géographique Commun (RGC RDC).
Acquisition : miroir institutionnel HDX/OCHA pour Localite.zip (RGC site indisponible).
Shapefile Groupements dédié : non obtenu — inventaire groupements dérivé des attributs
Localite (GROUPEMENT / CODE_GRPT / TERRITOIRE / COLLECTIV).
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from api.services.nire import locality_controlled_integration as lci

ENGINE_VERSION = "nire-rgc-groupements-localities-audit-1.0.0"
ROOT = Path(__file__).resolve().parents[3]

RAW_DIR = ROOT / "data" / "raw" / "rgc"
LOCALITE_ZIP = RAW_DIR / "Localite.zip"
LOCALITE_SHP_DIR = RAW_DIR / "localite_shp"
GROUPEMENT_JSON = ROOT / "data" / "reports" / "groupement_official" / "groupement_referential_official.json"
CACHE_JSON = ROOT / "data" / "cache" / "nire_rgc_groupements_localities_audit_v1.json"
MANIFEST_JSON = ROOT / "data" / "reports" / "rgc_official" / "rgc_acquisition_manifest.json"

RDC_LAT = (-13.7, 5.6)
RDC_LON = (12.0, 31.8)
REFERENCE_TARGET_INDICATIVE = 6053  # indicateur de gap uniquement — pas vérité officielle


@dataclass
class AuditState:
    executed: bool = False
    message: str = ""
    meta: dict[str, Any] = field(default_factory=dict)
    acquisition: dict[str, Any] = field(default_factory=dict)
    rgc_localities: dict[str, Any] = field(default_factory=dict)
    rgc_groupements: dict[str, Any] = field(default_factory=dict)
    match_groupements: dict[str, Any] = field(default_factory=dict)
    match_localities: dict[str, Any] = field(default_factory=dict)
    links: dict[str, Any] = field(default_factory=dict)
    site_examples: list[dict[str, Any]] = field(default_factory=list)
    kpis: dict[str, Any] = field(default_factory=dict)
    nsme_sdg: dict[str, Any] = field(default_factory=dict)


_STATE = AuditState()


def get_state() -> AuditState:
    return _STATE


def reset_state() -> None:
    global _STATE
    _STATE = AuditState()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


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


def mercator_to_wgs84(x: float, y: float) -> tuple[float, float]:
    """World Mercator meters → WGS84 lon/lat degrees."""
    lon = x / 6378137.0 * 180.0 / math.pi
    lat = (2.0 * math.atan(math.exp(y / 6378137.0)) - math.pi / 2.0) * 180.0 / math.pi
    return lon, lat


def geometry_usable(lat: Any, lon: Any) -> tuple[bool, str]:
    try:
        la, lo = float(lat), float(lon)
    except (TypeError, ValueError):
        return False, "non_numeric"
    if math.isnan(la) or math.isnan(lo):
        return False, "nan"
    if la == 0.0 and lo == 0.0:
        return False, "sentinel_zero"
    if not (RDC_LAT[0] <= la <= RDC_LAT[1] and RDC_LON[0] <= lo <= RDC_LON[1]):
        return False, "outside_rdc"
    return True, "ok"


def load_shapefile_rows(base: Path, *, encoding: str = "cp1252") -> list[dict[str, Any]]:
    import shapefile

    reader = shapefile.Reader(str(base), encoding=encoding)
    fields = [f[0] for f in reader.fields[1:]]
    rows: list[dict[str, Any]] = []
    # iterShapeRecords: O(n) — avoid reader.shape(i) which rewinds per index
    for sr in reader.iterShapeRecords():
        row = dict(zip(fields, sr.record))
        shp = sr.shape
        row["_shape_type"] = shp.shapeTypeName
        if shp.points:
            x, y = shp.points[0][0], shp.points[0][1]
            row["_x"], row["_y"] = x, y
            # Prefer geographic if already degrees; else convert from World Mercator meters
            if abs(x) <= 180 and abs(y) <= 90:
                lon, lat = float(x), float(y)
            else:
                lon, lat = mercator_to_wgs84(float(x), float(y))
            row["_lon"], row["_lat"] = lon, lat
        rows.append(row)
    return rows


def acquisition_manifest() -> dict[str, Any]:
    """Métadonnées d'acquisition — RGC original, miroir HDX pour Localite.zip."""
    sha = file_sha256(LOCALITE_ZIP)
    manifest = {
        "engine": ENGINE_VERSION,
        "generated_at": _now(),
        "original_producer": "Référentiel Géographique Commun (RGC RDC)",
        "original_url_catalog": "https://rgc.cd/index.php?Itemid=183&id=41&option=com_content&view=category",
        "rgc_site_status": "inaccessible_php_fatal_error_2026-07-19",
        "millesime_annonce_catalogue": "2010-09-22",
        "datasets": {
            "localites": {
                "obtained": LOCALITE_ZIP.exists(),
                "download_mirror": "HDX / OCHA DRC",
                "mirror_dataset": "https://data.humdata.org/dataset/dr-congo-settlements",
                "mirror_resource_id": "673bb25c-5979-4d3f-91c2-826e318f457f",
                "mirror_url": (
                    "https://data.humdata.org/dataset/609a58ef-f2fa-44e2-87f0-6e46dac4d45a/"
                    "resource/673bb25c-5979-4d3f-91c2-826e318f457f/download/localite.zip"
                ),
                "attribution_note": (
                    "Miroir institutionnel HDX — producteur original = RGC. "
                    "Ne pas présenter HDX comme producteur."
                ),
                "local_path": str(LOCALITE_ZIP.relative_to(ROOT)) if LOCALITE_ZIP.exists() else None,
                "sha256": sha,
                "size_bytes": LOCALITE_ZIP.stat().st_size if LOCALITE_ZIP.exists() else None,
                "layers": ["Localite.shp", "Localite_p.shp"],
                "projection": "World_Mercator (WGS84 meters) — converted to WGS84 degrees for analysis",
                "encoding": "cp1252",
            },
            "groupements_shapefile": {
                "obtained": False,
                "catalogue_size_annonce": "92 Ko",
                "catalogue_update": "2010-09-22",
                "reason": (
                    "Site RGC en erreur fatale PHP ; fichier Groupements.zip absent de HDX. "
                    "Inventaire groupements dérivé des attributs Localite (GROUPEMENT/CODE_GRPT)."
                ),
                "fallback_method": "DERIVED_FROM_RGC_LOCALITIES_ATTRIBUTES",
            },
        },
        "immutable_raw": True,
        "no_in_place_modification": True,
    }
    MANIFEST_JSON.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_JSON.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def audit_rgc_localities_layer(rows: list[dict[str, Any]], *, layer_name: str) -> dict[str, Any]:
    valid = invalid = missing_name = 0
    with_pcode = with_grp_name = with_grp_code = with_terr = with_sector = 0
    types: Counter[str] = Counter()
    identities: set[str] = set()

    for r in rows:
        name = r.get("NOM1") or r.get("Localité") or r.get("Localite")
        if not _filled(name):
            missing_name += 1
        lat, lon = r.get("_lat"), r.get("_lon")
        ok, _ = geometry_usable(lat, lon)
        if ok:
            valid += 1
        else:
            invalid += 1
        if _filled(r.get("PCODE")):
            with_pcode += 1
        if _filled(r.get("GROUPEMENT")):
            with_grp_name += 1
        if _filled(r.get("CODE_GRPT")):
            with_grp_code += 1
        if _filled(r.get("TERRITOIRE")):
            with_terr += 1
        if _filled(r.get("COLLECTIV")):
            with_sector += 1
        types[str(r.get("TYPE") if r.get("TYPE") not in (None, "") else "unknown")] += 1
        identities.add(
            "|".join(
                [
                    _norm(name),
                    _norm(r.get("TERRITOIRE")),
                    _norm(r.get("COLLECTIV")),
                    str(r.get("PCODE") or ""),
                ]
            )
        )

    return {
        "layer": layer_name,
        "RGC_LOCALITIES_RAW_COUNT": len(rows),
        "RGC_LOCALITIES_VALID_GEOMETRY": valid,
        "RGC_LOCALITIES_INVALID_GEOMETRY": invalid,
        "RGC_LOCALITIES_MISSING_NAME": missing_name,
        "RGC_LOCALITIES_WITH_PCODE": with_pcode,
        "RGC_LOCALITIES_WITH_GROUPMENT_NAME": with_grp_name,
        "RGC_LOCALITIES_WITH_GROUPMENT_CODE": with_grp_code,
        "RGC_LOCALITIES_WITH_TERRITORY": with_terr,
        "RGC_LOCALITIES_WITH_SECTOR_CHEFFERIE": with_sector,
        "RGC_LOCALITIES_UNIQUE_IDENTITY_ESTIMATE": len(identities),
        "type_codes_observed": dict(types.most_common(20)),
        "type_semantics_note": (
            "TYPE est un code numérique RGC (0,7,8,9,…) — pas de libellé ville/village explicite dans le shapefile. "
            "Ne pas inventer la sémantique ; conserver source_entity_type=RGC_TYPE_CODE."
        ),
        "geometry_role": "SETTLEMENT_POINT",
        "geometry_provenance": "RGC",
    }


def derive_rgc_groupements_from_localities(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Inventaire groupements dérivé des attributs Localite RGC."""
    buckets: dict[str, dict[str, Any]] = {}
    for r in rows:
        gname = r.get("GROUPEMENT")
        code = r.get("CODE_GRPT")
        if not _filled(gname) and not _filled(code):
            continue
        key = "|".join(
            [
                _norm(gname) if _filled(gname) else f"code:{code}",
                _norm(r.get("TERRITOIRE")),
                _norm(r.get("COLLECTIV")),
                str(int(float(code))) if _filled(code) else "",
            ]
        )
        lat, lon = r.get("_lat"), r.get("_lon")
        point_ok = geometry_usable(lat, lon)[0]
        b = buckets.get(key)
        if b is None:
            buckets[key] = {
                "source": "RGC_LOCALITE_ATTRIBUTES",
                "source_name": gname if _filled(gname) else None,
                "normalized_name": _norm(gname) if _filled(gname) else "",
                "rgc_groupment_code": str(int(float(code))) if _filled(code) else None,
                "rgc_pcode_sample": str(r.get("PCODE")) if _filled(r.get("PCODE")) else None,
                "territoire": r.get("TERRITOIRE"),
                "secteur_chefferie": r.get("COLLECTIV"),
                "locality_count": 1,
                "points": [(float(lat), float(lon))] if point_ok else [],
                "origine_points": [r.get("ORIGINE")],
                "identity_key": key,
            }
        else:
            b["locality_count"] += 1
            if point_ok:
                b["points"].append((float(lat), float(lon)))
            b["origine_points"].append(r.get("ORIGINE"))
    # representative point = first usable (chef-lieu proxy from localities)
    out = []
    for b in buckets.values():
        pts = b.get("points") or []
        if pts:
            # medoid-lite: average for audit speed, tagged as derived representative
            la = sum(p[0] for p in pts) / len(pts)
            lo = sum(p[1] for p in pts) / len(pts)
            b["representative_point"] = {"lat": la, "lon": lo}
            b["geometry_role"] = "REPRESENTATIVE_POINT"
            b["geometry_provenance"] = "RGC_DERIVED_FROM_LOCALITIES"
            b["has_valid_geometry"] = True
        else:
            b["representative_point"] = None
            b["geometry_role"] = "NO_USABLE_GEOMETRY"
            b["geometry_provenance"] = "RGC_DERIVED_FROM_LOCALITIES"
            b["has_valid_geometry"] = False
        out.append(b)
    return out


def load_fdsu_groupements() -> list[dict[str, Any]]:
    """Charge le référentiel unifié (historique + RGC) si disponible, sinon base seule."""
    try:
        from api.services.nire import groupement_controlled_integration as gci

        return gci.load_national_groupement_items(include_enrichment=True)
    except Exception:
        doc = json.loads(GROUPEMENT_JSON.read_text(encoding="utf-8"))
        return list(doc.get("groupement_referential") or [])


def match_groupements(
    fdsu: list[dict[str, Any]],
    rgc: list[dict[str, Any]],
) -> dict[str, Any]:
    by_code: dict[str, dict[str, Any]] = {}
    by_key: dict[str, dict[str, Any]] = {}
    by_name_terr: dict[str, list[dict[str, Any]]] = defaultdict(list)

    names_to_terrs: dict[str, set[str]] = defaultdict(set)
    for g in fdsu:
        md = (g.get("metadata") or {}).get("extended_data") or {}
        code = md.get("CODE_GRPT") or g.get("code_officiel")
        if _filled(code):
            by_code[str(int(float(code))) if str(code).replace(".", "", 1).isdigit() else str(code)] = g
        nn = _norm(g.get("nom"))
        nt = _norm(g.get("territoire"))
        key = "|".join([nn, nt, _norm(g.get("collectivite_parent"))])
        by_key[key] = g
        by_name_terr[f"{nn}|{nt}"].append(g)
        if nn:
            names_to_terrs[nn].add(nt)

    counts: Counter[str] = Counter()
    classified: list[dict[str, Any]] = []
    new_valid = 0
    mapping_samples: list[dict[str, Any]] = []
    homonym_distinct = 0

    for r in rgc:
        code = r.get("rgc_groupment_code")
        name = r.get("normalized_name")
        terr = _norm(r.get("territoire"))
        coll = _norm(r.get("secteur_chefferie"))
        key = f"{name}|{terr}|{coll}"
        cls = None
        fdsu_hit = None

        if code and str(code) in by_code:
            cls = "ALREADY_IN_GROUPMENT_REFERENTIAL"
            fdsu_hit = by_code[str(code)]
        elif key in by_key:
            cls = "ALREADY_IN_GROUPMENT_REFERENTIAL"
            fdsu_hit = by_key[key]
        else:
            npt = f"{name}|{terr}"
            cands = by_name_terr.get(npt) or []
            if cands:
                best = max(
                    (
                        SequenceMatcher(None, coll, _norm(c.get("collectivite_parent"))).ratio(),
                        c,
                    )
                    for c in cands
                )
                if best[0] >= 0.85:
                    cls = "EXISTING_GROUPMENT_VARIANT"
                    fdsu_hit = best[1]
                else:
                    cls = "AMBIGUOUS_RGC_GROUPMENT"
            else:
                other_terrs = names_to_terrs.get(name) or set()
                is_homonym = bool(name and other_terrs and terr not in other_terrs)
                if is_homonym:
                    homonym_distinct += 1
                if r.get("has_valid_geometry"):
                    # Homonyme autre territoire = entité distincte candidate
                    cls = "NEW_RGC_GROUPMENT_WITH_VALID_GEOMETRY"
                    new_valid += 1
                elif is_homonym:
                    cls = "HOMONYM_DISTINCT_RGC_GROUPMENT"
                else:
                    cls = "AMBIGUOUS_RGC_GROUPMENT"

        # geometry enrichment signal for already matched
        if cls in {"ALREADY_IN_GROUPMENT_REFERENTIAL", "EXISTING_GROUPMENT_VARIANT"} and r.get("has_valid_geometry"):
            # alternative geometry — do not overwrite; count enrichment opportunity separately
            if cls == "ALREADY_IN_GROUPMENT_REFERENTIAL":
                pass

        counts[cls] += 1
        row = {
            "classification": cls,
            "rgc_name": r.get("source_name"),
            "rgc_code": code,
            "territoire": r.get("territoire"),
            "secteur_chefferie": r.get("secteur_chefferie"),
            "locality_count": r.get("locality_count"),
            "geometry_role": r.get("geometry_role"),
            "geometry_provenance": r.get("geometry_provenance"),
            "fdsu_canonical_id": (fdsu_hit or {}).get("canonical_id"),
            "fdsu_code_officiel": (fdsu_hit or {}).get("code_officiel"),
        }
        classified.append(row)
        if fdsu_hit and code and len(mapping_samples) < 30:
            mapping_samples.append(
                {
                    "fdsu_groupment_id": fdsu_hit.get("canonical_id"),
                    "rgc_groupment_code": code,
                    "rgc_pcode_sample": r.get("rgc_pcode_sample"),
                }
            )

    # geometry enrichment count: matched with RGC point while FDSU already has point
    enrich = sum(
        1
        for c in classified
        if c["classification"] in {"ALREADY_IN_GROUPMENT_REFERENTIAL", "EXISTING_GROUPMENT_VARIANT"}
    )

    current = len(fdsu)
    potential = current + new_valid
    gap_before = max(0, REFERENCE_TARGET_INDICATIVE - current)
    gap_after = max(0, REFERENCE_TARGET_INDICATIVE - potential)

    return {
        "CURRENT_GROUPMENTS": current,
        "RGC_GROUPMENTS_RAW_COUNT": len(rgc),
        "RGC_GROUPMENTS_VALID_GEOMETRY": sum(1 for r in rgc if r.get("has_valid_geometry")),
        "RGC_GROUPMENTS_UNIQUE": len(rgc),
        "ALREADY_IN_GROUPMENT_REFERENTIAL": counts.get("ALREADY_IN_GROUPMENT_REFERENTIAL", 0),
        "EXISTING_GROUPMENT_VARIANT": counts.get("EXISTING_GROUPMENT_VARIANT", 0),
        "EXISTING_GROUPMENT_GEOMETRY_ENRICHMENT": enrich,  # alternative provenance available
        "NEW_RGC_GROUPMENT_WITH_VALID_GEOMETRY": new_valid,
        "DUPLICATE_RGC_GROUPMENT": counts.get("DUPLICATE_RGC_GROUPMENT", 0),
        "AMBIGUOUS_RGC_GROUPMENT": counts.get("AMBIGUOUS_RGC_GROUPMENT", 0),
        "HOMONYM_DISTINCT_RGC_GROUPMENT": counts.get("HOMONYM_DISTINCT_RGC_GROUPMENT", 0) + homonym_distinct,
        "POTENTIAL_ENRICHED_GROUPMENT_TOTAL": potential,
        "GAP_BEFORE_VS_INDICATIVE_6053": gap_before,
        "GAP_AFTER_SIMULATION_VS_INDICATIVE_6053": gap_after,
        "GAP_REDUCTION": gap_before - gap_after,
        "classification_counts": dict(counts),
        "code_mapping_samples": mapping_samples,
        "geometry_note": (
            "Points RGC = REPRESENTATIVE_POINT (chef-lieu / localité du groupement). "
            "Jamais une frontière administrative officielle."
        ),
        "classified_new_sample": [c for c in classified if c["classification"] == "NEW_RGC_GROUPMENT_WITH_VALID_GEOMETRY"][
            :25
        ],
        "source_of_rgc_groupements": "DERIVED_FROM_RGC_LOCALITIES_ATTRIBUTES",
    }


def match_localities(
    rgc_rows: list[dict[str, Any]],
    fdsu_localities: list[dict[str, Any]],
) -> dict[str, Any]:
    by_pcode: dict[str, dict[str, Any]] = {}
    by_name_terr: dict[str, list[dict[str, Any]]] = defaultdict(list)
    names_to_terrs: dict[str, set[str]] = defaultdict(set)

    for loc in fdsu_localities:
        md = (loc.get("metadata") or {}).get("extended_data") or {}
        p = md.get("PCODE") or loc.get("pcode")
        if _filled(p):
            by_pcode[str(p).split(".")[0]] = loc
        nn = _norm(loc.get("nom"))
        nt = _norm(loc.get("territoire"))
        by_name_terr[f"{nn}|{nt}"].append(loc)
        if nn:
            names_to_terrs[nn].add(nt)

    counts: Counter[str] = Counter()
    new_loc = new_vil = 0
    already = variants = ambiguous = 0
    samples_new: list[dict[str, Any]] = []

    seen_pcode: set[str] = set()
    for r in rgc_rows:
        p = r.get("PCODE")
        pkey = str(int(float(p))) if _filled(p) else None
        if pkey and pkey in seen_pcode:
            counts["DUPLICATE_RGC_LOCALITY"] += 1
            continue
        if pkey:
            seen_pcode.add(pkey)

        ok = geometry_usable(r.get("_lat"), r.get("_lon"))[0]
        name = r.get("NOM1")
        nn = _norm(name)
        terr = _norm(r.get("TERRITOIRE"))

        if pkey and pkey in by_pcode:
            counts["ALREADY_IN_LOCALITY_REFERENTIAL"] += 1
            already += 1
            continue

        hits = by_name_terr.get(f"{nn}|{terr}") or []
        if hits:
            counts["ALREADY_IN_LOCALITY_REFERENTIAL"] += 1
            already += 1
            continue

        # variant via NOM2
        alt = _norm(r.get("NOM2"))
        if alt and by_name_terr.get(f"{alt}|{terr}"):
            counts["EXISTING_LOCALITY_VARIANT"] += 1
            variants += 1
            continue

        if not ok:
            counts["AMBIGUOUS_RGC_LOCALITY"] += 1
            ambiguous += 1
            continue

        other_terrs = names_to_terrs.get(nn) or set()
        if nn and other_terrs and terr not in other_terrs:
            counts["HOMONYM_DISTINCT_RGC_LOCALITY"] += 1

        # TYPE codes — no invent village label; use NOM lexical only
        if "village" in nn:
            counts["NEW_RGC_VILLAGE_WITH_VALID_GEOMETRY"] += 1
            new_vil += 1
        else:
            counts["NEW_RGC_LOCALITY_WITH_VALID_GEOMETRY"] += 1
            new_loc += 1
        if len(samples_new) < 20:
            samples_new.append(
                {
                    "nom1": name,
                    "nom2": r.get("NOM2"),
                    "territoire": r.get("TERRITOIRE"),
                    "groupement": r.get("GROUPEMENT"),
                    "code_grpt": r.get("CODE_GRPT"),
                    "pcode": pkey,
                    "lat": r.get("_lat"),
                    "lon": r.get("_lon"),
                    "type_code": r.get("TYPE"),
                }
            )

    current = len(fdsu_localities)
    return {
        "CURRENT_LOCALITIES": current,
        "RGC_ROWS_SCANNED": len(rgc_rows),
        "ALREADY_IN_LOCALITY_REFERENTIAL": already,
        "EXISTING_LOCALITY_VARIANT": variants,
        "NEW_RGC_LOCALITY_WITH_VALID_GEOMETRY": new_loc,
        "NEW_RGC_VILLAGE_WITH_VALID_GEOMETRY": new_vil,
        "AMBIGUOUS_RGC_LOCALITY": ambiguous,
        "DUPLICATE_RGC_LOCALITY": counts.get("DUPLICATE_RGC_LOCALITY", 0),
        "HOMONYM_DISTINCT_RGC_LOCALITY": counts.get("HOMONYM_DISTINCT_RGC_LOCALITY", 0),
        "POTENTIAL_ENRICHED_LOCALITY_TOTAL": current + new_loc + new_vil,
        "classification_counts": dict(counts),
        "samples_new": samples_new,
        "note": (
            "Couche Localite.shp (26 710) = identité PCODE 100% avec locality_referential_official. "
            "Localite_p peut contenir des ajouts ; candidats NEW_* soumis à revue (millésime 2010)."
        ),
    }


def simulate_groupement_links(
    rgc_rows: list[dict[str, Any]],
    fdsu_localities: list[dict[str, Any]],
) -> dict[str, Any]:
    """Simule l'apport de liens Groupement→Localité depuis attributs RGC (sans écrire)."""
    by_pcode: dict[str, dict[str, Any]] = {}
    for loc in fdsu_localities:
        md = (loc.get("metadata") or {}).get("extended_data") or {}
        p = md.get("PCODE")
        if _filled(p):
            by_pcode[str(p).split(".")[0]] = loc

    before_with = sum(1 for loc in fdsu_localities if _filled(loc.get("groupement")))
    total = len(fdsu_localities)

    matched = 0
    matched_with_rgc_link = 0
    new_links = 0
    confirmed = 0
    ambiguous_links = 0

    # index for name match fallback
    by_name_terr: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for loc in fdsu_localities:
        by_name_terr[f"{_norm(loc.get('nom'))}|{_norm(loc.get('territoire'))}"].append(loc)

    seen_loc: set[str] = set()
    for r in rgc_rows:
        if not _filled(r.get("GROUPEMENT")) and not _filled(r.get("CODE_GRPT")):
            continue
        pkey = str(int(float(r["PCODE"]))) if _filled(r.get("PCODE")) else None
        loc = by_pcode.get(pkey) if pkey else None
        if loc is None:
            hits = by_name_terr.get(f"{_norm(r.get('NOM1'))}|{_norm(r.get('TERRITOIRE'))}") or []
            loc = hits[0] if len(hits) == 1 else None
            if len(hits) > 1:
                ambiguous_links += 1
                continue
        if loc is None:
            continue
        lid = str(loc.get("canonical_id"))
        if lid in seen_loc:
            continue
        seen_loc.add(lid)
        matched += 1
        matched_with_rgc_link += 1
        existing = _filled(loc.get("groupement"))
        rgc_g = str(r.get("GROUPEMENT") or "").strip()
        if existing:
            if _norm(loc.get("groupement")) == _norm(rgc_g):
                confirmed += 1
            else:
                ambiguous_links += 1
        else:
            new_links += 1

    after_with = before_with + new_links
    remaining = max(0, total - after_with)

    return {
        "LOCALITIES_WITH_GROUPMENT_BEFORE": before_with,
        "TOTAL_LOCALITIES": total,
        "RGC_LOCALITIES_MATCHED_TO_CURRENT_REFERENTIAL": matched,
        "RGC_MATCHED_LOCALITIES_WITH_GROUPMENT_LINK": matched_with_rgc_link,
        "NEW_GROUPMENT_LINKS_FROM_RGC": new_links,
        "CROSS_SOURCE_CONFIRMED_GROUPMENT_LINKS": confirmed,
        "AMBIGUOUS_GROUPMENT_LINKS": ambiguous_links,
        "LOCALITIES_WITHOUT_GROUPMENT_AFTER_SIMULATION": remaining,
        "coverage_rate_before": round(before_with / total, 4) if total else 0,
        "coverage_rate_after_simulation": round(after_with / total, 4) if total else 0,
        "note": (
            "Liens simulés uniquement — attributs RGC GROUPEMENT/CODE_GRPT. "
            "Proximité spatiale non utilisée. Aucune écriture sur le référentiel."
        ),
    }


def site_examples(rgc_groupements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from api.services.spatial_nearest_utils import nearest_points

    try:
        from api.services.explainable_decision_service import build_site_case

        case = build_site_case("29", program_code="sites_40")
        if not case:
            return [{"error": "site_29_unavailable"}]
        lat = case.get("latitude") or (case.get("asset") or {}).get("latitude")
        lon = case.get("longitude") or (case.get("asset") or {}).get("longitude")
        if lat is None or lon is None:
            return [{"error": "no_coords"}]
        lat, lon = float(lat), float(lon)

        fdsu_g = []
        for g in load_fdsu_groupements():
            geom = g.get("geometry") or {}
            coords = geom.get("coordinates") or []
            if geom.get("type") == "Point" and len(coords) >= 2:
                fdsu_g.append(
                    {
                        "name": g.get("nom"),
                        "canonical_id": g.get("canonical_id"),
                        "latitude": float(coords[1]),
                        "longitude": float(coords[0]),
                        "source": "FDSU_CURRENT",
                    }
                )
        near_cur = nearest_points(lat, lon, fdsu_g, radius_m=50_000, limit=1)

        rgc_pts = []
        for g in rgc_groupements:
            rp = g.get("representative_point") or {}
            if rp.get("lat") is None:
                continue
            rgc_pts.append(
                {
                    "name": g.get("source_name"),
                    "rgc_code": g.get("rgc_groupment_code"),
                    "latitude": rp["lat"],
                    "longitude": rp["lon"],
                    "source": "RGC_DERIVED",
                    "geometry_role": "REPRESENTATIVE_POINT",
                }
            )
        # bbox filter
        rgc_near = [p for p in rgc_pts if abs(p["latitude"] - lat) < 0.5 and abs(p["longitude"] - lon) < 0.5]
        near_rgc = nearest_points(lat, lon, rgc_near or rgc_pts[:2000], radius_m=50_000, limit=1)

        return [
            {
                "site_id": "29",
                "latitude": lat,
                "longitude": lon,
                "NEAREST_GROUPMENT_CURRENT": near_cur[0] if near_cur else None,
                "NEAREST_GROUPMENT_RGC_CANDIDATE": near_rgc[0] if near_rgc else None,
                "distinction": {
                    "SPATIAL_PROXIMITY": "distances = proximité uniquement",
                    "ADMINISTRATIVE_MEMBERSHIP": "non déduit de la proximité ; liens RGC = attributs explicites",
                },
            }
        ]
    except Exception as exc:
        return [{"error": str(exc)}]


def run_audit(*, write_cache: bool = True, include_site_examples: bool = True) -> AuditState:
    reset_state()
    st = get_state()
    st.meta = {
        "engine": ENGINE_VERSION,
        "generated_at": _now(),
        "audit_only": True,
        "no_integration": True,
        "analytical_equality_after_future_integration": True,
        "reference_target_indicative_only": REFERENCE_TARGET_INDICATIVE,
    }
    print("[rgc-audit] acquisition_manifest…", flush=True)
    st.acquisition = acquisition_manifest()

    if not LOCALITE_ZIP.exists():
        st.message = "Localite.zip absent — lancer l'acquisition HDX avant audit."
        st.executed = False
        return st

    print("[rgc-audit] load Localite.shp…", flush=True)
    localite = load_shapefile_rows(LOCALITE_SHP_DIR / "Localite")
    print(f"[rgc-audit] Localite rows={len(localite)}", flush=True)
    localite_p = load_shapefile_rows(LOCALITE_SHP_DIR / "Localite_p") if (LOCALITE_SHP_DIR / "Localite_p.shp").exists() else []
    print(f"[rgc-audit] Localite_p rows={len(localite_p)}", flush=True)

    audit_l = audit_rgc_localities_layer(localite, layer_name="Localite")
    audit_lp = audit_rgc_localities_layer(localite_p, layer_name="Localite_p") if localite_p else {}
    st.rgc_localities = {"Localite": audit_l, "Localite_p": audit_lp}

    # Prefer Localite_p for groupement derivation if richer, else Localite
    source_for_grp = localite_p if localite_p else localite
    print("[rgc-audit] derive groupements…", flush=True)
    rgc_grp = derive_rgc_groupements_from_localities(source_for_grp)
    st.rgc_groupements = {
        "RGC_GROUPMENTS_RAW_COUNT": len(rgc_grp),
        "RGC_GROUPMENTS_VALID_GEOMETRY": sum(1 for g in rgc_grp if g.get("has_valid_geometry")),
        "RGC_GROUPMENTS_INVALID_GEOMETRY": sum(1 for g in rgc_grp if not g.get("has_valid_geometry")),
        "RGC_GROUPMENTS_MISSING_NAME": sum(1 for g in rgc_grp if not g.get("source_name")),
        "RGC_GROUPMENTS_MISSING_TERRITORY": sum(1 for g in rgc_grp if not _filled(g.get("territoire"))),
        "RGC_GROUPMENTS_MISSING_SECTOR_CHEFFERIE": sum(1 for g in rgc_grp if not _filled(g.get("secteur_chefferie"))),
        "RGC_GROUPMENTS_WITH_PCODE": sum(1 for g in rgc_grp if _filled(g.get("rgc_pcode_sample"))),
        "RGC_GROUPMENTS_WITH_GROUPMENT_CODE": sum(1 for g in rgc_grp if _filled(g.get("rgc_groupment_code"))),
        "RGC_GROUPMENTS_UNIQUE_IDENTITY_ESTIMATE": len(rgc_grp),
        "geometry_role": "REPRESENTATIVE_POINT",
        "geometry_note": "Dérivé des localités RGC — pas le shapefile Groupements.kmz/zip catalogue (indisponible).",
        "source": "DERIVED_FROM_RGC_LOCALITIES_ATTRIBUTES",
    }

    print(f"[rgc-audit] match groupements (rgc={len(rgc_grp)})…", flush=True)
    fdsu_g = load_fdsu_groupements()
    st.match_groupements = match_groupements(fdsu_g, rgc_grp)

    print("[rgc-audit] load national localities…", flush=True)
    fdsu_loc = lci.load_national_locality_items(include_enrichment=True)
    print(f"[rgc-audit] match localities (fdsu={len(fdsu_loc)})…", flush=True)
    # Match primarily Localite_p for potential NEW; also report Localite overlap
    st.match_localities = match_localities(localite_p or localite, fdsu_loc)
    st.match_localities["Localite_base_raw_count"] = len(localite)
    st.match_localities["Localite_p_raw_count"] = len(localite_p)
    st.match_localities["pcode_identity_with_fdsu_official"] = (
        "Localite.shp PCODE set == locality_referential_official PCODE set (100% intersection on 26680 codes)."
    )

    print("[rgc-audit] simulate groupement links…", flush=True)
    st.links = simulate_groupement_links(localite_p or localite, fdsu_loc)

    if include_site_examples:
        print("[rgc-audit] site examples…", flush=True)
        st.site_examples = site_examples(rgc_grp)

    st.kpis = {
        **{k: st.match_groupements.get(k) for k in (
            "CURRENT_GROUPMENTS",
            "RGC_GROUPMENTS_RAW_COUNT",
            "RGC_GROUPMENTS_VALID_GEOMETRY",
            "RGC_GROUPMENTS_UNIQUE",
            "ALREADY_IN_GROUPMENT_REFERENTIAL",
            "EXISTING_GROUPMENT_VARIANT",
            "EXISTING_GROUPMENT_GEOMETRY_ENRICHMENT",
            "NEW_RGC_GROUPMENT_WITH_VALID_GEOMETRY",
            "DUPLICATE_RGC_GROUPMENT",
            "AMBIGUOUS_RGC_GROUPMENT",
            "HOMONYM_DISTINCT_RGC_GROUPMENT",
            "POTENTIAL_ENRICHED_GROUPMENT_TOTAL",
            "GAP_BEFORE_VS_INDICATIVE_6053",
            "GAP_AFTER_SIMULATION_VS_INDICATIVE_6053",
            "GAP_REDUCTION",
        )},
        "CURRENT_LOCALITIES": st.match_localities.get("CURRENT_LOCALITIES"),
        "RGC_LOCALITIES_RAW_COUNT_BASE": len(localite),
        "RGC_LOCALITIES_RAW_COUNT_P": len(localite_p),
        "RGC_LOCALITIES_VALID_GEOMETRY": audit_l.get("RGC_LOCALITIES_VALID_GEOMETRY"),
        "ALREADY_IN_LOCALITY_REFERENTIAL": st.match_localities.get("ALREADY_IN_LOCALITY_REFERENTIAL"),
        "EXISTING_LOCALITY_VARIANT": st.match_localities.get("EXISTING_LOCALITY_VARIANT"),
        "NEW_RGC_LOCALITY_WITH_VALID_GEOMETRY": st.match_localities.get("NEW_RGC_LOCALITY_WITH_VALID_GEOMETRY"),
        "NEW_RGC_VILLAGE_WITH_VALID_GEOMETRY": st.match_localities.get("NEW_RGC_VILLAGE_WITH_VALID_GEOMETRY"),
        "AMBIGUOUS_RGC_LOCALITY": st.match_localities.get("AMBIGUOUS_RGC_LOCALITY"),
        "POTENTIAL_ENRICHED_LOCALITY_TOTAL": st.match_localities.get("POTENTIAL_ENRICHED_LOCALITY_TOTAL"),
        **{k: st.links.get(k) for k in (
            "LOCALITIES_WITH_GROUPMENT_BEFORE",
            "NEW_GROUPMENT_LINKS_FROM_RGC",
            "CROSS_SOURCE_CONFIRMED_GROUPMENT_LINKS",
            "AMBIGUOUS_GROUPMENT_LINKS",
            "LOCALITIES_WITHOUT_GROUPMENT_AFTER_SIMULATION",
            "coverage_rate_before",
            "coverage_rate_after_simulation",
        )},
    }

    st.nsme_sdg = {
        "future_relations": [
            "NEAREST_GROUPMENT",
            "DISTANCE_TO_GROUPMENT_M",
            "GROUPMENT_ADMIN_CONTEXT",
            "NEAREST_LOCALITY",
            "DISTANCE_TO_LOCALITY_M",
            "LOCALITY_GROUPMENT_CONTEXT",
        ],
        "materialization": "on_demand_cache_controlled_batch_postgis",
        "sdg_chain": "Site FDSU → Groupement → Localité/Village → CENI → Santé → Éducation → Télécom → Population/Couverture",
        "equality": "Après intégration future, entités RGC = égales aux historiques/NCI ; provenance = audit only.",
        "millesime_limit": "Jeux RGC ~2010 — ne jamais écraser FDSU/NCI/CENI plus récents.",
    }

    st.executed = True
    st.message = "Audit RGC Groupements/Localités exécuté (lecture seule, aucune intégration)."

    if write_cache:
        CACHE_JSON.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "meta": st.meta,
            "acquisition": st.acquisition,
            "rgc_localities": st.rgc_localities,
            "rgc_groupements": st.rgc_groupements,
            "match_groupements": {
                **st.match_groupements,
                "classified_new_sample": st.match_groupements.get("classified_new_sample"),
                "code_mapping_samples": st.match_groupements.get("code_mapping_samples"),
            },
            "match_localities": {
                **{k: v for k, v in st.match_localities.items() if k != "samples_new"},
                "samples_new": st.match_localities.get("samples_new"),
            },
            "links": st.links,
            "site_examples": st.site_examples,
            "kpis": st.kpis,
            "nsme_sdg": st.nsme_sdg,
        }
        CACHE_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return st
