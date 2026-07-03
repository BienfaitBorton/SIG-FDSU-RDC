from zipfile import ZipFile

from app.referentials.territory_hierarchy.service import TerritoryHierarchyService


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
            <name>Haut-Uele</name>
            <Folder>
              <name>Territoire</name>
              <Placemark>
                <name>Dungu</name>
                <ExtendedData>
                  <Data name="TYPE"><value>Territoire</value></Data>
                  <Data name="NOM"><value>Dungu</value></Data>
                  <Data name="PROVINCE"><value>Haut-Uele</value></Data>
                  <Data name="ZONE"><value>EST</value></Data>
                </ExtendedData>
                <Polygon>
                  <outerBoundaryIs>
                    <LinearRing>
                      <coordinates>
                        29.0,3.0,0 29.1,3.0,0 29.1,2.9,0 29.0,2.9,0 29.0,3.0,0
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


def test_territory_hierarchy_service_reads_zone_province_territory_structure(tmp_path):
    kmz_path = tmp_path / "zones_fdsu.kmz"
    _build_zones_kmz(kmz_path)

    service = TerritoryHierarchyService()
    result = service.run(kmz_path, output_dir=tmp_path / "reports")

    assert result.report.territory_count == 1
    territory = result.report.territories[0]
    assert territory.nom == "Dungu"
    assert territory.province == "Haut-Uele"
    assert territory.zone_fdsu == "ET"
    assert territory.chemin_hierarchique == ["RDC", "Zone Est", "Haut-Uele", "Dungu"]
    assert territory.geometry is not None
    assert result.report_json_path.exists()
    assert result.report_markdown_path.exists()


def test_territory_hierarchy_service_reports_attribute_inconsistency(tmp_path):
    kmz_path = tmp_path / "zones_fdsu.kmz"
    _build_zones_kmz(kmz_path)

    # Rewrite kmz with conflicting province attribute.
    conflicted_kml = '''
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
            <name>Haut-Uele</name>
            <Folder>
              <name>Territoire</name>
              <Placemark>
                <name>Dungu</name>
                <ExtendedData>
                  <Data name="PROVINCE"><value>Ituri</value></Data>
                </ExtendedData>
                <Polygon>
                  <outerBoundaryIs>
                    <LinearRing>
                      <coordinates>
                        29.0,3.0,0 29.1,3.0,0 29.1,2.9,0 29.0,2.9,0 29.0,3.0,0
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
    with ZipFile(kmz_path, "w") as archive:
        archive.writestr("doc.kml", conflicted_kml)

    service = TerritoryHierarchyService()
    result = service.run(kmz_path, output_dir=tmp_path / "reports")

    territory = result.report.territories[0]
    assert any("Province attributaire incohérente" in issue for issue in territory.incoherences)
    assert result.report.incoherence_count >= 1
