from __future__ import annotations

import json
from pathlib import Path

from .models import ProvinceFactSheet, ProvinceQualityReport, ProvinceReferentialReport


class ProvinceReportWriter:
    def write_json(self, data: dict, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return output

    def write_referential_json(self, report: ProvinceReferentialReport, path: str | Path) -> Path:
        return self.write_json(report.to_dict(), path)

    def write_fact_sheets_json(self, fact_sheets: list[ProvinceFactSheet], path: str | Path) -> Path:
        payload = {
            "province_fact_sheets": [item.to_dict() for item in fact_sheets],
            "count": len(fact_sheets),
        }
        return self.write_json(payload, path)

    def write_quality_json(self, quality: ProvinceQualityReport, path: str | Path) -> Path:
        return self.write_json(quality.to_dict(), path)

    def write_markdown(self, report: ProvinceReferentialReport, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(self.to_markdown(report), encoding="utf-8")
        return output

    def to_markdown(self, report: ProvinceReferentialReport) -> str:
        lines = [
            "# Referentiel Officiel des Provinces",
            "",
            f"- Pays: {report.country['code']} - {report.country['name']}",
            f"- Source: {report.source_file}",
            f"- Date: {report.generated_at.isoformat(timespec='seconds')}",
            f"- Provinces: {len(report.province_referential)}",
            "",
            "## Hierarchie",
            "",
            "RDC -> Zone FDSU -> Province",
            "",
            "## Qualite",
            "",
            f"- Provinces sans geometrie: {report.quality.provinces_without_geometry}",
            f"- Provinces sans chef-lieu: {report.quality.provinces_without_capital}",
            f"- Provinces sans code: {report.quality.provinces_without_code}",
            f"- Doublons: {report.quality.duplicates}",
            f"- Score global: {report.quality.global_score}",
            "",
            "## Provinces",
            "",
            "| Zone | Province | Code | Chef-lieu | Geometrie | Qualite |",
            "|---|---|---|---|---|---:|",
        ]

        for item in report.province_referential:
            geom = (item.geometry or {}).get("type", "None") if item.geometry else "None"
            lines.append(
                f"| {item.zone_fdsu} | {item.nom} | {item.code_officiel or '-'} | {item.chef_lieu or '-'} | {geom} | {item.qualite} |"
            )

        return "\n".join(lines)
