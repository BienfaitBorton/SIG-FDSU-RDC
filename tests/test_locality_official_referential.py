import json
from zipfile import ZipFile

from app.referentials.locality_official.service import LocalityOfficialReferentialService


def _build_localities_kmz(path):
    kml = '''
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Localite.kmz</name>
    <Folder>
      <name>Localite</name>
      <Placemark>
        <styleUrl>#m_ylw-pushpin</styleUrl>
        <ExtendedData><SchemaData>
          <SimpleData name="PCODE">40520004</SimpleData>
          <SimpleData name="NOM1">Bigi</SimpleData>
          <SimpleData name="TYPE">7</SimpleData>
          <SimpleData name="TERRITOIRE">Yakoma</SimpleData>
          <SimpleData name="COLLECTIV">Abumombazi</SimpleData>
          <SimpleData name="GROUPEMENT">Bwato</SimpleData>
          <SimpleData name="CODE_GRPT">40520103</SimpleData>
          <SimpleData name="LONGITUDE">22.1</SimpleData>
          <SimpleData name="LATITUDE">3.7</SimpleData>
        </SchemaData></ExtendedData>
        <Point><coordinates>22.1,3.7,0</coordinates></Point>
      </Placemark>
      <Placemark>
        <ExtendedData><SchemaData>
          <SimpleData name="PCODE">40520005</SimpleData>
          <SimpleData name="NOM1">Sans parent</SimpleData>
          <SimpleData name="TYPE">456</SimpleData>
          <SimpleData name="TERRITOIRE">Inconnu</SimpleData>
        </SchemaData></ExtendedData>
        <Point><coordinates>22.2,3.8,0</coordinates></Point>
      </Placemark>
    </Folder>
  </Document>
</kml>
'''
    with ZipFile(path, "w") as archive:
        archive.writestr("doc.kml", kml)


def test_locality_referential_builds_hierarchy_indexes_and_future_profile(tmp_path):
    kmz_path = tmp_path / "Localités.kmz"
    output_dir = tmp_path / "reports"
    groupements = tmp_path / "groupements.json"
    collectivities = tmp_path / "collectivities.json"
    registry = tmp_path / "registry.json"
    _build_localities_kmz(kmz_path)
    groupements.write_text(
        json.dumps(
            {
                "groupement_referential": [
                    {
                        "nom": "Bwato",
                        "collectivite_parent": "Abumombazi",
                        "territoire": "Yakoma",
                        "province": "Nord-Ubangi",
                        "zone_fdsu": "ND",
                        "code_officiel": "40520103",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    collectivities.write_text(
        json.dumps(
            {
                "collectivity_referential": [
                    {
                        "nom": "Abumombazi",
                        "territoire": "Yakoma",
                        "province": "Nord-Ubangi",
                        "zone_fdsu": "ND",
                        "code_officiel": "405201",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    registry.write_text(json.dumps({"registre_national_des_compteurs": {}}), encoding="utf-8")

    result = LocalityOfficialReferentialService().run(kmz_path, output_dir, groupements, collectivities, registry)

    assert result["quality"]["locality_count"] == 2
    assert result["quality"]["attached_groupement_count"] == 1
    assert result["quality"]["orphan_count"] == 1
    entity = next(item for item in result["report"]["locality_referential"] if item["nom"] == "Bigi")
    assert entity["niveau"] == "Localité"
    assert entity["groupement"] == "Bwato"
    assert entity["future_profile"]["population"] is None
    assert (output_dir / "locality_referential_official.json").exists()
    assert (output_dir / "groupement_locality_index.json").exists()
    updated_registry = json.loads(registry.read_text(encoding="utf-8"))
    assert updated_registry["registre_national_des_compteurs"]["localites"]["nombre"] == 2
