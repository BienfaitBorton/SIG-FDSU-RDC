from __future__ import annotations

import json
from pathlib import Path

from .models import TerritoryHierarchyReport


class TerritoryHierarchyReportWriter:
    def write_json(self, report: TerritoryHierarchyReport, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return output

    def write_markdown(self, report: TerritoryHierarchyReport, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(self.to_markdown(report), encoding="utf-8")
        return output

    def to_markdown(self, report: TerritoryHierarchyReport) -> str:
        lines = [
            "# Rapport Territoires hiérarchiques (KMZ Zones)",
            "",
            f"- Source: {report.source_file}",
            f"- Généré le: {report.generated_at.isoformat(timespec='seconds')}",
            f"- Territoires: {report.territory_count}",
            f"- Incohérences: {report.incoherence_count}",
            "",
            "## Territoires",
            "",
            "| Nom | Province | Zone FDSU | Chemin hiérarchique | Géométrie | Score | Incohérences |",
            "|---|---|---|---|---|---:|---|",
        ]
        for item in report.territories:
            geom_type = (item.geometry or {}).get("type", "Non renseignée") if item.geometry else "Non renseignée"
            path_text = " -> ".join(item.chemin_hierarchique)
            inco_text = "; ".join(item.incoherences) if item.incoherences else "Aucune"
            lines.append(
                f"| {item.nom} | {item.province} | {item.zone_fdsu} | {path_text} | {geom_type} | {item.score_qualite} | {inco_text} |"
            )
        return "\n".join(lines)
