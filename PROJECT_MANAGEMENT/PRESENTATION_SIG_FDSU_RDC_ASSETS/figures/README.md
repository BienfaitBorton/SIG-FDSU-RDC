# Registre des figures et captures réelles

## Principe impératif

Toute figure qui représente le logiciel doit provenir d’une **capture d’écran réelle du SIG-FDSU RDC en fonctionnement**. Les maquettes, interfaces fictives, images générées d’interface et reconstructions graphiques de l’application sont interdites.

Les schémas conceptuels restent autorisés : ils décrivent une architecture, un flux ou un parcours sans prétendre représenter l’interface.

## Schémas conceptuels

| Référence | Emplacement | Légende proposée | Source |
|---|---|---|---|
| F-01 | Couverture | Territoires → Intelligence → Décision → Impact | `cover/01_couverture_conceptuelle.mmd` |
| F-02 | Architecture conceptuelle | La chaîne de valeur du SIG-FDSU RDC | `diagrams/01_national_data_fabric.mmd` à `05_executive_situation_room.mmd` |
| F-03 | Parcours décisionnel | De l’observation à l’évaluation | `diagrams/06_flux_decision.mmd` |

## Plan de captures réelles du produit

| Figure | Titre | Objectif de la capture | Écran concerné | État attendu du logiciel | Légende de publication |
|---|---|---|---|---|---|
| **Figure 1** | Vue nationale de la cartographie | Montrer le contexte national, les couches visibles et la capacité d’exploration spatiale | Cartographie nationale | Carte chargée ; légende visible ; couches et contrôles réels ; aucun overlay ni erreur visible | *Vue nationale du SIG-FDSU RDC : les territoires, données et couches d’analyse constituent un contexte partagé pour la décision.* |
| **Figure 2** | Territorial Intelligence — Dungu | Montrer la synthèse territoriale, les KPI, les données sectorielles et la carte synchronisée | `#territorial-intelligence/TERRITOIRE-05-002` | Territoire Dungu chargé ; données réelles visibles ; carte sans état de chargement ; aucun faux zéro | *Intelligence Territoriale : une lecture consolidée du territoire de Dungu, reliant population, services, infrastructures, programmes et priorités.* |
| **Figure 3** | Analyse d’Impact Territorial | Illustrer l’analyse d’un besoin, de ses actifs et de ses conséquences | Route officielle Analyse d’Impact Territorial | Dossier réel sélectionné ; graphe ou carte impact visible ; panneau d’explication affiché | *Analyse d’Impact Territorial : les faits spatiaux sont reliés à leurs conséquences pour éclairer l’action.* |
| **Figure 4** | Spatial Decision Graph | Montrer les nœuds, relations, filtres et explications du graphe spatial | Route officielle SDG | Un cas réel chargé ; nœuds et relations visibles ; légende et détail métier affichés | *Spatial Decision Graph : les relations entre besoins, actifs et territoires sont rendues visibles et explicables.* |
| **Figure 5** | Executive Situation Room | Présenter le parcours de pilotage de la Direction Générale | `#salle-pilotage` / cockpit DG | Briefing, KPI, alertes et actions réelles chargés ; aucun voile ou overlay fantôme | *Salle de Pilotage : une lecture priorisée de la situation nationale, des risques et des actions exécutives.* |
| **Figure 6** | Centre de Décision | Montrer la navigation d’un indicateur vers l’analyse et la recommandation | Centre de Décision / Decision Workspace | Données réelles et parcours de détail chargés ; action fonctionnelle visible | *Centre de Décision : des indicateurs aux preuves nécessaires à l’arbitrage.* |
| **Figure 7** | Référentiel Santé | Illustrer l’exploitation spatiale réelle des établissements de santé | Vue Santé ou couche Santé intégrée | Couche Santé activée ; objets réels visibles ; fiche ou tooltip réel affiché | *Référentiel Santé : les établissements disponibles deviennent une information territoriale exploitable.* |
| **Figure 8** | Référentiel Télécommunications | Illustrer les infrastructures, opérateurs et technologies réellement disponibles | Vue Télécom ou Intelligence Territoriale | Couche Télécom activée ; objets réels ; légende et détail de domaine visibles | *Référentiel Télécommunications : les infrastructures et opérateurs éclairent les possibilités de connectivité.* |
| **Figure 9** | Programmes FDSU | Montrer les sites, programmes, statuts et priorités | Vue Programmes / Centre de Décision | Programme réel sélectionné ; sites et statut visibles ; aucune donnée de démonstration non étiquetée | *Programmes FDSU : les interventions sont vues dans leur contexte territorial et décisionnel.* |
| **Figure 10** | Analyse explicable d’un site | Montrer la justification, les critères, les sources et l’action recommandée | Dossier de décision d’un site réel | Site réel résolu ; nom métier, score, justification et sources visibles ; aucune erreur HTTP | *Dossier de décision : une recommandation est accompagnée de ses faits, critères, limites et preuves.* |

## Sections de la présentation concernées

| Section V2.0 | Figure(s) recommandée(s) | Rôle éditorial |
|---|---|---|
| Contexte national | Figure 1 | Ancrer immédiatement la dimension territoriale |
| Les principaux modules | Figures 2 à 6 | Donner une preuve visuelle de la réalité produit |
| Innovations | Figures 3, 4 et 10 | Montrer l’explicabilité et la décision, pas seulement les données |
| Bénéfices par profil | Figures 5, 6 et 10 | Relier chaque public à un parcours réel |
| Doctrine d’expérience | Figures 2, 6, 7, 8 et 9 | Montrer la synchronisation carte, KPI, détail et action |

## Règles de préparation et validation

1. Réaliser les captures dans la version validée du logiciel, à partir des routes exactes indiquées.
2. Vérifier visuellement l’absence d’erreur HTTP, de code technique, d’overlay, de chargement bloqué ou de bouton décoratif.
3. Employer des données réelles ; une donnée de démonstration ne peut apparaître que si son statut est clairement visible.
4. Masquer toute information sensible avant publication, sans modifier le sens de la capture.
5. Conserver avec chaque capture : date, environnement, route, jeu de données ou cas affiché, auteur de la capture et validation.
6. Ne remplacer un emplacement dans le document final qu’après validation fonctionnelle et institutionnelle.
