from __future__ import annotations

import json
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent.parent
NOMENCLATURE_PATH = BASE_DIR / "data" / "reports" / "fdsu_nomenclature.json"
FDSU_CODE_FORMAT = "FDSU_<CODE_ZONE>_<CODE_PROVINCE>_<CODE_TERRITOIRE>_<CODE_SITE>"


def normalize_name(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return "".join(char for char in text if char.isalnum())


@lru_cache(maxsize=1)
def load_nomenclature() -> dict[str, Any]:
    if not NOMENCLATURE_PATH.exists():
        return {"zones": [], "provinces": [], "territoires": []}
    return json.loads(NOMENCLATURE_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def province_index() -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for province in load_nomenclature().get("provinces", []):
        index[normalize_name(province.get("nom"))] = province
        index[normalize_name(province.get("code"))] = province
    return index


@lru_cache(maxsize=1)
def territory_index() -> dict[tuple[str, str], dict[str, Any]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for territory in load_nomenclature().get("territoires", []):
        province_key = normalize_name(territory.get("province"))
        province_code_key = normalize_name(territory.get("province_code"))
        territory_key = normalize_name(territory.get("nom"))
        index[(province_key, territory_key)] = territory
        index[(province_code_key, territory_key)] = territory
    return index


def find_province(value: Any) -> dict[str, Any] | None:
    return province_index().get(normalize_name(value))


def find_territory(name: Any, province: Any = None, province_code: Any = None) -> dict[str, Any] | None:
    territory_key = normalize_name(name)
    for parent in (province, province_code):
        item = territory_index().get((normalize_name(parent), territory_key))
        if item:
            return item
    for (parent_key, item_key), item in territory_index().items():
        if item_key == territory_key:
            return item
    return None


def fdsu_zone_code_for_entity(item: dict[str, Any]) -> str | None:
    province_name = item.get("province") or (item.get("nom") if item.get("type") == "Province" or item.get("niveau") == "Province" else None)
    province = find_province(province_name) or find_province(item.get("code_province_fdsu")) or find_province(item.get("code"))
    if province:
        return str(province.get("zone_fdsu") or "").upper()
    zone = str(item.get("zone_fdsu") or item.get("zone") or "").upper()
    return zone if zone in {"ND", "SD", "CE", "OT", "ET"} else None


def enrich_entity(item: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(item)
    entity_name = enriched.get("nom") or enriched.get("name")
    entity_level = str(enriched.get("niveau") or enriched.get("type") or "").lower()
    is_province_entity = entity_level == "province" or (not enriched.get("province") and find_province(entity_name) is not None)
    province_name = enriched.get("province") or entity_name
    province = find_province(province_name) or find_province(enriched.get("code_province_fdsu"))
    if province:
        enriched["zone_fdsu"] = province.get("zone_fdsu")
        enriched["zone_nom"] = province.get("zone_nom")
        enriched["code_province_fdsu"] = province.get("code")
    elif fdsu_zone_code_for_entity(enriched):
        enriched["zone_fdsu"] = fdsu_zone_code_for_entity(enriched)

    if not is_province_entity:
        territory = find_territory(enriched.get("territoire") or entity_name, province_name, enriched.get("code_province_fdsu"))
        if territory:
            enriched["code_territoire_fdsu"] = territory.get("code")
            enriched["code_province_fdsu"] = territory.get("province_code")
            enriched["zone_fdsu"] = territory.get("zone_fdsu")

    enriched["fdsu_codification_format"] = FDSU_CODE_FORMAT
    return enriched
