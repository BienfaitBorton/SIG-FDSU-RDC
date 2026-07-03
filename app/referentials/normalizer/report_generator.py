from __future__ import annotations

import json
from pathlib import Path

from .normalizer import NormalizationReport


class ReportGenerator:
    """Serializes normalization reports to JSON and Markdown."""

    def to_json_dict(self, report: NormalizationReport) -> dict[str, object]:
        return report.to_dict()

    def write_json(self, path: str | Path, report: NormalizationReport) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(self.to_json_dict(report), ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path

    def to_markdown(self, report: NormalizationReport) -> str:
        lines = [
            f"# Normalization Report - {report.source_name}",
            "",
            f"- Source kind: {report.source_kind.value}",
            f"- Entity count: {report.entity_count}",
            f"- Issue count: {len(report.issues)}",
            f"- Duplicate candidates: {len(report.duplicates)}",
            f"- Orphans: {len(report.orphans)}",
            "",
            "## Statistics",
            "",
        ]
        for section_name in ("by_level", "by_province", "by_territoire"):
            section = report.statistics.get(section_name, {})
            lines.append(f"### {section_name}")
            if section:
                for key, value in section.items():
                    lines.append(f"- {key}: {value}")
            else:
                lines.append("- none")
            lines.append("")

        lines.extend([
            "## Quality",
            "",
        ])
        for key, value in report.quality.items():
            lines.append(f"- {key}: {value}")
        lines.append("")

        lines.extend([
            "## Issues",
            "",
        ])
        if report.issues:
            for issue in report.issues:
                entity_suffix = f" [{issue.entity_id}]" if issue.entity_id else ""
                lines.append(f"- {issue.level.value}/{issue.code.value}{entity_suffix}: {issue.message}")
        else:
            lines.append("- none")
        lines.append("")

        return "\n".join(lines)

    def write_markdown(self, path: str | Path, report: NormalizationReport) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.to_markdown(report), encoding="utf-8")
        return output_path
