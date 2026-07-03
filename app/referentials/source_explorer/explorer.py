from __future__ import annotations

from pathlib import Path

from .analyzer import SourceAnalyzer
from .models import SourceExplorerRunResult
from .readers import SourceReader
from .reporting import SourceReportWriter


class SourceExplorerService:
    """High-level read-only service for geographic source exploration."""

    def __init__(self) -> None:
        self.reader = SourceReader()
        self.analyzer = SourceAnalyzer()
        self.writer = SourceReportWriter()

    def run(
        self,
        source_path: str | Path,
        output_dir: str | Path = Path("data/reports/source_explorer"),
    ) -> SourceExplorerRunResult:
        source = Path(source_path)
        output = Path(output_dir)

        source_format, records, warnings = self.reader.read(source)
        report = self.analyzer.analyze(source, source_format, records, warnings)

        report_json_path = output / f"{source.stem}.catalog.json"
        report_markdown_path = output / f"{source.stem}.catalog.md"
        self.writer.write_json(report, report_json_path)
        self.writer.write_markdown(report, report_markdown_path)

        latest_json = output / "latest.catalog.json"
        latest_md = output / "latest.catalog.md"
        self.writer.write_json(report, latest_json)
        self.writer.write_markdown(report, latest_md)

        return SourceExplorerRunResult(
            source_path=source,
            report=report,
            report_json_path=report_json_path,
            report_markdown_path=report_markdown_path,
        )
