from __future__ import annotations

import json
from pathlib import Path

from .models import SourceCatalogReport


class SourceReportWriter:
    """Writes source catalog reports as JSON and Markdown."""

    def write_json(self, report: SourceCatalogReport, output_path: str | Path) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def write_markdown(self, report: SourceCatalogReport, output_path: str | Path) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_markdown(report), encoding="utf-8")
        return path

    def to_markdown(self, report: SourceCatalogReport) -> str:
        lines = [
            "# Rapport Explorateur de Sources",
            "",
            f"- Source: {report.source_file}",
            f"- Format: {report.source_format}",
            f"- Généré le: {report.generated_at.isoformat(timespec='seconds')}",
            f"- Objets: {report.object_count}",
            f"- Champs: {report.field_count}",
            "",
            "## Catalogue des Données",
            "",
            "| Dossier | Type | Objets | Champs | Géométrie | Qualité | Module SIG conseillé | Tags |",
            "|---|---:|---:|---:|---|---:|---|---|",
        ]

        for folder in report.folders:
            geometry = ", ".join(folder.geometry_types) if folder.geometry_types else "Non renseigné"
            tags = ", ".join(folder.tags) if folder.tags else "Non renseigné"
            lines.append(
                f"| {folder.folder_name} | {folder.dataset_type} | {folder.object_count} | {folder.field_count} | {geometry} | {folder.quality} | {folder.module_sig_conseille} | {tags} |"
            )

        lines.extend([
            "",
            "## Dictionnaire de Données",
            "",
            "| Champ | Type | Nombre de valeurs | Valeurs uniques | Valeurs nulles | Exemple |",
            "|---|---|---:|---:|---:|---|",
        ])

        for entry in report.data_dictionary:
            lines.append(
                f"| {entry.name} | {entry.value_type} | {entry.value_count} | {entry.unique_count} | {entry.null_count} | {entry.example} |"
            )

        if report.warnings:
            lines.extend(["", "## Avertissements", ""])
            for warning in report.warnings:
                lines.append(f"- {warning}")

        return "\n".join(lines)
