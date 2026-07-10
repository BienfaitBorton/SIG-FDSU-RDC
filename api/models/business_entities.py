"""Constantes métier légères du modèle d'entreprise SIG-FDSU RDC.

Pas d'ORM. Pas de couche de persistance. Uniquement le vocabulaire métier partagé.
Référence : PROJECT_MANAGEMENT/ARCHITECTURE/FDSU_ENTERPRISE_BUSINESS_MODEL.md
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class AssetType(str, Enum):
    """Types d'actifs / entités métier FDSU."""

    PROGRAM = "PROGRAM"
    BATCH = "BATCH"
    PROJECT = "PROJECT"
    SITE = "SITE"
    CCN = "CCN"
    ZONE = "ZONE"
    PROVINCE = "PROVINCE"
    TERRITOIRE = "TERRITOIRE"
    COLLECTIVITE = "COLLECTIVITE"
    GROUPEMENT = "GROUPEMENT"
    LOCALITE = "LOCALITE"
    VILLAGE = "VILLAGE"
    TELCO = "TELCO"
    FIBER = "FIBER"
    ROAD = "ROAD"
    SCHOOL = "SCHOOL"
    HEALTH = "HEALTH"
    MARKET = "MARKET"
    MISSION = "MISSION"
    SCORE = "SCORE"
    RECOMMENDATION = "RECOMMENDATION"
    DECISION = "DECISION"
    PARTNER = "PARTNER"
    DATA_SOURCE = "DATA_SOURCE"


class AssetStatus(str, Enum):
    """Cycle de vie d'un actif FDSU."""

    PROPOSED = "proposed"
    PRE_IDENTIFIED = "pre_identified"
    GEOCODED = "geocoded"
    VALIDATED = "validated"
    PLANNED = "planned"
    DEPLOYING = "deploying"
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class DataStatus(str, Enum):
    """Cycle de vie d'une donnée."""

    RAW = "raw"
    NORMALIZED = "normalized"
    ENRICHED = "enriched"
    VALIDATED = "validated"
    OBSOLETE = "obsolete"
    ARCHIVED = "archived"


class DecisionStatus(str, Enum):
    """Cycle de vie d'une décision."""

    DRAFT = "draft"
    PROPOSED = "proposed"
    VALIDATED = "validated"
    APPROVED = "approved"
    EXECUTED = "executed"
    CLOSED = "closed"


class RelationshipType(str, Enum):
    """Relations métier principales."""

    CONTAINS = "CONTAINS"
    TARGETS = "TARGETS"
    LOCATED_IN = "LOCATED_IN"
    ADMIN_PARENT = "ADMIN_PARENT"
    FEEDS_CONNECTIVITY = "FEEDS_CONNECTIVITY"
    HOSTED_IN = "HOSTED_IN"
    SERVES_POPULATION = "SERVES_POPULATION"
    OFFERS = "OFFERS"
    TRACKED_BY = "TRACKED_BY"
    SCORED_BY = "SCORED_BY"
    PRODUCES = "PRODUCES"
    FEEDS = "FEEDS"
    CONCERNS = "CONCERNS"
    VERIFIES = "VERIFIES"
    SOURCED_FROM = "SOURCED_FROM"
    CONTRIBUTES_TO = "CONTRIBUTES_TO"


class CcnHostType(str, Enum):
    """Lieux d'implantation possibles d'un CCN."""

    SCHOOL = "school"
    ADMIN_BUILDING = "admin_building"
    HEALTH_CENTER = "health_center"
    MARKET = "market"
    OTHER = "other"


class CcnServiceType(str, Enum):
    """Catalogue de services numériques d'un CCN."""

    PUBLIC_INTERNET = "public_internet"
    DIGITAL_TRAINING = "digital_training"
    E_ADMIN = "e_admin"
    E_HEALTH = "e_health"
    E_EDUCATION = "e_education"
    BUSINESS_SUPPORT = "business_support"
    OTHER = "other"


@dataclass(frozen=True)
class BusinessCodeScheme:
    """Schéma de codification métier."""

    code: str
    label: str
    pattern: str
    example: str
    is_official: bool
    source: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class CcnRelationshipSpec:
    """Spécification d'une relation métier CCN."""

    code: str
    label: str
    relationship_type: RelationshipType
    from_type: AssetType | str
    to_type: AssetType | str


@dataclass(frozen=True)
class DecisionExtensionPoint:
    """Point d'extension Centre de Décision (UI non branchée)."""

    code: str
    label: str
    description: str
    planned_intents: tuple[str, ...]
    ui_ready: bool = False


# Nomenclature officielle des sites FDSU
SITE_FDSU_CODE_SCHEME = BusinessCodeScheme(
    code="SITE_FDSU",
    label="Code officiel Site FDSU",
    pattern="FDSU_<ZONE>_<PROVINCE>_<TERRITOIRE>_<SITE>",
    example="FDSU_ND_18_003_10100",
    is_official=True,
    source="data/raw/FDSU Structure code Territoire zones.xlsx",
    notes="Référence unique pour génération et validation des codes sites.",
)

# Proposition technique préparatoire — PAS une nomenclature officielle validée
CCN_CODE_SCHEME = BusinessCodeScheme(
    code="CCN_PROPOSED",
    label="Schéma préparatoire CCN",
    pattern="FDSU_CCN_[ZONE]_[PROVINCE]_[TERRITOIRE]_[NUMERO]",
    example="FDSU_CCN_ND_18_003_00001",
    is_official=False,
    source=None,
    notes=(
        "Proposition technique préparatoire uniquement. "
        "Un CCN n'est pas un Site FDSU : le site apporte la connectivité, "
        "le CCN apporte le service numérique à la population."
    ),
)

OFFICIAL_SITE_NOMENCLATURE_PATH = "data/raw/FDSU Structure code Territoire zones.xlsx"

CCN_ATTRIBUTE_DOMAINS: tuple[str, ...] = (
    "identification",
    "implantation",
    "connectivite",
    "equipements",
    "services",
    "exploitation",
    "maintenance",
    "indicateurs",
    "impacts",
    "partenaires",
)

CCN_RELATIONSHIPS: tuple[CcnRelationshipSpec, ...] = (
    CcnRelationshipSpec(
        code="site_feeds_ccn",
        label="CCN alimenté par Site FDSU",
        relationship_type=RelationshipType.FEEDS_CONNECTIVITY,
        from_type=AssetType.SITE,
        to_type=AssetType.CCN,
    ),
    CcnRelationshipSpec(
        code="ccn_hosted_in_building",
        label="CCN implanté dans un bâtiment / lieu hôte",
        relationship_type=RelationshipType.HOSTED_IN,
        from_type=AssetType.CCN,
        to_type="HOST_PLACE",
    ),
    CcnRelationshipSpec(
        code="ccn_serves_population",
        label="CCN dessert une population",
        relationship_type=RelationshipType.SERVES_POPULATION,
        from_type=AssetType.CCN,
        to_type=AssetType.LOCALITE,
    ),
    CcnRelationshipSpec(
        code="ccn_offers_services",
        label="CCN propose plusieurs services",
        relationship_type=RelationshipType.OFFERS,
        from_type=AssetType.CCN,
        to_type="CCN_SERVICE",
    ),
    CcnRelationshipSpec(
        code="ccn_tracked_by_kpis",
        label="CCN suivi par des indicateurs",
        relationship_type=RelationshipType.TRACKED_BY,
        from_type=AssetType.CCN,
        to_type="KPI",
    ),
    CcnRelationshipSpec(
        code="program_funds_ccn",
        label="CCN financé par un programme",
        relationship_type=RelationshipType.CONTRIBUTES_TO,
        from_type=AssetType.PROGRAM,
        to_type=AssetType.CCN,
    ),
    CcnRelationshipSpec(
        code="mission_audits_ccn",
        label="CCN audité par une mission",
        relationship_type=RelationshipType.VERIFIES,
        from_type=AssetType.MISSION,
        to_type=AssetType.CCN,
    ),
)

CCN_DECISION_EXTENSIONS: tuple[DecisionExtensionPoint, ...] = (
    DecisionExtensionPoint(
        code="ccn.prioritization",
        label="Priorisation des CCN",
        description="Classer les implantations CCN selon population, déficit numérique et connectivité Site FDSU.",
        planned_intents=("prioriser_ccn", "comparer_territoires_ccn"),
        ui_ready=False,
    ),
    DecisionExtensionPoint(
        code="ccn.implantation_simulation",
        label="Simulation d'implantation CCN",
        description="Comparer des lieux hôtes (école, santé, marché, admin) pour une implantation.",
        planned_intents=("simuler_implantation_ccn",),
        ui_ready=False,
    ),
    DecisionExtensionPoint(
        code="ccn.performance_monitoring",
        label="Suivi des performances CCN",
        description="Suivre fréquentation, disponibilité et impacts des CCN opérationnels.",
        planned_intents=("suivre_performance_ccn", "alerter_ccn_degrade"),
        ui_ready=False,
    ),
)

# Site et CCN ne doivent jamais être confondus
DISTINCT_ASSET_PAIRS = frozenset({(AssetType.SITE, AssetType.CCN)})

_CCN_PROPOSED_RE = re.compile(
    r"^FDSU_CCN_(?P<zone>[A-Z]{2})_(?P<province>\d{1,2})_(?P<territoire>\d{1,3})_(?P<numero>\d{1,5})$",
    re.IGNORECASE,
)


def is_site_fdsu(asset_type: AssetType | str) -> bool:
    return AssetType(asset_type) == AssetType.SITE


def is_ccn(asset_type: AssetType | str) -> bool:
    return AssetType(asset_type) == AssetType.CCN


def assert_site_ccn_distinct(left: AssetType | str, right: AssetType | str) -> bool:
    """Retourne True si les deux types sont bien distincts Site vs CCN."""
    a, b = AssetType(left), AssetType(right)
    if a == b:
        return False
    return {a, b} == {AssetType.SITE, AssetType.CCN}


def build_proposed_ccn_code(
    *,
    zone: str,
    province_code: str | int,
    territoire_code: str | int,
    numero: str | int,
    numero_width: int = 5,
) -> str:
    """Construit un code CCN préparatoire (non officiel)."""
    zone_n = str(zone).strip().upper()
    prov = str(province_code).strip().zfill(2)
    terr = str(territoire_code).strip().zfill(3)
    num = str(numero).strip()
    if num.isdigit():
        num = num.zfill(max(3, min(5, numero_width)))
    return f"FDSU_CCN_{zone_n}_{prov}_{terr}_{num}"


def parse_proposed_ccn_code(business_id: str | None) -> dict[str, Any]:
    raw = str(business_id or "").strip().upper().replace(" ", "").replace("-", "_")
    match = _CCN_PROPOSED_RE.match(raw)
    if not match:
        return {
            "raw": business_id,
            "valid_format": False,
            "normalized": raw,
            "errors": ["Format CCN préparatoire invalide. Attendu: FDSU_CCN_ZONE_PROV_TERR_NUMERO."],
        }
    zone = match.group("zone").upper()
    province = match.group("province").zfill(2)
    territoire = match.group("territoire").zfill(3)
    numero = match.group("numero")
    normalized = f"FDSU_CCN_{zone}_{province}_{territoire}_{numero.zfill(max(3, len(numero)))}"
    return {
        "raw": business_id,
        "valid_format": True,
        "normalized": normalized,
        "prefix": "FDSU_CCN",
        "zone": zone,
        "province_code": province,
        "territoire_code": territoire,
        "numero": numero.zfill(max(3, len(numero))),
        "is_official": False,
        "errors": [],
    }


def validate_proposed_ccn_code(business_id: str | None) -> dict[str, Any]:
    parsed = parse_proposed_ccn_code(business_id)
    errors = list(parsed.get("errors") or [])
    warnings = [
        "Nomenclature CCN non officielle — schéma préparatoire uniquement.",
    ]
    if str(business_id or "").upper().startswith("FDSU_") and not str(business_id or "").upper().startswith(
        "FDSU_CCN_"
    ):
        errors.append("Ce code ressemble à un Site FDSU, pas à un CCN.")
    return {
        "business_id": parsed.get("normalized") or business_id,
        "is_valid_format": bool(parsed.get("valid_format")) and not errors,
        "is_official": False,
        "parsed": parsed,
        "errors": errors,
        "warnings": warnings,
    }
