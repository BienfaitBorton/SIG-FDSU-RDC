"""Parser / validateur / générateur de la nomenclature officielle des codes FDSU.

Source officielle unique :
  data/raw/FDSU Structure code Territoire zones.xlsx

Format officiel :
  FDSU_<ZONE>_<CODE_PROVINCE>_<CODE_TERRITOIRE>_<CODE_SITE>

Exemple métier :
  FDSU_ND_18_003_10100
  → préfixe FDSU | zone ND | province 18 (MONGALA) | territoire 003 (LISALA) | site 10100

Variante étendue acceptée (collectivité) :
  FDSU_<ZONE>_<PROV>_<TERR>_<COLLECTIVITE>_<SITE>

Interdit : SITE-FDSU-000001 et toute codification artificielle de site.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from typing import Any

from app.fdsu_nomenclature import OFFICIAL_STRUCTURE_RELATIVE, load_nomenclature

# Zones officielles FDSU (feuilles ZONE ND / SD / CE / OT / ET
# du fichier data/raw/FDSU Structure code Territoire zones.xlsx)
OFFICIAL_ZONES = frozenset({"ND", "SD", "CE", "OT", "ET"})
OFFICIAL_NOMENCLATURE_SOURCE = OFFICIAL_STRUCTURE_RELATIVE
ZONE_LABELS = {
    "ND": "Zone Nord",
    "SD": "Zone Sud",
    "CE": "Zone Centre",
    "OT": "Zone Ouest",
    "ET": "Zone Est",
}

# Alias historiques A/B/C/D/E → codes officiels
ZONE_ALIASES = {
    "A": "ND",
    "B": "SD",
    "C": "CE",
    "D": "OT",
    "E": "ET",
    "NORD": "ND",
    "SUD": "SD",
    "CENTRE": "CE",
    "OUEST": "OT",
    "EST": "ET",
}

FDSU_CODE_PATTERN = re.compile(
    r"^FDSU_"
    r"(?P<zone>[A-Z]{2})"
    r"_(?P<province>\d{1,2})"
    r"_(?P<territoire>\d{1,3})"
    r"(?:_(?P<collectivite>\d{1,3}))?"
    r"_(?P<site>\d{1,5})$",
    re.IGNORECASE,
)

ARTIFICIAL_SITE_PATTERN = re.compile(
    r"^(SITE[-_]?FDSU[-_]?\d+|FDSU[-_]?SITE[-_]?\d+)$",
    re.IGNORECASE,
)


@dataclass
class ParsedFdsuCode:
    raw: str
    normalized: str
    prefix: str
    zone: str
    province_code: str
    territoire_code: str
    site_code: str
    collectivite_code: str | None = None
    zone_label: str | None = None
    province_name: str | None = None
    territoire_name: str | None = None
    valid_format: bool = True
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FdsuCodeValidation:
    business_id: str
    is_valid: bool
    parsed: dict[str, Any] | None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    nomenclature_match: bool = False
    territory_consistent: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_zone(zone: str | None) -> str:
    raw = str(zone or "").strip().upper()
    if raw in ZONE_ALIASES:
        return ZONE_ALIASES[raw]
    return raw


def normalize_fdsu_code(value: str | None) -> str:
    text = str(value or "").strip().upper().replace(" ", "").replace("-", "_")
    while "__" in text:
        text = text.replace("__", "_")
    return text


def is_artificial_site_id(value: str | None) -> bool:
    return bool(ARTIFICIAL_SITE_PATTERN.match(str(value or "").strip()))


@lru_cache(maxsize=1)
def _province_by_code() -> dict[str, dict[str, Any]]:
    return {
        str(item.get("code")).zfill(2): item
        for item in load_nomenclature().get("provinces", [])
        if item.get("code") is not None
    }


@lru_cache(maxsize=1)
def _territoire_index() -> dict[tuple[str, str], dict[str, Any]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for item in load_nomenclature().get("territoires", []):
        prov = str(item.get("province_code") or "").zfill(2)
        terr = str(item.get("code") or "").zfill(3)
        if prov and terr:
            index[(prov, terr)] = item
    return index


def parse_fdsu_code(business_id: str | None) -> ParsedFdsuCode:
    """Découpe un code FDSU officiel en composants métier."""
    raw = str(business_id or "").strip()
    normalized = normalize_fdsu_code(raw)
    errors: list[str] = []

    if not raw:
        return ParsedFdsuCode(
            raw=raw,
            normalized="",
            prefix="FDSU",
            zone="",
            province_code="",
            territoire_code="",
            site_code="",
            valid_format=False,
            errors=["Code FDSU vide."],
        )

    if is_artificial_site_id(raw):
        return ParsedFdsuCode(
            raw=raw,
            normalized=normalized,
            prefix="FDSU",
            zone="",
            province_code="",
            territoire_code="",
            site_code="",
            valid_format=False,
            errors=[
                "Identifiant artificiel interdit (ex. SITE-FDSU-000001). "
                "Utiliser le code officiel FDSU_<ZONE>_<PROV>_<TERR>_<SITE>."
            ],
        )

    match = FDSU_CODE_PATTERN.match(normalized)
    if not match:
        return ParsedFdsuCode(
            raw=raw,
            normalized=normalized,
            prefix="FDSU",
            zone="",
            province_code="",
            territoire_code="",
            site_code="",
            valid_format=False,
            errors=[
                "Format invalide. Attendu : FDSU_<ZONE>_<PROVINCE>_<TERRITOIRE>_<SITE> "
                "(ex. FDSU_ND_18_003_10100)."
            ],
        )

    zone = normalize_zone(match.group("zone"))
    province = match.group("province").zfill(2)
    territoire = match.group("territoire").zfill(3)
    collectivite = match.group("collectivite")
    collectivite = collectivite.zfill(3) if collectivite else None
    site = match.group("site").zfill(3 if len(match.group("site")) <= 3 else len(match.group("site")))
    # Conserver la largeur métier du site (3 à 5 chiffres) sans forcer 5.
    site_raw = match.group("site")
    site = site_raw.zfill(max(3, len(site_raw)))

    if zone not in OFFICIAL_ZONES:
        errors.append(f"Zone '{zone}' hors nomenclature officielle {sorted(OFFICIAL_ZONES)}.")

    rebuilt = f"FDSU_{zone}_{province}_{territoire}"
    if collectivite:
        rebuilt += f"_{collectivite}"
    rebuilt += f"_{site}"

    province_meta = _province_by_code().get(province)
    territoire_meta = _territoire_index().get((province, territoire))

    return ParsedFdsuCode(
        raw=raw,
        normalized=rebuilt,
        prefix="FDSU",
        zone=zone,
        province_code=province,
        territoire_code=territoire,
        site_code=site,
        collectivite_code=collectivite,
        zone_label=ZONE_LABELS.get(zone),
        province_name=(province_meta or {}).get("nom"),
        territoire_name=(territoire_meta or {}).get("nom"),
        valid_format=len(errors) == 0,
        errors=errors,
    )


def validate_fdsu_code(
    business_id: str | None,
    *,
    expected_zone: str | None = None,
    expected_province_code: str | None = None,
    expected_territoire_code: str | None = None,
) -> FdsuCodeValidation:
    """Valide format + cohérence avec la nomenclature officielle."""
    parsed = parse_fdsu_code(business_id)
    errors = list(parsed.errors)
    warnings: list[str] = []

    if not parsed.valid_format:
        return FdsuCodeValidation(
            business_id=str(business_id or ""),
            is_valid=False,
            parsed=parsed.as_dict(),
            errors=errors,
        )

    province = _province_by_code().get(parsed.province_code)
    territoire = _territoire_index().get((parsed.province_code, parsed.territoire_code))
    nomenclature_match = bool(province and territoire)
    territory_consistent = True

    if not province:
        errors.append(f"Province '{parsed.province_code}' absente de la nomenclature officielle.")
        nomenclature_match = False
        territory_consistent = False
    else:
        official_zone = normalize_zone(province.get("zone_fdsu"))
        if official_zone and official_zone != parsed.zone:
            errors.append(
                f"Incohérence zone : code={parsed.zone}, nomenclature province={official_zone} "
                f"({province.get('nom')})."
            )
            territory_consistent = False

    if not territoire:
        errors.append(
            f"Territoire '{parsed.territoire_code}' introuvable pour la province "
            f"'{parsed.province_code}' dans la nomenclature."
        )
        nomenclature_match = False
        territory_consistent = False
    elif territoire.get("zone_fdsu") and normalize_zone(territoire.get("zone_fdsu")) != parsed.zone:
        warnings.append(
            f"Zone territoire nomenclature={territoire.get('zone_fdsu')} vs code={parsed.zone}."
        )

    if expected_zone and normalize_zone(expected_zone) != parsed.zone:
        errors.append(f"Zone attendue '{expected_zone}' ≠ '{parsed.zone}'.")
        territory_consistent = False
    if expected_province_code and str(expected_province_code).zfill(2) != parsed.province_code:
        errors.append(f"Province attendue '{expected_province_code}' ≠ '{parsed.province_code}'.")
        territory_consistent = False
    if expected_territoire_code and str(expected_territoire_code).zfill(3) != parsed.territoire_code:
        errors.append(
            f"Territoire attendu '{expected_territoire_code}' ≠ '{parsed.territoire_code}'."
        )
        territory_consistent = False

    if len(parsed.site_code) > 5:
        errors.append("Code site trop long (max 5 chiffres).")

    return FdsuCodeValidation(
        business_id=parsed.normalized,
        is_valid=len(errors) == 0,
        parsed=parsed.as_dict(),
        errors=errors,
        warnings=warnings,
        nomenclature_match=nomenclature_match,
        territory_consistent=territory_consistent and len(errors) == 0,
    )


def generate_fdsu_code(
    *,
    zone: str,
    province_code: str | int,
    territoire_code: str | int,
    site_number: str | int,
    collectivite_code: str | int | None = None,
    site_width: int = 5,
    validate: bool = True,
) -> dict[str, Any]:
    """Génère un code FDSU officiel (jamais SITE-FDSU-######)."""
    zone_n = normalize_zone(zone)
    prov = str(province_code).strip().zfill(2)
    terr = str(territoire_code).strip().zfill(3)
    site = str(site_number).strip()
    if site.isdigit():
        width = max(3, min(5, int(site_width)))
        site = site.zfill(width)
    parts = ["FDSU", zone_n, prov, terr]
    if collectivite_code not in (None, ""):
        parts.append(str(collectivite_code).strip().zfill(3))
    parts.append(site)
    code = "_".join(parts)

    result: dict[str, Any] = {
        "business_id": code,
        "generated": True,
        "components": {
            "prefix": "FDSU",
            "zone": zone_n,
            "province_code": prov,
            "territoire_code": terr,
            "collectivite_code": (
                str(collectivite_code).strip().zfill(3) if collectivite_code not in (None, "") else None
            ),
            "site_code": site,
        },
    }
    if validate:
        validation = validate_fdsu_code(code)
        result["validation"] = validation.as_dict()
        result["is_valid"] = validation.is_valid
    return result


def next_site_code_candidate(
    existing_codes: list[str],
    *,
    zone: str,
    province_code: str | int,
    territoire_code: str | int,
    collectivite_code: str | int | None = None,
    site_width: int = 5,
) -> dict[str, Any]:
    """Propose le prochain numéro de site libre pour un territoire donné."""
    prefix_parts = [
        "FDSU",
        normalize_zone(zone),
        str(province_code).zfill(2),
        str(territoire_code).zfill(3),
    ]
    if collectivite_code not in (None, ""):
        prefix_parts.append(str(collectivite_code).zfill(3))
    prefix = "_".join(prefix_parts) + "_"

    used: set[int] = set()
    for code in existing_codes:
        normalized = normalize_fdsu_code(code)
        if not normalized.startswith(prefix):
            continue
        parsed = parse_fdsu_code(normalized)
        if parsed.valid_format and parsed.site_code.isdigit():
            used.add(int(parsed.site_code))

    candidate = 1
    while candidate in used:
        candidate += 1
    return generate_fdsu_code(
        zone=zone,
        province_code=province_code,
        territoire_code=territoire_code,
        site_number=candidate,
        collectivite_code=collectivite_code,
        site_width=site_width,
        validate=True,
    )
