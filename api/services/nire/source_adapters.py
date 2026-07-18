"""Adaptateurs NIRE Phase 2 en lecture seule, charges uniquement a la demande."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Iterable

from api.services.national_semantic_classification_engine import normalize_name

from .adapters import SourceAdapter
from .models import EntityReference

ROOT = Path(__file__).resolve().parents[3]
RowsProvider = Callable[[], Iterable[dict[str, Any]]]


def _pick(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if row.get(key) not in (None, ""):
            return row[key]
    return None


class ReadOnlySourceAdapter(SourceAdapter):
    """Projection sans ecriture d'un fournisseur reel ou injecte."""

    source_name = "SOURCE"
    entity_type = "ENTITY"
    id_keys = ("id",)

    def __init__(self, provider: RowsProvider | None = None, *, source_version: str = "unknown") -> None:
        self._provider = provider or self.default_provider
        self.source_version = source_version

    def default_provider(self) -> Iterable[dict[str, Any]]:
        return ()

    def get_source_name(self) -> str:
        return self.source_name

    def get_entity_type(self) -> str:
        return self.entity_type

    def get_entities(self) -> Iterable[dict[str, Any]]:
        return (dict(row) for row in self._provider())

    def source_id(self, row: dict[str, Any]) -> str:
        value = _pick(row, *self.id_keys)
        if value is None:
            raise ValueError(f"Identifiant source absent pour {self.source_name}")
        return str(value)

    def get_entity_by_id(self, entity_id: str) -> dict[str, Any] | None:
        return next((row for row in self.get_entities() if self.source_id(row) == str(entity_id)), None)

    def extract_identity_features(self, row: dict[str, Any]) -> dict[str, Any]:
        name = str(_pick(row, "name", "nom", "original_name", "site_name", "infra_name", "line_name", "polygon_name", "label") or "").strip()
        attrs: dict[str, Any] = {
            "name": name, "normalized_name": normalize_name(name),
            "institutional_id": _pick(row, "institutional_id", "official_code", "source_id", "site_code", "infra_code", "line_code", "polygon_code", "code_officiel"),
            "latitude": _pick(row, "latitude", "lat"), "longitude": _pick(row, "longitude", "lon", "lng"),
            "province": _pick(row, "province", "province_name"),
            "territory": _pick(row, "territory", "territoire", "territory_name"),
            "locality": _pick(row, "locality", "localite", "locality_name"),
            "operator": _pick(row, "operator", "operator_code", "operator_name"),
            "technology": _pick(row, "technology", "technologie"),
            "geometry_kind": _pick(row, "geometry_kind", "geometry_type") or "POINT",
            "quality_status": _pick(row, "quality_status", "validation_status", "geometry_status", "review_status") or "UNKNOWN",
            "provenance": _pick(row, "provenance", "data_source", "source") or self.source_name,
            "source_version": _pick(row, "source_version", "schema_version", "engine_version") or self.source_version,
        }
        for key in ("province", "territory", "locality", "operator", "institutional_id"):
            if attrs.get(key) is not None:
                attrs[key] = normalize_name(str(attrs[key]))
        return attrs

    def normalize_entity(self, row: dict[str, Any]) -> EntityReference:
        return EntityReference(self.source_id(row), self.source_name, str(row.get("entity_type") or self.entity_type), self.extract_identity_features(row))


class CeniSourceAdapter(ReadOnlySourceAdapter):
    source_name, entity_type, id_keys = "CENI", "CENI_SITE", ("asset_uid", "source_record_id")

    def __init__(self, provider: RowsProvider | None = None, *, include_quarantine: bool = False, source_version: str = "ceni_registry_v1") -> None:
        self.include_quarantine = include_quarantine
        super().__init__(provider, source_version=source_version)

    def default_provider(self):
        from api.services.ceni_registry_service import registry
        rows = registry().get("assets", ())
        return (row for row in rows if self.include_quarantine or row.get("geometry_status") != "quarantined_sentinel_coordinates")

    def extract_identity_features(self, row):
        projected = dict(row)
        projected.update(row.get("administrative_attachment") or {})
        projected["institutional_id"] = row.get("asset_uid")
        projected["quality_status"] = "QUARANTINE" if row.get("quarantine") else row.get("geometry_status")
        attrs = super().extract_identity_features(projected)
        attrs["resolution_candidate"] = bool((row.get("quarantine") or {}).get("resolution_candidate"))
        if attrs["latitude"] in (0, 0.0, "0") and attrs["longitude"] in (0, 0.0, "0"):
            attrs["latitude"] = attrs["longitude"] = None
        return attrs


class EducationSourceAdapter(ReadOnlySourceAdapter):
    source_name, entity_type, id_keys = "EDUCATION", "SCHOOL", ("education_id", "source_id")

    def __init__(self, provider: RowsProvider | None = None, *, include_quarantine: bool = False, source_version: str = "education-referential-provisional-v1") -> None:
        self.include_quarantine = include_quarantine
        super().__init__(provider, source_version=source_version)

    def default_provider(self):
        from api.services.education_referential_service import list_establishments
        rows=list(list_establishments(limit=100_000)["establishments"])
        if self.include_quarantine:
            from api.services.ceni_registry_service import registry
            for row in registry().get("assets",()):
                if row.get("normalized_category")=="SCHOOL" and row.get("geometry_status")=="quarantined_sentinel_coordinates":
                    admin=row.get("administrative_attachment") or {}
                    rows.append({"education_id":f"EDU-{row.get('asset_uid')}","source_id":row.get("asset_uid"),"original_name":row.get("name"),"province":admin.get("province"),"territory":admin.get("territory"),"validation_status":"QUARANTINE","latitude":None,"longitude":None,"provenance":{"source":"CENI","derived_projection":True}})
        return rows

    def extract_identity_features(self, row):
        projected = dict(row, name=row.get("original_name"), institutional_id=row.get("source_id"))
        attrs = super().extract_identity_features(projected)
        attrs["provenance"] = row.get("provenance") or {"source": row.get("source_system", "CENI")}
        return attrs


class HealthSourceAdapter(ReadOnlySourceAdapter):
    source_name, entity_type, id_keys = "HEALTH", "HEALTH_FACILITY", ("id", "official_code")
    def default_provider(self):
        from api.services.health_service import list_facilities
        return list_facilities(limit=100_000)


class TelecomSourceAdapter(ReadOnlySourceAdapter):
    source_name, entity_type, id_keys = "TELECOM", "TELECOM", ("id", "infra_code", "line_code", "polygon_code")

    def default_provider(self):
        from api.services.telecom_service import list_infrastructure, list_network_lines, list_coverage_polygons
        def tagged(rows, kind):
            for row in rows:
                yield {**row, "geometry_kind": kind}
        return (*tagged(list_infrastructure(limit=100_000), "POINT"), *tagged(list_network_lines(limit=100_000), "LINESTRING"), *tagged(list_coverage_polygons(limit=100_000), "POLYGON"))

    def normalize_entity(self, row):
        kind = str(_pick(row, "geometry_kind", "geometry_type") or "POINT").upper()
        entity_type = "TELECOM_SITE" if kind == "POINT" else "TELECOM_NETWORK_GEOMETRY"
        base = super().normalize_entity(row)
        return EntityReference(base.entity_id, base.source_name, entity_type, base.attributes)


class FdsuSiteSourceAdapter(ReadOnlySourceAdapter):
    source_name, entity_type, id_keys = "FDSU", "FDSU_SITE", ("site_id", "id", "code")
    def default_provider(self):
        document = json.loads((ROOT / "data/programs/sites_20476/sites_20476.json").read_text(encoding="utf-8"))
        return document.get("sites", document.get("features", ()))


class AdministrativeSourceAdapter(ReadOnlySourceAdapter):
    source_name, entity_type, id_keys = "ADMINISTRATION", "ADMIN_ENTITY", ("entity_id", "canonical_id", "id", "code_officiel", "code")

    def default_provider(self):
        specs = (
            ("province_official/province_referential_official.json", "province_referential", "PROVINCE"),
            ("city_official/city_referential_official.json", "city_referential", "CITY"),
            ("collectivity_official/collectivity_referential_official.json", "collectivity_referential", None),
            ("groupement_official/groupement_referential_official.json", "groupement_referential", "GROUPEMENT"),
            ("locality_official/locality_referential_official.json", "locality_referential", "LOCALITY"),
        )
        rows=[]
        for relative,key,level in specs:
            path=ROOT / "data/reports" / relative
            if not path.exists(): continue
            document=json.loads(path.read_text(encoding="utf-8"))
            for row in document.get(key,()):
                inferred=level or ("SECTOR" if "SECTEUR" in str(row.get("type_collectivite","")).upper() else "CHIEFDOM" if "CHEFFER" in str(row.get("type_collectivite","")).upper() else "COLLECTIVITY")
                rows.append({**row,"administrative_level":inferred,"source_version":document.get("generated_at")})
        # Les territoires sont derives des rattachements officiels, sans inventer de geometrie.
        seen=set()
        for row in tuple(rows):
            territory=row.get("territoire")
            if territory and (row.get("province"),territory) not in seen:
                seen.add((row.get("province"),territory)); rows.append({"canonical_id":f"TERRITORY-{normalize_name(str(row.get('province')))}-{normalize_name(str(territory))}","nom":territory,"province":row.get("province"),"administrative_level":"TERRITORY","source":"official administrative attachments"})
        return rows

    def normalize_entity(self, row):
        level = str(_pick(row, "administrative_level", "level", "entity_type", "niveau") or "LOCALITY").upper()
        base = super().normalize_entity(row)
        return EntityReference(base.entity_id, base.source_name, f"ADMIN_{level}", base.attributes)

    def extract_identity_features(self, row):
        attrs = super().extract_identity_features(row)
        attrs["locality_village_equivalence_proven"] = bool(row.get("locality_village_equivalence_proven", False))
        return attrs
