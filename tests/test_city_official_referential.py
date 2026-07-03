from zipfile import ZipFile

from app.referentials.city_official.service import CityOfficialReferentialService


def _build_zones_kmz(path):
    kml = '''
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>ZONES.kmz</name>
    <Folder>
      <name>ZONES</name>
      <Folder>
        <name>ZONE EST</name>
        <Folder>
          <name>Provinces</name>
          <Folder>
            <name>Nord-Kivu</name>
            <Folder>
              <name>Territoires</name>
              <Placemark>
                <name>Goma</name>
                <ExtendedData>
                  <Data name="TYPE"><value>Communes</value></Data>
                  <Data name="NOM"><value>Goma</value></Data>
                </ExtendedData>
                <Polygon>
                  <outerBoundaryIs>
                    <LinearRing>
                      <coordinates>
                        29.0,-1.6,0 29.1,-1.6,0 29.1,-1.7,0 29.0,-1.7,0 29.0,-1.6,0
                      </coordinates>
                    </LinearRing>
                  </outerBoundaryIs>
                </Polygon>
              </Placemark>
              <Placemark>
                <name>Nyiragongo</name>
                <ExtendedData>
                  <Data name="TYPE"><value>Territoire</value></Data>
                  <Data name="NOM"><value>Nyiragongo</value></Data>
                </ExtendedData>
                <Polygon>
                  <outerBoundaryIs>
                    <LinearRing>
                      <coordinates>
                        29.2,-1.6,0 29.3,-1.6,0 29.3,-1.7,0 29.2,-1.7,0 29.2,-1.6,0
                      </coordinates>
                    </LinearRing>
                  </outerBoundaryIs>
                </Polygon>
              </Placemark>
            </Folder>
          </Folder>
        </Folder>
      </Folder>
    </Folder>
  </Document>
</kml>
'''
    with ZipFile(path, "w") as archive:
        archive.writestr("doc.kml", kml)


def test_city_referential_extracts_only_type_commune(tmp_path):
    kmz_path = tmp_path / "zones_fdsu.kmz"
    _build_zones_kmz(kmz_path)

    service = CityOfficialReferentialService()
    result = service.run(kmz_path, output_dir=tmp_path / "reports")

    assert len(result.report.city_referential) == 1
    city = result.report.city_referential[0]
    assert city.nom == "Goma"
    assert city.niveau == "Ville"
    assert city.province == "Nord-Kivu"
    assert city.zone_fdsu == "ET"
    assert city.geometry is not None
    assert result.report.quality.city_count == 1
    assert result.report.quality.empty_geometry_count == 0
    assert result.referential_json_path.exists()
    assert result.fact_sheets_json_path.exists()
    assert result.quality_json_path.exists()
    assert result.report_markdown_path.exists()
    assert result.files_report_path.exists()


def test_city_referential_quality_detects_duplicate_names(tmp_path):
    kmz_path = tmp_path / "zones_fdsu.kmz"
    kml = '''
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>ZONES.kmz</name>
    <Folder>
      <name>ZONES</name>
      <Folder>
        <name>ZONE EST</name>
        <Folder>
          <name>Provinces</name>
          <Folder>
            <name>Nord-Kivu</name>
            <Folder>
              <name>Territoires</name>
              <Placemark>
                <name>Goma</name>
                <ExtendedData><Data name="TYPE"><value>Communes</value></Data></ExtendedData>
                <Polygon><outerBoundaryIs><LinearRing><coordinates>29.0,-1.6,0 29.1,-1.6,0 29.1,-1.7,0 29.0,-1.7,0 29.0,-1.6,0</coordinates></LinearRing></outerBoundaryIs></Polygon>
              </Placemark>
            </Folder>
          </Folder>
        </Folder>
      </Folder>
      <Folder>
        <name>ZONE OUEST</name>
        <Folder>
          <name>Provinces</name>
          <Folder>
            <name>Kinshasa</name>
            <Folder>
              <name>Territoires</name>
              <Placemark>
                <name>Goma</name>
                <ExtendedData><Data name="TYPE"><value>Communes</value></Data></ExtendedData>
                <Polygon><outerBoundaryIs><LinearRing><coordinates>15.2,-4.3,0 15.3,-4.3,0 15.3,-4.4,0 15.2,-4.4,0 15.2,-4.3,0</coordinates></LinearRing></outerBoundaryIs></Polygon>
              </Placemark>
            </Folder>
          </Folder>
        </Folder>
      </Folder>
    </Folder>
  </Document>
</kml>
'''
    with ZipFile(kmz_path, "w") as archive:
        archive.writestr("doc.kml", kml)

    service = CityOfficialReferentialService()
    result = service.run(kmz_path, output_dir=tmp_path / "reports")

    assert result.report.quality.duplicate_count == 1
    assert result.report.quality.multi_province_conflicts == 1
    assert result.report.quality.multi_zone_conflicts == 1
