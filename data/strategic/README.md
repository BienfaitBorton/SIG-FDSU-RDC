# Référentiel stratégique FDSU — SIG-FDSU RDC

Ce dossier regroupe les documents stratégiques officiels du programme FDSU / CCN, intégrés au dépôt de données du SIG sans transformation de leur contenu. Ils servent de base documentaire pour le centre de pilotage et le futur moteur décisionnel.

## Fichiers indexés

### `strategie_fdsu_ccn_2026_2030.docx`

| Attribut | Détail |
| --- | --- |
| **Nom** | `strategie_fdsu_ccn_2026_2030.docx` |
| **Description** | Document stratégique FDSU–CCN (cadre 2026–2030) : orientations du programme, objectifs de déploiement, logique d’intervention territoriale et articulation entre sites FDSU et Centres Communautaires Numériques. |
| **Rôle dans le SIG-FDSU** | Référence normative pour contextualiser les décisions d’implantation, les indicateurs du tableau de bord national et les scénarios du centre de décision. |
| **Usage prévu dans le moteur décisionnel** | Source de critères qualitatifs et de règles métier (priorités sectorielles, séquences de déploiement, seuils d’éligibilité) à traduire ultérieurement en paramètres de scoring et en pondérations multicritères — **sans scoring automatique à ce stade**. |

### `matrice_priorisation_300_sites.xlsx`

| Attribut | Détail |
| --- | --- |
| **Nom** | `matrice_priorisation_300_sites.xlsx` |
| **Description** | Matrice de ciblage et de priorisation des 300 sites pilotes : critères de sélection, notes ou rangs de priorité, et données associées par site ou localité cible. |
| **Rôle dans le SIG-FDSU** | Référentiel opérationnel de priorisation pour croiser les sites géolocalisés, les fiches localité et les vues « Priorisation » / « Analyse multicritère » du centre de décision. |
| **Usage prévu dans le moteur décisionnel** | Base tabulaire pour alimenter le calcul de scores FDSU, le classement des localités prioritaires CCN et les simulations d’investissement — **import et scoring automatique non activés à ce stade**. |

## Principe d’intégration

- Les fichiers sont conservés **tels quels** (copie binaire, sans modification).
- Aucune logique métier ni pipeline de scoring n’est branché sur ce dossier pour l’instant.
- Les traitements futurs (lecture, normalisation, indexation) seront documentés dans les modules API et le centre de décision lors de leur implémentation.

## Source d’origine

| Fichier cible | Fichier source (téléchargement / fourni) |
| --- | --- |
| `strategie_fdsu_ccn_2026_2030.docx` | `Strategie_FDSU_CCN_Mai_5_5_26.docx` |
| `matrice_priorisation_300_sites.xlsx` | `Matrice de ciblage et de priorisation de 300 sites.xlsx` |
