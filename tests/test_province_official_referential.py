from zipfile import ZipFile

from app.referentials.province_official.service import ProvinceOfficialReferentialService


def _build_province_kmz(path):
    kml = '''
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Province26</name>
    <Folder>
      <name>Provinces officielles</name>
      <Placemark>
        <name>Kinshasa</name>
        <description>chef lieu: Kinshasa\ncode: 11</description>
        <ExtendedData>
          <Data name="CODE_OFFICIEL"><value>11</value></Data>
          <Data name="CHEF_LIEU"><value>Kinshasa</value></Data>
        </ExtendedData>
        <Polygon>
          <outerBoundaryIs>
            <LinearRing>
              <coordinates>
                15.0,-4.0,0 15.1,-4.0,0 15.1,-4.1,0 15.0,-4.1,0 15.0,-4.0,0
              </coordinates>
            </LinearRing>
          </outerBoundaryIs>
        </Polygon>
      </Placemark>
      <Placemark>
        <name>Kwilu</name>
        <description>chef lieu: Bandundu</description>
        <ExtendedData>
          <Data name="CODE_OFFICIEL"><value>31</value></Data>
        </ExtendedData>
        <Polygon>
          <outerBoundaryIs>
            <LinearRing>
              <coordinates>
                17.0,-4.0,0 17.1,-4.0,0 17.1,-4.1,0 17.0,-4.1,0 17.0,-4.0,0
              </coordinates>
            </LinearRing>
          </outerBoundaryIs>
        </Polygon>
      </Placemark>
      <Placemark>
        <name>Objet non provincial</name>
        <Point><coordinates>15.1,-4.2,0</coordinates></Point>
      </Placemark>
    </Folder>
  </Document>
</kml>
'''
    with ZipFile(path, "w") as archive:
        archive.writestr("doc.kml", kml)


def test_province_official_service_builds_referential_from_kmz(tmp_path):
    kmz_path = tmp_path / "Province26.kmz"
    _build_province_kmz(kmz_path)

    output_dir = tmp_path / "out"
    zones_config = tmp_path / "zones_fdsu.yaml"
    zones_config.write_text(
        '''
country:
  code: RDC
  name: Republique Democratique du Congo

zones:
  - code: OT
    nom: Ouest
    couleur: "#2CA02C"
    provinces:
      - Kinshasa
      - Kwilu
''',
        encoding="utf-8",
    )

    service = ProvinceOfficialReferentialService()
    result = service.run(kmz_path, output_dir=output_dir, zones_config_path=zones_config)

    assert len(result.report.province_referential) == 2
    assert all(item.niveau == "Province" for item in result.report.province_referential)
    assert all(item.zone_fdsu == "OT" for item in result.report.province_referential)
    assert result.report.quality.province_count == 2
    assert result.referential_json_path.exists()
    assert result.fact_sheets_json_path.exists()
    assert result.quality_json_path.exists()
    assert result.report_markdown_path.exists()
    assert result.files_report_path.exists()


def test_province_official_service_ignores_non_mapped_features(tmp_path):
    kmz_path = tmp_path / "Province26.kmz"
    _build_province_kmz(kmz_path)

    output_dir = tmp_path / "out"
    zones_config = tmp_path / "zones_fdsu.yaml"
    zones_config.write_text(
        '''
country:
  code: RDC
  name: RDC

zones:
  - code: OT
    nom: Ouest
    couleur: "#2CA02C"
    provinces:
      - Kinshasa
''',
        encoding="utf-8",
    )

    service = ProvinceOfficialReferentialService()
    result = service.run(kmz_path, output_dir=output_dir, zones_config_path=zones_config)

    assert [item.nom for item in result.report.province_referential] == ["Kinshasa"]
    assert result.report.quality.province_count == 1
