# Audit des données du KMZ CENI — v1.0

## Objet et source

Cet audit décrit exclusivement le fichier officiel `data/raw/ceni/KMZ File Sites CENI.kmz`. Il ne qualifie pas automatiquement chaque objet de bâtiment, de centre de vote ou de site propre à la CENI.

| Propriété | Valeur observée |
|---|---:|
| Taille KMZ | 737 794 octets |
| SHA-256 | `C3762911DF483D0B291145AF31CF612A30332039BB3D7BFD86FA894C650ABE9D` |
| Membre KML | `doc.kml` |
| Taille KML décompressée | 16 049 237 octets |
| Encodage déclaré | UTF-8 |
| Placemark | 32 221 |
| Géométries Point | 32 221 |
| Dossiers | 1 |
| Styles | 2 |
| StyleMap | 1 |
| Descriptions | 0 |

## Schéma réel

Le document contient un schéma `S_KMZ_File_Election_SDD`, nommé `KMZ File Election`, avec trois champs seulement :

- `Name` (`string`) ;
- `Latitude` (`double`) ;
- `Longitude` (`double`).

Chaque Placemark expose ces trois valeurs via `SchemaData/SimpleData`. Aucun champ `Data` libre n’a été observé. Il n’existe ni code administratif, ni catégorie institutionnelle explicite, ni identifiant source métier, ni description.

## Conséquences Data First

1. La présence dans le fichier ne prouve pas qu’un objet est un bâtiment appartenant à la CENI.
2. La catégorie source est conservée à `null` lorsqu’elle n’existe pas.
3. Une classification n’est appliquée que lorsqu’un terme explicite du nom la justifie. Dans les autres cas, la catégorie est `UNCLASSIFIED`.
4. Le rattachement administratif ne peut pas utiliser de code ou de nom fourni par le KMZ. Il utilise donc l’équivalent fichier de `ST_Contains` sur les polygones officiels Province et Collectivité. Les niveaux non démontrables restent `null`.
5. Les doublons sont signalés mais jamais supprimés automatiquement.

## Résultats de qualité

| Contrôle | Nombre |
|---|---:|
| Géométrie valide et rattachée | 31 888 |
| Géométrie suspecte | 68 |
| Coordonnées hors emprise nationale | 265 |
| Rattachement collectivité résolu | 24 813 |
| Rattachement province seulement | 7 075 |
| Rattachement non résolu | 333 |
| Occurrences dans un groupe de doublons exacts | 22 044 |
| Doublons exacts | 22 044 |
| Même géométrie, enregistrements distincts | 78 |
| Doublons probables | 2 |
| Même nom, géométries distinctes | 612 |
| Sans signal de doublon | 9 485 |

Les 265 objets `outside_country` ne sont pas supprimés. Ils restent dans le registre, avec leur géométrie et leurs propriétés brutes.

## Catégories normalisées observées

| Catégorie | Nombre |
|---|---:|
| `UNCLASSIFIED` | 29 517 |
| `HEALTH_FACILITY` | 1 524 |
| `SCHOOL` | 1 148 |
| `RELIGIOUS_BUILDING` | 17 |
| `ADMINISTRATIVE_BUILDING` | 9 |
| `PUBLIC_BUILDING` | 6 |
| autres catégories prévues | 0 |

L’absence de `VOTING_CENTER`, `REGISTRATION_CENTER` ou `CENI_SITE` dans cette version signifie qu’aucun nom ne satisfait les règles explicites retenues. Elle ne signifie pas que ces fonctions n’existent pas sur le terrain.

## Reproductibilité

Le pipeline se lance par :

```powershell
python -m app.referentials.ceni_official audit
python -m app.referentials.ceni_official dry-run
python -m app.referentials.ceni_official validation
python -m app.referentials.ceni_official import
python -m app.referentials.ceni_official report
python -m app.referentials.ceni_official rollback
```

L’audit est réalisé directement dans l’archive ZIP/KMZ. Aucun fichier n’est extrait dans `work/`, conformément à la contrainte de protection absolue de ce répertoire.
