from __future__ import annotations

from pathlib import Path

from .models import ZoneDefinition, ZonesFDSUConfig


def load_zones_config(path: str | Path) -> ZonesFDSUConfig:
    raw = Path(path).read_text(encoding="utf-8")
    return _parse_simple_yaml(raw)


def _parse_simple_yaml(raw: str) -> ZonesFDSUConfig:
    country_code = "RDC"
    country_name = "Republique Democratique du Congo"
    zones: list[ZoneDefinition] = []

    current_zone: dict[str, object] | None = None
    in_province_list = False

    section = ""
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped == "country:":
            section = "country"
            continue
        if stripped == "zones:":
            section = "zones"
            continue

        if section == "country" and stripped.startswith("code:"):
            country_code = stripped.split(":", 1)[1].strip().strip('"')
            continue

        if section == "country" and stripped.startswith("name:"):
            country_name = stripped.split(":", 1)[1].strip().strip('"')
            continue

        if stripped.startswith("- code:"):
            if current_zone is not None:
                zones.append(
                    ZoneDefinition(
                        code=str(current_zone["code"]),
                        name=str(current_zone["nom"]),
                        color=str(current_zone["couleur"]),
                        provinces=list(current_zone["provinces"]),
                    )
                )
            current_zone = {
                "code": stripped.split(":", 1)[1].strip().strip('"'),
                "nom": "",
                "couleur": "",
                "provinces": [],
            }
            in_province_list = False
            continue

        if current_zone is None:
            continue

        if stripped.startswith("nom:"):
            current_zone["nom"] = stripped.split(":", 1)[1].strip().strip('"')
            in_province_list = False
            continue

        if stripped.startswith("couleur:"):
            current_zone["couleur"] = stripped.split(":", 1)[1].strip().strip('"')
            in_province_list = False
            continue

        if stripped.startswith("provinces:"):
            in_province_list = True
            continue

        if in_province_list and stripped.startswith("-"):
            province_name = stripped[1:].strip().strip('"')
            if province_name:
                current_zone["provinces"].append(province_name)

    if current_zone is not None:
        zones.append(
            ZoneDefinition(
                code=str(current_zone["code"]),
                name=str(current_zone["nom"]),
                color=str(current_zone["couleur"]),
                provinces=list(current_zone["provinces"]),
            )
        )

    return ZonesFDSUConfig(country_code=country_code, country_name=country_name, zones=zones)


def build_zone_index(config: ZonesFDSUConfig) -> dict[str, str]:
    index: dict[str, str] = {}
    for zone in config.zones:
        for province in zone.provinces:
            index[_normalize_name(province)] = zone.code
    return index


def build_zone_name_index(config: ZonesFDSUConfig) -> dict[str, str]:
    return {zone.code: zone.name for zone in config.zones}


def _normalize_name(value: str) -> str:
    normalized = value.strip().lower()
    replacements = str.maketrans(
        {
            "é": "e",
            "è": "e",
            "ê": "e",
            "ë": "e",
            "à": "a",
            "â": "a",
            "ä": "a",
            "î": "i",
            "ï": "i",
            "ô": "o",
            "ö": "o",
            "ù": "u",
            "û": "u",
            "ü": "u",
            "ç": "c",
        }
    )
    normalized = normalized.translate(replacements)
    normalized = " ".join(normalized.replace("_", " ").split())
    normalized = normalized.replace("kasaï", "kasai")
    return normalized


def normalize_province_name(value: str) -> str:
    return _normalize_name(value)
