# Rapport final — Référentiel National CENI v1.0

## Exécution

- Date de génération : 16 juillet 2026.
- Branche : `feature/smart-map-interactions`.
- Commit créé : aucun.
- Source officielle : `data/raw/ceni/KMZ File Sites CENI.kmz`.
- SHA-256 avant et après : `C3762911DF483D0B291145AF31CF612A30332039BB3D7BFD86FA894C650ABE9D`.
- Taille : 737 794 octets.
- Temps de génération complète observé : 194 secondes.
- `data/decision/case_history.json` et `work/` : non modifiés par le sprint.

## Volumétrie

| Indicateur | Valeur |
|---|---:|
| Placemark réels | 32 221 |
| Enregistrements conservés | 32 221 |
| Intégrables | 31 956 |
| Rejetés du jeu intégrable, mais conservés dans le registre | 265 |
| Suspects | 68 |
| Rattachements Collectivité/Territoire/Province | 24 813 |
| Rattachements Province seulement | 7 075 |
| Non résolus | 333 |

## Catégories

La source n’expose aucune catégorie. La taxonomie normalisée conserve 29 517 objets `UNCLASSIFIED`. Seuls les noms explicites produisent une catégorie : 1 524 Santé, 1 148 Éducation, 17 Religieux, 9 Administratif et 6 Bâtiment public. Aucun centre de vote ou d’enrôlement n’est affirmé sans preuve textuelle.

## Déduplication

| Statut | Occurrences |
|---|---:|
| Exact | 22 044 |
| Même géométrie | 78 |
| Probable | 2 |
| Même nom | 612 |
| Aucun signal | 9 485 |

Aucune occurrence n’est supprimée. Les groupes et identifiants liés restent disponibles pour validation humaine.

## API et Dashboard

Les sept routes `/api/ceni/*` sont disponibles. La route dashboard `#ceni-registry` fournit indicateurs, provenance, hash, carte, filtres, recherche, tableau et fiche détaillée.

## Compatibilité

- National Asset Registry : contrat préparé `INSTITUTIONAL/CENI`, jamais `FDSU`.
- NTIE : dimensions documentaires seulement, aucun score.
- SDG : relations futures documentées, aucune règle activée.

## Validation

- Tests CENI : 7 réussis.
- Non-régression NFAR, NTIE et SDG : 37 réussis.
- Playwright CENI : les deux scénarios ont été lancés successivement sans trace d’échec ; le processus de commande a atteint son timeout lors de l’arrêt du serveur isolé, comportement déjà observé dans cet environnement.
- `py_compile`, `node --check` et `git diff --check` : utilisés comme contrôles finaux.
- Idempotence contrôlée sur les 100 premiers objets : `asset_uid` et `source_record_id` identiques après reconstruction.

## Limites

Le KMZ ne contient que le nom et les coordonnées. Les fonctions électorales, la propriété institutionnelle, les codes administratifs, le Groupement et la Localité ne peuvent pas être inventés. La publication doit donc conserver la provenance, les `UNCLASSIFIED`, les anomalies et les rattachements partiels.
