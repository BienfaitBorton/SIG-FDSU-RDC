# SIG-FDSU RDC - Rapport Sprint 3.3.1

## Correction complete UTF-8

Date : 2026-07-05

## Fichiers corriges

- `dashboard/index.html`
- `dashboard/app.js`
- `dashboard/styles.css`
- `dashboard/serve_utf8.py`
- `api/main.py`
- `api/services/territorial_enrichment_service.py`
- `scripts/import_all_referentiel.py`

## Causes identifiees

- Des chaines du dashboard avaient ete interpretees avec une mauvaise page de code Windows avant d'etre enregistrees en UTF-8.
- Les caracteres accentues apparaissaient sous forme mojibake sur certains libelles francais du dashboard.
- Certains emojis etaient affiches sous forme de sequences corrompues.
- Le serveur statique Python standard renvoyait `text/html`, `text/javascript` et `text/css` sans `charset=utf-8`.
- FastAPI renvoyait `application/json` sans charset explicite.

## Corrections realisees

- Restauration des fichiers dashboard depuis une base Git saine puis reecriture en UTF-8 sans BOM.
- Verification de `<meta charset="UTF-8">` dans `dashboard/index.html`.
- Ajout de `dashboard/serve_utf8.py` pour servir :
  - HTML : `text/html; charset=utf-8`
  - JS : `application/javascript; charset=utf-8`
  - CSS : `text/css; charset=utf-8`
  - JSON : `application/json; charset=utf-8`
- Ajout d'un middleware FastAPI pour forcer `application/json; charset=utf-8`.
- Correction des statuts d'enrichissement dans les compteurs : `proposé`, `validé`, `rejeté`.
- Correction d'une chaine residuelle dans `scripts/import_all_referentiel.py`.

## Tests realises

- Verification UTF-8 sans BOM :
  - `dashboard/index.html`
  - `dashboard/app.js`
  - `dashboard/styles.css`
  - `dashboard/serve_utf8.py`
- Verification des modules dashboard dans `index.html` :
  - Dashboard
  - Cartographie
  - Referentiel
  - Gestion des referentiels
  - CNCT
  - Assistant d'enrichissement
  - Aide a la decision
- Verification des Content-Type via `dashboard/serve_utf8.py` :
  - `index.html` : `text/html; charset=utf-8`
  - `app.js` : `application/javascript; charset=utf-8`
  - `styles.css` : `text/css; charset=utf-8`
- Verification FastAPI :
  - `/` : `application/json; charset=utf-8`
- Compilation Python :
  - `api/main.py`
  - `api/routes/enrichment.py`
  - `api/services/territorial_enrichment_service.py`
  - `dashboard/serve_utf8.py`
  - `scripts/import_all_referentiel.py`
- Tests automatises :
  - `.venv\Scripts\python.exe -m pytest tests\test_enrichment_assistant.py -q`
  - Resultat : `2 passed`

## Limites

- `tracked_pycache.txt` contient des octets NUL et ressemble a un artefact binaire/UTF-16 de suivi de cache Python ; il n'est pas servi par le dashboard et n'a pas ete traite comme fichier applicatif.
- Le serveur standard `python -m http.server` ne force pas les charsets ; utiliser `python dashboard/serve_utf8.py`, qui sert automatiquement le dossier `dashboard`, ou un serveur equivalent configuré en UTF-8.

## Confirmation

Les fichiers applicatifs du dashboard et les endpoints JSON FastAPI verifies sont desormais servis ou prepares en UTF-8. Les sequences mojibake connues ne sont plus detectees dans les fichiers dashboard, API modifies et scripts verifies.
