# SPRINT 3.1 UX FIX REPORT - SIG-FDSU RDC

Date: 2026-07-04

## Problemes corriges

- Fiches trop generiques: ajout d'une logique de fiche par type d'entite, avec cas specifique Ville-Province / Kinshasa.
- Fiche masquee par la carte: fermeture des popups Leaflet et z-index renforce du panneau fiche.
- Export confondu avec impression: separation entre Exporter, Enregistrer la fiche et Imprimer.
- Boutons Gestion des Referentiels decoratifs: ajout d'actions explicites pour Importer, Comparer, Valider, Publier et Exporter.
- Modules perçus comme vides: navigation recentree en haut du contenu apres changement de module.
- Dashboard remplace par une liste: ajout d'un bouton Retour au tableau de bord et maintien du parcours Compteur > Liste > Selection > Fiche.
- Listes metier trop generiques: colonnes adaptees pour provinces, territoires, groupements et localites.
- Zones FDSU non interactives: clic sur ND, SD, CE, OT, ET depuis dashboard et legende carte pour ouvrir les provinces de la zone.

## Fichiers modifies

- `dashboard/index.html`
- `dashboard/app.js`
- `dashboard/styles.css`
- `PROJECT_MANAGEMENT/SPRINT_REPORTS/SPRINT_3_1_UX_FIX_REPORT.md`

## Tests realises

- Verification statique des points d'ancrage Dashboard.
- Verification de coherence avec les documents officiels v1.0.
- Compilation Python de `api/main.py`.
- Appels directs API existants:
  - `read_provinces_json(skip=0, limit=5)` retourne 5 lignes.
  - `search_entities(q='kinshasa', skip=0, limit=3)` retourne 90 resultats au total et 3 items pagines.
  - `read_province_detail('KINSHASA')` retourne une fiche.
- Verification `git diff --check`.

## Limites restantes

- Le test navigateur automatise reste a completer si Playwright ou navigateur integre devient disponible.
- Le navigateur integre `iab` n'est pas disponible dans cette session.
- La verification syntaxique JS automatisee n'a pas pu etre executee car `node` n'est pas installe et le runtime Node disponible interdit la generation de code par chaine.
- Les exports KMZ restent fournis sous forme KML pret a compresser.
- La synchronisation carte-table-fiche complete reste a renforcer en Sprint 3.2.
- Les profils territoriaux ne sont pas encore persistants en PostgreSQL.

## Recommandations pour Sprint 3.2

- Ajouter des tests navigateur pour les parcours recette: 26 Provinces, recherche Kinshasa, carte groupement, exports et Gestion des Referentiels.
- Brancher l'autocomplete universel sur `/entities/search`.
- Ajouter une enveloppe API paginee uniforme.
- Implementer les exports serveur PDF/KMZ natifs.
- Finaliser la synchronisation carte-table-fiche avec filtrage cartographique.
