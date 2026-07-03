from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile
import json
import xml.etree.ElementTree as ET

from app.geospatial.description_parser import DescriptionParser
from app.geospatial.kmz_reader import KML_NAMESPACE, KMZReader

from .normalizer import SourceKind, StagingEntity
from .source_interfaces import BaseStagingAdapter

_XLSX_NAMESPACE = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


class ExcelFDSUAdapter(BaseStagingAdapter):
    """Converts FDSU Excel referential sheets into staging entities."""

    source_kind = SourceKind.EXCEL_FDSU

    def load(self, source_path: str | Path) -> list[StagingEntity]:
        workbook_path = Path(source_path)
        sheet_names = self._load_sheet_names(workbook_path)
        shared_strings = self._load_shared_strings(workbook_path)

        entities: list[StagingEntity] = []
        for sheet_index, sheet_name in enumerate(sheet_names, start=1):
            zone_code = self._extract_zone_code(sheet_name)
            zone_entity = StagingEntity(
                source_id=f"excel-zone-{zone_code.lower()}",
                source_kind=self.source_kind,
                raw_name=sheet_name,
                raw_code=zone_code,
                zone_code=zone_code,
                metadata={"sheet_name": sheet_name, "sheet_index": sheet_index, "level": "zone_fdsu"},
            )
            entities.append(zone_entity)

            current_province: StagingEntity | None = None
            for row in self._iter_sheet_rows(workbook_path, sheet_index, shared_strings):
                province_name = row.get("C", "")
                local_name = row.get("E", "")
                code = row.get("G", "")
                sites = row.get("I", "")

                if province_name and province_name.upper() != "PROVINCE":
                    province_code = row.get("B") or code or province_name
                    current_province = StagingEntity(
                        source_id=f"excel-province-{sheet_index}-{len(entities)}",
                        source_kind=self.source_kind,
                        raw_name=province_name,
                        raw_code=province_code,
                        parent_source_id=zone_entity.source_id,
                        parent_code=zone_entity.raw_code,
                        zone_code=zone_code,
                        province_name=province_name,
                        attributes={"sites_gsm": sites},
                        metadata={"sheet_name": sheet_name, "level": "province"},
                    )
                    entities.append(current_province)

                if local_name and local_name.upper() != "TOWN/TERRITORY":
                    level = "ville" if "VILLE" in local_name.upper() else "territoire"
                    entities.append(
                        StagingEntity(
                            source_id=f"excel-local-{sheet_index}-{len(entities)}",
                            source_kind=self.source_kind,
                            raw_name=local_name,
                            raw_code=code or None,
                            parent_source_id=current_province.source_id if current_province else zone_entity.source_id,
                            parent_code=current_province.raw_code if current_province else zone_entity.raw_code,
                            zone_code=zone_code,
                            province_name=current_province.raw_name if current_province else None,
                            territoire_name=local_name if level == "territoire" else None,
                            attributes={"sites_gsm": sites},
                            metadata={"sheet_name": sheet_name, "level": level},
                        )
                    )

        return entities

    def _load_sheet_names(self, workbook_path: Path) -> list[str]:
        with ZipFile(workbook_path, "r") as archive:
            workbook_xml = ET.fromstring(archive.read("xl/workbook.xml"))
        return [sheet.attrib.get("name", f"Sheet {index}") for index, sheet in enumerate(workbook_xml.findall("a:sheets/a:sheet", _XLSX_NAMESPACE), start=1)]

    def _load_shared_strings(self, workbook_path: Path) -> list[str]:
        with ZipFile(workbook_path, "r") as archive:
            if "xl/sharedStrings.xml" not in archive.namelist():
                return []
            shared_xml = ET.fromstring(archive.read("xl/sharedStrings.xml"))

        values: list[str] = []
        for item in shared_xml.findall("a:si", _XLSX_NAMESPACE):
            text_node = item.find("a:t", _XLSX_NAMESPACE)
            if text_node is not None:
                values.append(text_node.text or "")
                continue
            runs = item.findall("a:r/a:t", _XLSX_NAMESPACE)
            values.append("".join(run.text or "" for run in runs))
        return values

    def _iter_sheet_rows(self, workbook_path: Path, sheet_index: int, shared_strings: list[str]) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        with ZipFile(workbook_path, "r") as archive:
            sheet_xml = ET.fromstring(archive.read(f"xl/worksheets/sheet{sheet_index}.xml"))

        for row in sheet_xml.findall(".//a:sheetData/a:row", _XLSX_NAMESPACE):
            values: dict[str, str] = {}
            for cell in row.findall("a:c", _XLSX_NAMESPACE):
                reference = cell.attrib.get("r", "")
                column = "".join(character for character in reference if character.isalpha())
                value_node = cell.find("a:v", _XLSX_NAMESPACE)
                if value_node is None:
                    continue
                value = value_node.text or ""
                if cell.attrib.get("t") == "s" and value.isdigit():
                    value = shared_strings[int(value)]
                values[column] = value.strip()
            rows.append(values)
        return rows

    def _extract_zone_code(self, sheet_name: str) -> str:
        suffix = sheet_name.split()[-1].strip().upper()
        return suffix or "UNKNOWN"


class KMZAdapter(BaseStagingAdapter):
    """Converts KMZ placemarks into staging entities using existing geospatial readers."""

    source_kind = SourceKind.KMZ

    def __init__(self) -> None:
        self.reader = KMZReader()
        self.description_parser = DescriptionParser()

    def load(self, source_path: str | Path) -> list[StagingEntity]:
        document = self.reader.read(source_path)
        root = ET.fromstring(document.kml_text)
        entities: list[StagingEntity] = []

        for index, placemark in enumerate(root.findall(".//kml:Placemark", KML_NAMESPACE), start=1):
            name = placemark.findtext("kml:name", default="", namespaces=KML_NAMESPACE).strip()
            description_html = placemark.findtext("kml:description", default="", namespaces=KML_NAMESPACE)
            description_values = self.description_parser.parse(description_html)
            extended_data = self._extract_extended_data(placemark)
            geometry_type = self._detect_geometry_type(placemark)
            raw_code = extended_data.get("CODE_INS") or extended_data.get("CODE") or description_values.get("code")
            zone_code = description_values.get("zone") or extended_data.get("ZONE")
            parent_hint = description_values.get("province") or extended_data.get("PROVINCE")

            entities.append(
                StagingEntity(
                    source_id=f"kmz-{Path(source_path).stem.lower()}-{index}",
                    source_kind=self.source_kind,
                    raw_name=name or extended_data.get("NOM") or f"Placemark {index}",
                    raw_code=raw_code,
                    zone_code=zone_code,
                    province_name=parent_hint,
                    geometry_type=geometry_type,
                    geometry={"type": geometry_type} if geometry_type else None,
                    attributes=extended_data | {"description_values": description_values},
                    metadata={
                        "document_name": document.document_name,
                        "source_path": str(document.source_path),
                        "level": extended_data.get("TYPE") or description_values.get("type"),
                    },
                )
            )
        return entities

    def _extract_extended_data(self, placemark: ET.Element) -> dict[str, str]:
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

    def _detect_geometry_type(self, placemark: ET.Element) -> str | None:
        for geometry_name in ("Polygon", "MultiGeometry", "Point", "LineString"):
            if placemark.find(f"kml:{geometry_name}", KML_NAMESPACE) is not None:
                return geometry_name
        return None


class HDXAdapter(BaseStagingAdapter):
    """Converts official HDX/OCHA COD GeoJSON layers into staging entities."""

    source_kind = SourceKind.HDX

    def load(self, source_path: str | Path) -> list[StagingEntity]:
        archive_path = Path(source_path)
        entities: list[StagingEntity] = []

        with ZipFile(archive_path, "r") as archive:
            members = [name for name in archive.namelist() if name.lower().endswith(".geojson")]
            for member in members:
                payload = json.loads(archive.read(member).decode("utf-8"))
                layer_name = Path(member).stem
                for index, feature in enumerate(payload.get("features", []), start=1):
                    properties = feature.get("properties", {})
                    geometry = feature.get("geometry")
                    entity_level = self._infer_level(layer_name, properties)
                    raw_name = self._extract_name(properties)
                    raw_code = self._extract_code(properties)
                    entities.append(
                        StagingEntity(
                            source_id=f"hdx-{layer_name}-{index}",
                            source_kind=self.source_kind,
                            raw_name=raw_name,
                            raw_code=raw_code,
                            province_name=properties.get("adm1_name") or properties.get("adm1_name1"),
                            territoire_name=properties.get("adm2_name") or properties.get("adm2_name1"),
                            geometry_type=geometry.get("type") if isinstance(geometry, dict) else None,
                            geometry=geometry if isinstance(geometry, dict) else None,
                            attributes=properties,
                            metadata={
                                "layer_name": layer_name,
                                "level": entity_level,
                                "source_member": member,
                                "pcode_fields": [key for key in properties if "pcode" in key.lower()],
                            },
                        )
                    )

        return entities

    def _extract_name(self, properties: dict[str, object]) -> str:
        for key in (
            "name",
            "adm3_name",
            "adm2_name",
            "adm1_name",
            "adm0_name",
            "name_1",
            "name1",
        ):
            value = properties.get(key)
            if value:
                return str(value)
        return "Unknown HDX entity"

    def _extract_code(self, properties: dict[str, object]) -> str | None:
        for key in (
            "loc_pcode",
            "adm4_pcode",
            "adm3_pcode",
            "adm2_pcode",
            "adm1_pcode",
            "adm0_pcode",
        ):
            value = properties.get(key)
            if value:
                return str(value)
        return None

    def _infer_level(self, layer_name: str, properties: dict[str, object]) -> str:
        if layer_name.startswith("cod_admin0"):
            return "country"
        if layer_name.startswith("cod_admin1"):
            return "province"
        if layer_name.startswith("cod_admin2"):
            return "territoire"
        if layer_name.startswith("cod_admin3"):
            return "admin3"
        if layer_name.startswith("cod_admincapitals"):
            return "capital"
        if layer_name.startswith("cod_adminpoints"):
            return str(properties.get("admin_level") or "point")
        if layer_name.startswith("cod_adminlines"):
            return str(properties.get("adm_level") or "line")
        return "unknown"