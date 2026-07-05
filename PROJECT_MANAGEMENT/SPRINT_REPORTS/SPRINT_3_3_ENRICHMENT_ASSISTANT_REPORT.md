# SIG-FDSU RDC - Rapport Sprint 3.3

## Assistant d'Enrichissement Territorial

Date : 2026-07-05

## Objectifs realises

- Creation du module Dashboard "Assistant d'enrichissement".
- Ajout d'un etat de completude national avec score global.
- Calcul de completude par entite sur les champs metier demandes : identite, subdivision, activites economiques, particularites, defis, potentiel, services publics, connectivite, documents, photos et sources.
- Affichage des entites a enrichir, champs manquants et priorites.
- Conservation du CNCT comme socle de lecture des profils territoriaux.
- Reutilisation de `territorial_enrichment_suggestions` pour toutes les propositions.
- Ajout d'un formulaire de proposition manuelle.
- Validation et rejet sans injection directe dans le referentiel officiel.
- Preparation d'une couche thematique de completude avec fallback tableau si geometrie indisponible.

## Fichiers modifies

- `api/main.py`
- `api/routes/enrichment.py`
- `api/schemas/enrichment.py`
- `api/services/territorial_enrichment_service.py`
- `dashboard/index.html`
- `dashboard/app.js`
- `dashboard/styles.css`
- `tests/test_enrichment_assistant.py`

## Endpoints ajoutes

- `GET /enrichment/dashboard`
- `GET /enrichment/completeness`
- `GET /enrichment/priorities`
- `GET /enrichment/suggestions`
- `POST /enrichment/suggestions`
- `PATCH /enrichment/suggestions/{id}/validate`
- `PATCH /enrichment/suggestions/{id}/reject`
- `GET /enrichment/suggestions/{id}/traceability`

Les endpoints historiques `/territorial-enrichment/...` sont conserves pour compatibilite.

## Limites restantes

- La completude Sprint 3.3 s'appuie sur les profils CNCT de demonstration et les propositions existantes.
- La couche carte reste en mode fallback tableau lorsque la geometrie n'est pas disponible.
- Les filtres zone, territoire et source sont prepares cote API ; l'interface expose province, type, completude, champ manquant, priorite, source et statut.
- Aucune collecte web automatique n'est declenchee.
- Aucune proposition validee ou rejetee n'est publiee dans le referentiel officiel.

## Tests effectues

- Ouverture de l'assistant via `GET /enrichment/dashboard`.
- Consultation des entites incompletes via `GET /enrichment/completeness`.
- Filtre par province.
- Filtre par champ manquant.
- Creation d'une proposition manuelle via `POST /enrichment/suggestions`.
- Validation via `PATCH /enrichment/suggestions/{id}/validate`.
- Rejet via `PATCH /enrichment/suggestions/{id}/reject`.
- Verification de tracabilite via `GET /enrichment/suggestions/{id}/traceability`.
- Verification explicite que `published_to_official_referential` reste `false`.

## Recommandations Sprint 3.4

- Brancher la completude sur les profils territoriaux PostgreSQL reels lorsque le schema metier sera stabilise.
- Ajouter les roles et permissions de validation CNCT.
- Ajouter une file de traitement utilisateur pour les entites marquees "a traiter".
- Connecter la couche thematique a des geometries PostGIS disponibles.
- Ajouter un import controle de propositions depuis fichier avec rapport d'anomalies avant creation.
