from pathlib import Path

from app.referentials.source_explorer.explorer import SourceExplorerService


def test_source_explorer_builds_catalog_and_dictionary_from_geojson(tmp_path):
    geojson_path = tmp_path / "sample.geojson"
    geojson_path.write_text(
        """
        {
          "type": "FeatureCollection",
          "features": [
            {
              "type": "Feature",
              "properties": {
                "folder": "Sites Télécom",
                "province": "Kinshasa",
                "site_name": "Site A",
                "kpi_score": 95
              },
              "geometry": {
                "type": "Point",
                "coordinates": [15.2663, -4.4419]
              }
            },
            {
              "type": "Feature",
              "properties": {
                "folder": "Sites Télécom",
                "province": "Kinshasa",
                "site_name": "Site B",
                "kpi_score": 88
              },
              "geometry": {
                "type": "Point",
                "coordinates": [15.2670, -4.4421]
              }
            }
          ]
        }
        """,
        encoding="utf-8",
    )

    output_dir = tmp_path / "reports"
    service = SourceExplorerService()
    result = service.run(geojson_path, output_dir=output_dir)

    assert result.report.source_format == "GeoJSON"
    assert result.report.object_count == 2
    assert len(result.report.folders) == 1
    folder = result.report.folders[0]
    assert folder.folder_name == "Sites Télécom"
    assert folder.dataset_type in {"Télécommunications", "Sites"}
    assert "KPI" in folder.tags
    assert result.report_json_path.exists()
    assert result.report_markdown_path.exists()


def test_source_explorer_reads_kml_folder_and_geometry(tmp_path):
    kml_path = tmp_path / "sample.kml"
    kml_path.write_text(
        """
        <kml xmlns=\"http://www.opengis.net/kml/2.2\">
          <Document>
            <name>Test KMZ</name>
            <Folder>
              <name>Territoires</name>
              <Placemark>
                <name>Territoire A</name>
                <ExtendedData>
                  <Data name=\"territoire\"><value>Funa</value></Data>
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
            </Folder>
          </Document>
        </kml>
        """,
        encoding="utf-8",
    )

    service = SourceExplorerService()
    result = service.run(kml_path, output_dir=tmp_path / "reports")

    assert result.report.source_format == "KML"
    assert result.report.object_count == 1
    assert result.report.folders[0].folder_name == "Territoires"
    assert "Polygone" in result.report.folders[0].geometry_types
