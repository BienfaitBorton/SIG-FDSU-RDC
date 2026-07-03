import json
from zipfile import ZipFile

from app.referentials.collectivity_official.service import CollectivityOfficialReferentialService


def _build_collectivities_kmz(path):
    kml = '''
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Collectivités</name>
    <Folder>
      <name>Zone Est</name>
      <Folder>
        <name>Collectivités Ituri</name>
        <Placemark>
          <name>Walendu-Pitsi</name>
          <ExtendedData>
            <Data name="CODE_INS"><value>503101.00000000000</value></Data>
            <Data name="TYPE"><value>Secteur</value></Data>
          </ExtendedData>
          <Polygon><outerBoundaryIs><LinearRing><coordinates>30.0,1.0,0 30.1,1.0,0 30.1,1.1,0 30.0,1.1,0 30.0,1.0,0</coordinates></LinearRing></outerBoundaryIs></Polygon>
        </Placemark>
        <Placemark>
          <name>Bahema-Nord</name>
          <ExtendedData>
            <Data name="CODE_INS"><value>503102.00000000000</value></Data>
            <Data name="TYPE"><value>Chefferie</value></Data>
          </ExtendedData>
          <Polygon><outerBoundaryIs><LinearRing><coordinates>30.2,1.0,0 30.3,1.0,0 30.3,1.1,0 30.2,1.1,0 30.2,1.0,0</coordinates></LinearRing></outerBoundaryIs></Polygon>
        </Placemark>
        <Placemark>
          <name>Bunia</name>
          <ExtendedData>
            <Data name="CODE_INS"><value>501001.00000000000</value></Data>
            <Data name="TYPE"><value>Commune</value></Data>
          </ExtendedData>
          <Polygon><outerBoundaryIs><LinearRing><coordinates>30.4,1.0,0 30.5,1.0,0 30.5,1.1,0 30.4,1.1,0 30.4,1.0,0</coordinates></LinearRing></outerBoundaryIs></Polygon>
        </Placemark>
      </Folder>
    </Folder>
  </Document>
</kml>
'''
    with ZipFile(path, "w") as archive:
        archive.writestr("doc.kml", kml)


def _build_territory_report(path):
    payload = {
        "territories": [
            {
                "nom": "Djugu",
                "province": "Ituri",
                "zone_fdsu": "ET",
                "attributs": {
                    "extended_data": {
                        "CODE_INS": "5031",
                        "TYPE": "Territoire",
                    }
                },
            }
        ]
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_collectivity_referential_extracts_sectors_and_chiefdoms_only(tmp_path):
    kmz_path = tmp_path / "collectivites.kmz"
    territory_report = tmp_path / "territories.json"
    _build_collectivities_kmz(kmz_path)
    _build_territory_report(territory_report)

    service = CollectivityOfficialReferentialService()
    result = service.run(kmz_path, output_dir=tmp_path / "reports", territory_report_path=territory_report)

    assert result.report.quality.collectivity_count == 2
    assert result.report.quality.secteur_count == 1
    assert result.report.quality.chefferie_count == 1
    assert result.report.quality.missing_territory_count == 0
    assert result.report.quality.global_score == 100.0

    names = {item.nom for item in result.report.collectivity_referential}
    assert names == {"Walendu-Pitsi", "Bahema-Nord"}
    assert all(item.territoire == "Djugu" for item in result.report.collectivity_referential)
    assert all(item.province == "Ituri" for item in result.report.collectivity_referential)
    assert all(item.zone_fdsu == "ET" for item in result.report.collectivity_referential)
    assert all(item.metadata["future_children"] == "Groupements" for item in result.report.collectivity_referential)

    territory_index = result.report.territory_collectivity_index["territories"][0]
    assert territory_index["territoire"] == "Djugu"
    assert territory_index["secteurs"] == ["Walendu-Pitsi"]
    assert territory_index["chefferies"] == ["Bahema-Nord"]
    assert territory_index["nombre_collectivites"] == 2

    assert result.referential_json_path.exists()
    assert result.fact_sheets_json_path.exists()
    assert result.quality_json_path.exists()
    assert result.report_markdown_path.exists()
    assert result.files_report_path.exists()
    assert result.territory_index_json_path.exists()
    assert result.province_index_json_path.exists()
