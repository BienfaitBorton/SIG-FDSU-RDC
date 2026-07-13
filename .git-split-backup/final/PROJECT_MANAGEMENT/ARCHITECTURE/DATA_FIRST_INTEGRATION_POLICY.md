# Data First Integration Policy — SIG-FDSU RDC

**Version :** 1.0  
**Statut :** Obligatoire — règle d’architecture permanente  
**Date :** 2026-07-12

---

## Devise officielle

> **Chaque décision doit exploiter toutes les connaissances actuellement disponibles, tout en indiquant explicitement les connaissances encore manquantes.**

Cette devise est la philosophie officielle du SIG-FDSU RDC pour toute évolution future de la plateforme.

---

## Principes

1. **Données d’abord** — Avant toute nouvelle fonctionnalité, inventorier et exploiter les référentiels, API, moteurs et calculs déjà présents.
2. **Pas d’invention** — Aucun objet, score, distance ou relation fictive pour « remplir » une maquette.
3. **Maturité visible** — Les capacités futures ne sont pas masquées ; elles affichent leur niveau de maturité.
4. **Anomalie bloquante** — Si une donnée existe mais n’est pas exploitée, c’est une **Anomalie d’intégration** (Integrity Gate).
5. **Propagation métier** — Toute donnée à valeur décisionnelle doit remonter vers Spatial Decision Graph, TDT, Intelligence Territoriale, Salle DG et Dossier de décision lorsque pertinent.

---

## États de maturité autorisés

| État | Signification | Affichage UI |
|---|---|---|
| 🟢 **Opérationnel** | Données présentes, analyses fonctionnelles, exploitation réelle | Actif |
| 🟡 **Partiellement intégré** | Données présentes, couverture ou câblage partiel — limites explicites | Partiel + note |
| 🔵 **En cours d’intégration** | Référentiel absent — normal pour Education, Énergie, etc. | Futur + justification |
| 🔴 **Anomalie d’intégration** | Données existent mais non exploitées — **bloquant** | Anomalie + Integrity Gate |

### Interdiction

- Interdit d’afficher « UI non branchée » lorsque les données existent déjà.
- « En cours d’intégration » est autorisé **uniquement** si le référentiel n’existe réellement pas encore.

---

## Cas d’analyse spatiale (obligatoires)

| Cas | Situation | Verdict |
|---|---|---|
| **1** | Référentiel existe → recherche exécutée → 0 relation | **Normal** — « Aucune relation trouvée » |
| **2** | Référentiel existe → aucune recherche | **Anomalie** |
| **3** | Référentiel absent | **En cours d’intégration** — normal |
| **4** | Référentiel + calcul existent → vue non consommée | **Anomalie — priorité très haute** |

Un compteur `0` sans explication est **interdit**.

---

## Champ d’application

Obligatoire pour tout nouveau module, sprint, API ou vue UI, y compris :

- Spatial Decision Graph / Analyse d’Impact Territorial  
- Territorial Digital Twin  
- Intelligence Territoriale / Territorial Summary  
- Decision Engine / Explainable Decision / Workspace / Scenarios  
- Executive Situation Room / Salle DG  
- NSME / Spatial Matching  
- Santé, Télécom, Fibre, Routes, Transport, Population, Localités, CCN, Programmes  

---

## Integrity Gate

Un sprint est **refusé** si :

- une donnée existe mais n’est pas exploitée ;
- une API existe mais n’est jamais appelée alors qu’elle apporterait une valeur métier ;
- un moteur existe mais n’est jamais utilisé ;
- une couche SIG existe mais n’est pas affichée là où elle est utile ;
- une relation spatiale possible n’est jamais calculée ;
- l’UI affiche « non branchée » alors que les données existent.

Documents associés :

- `DATA_FIRST_INTEGRATION_AUDIT_V1.md`
- `INTEGRITY_GATE_REPORT_V1.md`
- `.cursor/rules/e2e-integrity-gate.mdc`
- `.cursor/rules/data-first-integration.mdc`

---

## Processus pour tout futur développement

1. Consulter l’inventaire NDF (`data/ndf/registries.json`) et l’audit Data First.  
2. Lister les référentiels déjà disponibles utiles au besoin.  
3. Brancher ou composer (pas réinventer).  
4. Afficher maturité + lacunes.  
5. Passer l’Integrity Gate avant commit.
