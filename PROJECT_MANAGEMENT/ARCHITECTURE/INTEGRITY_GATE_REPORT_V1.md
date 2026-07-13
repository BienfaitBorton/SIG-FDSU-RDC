# Integrity Gate Report v1.0 — Data First Integration

**Date :** 2026-07-12  
**Politique :** `DATA_FIRST_INTEGRATION_POLICY.md`  
**Audit :** `DATA_FIRST_INTEGRATION_AUDIT_V1.md`

---

## Verdict

| Critère Gate | Résultat |
|---|---|
| Inventaire référentiels / API / moteurs | **Pass** — documenté |
| Zéros SDG sans explication | **Corrigé** — `empty_reason` + maturité |
| Panneau détail sélection vide | **Corrigé** — champs métier obligatoires |
| Anomalies CAS 2/4 documentées | **Pass** |
| Anomalies P0 entièrement résolues (câblage santé NSME) | **Pass** — A14 corrigé (PostGIS `health.health_facilities`) |
| Commit créé | **Aucun** (consigne sprint) |

Le Gate **bloque les futurs sprints fonctionnels** tant que les anomalies 🔴 P0 listées ci-dessous ne sont pas traitées ou explicitement dérogées.

---

## Anomalies d’intégration

| ID | Anomalie | Cas | Priorité | Statut |
|---|---|---|---|---|
| A1 | API Coverage/NCI sans module UI | 4 | P1 | Documentée |
| A2 | API NDF sans consommateur UI | 4 | P2 | Documentée (by design actuel) |
| A3 | Knowledge Hub `/api/knowledge` non appelé | 4 | P1 | Documentée |
| A4 | `POST /spatial-matching/refresh` jamais depuis UI | 2 | P0 | **Corrigé** — bouton SDG « Recalculer les relations spatiales » |
| A5 | Import sites_20476 non branché UI | 4 | P2 | Documentée |
| A6 | Master Registry sans entités SITE/CCN | 4 | P2 | Documentée |
| A7 | Sous-API Telecom non consommées | 4 | P2 | Documentée |
| A8 | Drift SDG↔NSME (types jamais émis) | 2 | P1 | Documentée |
| A9 | Transport fichier vs DB (503 hors db) | 2 | P1 | Documentée |
| A10 | CCN demo fichier uniquement | 3→🟡 | P2 | Documentée |
| A11 | Education/markets `future` vs dérivation NCI possible | 3/1 | P2 | Documentée |
| A12 | Reference catalog endpoints sous-utilisés | 4 | P3 | Documentée |
| A13 | Analysis `/site/{id}` non utilisé modules | 4 | P3 | Documentée |
| A14 | **Santé 37k** — NSME branché sur `health.health_facilities` | **4→1** | **P0** | **Corrigé** — relations PostGIS ; SDG maturité 🟢/🟡 |
| A15 | **Profil territorial incomplet** malgré admin/santé/télécom/routes | **4** | **P0** | **Corrigé** — `TerritorialProfileService` (2026-07-13) |

---

## Correctifs livrés (ce sprint)

1. **Politique Data First** officielle + devise.  
2. **SDG** : pour chaque catégorie vide — maturité + cas + note (jamais un `0` nu).  
3. **SDG** : payload `data_first.anomalies[]`.  
4. **UI SDG** : pastilles de maturité dans les filtres ; panneau détail enrichi.  
5. **Audit + Gate Report** complets.  
6. **P0 Santé (2026-07-12)** : matching PostGIS `health.health_facilities`.  
7. **P0 Profil territorial (2026-07-13)** : resolver + composition Data First ; superficie, groupements, localités, santé spatiale, télécom, routes ; voir `TERRITORIAL_DATA_FIRST_COMPLETENESS_AUDIT_V1.md`.

---

## Audit UI (synthèse)

| Symptôme | Constat |
|---|---|
| « UI non branchée » | Présent Decision Center CCN extensions (`ui_ready`) — à remplacer par maturité Data First |
| Placeholders | Inputs search (OK) ; panneaux Decision Center historiques |
| KPI fictifs | Budget « Référentiel Budget non branché » (`index.html`) — 🔵 si absent, à reclasser |
| Voile / overlay | Traité Integrity Gate E2E précédent (ESR CSS + app.js) |
| Double Leaflet | Guard SDG v2.1 + tests e2e |
| TODO / Coming Soon visibles | À surveiller ; pas de « Coming Soon » massif détecté en grep modules SDG |

---

## Spatial Decision Graph — lecture des 0

Pour un site typique (ex. 30 BAKI) :

| Catégorie | Lecture Data First |
|---|---|
| Localités / Population | 🟢 Relations NSME présentes |
| Santé | 🟢 Opérationnel (PostGIS) ou 🟡 Partiel si 0 dans le rayon documenté |
| Routes | 🟡 Aucune relation pour le site **ou** table transport absente |
| Télécom | 🟡 Aucune relation NCI fibre pour le site |
| CCN | 🟡 Demo présent, pas de CONNECTS_CCN pour ce site |
| Education / Énergie / Marchés | 🔵 En cours d’intégration |
| Sites FDSU voisins | 🔴 Recherche `NEAR_FDSU_SITE` non câblée NSME |

---

## Confirmations obligatoires

- Aucun référentiel majeur inventorié dans NDF / `data/` / routers n’a été volontairement omis de l’audit.  
- Aucune donnée disponible n’est **volontairement** laissée inutilisée sans documentation d’anomalie.  
- Chaque anomalie détectée est listée (A1–A14) avec priorité.  
- La **Data First Integration Policy** est désormais **obligatoire** pour tous les futurs développements SIG-FDSU RDC.
