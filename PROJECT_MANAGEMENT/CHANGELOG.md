# CHANGELOG - SIG-FDSU RDC

## Version 0.8.6-cnct

Date: 2026-07-04

### Ajouts

- Module Dashboard principal `Centre de connaissances`.
- Socle API CNCT `/knowledge`, `/knowledge/{entity}`, `/knowledge/search`, `/knowledge/completeness`, `/knowledge/suggestions`.
- Tables PostgreSQL `territorial_documents`, `territorial_sources`, `territorial_statistics`, `territorial_history`, `territorial_quality`, `territorial_completeness`.
- Fiche encyclopédique à onglets avec toutes les rubriques CNCT.
- Indicateurs de complétude et tableau des priorités d'enrichissement.

### Corrections

- Les rubriques sans donnée affichent explicitement `Donnée non encore renseignée`.

### Optimisations

- Préparation de la liaison future avec Matrice FDSU, KPI, scores, simulation, classements et recommandations.
- Séparation stricte entre connaissance publiée, source, suggestion et workflow de validation.

### Documentation

- Ajout du rapport `PROJECT_MANAGEMENT/SPRINT_REPORTS/SPRINT_3_2_CNCT_REPORT.md`.

### Incompatibilites eventuelles

- Aucune collecte web automatique n'est activée dans ce sprint.
- Les données CNCT livrées sont un socle préparatoire et non une base publique enrichie.

## Version 0.8.5-enrichment

Date: 2026-07-04

### Ajouts

- Module Dashboard `Enrichissement territorial`.
- Table PostgreSQL `territorial_enrichment_suggestions`.
- Endpoints FastAPI `/territorial-enrichment/sources`, `/fields`, `/statuses` et `/suggestions`.
- Workflow accepter, rejeter et modifier avant validation.
- Cas Kinshasa affiche `Ville-Province` et les districts Funa, Lukunga, Mont-Amba, Tshangu.

### Corrections

- Les fiches territoriales conservent les rubriques activites, particularites, defis et potentiel meme sans donnee renseignee.

### Optimisations

- Controle centralise des sources publiques autorisees et des champs enrichissables.
- Aucune ecriture directe dans les fiches officielles avant validation.

### Documentation

- Ajout du rapport `PROJECT_MANAGEMENT/SPRINT_REPORTS/SPRINT_3_1_ENRICHMENT_REPORT.md`.

### Incompatibilites eventuelles

- Les propositions validees ne sont pas encore fusionnees automatiquement dans les profils territoriaux officiels.

## Version 0.8.4-ux-fix

Date: 2026-07-04

### Ajouts

- Rapport `PROJECT_MANAGEMENT/SPRINT_REPORTS/SPRINT_3_1_UX_FIX_REPORT.md`.
- Fiches adaptees par type d'entite.
- Zones FDSU interactives dans le dashboard et la legende cartographique.
- Bouton Retour au tableau de bord dans le workbench.

### Corrections

- Separation entre Exporter, Enregistrer la fiche et Imprimer.
- Correction du chevauchement fiche/carte.
- Activation des boutons Gestion des Referentiels.
- Navigation recentree en haut du contenu apres changement de module.

### Optimisations

- Colonnes de listes metier adaptees au type de couche.
- Export referentiel base sur le filtre actif.

### Documentation

- Ajout du rapport de correctif UX Sprint 3.1.

## Version 0.8.4-sprint-3.1

Date: 2026-07-04

### Ajouts

- Ajout du dossier `PROJECT_MANAGEMENT/` et des fichiers de pilotage projet.
- Ajout du rapport `PROJECT_MANAGEMENT/SPRINT_REPORTS/SPRINT_3.1_REPORT.md`.
- Ajout de la recherche API `GET /entities/search`.
- Ajout des routes detail JSON/API pour provinces, territoires, collectivites, groupements et localites.
- Ajout des controles de liste Dashboard: tri, taille de page, export et impression.
- Ajout de la section "Base de connaissances territoriale" dans les fiches.

### Corrections

- Les compteurs Dashboard ouvrent une liste metier avant toute fiche.
- La recherche globale ouvre une liste filtrable au lieu d'ouvrir directement une fiche.
- Les couleurs Zones FDSU suivent la demande Sprint 3.1: OT jaune, CE rose, SD vert sombre, ND gris olive, ET bleu.

### Optimisations

- Les listes Dashboard reutilisent le workbench existant.
- Les exports de fiche reutilisent les donnees normalisees deja presentes dans les proprietes d'entite.
- Les endpoints `/sites` et `/missions` acceptent `skip` et `limit`.

### Documentation

- Creation du rapport de sprint complet.
- Initialisation de la roadmap, du backlog, des release notes, des decisions et des anomalies connues.

### Incompatibilites eventuelles

- Le format KMZ est fourni comme KML pret a compresser dans le navigateur, sans archive native.
- Les routes detail ajoutees dans `api/main.py` coexistent avec les routeurs CRUD existants.
