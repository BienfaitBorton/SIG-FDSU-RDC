# SIG-FDSU RDC — Explainable Decision Engine v1

**Statut :** Opérationnel (structure + API + UI)  
**Date :** 10 juillet 2026  
**Principe :** Aucune recommandation sans justification.

## Concept

Chaque recommandation produit un **Decision Case File** (Dossier de Décision) traçable.

## Consommation (pas de lecture directe des tables métier)

1. Doctrines versionnées (`data/business/doctrines/`)
2. Matrices (`data/business/priority_matrix.json`)
3. Knowledge Hub (`/api/knowledge/*`)
4. Référentiel / programmes (via services existants)

## API

- `GET /api/decision/case/{id}`
- `GET /api/decision/explain/{id}`
- `GET /api/decision/doctrine/{id}`
- `GET /api/decision/case-history`
- `GET /api/decision/pdf-template` (structure only)

## UI

- Fiche CCN : onglets Justification + Dossier de décision
- Centre de Décision / Priorisation : Justification + Dossier
- Fiche décisionnelle nationale : miroir de la justification

## PDF

Modèle : `data/decision/pdf_templates/decision_case_file_v1.json`  
Génération PDF : **non activée**.
