# End-to-End Integrity Gate — Decision Case & Visual Integrity

## Cause racine (site/29)

**Endpoint fautif :** `GET /api/decision/case/29?asset_type=site&program_code=sites_40`

**Erreur :** HTTP 400 — `{"detail":"Extra data: line 4199 column 2 (char 137914)"}`

**Mécanisme :**
1. `build_site_case` → `_build_case_shell` → `_append_history`
2. `_append_history` charge `data/decision/case_history.json` via `json.loads`
3. Le fichier était **corrompu** : un JSON valide suivi de fragments concaténés (`}d": "DCF-CCN-...`)
4. `JSONDecodeError` remontait jusqu’à l’API → 400
5. Le frontend affichait « Dossier partiel — Réponse HTTP 400 » et le titre « Dossier de décision — 29 »

Ce n’était **pas** un mismatch d’identifiant site/programme : `explain_site(29, sites_40)` résolvait correctement **Village Nsona**.

## Correctifs

| Correctif | Fichier |
|---|---|
| Chargement JSON tolérant + écriture atomique | `explainable_decision_service.py` |
| Historique best-effort (ne bloque plus le dossier) | idem |
| Resolver centralisé site/programme | `site_entity_resolver.py` |
| Asset enrichi (`site_name`, score, géométrie) | `build_site_case` |
| Messages métier (jamais « HTTP 400 ») + Réessayer | `decision-experience.js` |
| Voile blanc ESR (thème sombre) | `executive-situation-room.css` |
| Nettoyage overlays au changement de module | `app.js` |

## Voile blanc — Salle de Pilotage

**Cause :** cartes ESR en `rgba(255,255,255,0.88)` / `#fff` sur UI dark → aspect de voile semi-transparent.

**Correctif :** surfaces alignées sur `--surface` / fond sombre ; purge `edvs-presentation-mode` + drawers au changement de module.

## Gate obligatoire avant commit futur

1. API DB : `GET /api/decision/case/29?asset_type=site&program_code=sites_40` → 200 + nom métier
2. UI exacte : `#decision-case/site/29?program_code=sites_40`
3. Aucun texte `HTTP 4xx/5xx` visible
4. Aucun `[object Object]`
5. Aucune instance serveur obsolète (un seul Uvicorn 8001)
6. Aucun overlay fantôme (`edvs-presentation-mode`, loading overlay)
7. Zero Decorative Actions respecté
8. Tests : `tests/test_integrity_gate_decision_case.py` + `tests/e2e/integrity-gate-decision-case.spec.js`

## Processus

Avant correction : processus 18036 sur 8001 (instance ancienne / conflictuelle).  
Après correction : relancer `.\start_sig.ps1 -Mode db` — une API, un dashboard.
