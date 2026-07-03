import json
from zipfile import ZipFile

from app.referentials.groupement_official.service import GroupementOfficialReferentialService


def _build_groupements_kmz(path):
    kml = '''
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Groupements</name>
    <Folder>
      <name>Groupement</name>
      <Placemark>
        <styleUrl>#m_ylw-pushpin2</styleUrl>
        <ExtendedData>
          <SchemaData schemaUrl="#Groupement0">
            <SimpleData name="PCODE">40520016</SimpleData>
            <SimpleData name="TERRITOIRE">Yakoma</SimpleData>
            <SimpleData name="COLLECTIV">Abumombazi</SimpleData>
            <SimpleData name="GENRE">localite centrale GRPT</SimpleData>
            <SimpleData name="NOM_BD">Bwato</SimpleData>
            <SimpleData name="NOM_RGC">Bwato</SimpleData>
            <SimpleData name="CODE_GRPT">40520103</SimpleData>
          </SchemaData>
        </ExtendedData>
        <Point><coordinates>22.03333308,3.75000003860751,0</coordinates></Point>
      </Placemark>
      <Placemark>
        <styleUrl>#m_ylw-pushpin2</styleUrl>
        <ExtendedData>
          <SchemaData schemaUrl="#Groupement0">
            <SimpleData name="PCODE">40520018</SimpleData>
            <SimpleData name="TERRITOIRE">Yakoma</SimpleData>
            <SimpleData name="COLLECTIV">Nom source divergent</SimpleData>
            <SimpleData name="GENRE">localite centrale GRPT</SimpleData>
            <SimpleData name="NOM_BD">Pombi</SimpleData>
            <SimpleData name="NOM_RGC">Pumbi</SimpleData>
            <SimpleData name="CODE_GRPT">40520116</SimpleData>
          </SchemaData>
        </ExtendedData>
        <Point><coordinates>22.18333284,3.39999993923161,0</coordinates></Point>
      </Placemark>
    </Folder>
  </Document>
</kml>
'''
    with ZipFile(path, "w") as archive:
        archive.writestr("doc.kml", kml)


def _build_collectivity_referential(path):
    payload = {
        "collectivity_referential": [
            {
                "nom": "Abumombazi",
                "type_collectivite": "Secteur",
                "territoire": "Yakoma",
                "province": "Nord-Ubangi",
                "zone_fdsu": "ND",
                "code_officiel": "405201",
            }
        ]
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_groupement_referential_attaches_by_parent_code_and_flags_inconsistency(tmp_path):
    kmz_path = tmp_path / "Groupements.kmz"
    collectivity_referential = tmp_path / "collectivities.json"
    output_dir = tmp_path / "reports"
    _build_groupements_kmz(kmz_path)
    _build_collectivity_referential(collectivity_referential)

    service = GroupementOfficialReferentialService()
    result = service.run(kmz_path, output_dir=output_dir, collectivity_referential_path=collectivity_referential)

    assert result.report.quality.groupement_count == 2
    assert result.report.quality.attached_count == 2
    assert result.report.quality.orphan_count == 0
    assert result.report.quality.inconsistency_count == 1
    assert len(result.report.quality.anomalies) == 1

    groupement = result.report.groupement_referential[0]
    assert groupement.collectivite_parent == "Abumombazi"
    assert groupement.type_collectivite_parent == "Secteur"
    assert groupement.territoire == "Yakoma"
    assert groupement.province == "Nord-Ubangi"
    assert groupement.zone_fdsu == "ND"

    collectivity_index = result.report.collectivity_groupement_index["collectivites"][0]
    assert collectivity_index["collectivite_parent"] == "Abumombazi"
    assert collectivity_index["nombre_groupements"] == 2

    assert result.referential_json_path.exists()
    assert result.fact_sheets_json_path.exists()
    assert result.quality_json_path.exists()
    assert result.report_markdown_path.exists()
    assert result.files_report_path.exists()
    assert result.collectivity_index_json_path.exists()
    assert result.territory_index_json_path.exists()
    assert result.province_index_json_path.exists()
