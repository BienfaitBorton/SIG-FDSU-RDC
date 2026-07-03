from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import (
    CollectivityFactSheet,
    CollectivityQualityReport,
    CollectivityReferentialReport,
)


class CollectivityReportWriter:
    def write_json(self, data: dict[str, Any], path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return output

    def write_referential_json(self, report: CollectivityReferentialReport, path: str | Path) -> Path:
        return self.write_json(report.to_dict(), path)

    def write_fact_sheets_json(self, fact_sheets: list[CollectivityFactSheet], path: str | Path) -> Path:
        return self.write_json(
            {
                "collectivity_fact_sheets": [item.to_dict() for item in fact_sheets],
                "count": len(fact_sheets),
            },
            path,
        )

    def write_quality_json(self, quality: CollectivityQualityReport, path: str | Path) -> Path:
        return self.write_json(quality.to_dict(), path)

    def write_markdown(self, report: CollectivityReferentialReport, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(self.to_markdown(report), encoding="utf-8")
        return output

    def to_markdown(self, report: CollectivityReferentialReport) -> str:
        lines = [
            "# Referentiel Officiel des Collectivites",
            "",
            f"- Source: {report.source_file}",
            f"- Date: {report.generated_at.isoformat(timespec='seconds')}",
            f"- Secteurs: {report.quality.secteur_count}",
            f"- Chefferies: {report.quality.chefferie_count}",
            f"- Total collectivites: {report.quality.collectivity_count}",
            "",
            "## Qualite",
            "",
            f"- Collectivites sans territoire: {report.quality.missing_territory_count}",
            f"- Collectivites sans province: {report.quality.missing_province_count}",
            f"- Collectivites sans zone: {report.quality.missing_zone_count}",
            f"- Geometries invalides: {report.quality.invalid_geometry_count}",
            f"- Doublons: {report.quality.duplicate_count}",
            f"- Types inconnus: {report.quality.unknown_type_count}",
            f"- Anomalies: {len(report.quality.anomalies)}",
            f"- Score global: {report.quality.global_score}",
            "",
            "## Index territorial",
            "",
            "| Territoire | Province | Zone | Secteurs | Chefferies | Total |",
            "|---|---|---|---:|---:|---:|",
        ]

        for item in report.territory_collectivity_index.get("territories", []):
            lines.append(
                f"| {item['territoire']} | {item['province']} | {item['zone_fdsu']} | "
                f"{len(item['secteurs'])} | {len(item['chefferies'])} | {item['nombre_collectivites']} |"
            )

        lines.extend(
            [
                "",
                "## Collectivites",
                "",
                "| Nom | Type | Province | Territoire | Zone | Code | Qualite |",
                "|---|---|---|---|---|---|---:|",
            ]
        )
        for item in report.collectivity_referential:
            lines.append(
                f"| {item.nom} | {item.type_collectivite} | {item.province} | {item.territoire} | "
                f"{item.zone_fdsu} | {item.code_officiel or ''} | {item.qualite} |"
            )

        if report.quality.anomalies:
            lines.extend(["", "## Registre des anomalies", ""])
            lines.append("| Entite | Type | Province | Probleme | Cause | Statut | Suggestion |")
            lines.append("|---|---|---|---|---|---|---|")
            for anomaly in report.quality.anomalies:
                lines.append(
                    f"| {anomaly.entite} | {anomaly.type} | {anomaly.province} | {anomaly.probleme} | "
                    f"{anomaly.cause} | {anomaly.statut} | {anomaly.suggestion} |"
                )

        return "\n".join(lines)
