from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import (
    ProvinceCanonicalEntity,
    ProvinceFactSheet,
    ProvinceOfficialRunResult,
    ProvinceQualityReport,
    ProvinceReferentialReport,
)
from .reader import ProvinceKMZReader
from .reporting import ProvinceReportWriter
from .zones import build_zone_index, build_zone_name_index, load_zones_config, normalize_province_name


class ProvinceReferentialValidationError(RuntimeError):
    def __init__(self, message: str, anomalies: dict[str, Any]) -> None:
        super().__init__(message)
        self.anomalies = anomalies


class ProvinceOfficialReferentialService:
    def __init__(self) -> None:
        self.reader = ProvinceKMZReader()
        self.writer = ProvinceReportWriter()

    def run(
        self,
        source_path: str | Path,
        output_dir: str | Path = Path("data/reports/province_official"),
        zones_config_path: str | Path = Path("app/referentials/config/zones_fdsu.yaml"),
        expected_province_count: int | None = None,
    ) -> ProvinceOfficialRunResult:
        source = Path(source_path)
        output = Path(output_dir)

        config = load_zones_config(zones_config_path)
        zone_by_province = build_zone_index(config)
        zone_name_by_code = build_zone_name_index(config)

        source_records = self.reader.read(source)
        canonical_entities = self._build_canonical_entities(source_records, zone_by_province, source.name)
        if expected_province_count is not None and len(canonical_entities) != expected_province_count:
            anomalies = self._collect_validation_anomalies(
                source_records=source_records,
                canonical_entities=canonical_entities,
                expected_province_names=[province for zone in config.zones for province in zone.provinces],
                expected_count=expected_province_count,
            )
            raise ProvinceReferentialValidationError(
                f"Nombre de provinces invalide: {len(canonical_entities)} au lieu de {expected_province_count}.",
                anomalies=anomalies,
            )

        fact_sheets = self._build_fact_sheets(canonical_entities, zone_name_by_code)
        quality = self._build_quality_report(source.name, canonical_entities)

        report = ProvinceReferentialReport(
            country={"code": config.country_code, "name": config.country_name},
            source_file=source.name,
            generated_at=datetime.now(timezone.utc),
            province_referential=canonical_entities,
            province_fact_sheets=fact_sheets,
            quality=quality,
        )

        referential_json_path = output / "province_referential_official.json"
        fact_sheets_json_path = output / "province_fact_sheets.json"
        quality_json_path = output / "province_quality_report.json"
        report_markdown_path = output / "province_referential_report.md"
        files_report_path = output / "province_files_report.json"

        self.writer.write_referential_json(report, referential_json_path)
        self.writer.write_fact_sheets_json(report.province_fact_sheets, fact_sheets_json_path)
        self.writer.write_quality_json(report.quality, quality_json_path)
        self.writer.write_markdown(report, report_markdown_path)

        files_report = {
            "source": source.name,
            "created_files": [
                str(referential_json_path),
                str(fact_sheets_json_path),
                str(quality_json_path),
                str(report_markdown_path),
            ],
            "generated_at": report.generated_at.isoformat(timespec="seconds"),
        }
        self.writer.write_json(files_report, files_report_path)

        return ProvinceOfficialRunResult(
            source_path=source,
            report=report,
            referential_json_path=referential_json_path,
            quality_json_path=quality_json_path,
            fact_sheets_json_path=fact_sheets_json_path,
            report_markdown_path=report_markdown_path,
            files_report_path=files_report_path,
        )

    def _collect_validation_anomalies(
        self,
        source_records,
        canonical_entities: list[ProvinceCanonicalEntity],
        expected_province_names: list[str],
        expected_count: int,
    ) -> dict[str, Any]:
        expected_normalized_to_official = {
            normalize_province_name(name): name for name in expected_province_names
        }
        expected_set = set(expected_normalized_to_official.keys())
        found_set = {normalize_province_name(entity.nom) for entity in canonical_entities}

        missing = sorted(
            expected_normalized_to_official[name]
            for name in (expected_set - found_set)
        )
        unexpected = sorted(
            entity.nom
            for entity in canonical_entities
            if normalize_province_name(entity.nom) not in expected_set
        )

        source_name_counts = Counter(normalize_province_name(record.name) for record in source_records)
        duplicate_names = sorted(
            expected_normalized_to_official.get(name, name)
            for name, count in source_name_counts.items()
            if count > 1 and name in expected_set
        )

        unmapped_candidates = sorted(
            record.name
            for record in source_records
            if normalize_province_name(record.name) not in expected_set
        )

        return {
            "expected_count": expected_count,
            "found_count": len(canonical_entities),
            "missing_provinces": missing,
            "unexpected_provinces": unexpected,
            "duplicate_province_names_in_source": duplicate_names,
            "non_provincial_or_unmapped_objects": unmapped_candidates,
        }

    def _build_canonical_entities(
        self,
        source_records,
        zone_by_province: dict[str, str],
        source_name: str,
    ) -> list[ProvinceCanonicalEntity]:
        filtered: dict[str, ProvinceCanonicalEntity] = {}

        for record in source_records:
            normalized_name = normalize_province_name(record.name)
            zone_code = zone_by_province.get(normalized_name)
            if not zone_code:
                continue

            code_officiel = self._extract_code(record)
            chef_lieu = self._extract_capital(record)
            quality = self._compute_entity_quality(record.geometry, code_officiel, chef_lieu)

            canonical = ProvinceCanonicalEntity(
                canonical_id=f"RDC-{zone_code}-PROV-{normalized_name.replace(' ', '_').upper()}",
                nom=record.name,
                code_officiel=code_officiel,
                niveau="Province",
                chef_lieu=chef_lieu,
                zone_fdsu=zone_code,
                source=source_name,
                statut="official_candidate",
                qualite=quality,
                geometry=record.geometry,
                metadata={
                    "description": record.description,
                    "description_values": record.description_values,
                    "extended_data": record.extended_data,
                    "styles": {
                        "style_url": record.style_url,
                        "style_inline": record.style_inline,
                        "resolved_style": record.metadata.get("resolved_style", {}),
                    },
                    "folder": record.folder,
                    "geometry_type": record.geometry_type,
                },
            )

            # Keep first occurrence to preserve original geometry and attributes.
            if normalized_name not in filtered:
                filtered[normalized_name] = canonical

        return sorted(filtered.values(), key=lambda item: (item.zone_fdsu, item.nom.lower()))

    def _extract_code(self, record) -> str | None:
        for key in (
            "code_officiel",
            "CODE_OFFICIEL",
            "code",
            "CODE",
            "code_ins",
            "CODE_INS",
            "code_province",
            "CODE_PROVINCE",
        ):
            value = record.extended_data.get(key)
            if value:
                return str(value).strip()
        for key in ("code", "code_officiel", "code province"):
            value = record.description_values.get(key)
            if value:
                return str(value).strip()
        return None

    def _extract_capital(self, record) -> str | None:
        for key in (
            "chef_lieu",
            "CHEF_LIEU",
            "chef-lieu",
            "CHEF-LIEU",
            "capitale",
            "CAPITALE",
        ):
            value = record.extended_data.get(key)
            if value:
                return str(value).strip()
        for key in ("chef lieu", "chef_lieu", "capitale"):
            value = record.description_values.get(key)
            if value:
                return str(value).strip()
        return None

    def _compute_entity_quality(self, geometry, code: str | None, chef_lieu: str | None) -> float:
        score = 100.0
        if not geometry:
            score -= 35.0
        if not code:
            score -= 15.0
        if not chef_lieu:
            score -= 10.0
        return max(0.0, round(score, 2))

    def _build_fact_sheets(self, entities: list[ProvinceCanonicalEntity], zone_name_by_code: dict[str, str]) -> list[ProvinceFactSheet]:
        fact_sheets: list[ProvinceFactSheet] = []
        for entity in entities:
            flags: list[str] = []
            if entity.geometry is None:
                flags.append("missing_geometry")
            if not entity.chef_lieu:
                flags.append("missing_chef_lieu")
            if not entity.code_officiel:
                flags.append("missing_code")

            fact_sheets.append(
                ProvinceFactSheet(
                    canonical_id=entity.canonical_id,
                    nom=entity.nom,
                    zone_fdsu=entity.zone_fdsu,
                    zone_nom=zone_name_by_code.get(entity.zone_fdsu, "Unknown"),
                    code_officiel=entity.code_officiel,
                    chef_lieu=entity.chef_lieu,
                    geometry_type=(entity.geometry or {}).get("type") if entity.geometry else None,
                    source=entity.source,
                    quality_flags=flags,
                    metadata={
                        "niveau": entity.niveau,
                        "statut": entity.statut,
                        "qualite": entity.qualite,
                    },
                )
            )
        return fact_sheets

    def _build_quality_report(self, source_file: str, entities: list[ProvinceCanonicalEntity]) -> ProvinceQualityReport:
        names = [normalize_province_name(item.nom) for item in entities]
        counts = Counter(names)
        duplicate_names = sorted([name for name, count in counts.items() if count > 1])

        without_geometry = sum(1 for item in entities if not item.geometry)
        without_capital = sum(1 for item in entities if not item.chef_lieu)
        without_code = sum(1 for item in entities if not item.code_officiel)

        total = len(entities)
        penalties = (without_geometry * 3.0) + (without_capital * 1.0) + (without_code * 1.0) + (len(duplicate_names) * 4.0)
        raw = 100.0 - (penalties / max(total, 1))
        global_score = round(max(0.0, raw), 2)

        return ProvinceQualityReport(
            source_file=source_file,
            generated_at=datetime.now(timezone.utc),
            province_count=total,
            provinces_without_geometry=without_geometry,
            provinces_without_capital=without_capital,
            provinces_without_code=without_code,
            duplicates=len(duplicate_names),
            duplicate_names=duplicate_names,
            global_score=global_score,
        )
