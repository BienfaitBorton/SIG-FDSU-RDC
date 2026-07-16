"""National Territorial Intelligence Engine v1.

Couche analytique federatrice : elle ne relit pas les sources metier et ne
recalcule pas les regles des moteurs existants. Les valeurs absentes restent
explicitement indisponibles.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any

from api.services import national_asset_registry_service as registry
from api.services import territorial_multiscale_service as multiscale

ENGINE_VERSION = "ntie-1.0.0"
SUPPORTED_LEVELS = ("province", "territoire", "secteur", "chefferie", "collectivite", "groupement", "localite")

DIMENSIONS = (
    ("population", "Population", "personnes"),
    ("mobile_coverage", "Couverture mobile", "%"),
    ("population_covered", "Population couverte", "personnes"),
    ("population_uncovered", "Population non couverte", "personnes"),
    ("localities", "Nombre de localites", "localites"),
    ("localities_covered", "Localites couvertes", "localites"),
    ("localities_uncovered", "Localites non couvertes", "localites"),
    ("fdsu_sites", "Nombre de sites FDSU", "sites"),
    ("operator_sites", "Nombre de sites operateurs", "sites"),
    ("ccn", "Nombre de CCN", "centres"),
    ("health", "Sante", "etablissements"),
    ("education", "Education", "etablissements"),
    ("roads", "Routes", "elements"),
    ("fiber", "Fibre", "elements"),
    ("energy", "Energie", "elements"),
    ("public_services", "Services publics", "services"),
    ("economic_activities", "Activites economiques", "elements"),
    ("economic_potential", "Potentiel economique", "indice"),
    ("geographic_constraints", "Contraintes geographiques", "elements"),
    ("digital_vulnerability_index", "Indice de vulnerabilite numerique", "score/100"),
    ("accessibility_index", "Indice d'accessibilite", "score/100"),
    ("digital_maturity_index", "Indice de maturite numerique", "score/100"),
    ("territorial_development_index", "Indice de developpement territorial", "score/100"),
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().replace("-", " ").split())


def _value(field: Any) -> Any:
    return field.get("value") if isinstance(field, dict) and "value" in field else field


def _indicator(
    key: str,
    value: Any = None,
    *,
    field: dict[str, Any] | None = None,
    source: str | None = None,
    version: str | None = None,
    method: str | None = None,
    confidence: str | None = None,
    quality: str | None = None,
    explanation: str | None = None,
) -> dict[str, Any]:
    label, unit = next((label, unit) for code, label, unit in DIMENSIONS if code == key)
    field = field if isinstance(field, dict) else {}
    available = value is not None
    return {
        "id": key,
        "label": label,
        "value": value,
        "unit": unit,
        "status": field.get("status") or ("available" if available else "unavailable"),
        "source": source or field.get("source"),
        "version": version,
        "date": field.get("date") or field.get("as_of"),
        "confidence": confidence or field.get("confidence") or ("unknown" if not available else "medium"),
        "quality": quality or ("not_assessed" if available else "unavailable"),
        "method": method or field.get("method") or ("not_calculated_no_source" if not available else "federated_value"),
        "explanation": explanation or field.get("note") or (
            "Valeur federée depuis un moteur existant." if available
            else "Aucune valeur tracable n'est disponible dans les moteurs raccordes."
        ),
    }


def _matches(asset: dict[str, Any], entity: dict[str, Any]) -> bool:
    territory = asset.get("territory") or {}
    level = entity.get("type")
    name = _norm(entity.get("name"))
    if level == "province":
        return _norm(territory.get("province")) == name
    if level == "territoire":
        return _norm(territory.get("territoire")) == name
    if level == "collectivite":
        return name in {_norm(territory.get(k)) for k in ("secteur", "chefferie", "collectivite")}
    if level == "groupement":
        return _norm(territory.get("groupement")) == name
    if level == "localite":
        return name in {_norm(territory.get("localite")), _norm(territory.get("village"))}
    return False


def _asset_counts(entity: dict[str, Any]) -> dict[str, Any]:
    assets = [asset for asset in registry.asset_snapshot() if _matches(asset, entity)]
    programs = Counter(asset.get("program") for asset in assets)
    return {
        "fdsu_sites": sum(1 for asset in assets if asset.get("asset_type") == "FDSU_SITE"),
        "ccn": sum(1 for asset in assets if asset.get("asset_type") == "CCN"),
        "by_program": {key: programs.get(key, 0) for key in (*registry.PROGRAMS, "ccn")},
        "source": "National FDSU Asset Registry",
        "version": registry.REGISTRY_VERSION,
    }


def _build_indicators(base: dict[str, Any], counts: dict[str, Any]) -> list[dict[str, Any]]:
    population = base.get("population") or {}
    coverage = base.get("coverage") or {}
    covered = coverage.get("localities_covered") or {}
    uncovered = coverage.get("localities_uncovered") or {}
    covered_n, uncovered_n = _value(covered), _value(uncovered)
    localities = covered_n + uncovered_n if isinstance(covered_n, (int, float)) and isinstance(uncovered_n, (int, float)) else None
    ndci = coverage.get("ndci") or {}

    known = {
        "population": _indicator("population", _value(population), field=population),
        "mobile_coverage": _indicator("mobile_coverage", _value(coverage.get("coverage_rate_pct")), field=coverage.get("coverage_rate_pct")),
        "population_covered": _indicator("population_covered", _value(coverage.get("population_covered")), field=coverage.get("population_covered")),
        "population_uncovered": _indicator("population_uncovered", _value(coverage.get("population_uncovered")), field=coverage.get("population_uncovered")),
        "localities": _indicator("localities", localities, source=(covered or uncovered).get("source"), method="covered_plus_uncovered_exclusive_sets" if localities is not None else None, confidence=(covered or uncovered).get("confidence"), explanation="Somme des ensembles NCI couverts et non couverts, declares exclusifs." if localities is not None else None),
        "localities_covered": _indicator("localities_covered", covered_n, field=covered),
        "localities_uncovered": _indicator("localities_uncovered", uncovered_n, field=uncovered),
        "fdsu_sites": _indicator("fdsu_sites", counts["fdsu_sites"], source=counts["source"], version=counts["version"], method="registry_assets_matched_to_territorial_hierarchy", confidence="medium", quality="federated"),
        "ccn": _indicator("ccn", counts["ccn"], source=counts["source"], version=counts["version"], method="registry_ccn_matched_to_territorial_hierarchy", confidence="low", quality="demonstration"),
        "operator_sites": _indicator("operator_sites", _value(base.get("telecom")), field=base.get("telecom")),
        "health": _indicator("health", _value(base.get("health")), field=base.get("health")),
        "roads": _indicator("roads", _value(base.get("routes")), field=base.get("routes")),
        "fiber": _indicator("fiber", _value(base.get("fiber")), field=base.get("fiber")),
        "digital_vulnerability_index": _indicator("digital_vulnerability_index", ndci.get("index"), source="National Coverage Intelligence / NDCI", version=ndci.get("version"), method="existing_ndci_formula", confidence=(population or {}).get("confidence"), quality="existing_engine", explanation="Indice NDCI repris sans recalcul ; composantes et ponderations exposees dans l'explicabilite." if ndci.get("index") is not None else None),
    }
    return [known.get(key) or _indicator(key) for key, _, _ in DIMENSIONS]


def _score(base: dict[str, Any], indicators: list[dict[str, Any]]) -> dict[str, Any]:
    existing = _value(base.get("score"))
    if isinstance(existing, (int, float)):
        return {
            "value": existing, "label": "Score existant", "status": "official_existing_engine",
            "confidence": base.get("confidence") or "medium", "confidence_limited": False,
            "method": "reference_existing_territorial_engine", "weights": None,
            "explanation": "Score repris du moteur territorial existant, sans nouveau coefficient NTIE.",
        }
    available = [item["id"] for item in indicators if item["id"] in {"digital_vulnerability_index", "accessibility_index", "digital_maturity_index", "territorial_development_index"} and isinstance(item["value"], (int, float))]
    return {
        "value": None,
        "label": "Score indicatif",
        "status": "not_calculated_no_official_weights",
        "confidence": "limited",
        "confidence_limited": True,
        "method": "not_calculated_without_official_weights_and_sufficient_indices",
        "weights": None,
        "available_inputs": available,
        "explanation": "Confiance limitee. Aucun coefficient officiel NTIE n'est disponible ; aucune ponderation n'a ete inventee.",
    }


def _evolution(base: dict[str, Any], counts: dict[str, Any]) -> list[dict[str, Any]]:
    coverage = base.get("coverage") or {}
    scenarios = (
        ("today", "Aujourd'hui", ()),
        ("after_40", "Apres 40 sites", ("sites_40",)),
        ("after_300", "Apres 300 sites", ("sites_40", "sites_300")),
        ("after_20476", "Apres 20 476 sites", ("sites_40", "sites_300", "sites_20476")),
        ("after_ccn", "Apres CCN", ("sites_40", "sites_300", "sites_20476", "ccn")),
    )
    result = []
    for code, label, programs in scenarios:
        result.append({
            "id": code,
            "label": label,
            "documented_assets": sum(counts["by_program"].get(p, 0) for p in programs) if programs else counts["fdsu_sites"] + counts["ccn"],
            "coverage_rate_pct": _value(coverage.get("coverage_rate_pct")) if code == "today" else None,
            "population_covered": _value(coverage.get("population_covered")) if code == "today" else None,
            "projected_impact": None,
            "method": "current_observation" if code == "today" else "registry_program_presence_only",
            "note": None if code == "today" else "Le Registry documente les actifs, mais aucune hypothese d'impact territorial n'est disponible ; aucune projection n'est inventee.",
        })
    return result


def build_profile(entity_id: str) -> dict[str, Any] | None:
    base = multiscale.build_entity_intelligence(entity_id)
    if not base:
        return None
    entity = base["entity"]
    counts = _asset_counts(entity)
    indicators = _build_indicators(base, counts)
    score = _score(base, indicators)
    return {
        "_meta": {"engine": ENGINE_VERSION, "generated_at": _now(), "data_first": True, "no_invented_values": True},
        "entity": entity,
        "breadcrumb": base.get("breadcrumb"),
        "indicators": indicators,
        "indicator_index": {item["id"]: item for item in indicators},
        "score": score,
        "evolution": _evolution(base, counts),
        "rankings": {"status": "available_on_comparable_documented_values_only", "items": []},
        "map": base.get("map"),
        "children": base.get("children") or [],
        "data_quality": {
            "available": sum(1 for item in indicators if item["value"] is not None),
            "unavailable": sum(1 for item in indicators if item["value"] is None),
            "total": len(indicators),
            "rule": "Une valeur absente reste null et n'entre dans aucun score.",
        },
        "explainability": {
            "sources": base.get("sources") or [],
            "indicator_contract": ["source", "version", "date", "confidence", "quality", "method"],
            "score": score,
            "ndci": (base.get("coverage") or {}).get("ndci"),
            "limits": (base.get("explainability") or {}).get("limits"),
            "dependencies": ["National Asset Registry", "Territorial Intelligence multi-echelle", "Territorial Impact Engine", "Program Lifecycle Engine", "Spatial Decision Graph"],
        },
    }


def list_profiles(level: str | None = None, limit: int = 100) -> dict[str, Any]:
    if level and level not in SUPPORTED_LEVELS:
        raise ValueError(f"Niveau non supporte: {level}")
    assets = registry.asset_snapshot()
    names: set[tuple[str, str]] = set()
    levels = (level,) if level else ("province", "territoire")
    for current in levels:
        for asset in assets:
            territory = asset.get("territory") or {}
            keys = (current,) if current not in {"secteur", "chefferie", "collectivite"} else (current, "collectivite")
            for key in keys:
                value = territory.get(key)
                if value:
                    names.add((current, str(value)))
    items = [{"id": f"{lvl.upper()}-{name}", "level": lvl, "name": name, "status": "documented_in_registry"} for lvl, name in sorted(names)[:limit]]
    return {"_meta": {"engine": ENGINE_VERSION, "count": len(items), "supported_levels": list(SUPPORTED_LEVELS)}, "profiles": items}


def indicator_section(profile: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    return {key: profile["indicator_index"][key] for key in keys}
