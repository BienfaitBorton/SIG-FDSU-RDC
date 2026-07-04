# Rapport Sprint 3.1 - Enrichissement public controle

Date: 2026-07-04

## Objectifs du sprint

Preparer un module d'enrichissement territorial base sur des sources publiques fiables, sans invention de donnees et sans injection automatique dans les fiches officielles.

## Fonctionnalites realisees

- Creation du module `Enrichissement territorial`.
- Creation d'un workflow de propositions consultables, modifiables, validables ou rejetables.
- Conservation de la source, de l'URL, de la date de consultation, du niveau de confiance, du champ concerne et du statut.
- Specialisation de la fiche Kinshasa en `Ville-Province`.

## Fichiers crees

- `api/routes/territorial_enrichment.py`
- `api/services/territorial_enrichment_service.py`
- `alembic/versions/0004_territorial_enrichment_suggestions.py`
- `PROJECT_MANAGEMENT/SPRINT_REPORTS/SPRINT_3_1_ENRICHMENT_REPORT.md`

## Fichiers modifies

- `app/models.py`
- `api/main.py`
- `api/schemas/base.py`
- `dashboard/index.html`
- `dashboard/app.js`
- `dashboard/styles.css`
- `PROJECT_MANAGEMENT/CHANGELOG.md`
- `PROJECT_MANAGEMENT/RELEASE_NOTES.md`
- `PROJECT_MANAGEMENT/ROADMAP.md`

## Nouvelles tables PostgreSQL

- `territorial_enrichment_suggestions`

## Nouveaux endpoints FastAPI

- `GET /territorial-enrichment/sources`
- `GET /territorial-enrichment/fields`
- `GET /territorial-enrichment/statuses`
- `GET /territorial-enrichment/suggestions`
- `POST /territorial-enrichment/suggestions`
- `GET /territorial-enrichment/suggestions/{suggestion_id}`
- `PATCH /territorial-enrichment/suggestions/{suggestion_id}`
- `POST /territorial-enrichment/suggestions/{suggestion_id}/accept`
- `POST /territorial-enrichment/suggestions/{suggestion_id}/reject`

## Nouveaux composants Dashboard

- Navigation `Enrichissement territorial`.
- Ecran `Propositions d'enrichissement`.
- Table de consultation des propositions.
- Panneau de revue avec source, URL, edition, acceptation et rejet.

## Tests effectues

- Compilation Python ciblee.
- Verification statique des routes et schemas.
- Controle de coherence Dashboard sans navigateur automatise disponible.

## Anomalies corrigees

- Kinshasa affiche les districts Funa, Lukunga, Mont-Amba et Tshangu sans niveaux non applicables dans la fiche Ville-Province.

## Limitations restantes

- Les propositions validees ne sont pas encore fusionnees automatiquement dans les profils territoriaux officiels.
- Aucune collecte web automatique n'est activee dans ce sprint.
- Les tests navigateur automatises restent a completer.

## Risques identifies

- Risque de confusion entre proposition validee et donnee officiellement publiee si le workflow de publication final n'est pas explicite.
- Risque de source non institutionnelle si les noms autorises evoluent sans gouvernance.

## Dette technique eventuelle

- Ajouter une table d'historique de publication lorsque l'integration finale dans les profils sera implementee.
- Ajouter des tests API complets avec base de test.

## Performances

- Index ajoutes sur entite, champ, statut et source pour filtrer les propositions.
- Aucun traitement lourd ni collecte reseau automatique.

## Recommandations

- Implementer l'etape separee `publier dans le profil territorial` avec journal d'audit.
- Ajouter un role validateur avant usage multi-utilisateur.
- Remplacer le jeu local de demonstration par des donnees de test documentees.

## Dependances pour le sprint suivant

- Migration Alembic appliquee.
- Regles de validation des sources approuvees par le metier.
- Design du workflow de publication officielle.

## Taux d'avancement estime du projet

61%.

## Estimation de la prochaine version

Version cible: `0.8.6`, avec publication controlee des propositions validees vers les profils territoriaux.
