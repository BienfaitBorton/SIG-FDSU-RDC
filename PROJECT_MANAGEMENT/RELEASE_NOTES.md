# RELEASE NOTES - SIG-FDSU RDC

## Version 0.8.6-cnct

Date: 2026-07-04

Cette version crée le socle du Centre National de Connaissances Territoriales. Le SIG-FDSU RDC prépare des fiches encyclopédiques, des indicateurs de complétude, des priorités d'enrichissement et une API dédiée, sans collecte web automatique.

### Nouveautes

- Menu principal `Centre de connaissances`.
- Tableau de bord CNCT avec profils incomplets et données manquantes.
- Fiche encyclopédique à onglets pour les entités territoriales.
- Endpoints `/knowledge`.
- Tables de sources, documents, statistiques, historique, qualité et complétude.

### Corrections

- Affichage systématique de `Donnée non encore renseignée` pour les rubriques vides.

### Limites connues

- Aucune collecte publique automatique.
- Les profils CNCT de démonstration ne remplacent pas les données officielles.
- La publication finale vers les profils territoriaux reste à implémenter.

## Version 0.8.5-enrichment

Date: 2026-07-04

Cette version prepare l'enrichissement public controle des fiches territoriales. Les donnees externes deviennent des propositions tracables, avec source, URL, date de consultation, niveau de confiance et statut de revue.

### Nouveautes

- Interface `Propositions d'enrichissement`.
- Table de propositions avant toute integration officielle.
- Sources autorisees limitees aux sources institutionnelles et OSM comme appui geographique.
- Acceptation, rejet et modification avant validation.

### Corrections

- Kinshasa est affichee comme Ville-Province avec ses districts usuels.

### Limites connues

- La validation change le statut de la proposition, mais l'ecriture finale dans les profils territoriaux reste a implementer comme etape controlee separee.
- Aucune collecte web automatique n'a ete activee.

## Version 0.8.4-ux-fix

Date: 2026-07-04

Correctif UX prioritaire apres revue utilisateur.

### Nouveautes

- Fiches metier adaptees au type d'entite.
- Zones FDSU cliquables.
- Actions referentielles actives.
- Export fiche separe de l'impression.

### Corrections

- Meilleure lisibilite du panneau fiche au-dessus de la carte.
- Retour explicite au centre de pilotage du dashboard.
- Colonnes de listes metier plus pertinentes.

### Limites connues

- Tests navigateur automatises a completer.
- KMZ natif serveur reporte.

## Version 0.8.4-sprint-3.1

Date: 2026-07-04

Cette version transforme le dashboard en interface metier navigable. Les compteurs ouvrent des listes professionnelles, la recherche globale renvoie une liste de resultats et les fiches deviennent des supports de consultation territoriale plus complets.

### Nouveautes

- Listes Dashboard avec recherche, filtres, tri, pagination, export et impression.
- Recherche API universelle initiale.
- Fiches avec exports multi-formats.
- Socle de base de connaissances territoriale.
- Documentation de gestion projet centralisee.

### Corrections

- Suppression du parcours compteur vers fiche directe.
- Correction des couleurs Zones FDSU selon le Sprint 3.1.

### Limites connues

- Pas de KMZ natif compresse cote navigateur.
- Pas de persistance PostgreSQL des profils territoriaux dans ce sprint.
- Tests navigateur automatises a completer.
