from __future__ import annotations

from pathlib import Path

from .kmz_reader import KMZReader
from .geometry_parser import GeometryParser
from .description_parser import DescriptionParser
from .feature_classifier import FeatureClassifier
from .geojson_writer import GeoJSONWriter
from .report import GeospatialAnalysisReport


class GeospatialPipeline:
    """Orchestre la lecture KMZ, l'analyse et la production GeoJSON/report."""

    def __init__(self) -> None:
        self.reader = KMZReader()
        self.geometry_parser = GeometryParser()
        self.description_parser = DescriptionParser()
        self.classifier = FeatureClassifier()
        self.writer = GeoJSONWriter()

    def process(self, kmz_path: str | Path, output_geojson: str | Path, output_report: str | Path) -> GeospatialAnalysisReport:
        document = self.reader.read(kmz_path)
        report = GeospatialAnalysisReport(source_file=str(document.source_path), kml_document=document.document_name)
        features = self._build_features(document.kml_text, report)
        self.writer.write(output_geojson, features)
        report.to_json(output_report)
        return report

    def _build_features(self, kml_text: str, report: GeospatialAnalysisReport) -> list[dict]:
        import xml.etree.ElementTree as ET

        from .kmz_reader import KML_NAMESPACE

        root = ET.fromstring(kml_text)
        features: list[dict] = []

        for placemark in root.findall(".//kml:Placemark", KML_NAMESPACE):
            name = placemark.findtext("kml:name", default="", namespaces=KML_NAMESPACE).strip()
            description_html = placemark.findtext("kml:description", default="", namespaces=KML_NAMESPACE)
            extended_data = self._extract_extended_data(placemark)
            description_values = self.description_parser.parse(description_html)
            parsed_geometry = self.geometry_parser._parse_placemark_geometry(placemark)

            properties = {
                "name": name or "Non disponible",
                "description_html": description_html or "",
                "extended_data": extended_data,
                "description_values": description_values,
            }

            geometry = parsed_geometry.geometry if parsed_geometry is not None else None
            if geometry is None:
                report.missing_geometries += 1

            classification = self.classifier.classify(properties, description_values)
            report.classified_counts[classification.entity_type] = report.classified_counts.get(classification.entity_type, 0) + 1
            report.feature_count += 1
            if description_values:
                report.parsed_descriptions += 1

            properties.update(
                {
                    "entity_type": classification.entity_type,
                    "classification_confidence": classification.confidence,
                    "classification_terms": classification.matched_terms,
                    "geometry": geometry,
                }
            )
            report.add_detail(
                {
                    "name": name or "Non disponible",
                    "entity_type": classification.entity_type,
                    "confidence": classification.confidence,
                }
            )
            features.append(properties)

        return features

    def _extract_extended_data(self, placemark) -> dict[str, str]:
        from .kmz_reader import KML_NAMESPACE

        data: dict[str, str] = {}
        for data_node in placemark.findall(".//kml:Data", KML_NAMESPACE):
            key = data_node.attrib.get("name")
            value = data_node.findtext("kml:value", default="", namespaces=KML_NAMESPACE).strip()
            if key:
                data[key] = value
        for pair in placemark.findall(".//kml:SimpleData", KML_NAMESPACE):
            key = pair.attrib.get("name")
            value = (pair.text or "").strip()
            if key:
                data[key] = value
        return data
