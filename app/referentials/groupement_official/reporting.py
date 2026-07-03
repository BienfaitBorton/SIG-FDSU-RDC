from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import GroupementFactSheet, GroupementQualityReport, GroupementReferentialReport


class GroupementReportWriter:
    def write_json(self, data: dict[str, Any], path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return output

    def write_referential_json(self, report: GroupementReferentialReport, path: str | Path) -> Path:
        return self.write_json(report.to_dict(), path)

    def write_fact_sheets_json(self, fact_sheets: list[GroupementFactSheet], path: str | Path) -> Path:
        return self.write_json(
            {"groupement_fact_sheets": [item.to_dict() for item in fact_sheets], "count": len(fact_sheets)},
            path,
        )

    def write_quality_json(self, quality: GroupementQualityReport, path: str | Path) -> Path:
        return self.write_json(quality.to_dict(), path)

    def write_markdown(self, report: GroupementReferentialReport, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(self.to_markdown(report), encoding="utf-8")
        return output

    def to_markdown(self, report: GroupementReferentialReport) -> str:
        q = report.quality
        lines = [
            "# Referentiel Officiel des Groupements",
            "",
            f"- Source: {report.source_file}",
            f"- Date: {report.generated_at.isoformat(timespec='seconds')}",
            f"- Groupements: {q.groupement_count}",
            f"- Rattaches: {q.attached_count}",
            f"- Orphelins: {q.orphan_count}",
            f"- Anomalies: {len(q.anomalies)}",
            f"- Score global: {q.global_score}",
            "",
            "## Qualite",
            "",
            f"- Sans collectivite parente: {q.orphan_count}",
            f"- Sans territoire: {q.missing_territory_count}",
            f"- Sans province: {q.missing_province_count}",
            f"- Sans zone FDSU: {q.missing_zone_count}",
            f"- Doublons: {q.duplicate_count}",
            f"- Geometries invalides: {q.invalid_geometry_count}",
            f"- Codes manquants: {q.missing_code_count}",
            f"- Incoherences attributs/rattachement: {q.inconsistency_count}",
            "",
            "## Index collectivites",
            "",
            "| Collectivite | Type | Territoire | Province | Zone | Groupements |",
            "|---|---|---|---|---|---:|",
        ]
        for item in report.collectivity_groupement_index.get("collectivites", []):
            lines.append(
                f"| {item['collectivite_parent']} | {item['type_collectivite_parent']} | {item['territoire']} | "
                f"{item['province']} | {item['zone_fdsu']} | {item['nombre_groupements']} |"
            )

        lines.extend(["", "## Groupements", "", "| Nom | Collectivite | Territoire | Province | Zone | Code | Qualite |", "|---|---|---|---|---|---|---:|"])
        for item in report.groupement_referential:
            lines.append(
                f"| {item.nom} | {item.collectivite_parent} | {item.territoire} | {item.province} | "
                f"{item.zone_fdsu} | {item.code_officiel or ''} | {item.qualite} |"
            )

        if q.anomalies:
            lines.extend(["", "## Registre des anomalies", ""])
            lines.append("| Entite | Type | Code | Province | Territoire | Collectivite | Probleme | Cause | Statut | Suggestion |")
            lines.append("|---|---|---|---|---|---|---|---|---|---|")
            for anomaly in q.anomalies:
                lines.append(
                    f"| {anomaly.entite} | {anomaly.type} | {anomaly.code or ''} | {anomaly.province} | {anomaly.territoire} | "
                    f"{anomaly.collectivite_parent} | {anomaly.probleme} | {anomaly.cause} | "
                    f"{anomaly.statut} | {anomaly.suggestion} |"
                )
        return "\n".join(lines)
