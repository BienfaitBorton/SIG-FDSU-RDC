from __future__ import annotations

import json
from pathlib import Path

from .models import CityFactSheet, CityQualityReport, CityReferentialReport


class CityReportWriter:
    def write_json(self, data: dict, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return output

    def write_referential_json(self, report: CityReferentialReport, path: str | Path) -> Path:
        return self.write_json(report.to_dict(), path)

    def write_fact_sheets_json(self, fact_sheets: list[CityFactSheet], path: str | Path) -> Path:
        payload = {
            "city_fact_sheets": [item.to_dict() for item in fact_sheets],
            "count": len(fact_sheets),
        }
        return self.write_json(payload, path)

    def write_quality_json(self, quality: CityQualityReport, path: str | Path) -> Path:
        return self.write_json(quality.to_dict(), path)

    def write_markdown(self, report: CityReferentialReport, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(self.to_markdown(report), encoding="utf-8")
        return output

    def to_markdown(self, report: CityReferentialReport) -> str:
        lines = [
            "# Referentiel Officiel des Villes",
            "",
            f"- Source: {report.source_file}",
            f"- Date: {report.generated_at.isoformat(timespec='seconds')}",
            f"- Villes: {len(report.city_referential)}",
            "",
            "## Qualite",
            "",
            f"- Villes orphelines: {report.quality.orphan_city_count}",
            f"- Conflits multi-province: {report.quality.multi_province_conflicts}",
            f"- Conflits multi-zone: {report.quality.multi_zone_conflicts}",
            f"- Geometries vides: {report.quality.empty_geometry_count}",
            f"- Doublons: {report.quality.duplicate_count}",
            f"- Score global: {report.quality.global_score}",
            "",
            "## Villes",
            "",
            "| Ville | Province | Zone | Geometrie | Qualite |",
            "|---|---|---|---|---:|",
        ]

        for item in report.city_referential:
            geometry_type = (item.geometry or {}).get("type", "None") if item.geometry else "None"
            lines.append(
                f"| {item.nom} | {item.province} | {item.zone_fdsu} | {geometry_type} | {item.qualite} |"
            )

        if report.quality.anomalies:
            lines.extend(["", "## Anomalies", ""])
            for issue in report.quality.anomalies:
                lines.append(f"- {issue}")

        return "\n".join(lines)
