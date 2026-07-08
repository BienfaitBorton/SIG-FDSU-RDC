# Programme Sites 40 — SIG-FDSU RDC

Premier programme opérationnel intégré au SIG-FDSU, issu du fichier KMZ officiel des 40 sites pilotes.

## Source

| Élément | Chemin |
| --- | --- |
| KMZ source | `data/programs/sites_40/raw/Sites_FDSU_40.kmz` |
| KML extrait | `data/programs/sites_40/raw/doc.kml` |
| GeoJSON | `data/programs/sites_40/sites_40.geojson` |
| JSON plat | `data/programs/sites_40/sites_40.json` |

## Volume

**40 sites** répartis sur **5 zones FDSU** et **17 provinces**.

| Zone | Sites |
| --- | ---: |
| Centre | 11 |
| Ouest | 8 |
| Sud | 8 |
| Est | 7 |
| Nord | 6 |

## Champs disponibles

Chaque site contient :

| Champ | Description |
| --- | --- |
| `name` | Nom du site (placemark KML) |
| `province` | Province administrative (noms normalisés) |
| `territoire` | Territoire ou entité territoriale |
| `zone` | Zone FDSU (Centre, Est, Nord, Ouest, Sud) |
| `latitude` | Latitude WGS84 |
| `longitude` | Longitude WGS84 |
| `programme` | `"Sites 40"` |
| `status` | `"à qualifier"` |

## Normalisation appliquée

- `Kongo-Central` → `Kongo Central`
- `Kasai-Central` → `Kasai Central`
- `Tanganyka` → `Tanganyika`

Les coordonnées n'ont pas été modifiées.

## Usage prévu dans SIG-FDSU

- **Cartographie** : couche « Sites 40 FDSU » avec popup compact et style distinct.
- **Centre de Décision** : tableau de bord du programme (total, répartition zone/province, statut d'intégration).
- **Prochains sprints** : qualification des sites, scoring FDSU, lien avec `data/business/fdsu_programs.json` et matrice de priorisation.

## Régénération

```bash
python scripts/import_sites_40_kmz.py
```
