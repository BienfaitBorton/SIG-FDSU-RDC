# Reprise Sprint Groupements

Date: 2026-07-03

## Etat sauvegarde

- PostgreSQL non modifie.
- API non modifiees pour le sprint Groupements.
- Travail realise uniquement dans les referentiels et rapports hors base.

## Fichiers principaux

- `app/referentials/groupement_official/`
- `tests/test_groupement_official_referential.py`
- `data/reports/groupement_official/groupement_referential_official.json`
- `data/reports/groupement_official/groupement_quality_report.json`
- `data/reports/groupement_official/groupement_coverage_audit.json`
- `data/reports/groupement_official/groupement_coverage_audit.md`
- `data/reports/national_counter_registry.json`

## Resultats Groupements

- Attendu officiel: 6053
- Trouve: 1681
- Couverture: 27.77%
- Statut: partiel
- Validation: non publie
- Anomalies: 179
- Orphelins: 1
- Territoires sans groupement: 27
- Collectivites sans groupement: 250

## Anomalie orpheline cle

- Entite: Bena muhona
- Type: Groupement
- Code: 70650801
- Probleme: collectivite parente non determinee
- Cause: prefixe CODE_GRPT sans correspondance dans les collectivites officielles generees
- Statut: A valider manuellement
- Suggestion: verifier le rattachement officiel collectivite/territoire avant publication

## Verification executee

- `.\.venv\Scripts\python.exe -m pytest tests\test_groupement_official_referential.py -q`
- Resultat: 1 passed

## A la reprise

- Recharger le contexte depuis ce fichier.
- Verifier `git status --short`.
- Continuer par le sprint suivant ou completer la source Groupements avec une source nationale plus exhaustive.
