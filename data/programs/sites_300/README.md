# Programme Sites 300 — SIG-FDSU RDC

Programme national **planifié** de 300 sites FDSU. Les géométries proviennent du KMZ officiel ; la matrice de priorisation est disponible pour le futur scoring.

## Statut programme

| Attribut | Valeur |
| --- | --- |
| Cycle de vie | **Planifié** (`PLANIFIE`) |
| Déploiement | Non démarré |
| Scoring FDSU | À calculer |

## Fichiers

| Fichier | Rôle |
| --- | --- |
| `raw/300_sites_new.csv.kmz` | KMZ source (géométries officielles) |
| `raw/doc.kml` | KML extrait |
| `sites_300.geojson` | 300 points pour la cartographie |
| `sites_300.json` | JSON plat pour le Centre de Décision |
| `matrice_priorisation_300_sites.xlsx` | Copie de la matrice officielle |

## Champs site

| Champ | Description |
| --- | --- |
| `name` | Nom du site |
| `province` | Province |
| `territoire` | Territoire |
| `zone` | Zone FDSU régionale |
| `latitude` / `longitude` | Coordonnées WGS84 (KMZ, non modifiées) |
| `programme` | `"Sites 300"` |
| `status` | `"Planifié"` |
| `priority_status` | `"À calculer"` |
| `fdsu_score` | `null` (en attente du moteur de scoring) |
| `source` | `"KMZ 300 Sites"` |

## Volume

**300 sites** — répartition par zone : Ouest 60, Nord 100, Est 20, Centre 60, Sud 60.

## Couche « Tous les sites »

Agrège Sites 40 + Sites 300 = **340 sites** (extensible aux futurs programmes).

## Régénération

```bash
python scripts/import_sites_300_kmz.py
```
