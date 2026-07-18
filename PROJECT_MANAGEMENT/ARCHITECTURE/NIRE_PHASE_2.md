# NIRE Phase 2 — Real Source Adapters & Candidate Generation Engine

## Statut et doctrine

Cette phase est additive, réversible et sans persistance. Elle ne fusionne aucune identité, ne modifie aucun référentiel source et ne monte ni API ni interface. NIRE reste un service métier chargé uniquement à la demande : aucun index ni référentiel n'est chargé lors de l'import Python ou au démarrage du Dashboard.

## Adaptateurs réels en lecture seule

`CeniSourceAdapter`, `EducationSourceAdapter`, `HealthSourceAdapter`, `TelecomSourceAdapter`, `FdsuSiteSourceAdapter` et `AdministrativeSourceAdapter` implémentent le contrat `SourceAdapter`. Leurs fournisseurs différés accèdent respectivement au registre CENI, à sa projection Éducation, aux services PostgreSQL Santé/Télécom, au JSON des 20 476 sites et aux lignes administratives fournies par le futur orchestrateur. Un fournisseur injectable rend chaque contrat testable et remplaçable.

Chaque projection conserve identifiant source, provenance, version et statut qualité. CENI sépare le flux intégré du flux de quarantaine, expose `resolution_candidate` et neutralise `(0,0)`. Éducation conserve son `source_id` CENI. Une géométrie Télécom ligne ou polygone devient `TELECOM_NETWORK_GEOMETRY`, jamais un site. FDSU conserve son identifiant et son nom technique sans en inventer un. Administration couvre province, ville, territoire, secteur, chefferie, groupement et localité ; localité et village ne sont jamais déclarés équivalents sans preuve explicite.

## Génération de candidats et index

`CandidateGenerationEngine` construit un `MemoryCandidateIndex` une seule fois pour la cible. Les index sont : identifiant institutionnel, type, province, territoire, opérateur, nom normalisé et grille spatiale légère. `CandidateIndex` est le point d'extension prévu pour PostgreSQL/PostGIS sans changement du moteur.

Le blocking combine identifiant exact prioritaire, compatibilité de types, contexte administratif, cellules spatiales avec distance Haversine, opérateur Télécom et nom comme filtre secondaire. Les conflits explicites de province, territoire ou opérateur requis sont exclus. Le classement pondéré applique un top-k versionné par domaine. Le coût est `O(cibles + sources × hits d'index)` et non `O(sources × cibles)` ; les métriques rendent visibles comparaisons théoriques, candidats réels, réduction, moyenne, temps d'indexation et temps de génération.

## Preuves et calibration

Sept extracteurs indépendants produisent les preuves lexicales, géographiques, administratives, institutionnelles, de type, d'opérateur et de qualité source. Chaque preuve conserve valeur, valeur normalisée, méthode, sources, poids, confiance, fiabilité et version. Les adaptateurs fournissent les données ; les extracteurs qualifient ; le Fusion Engine décide.

La calibration synthétique contrôle vrais matchs/non-matchs, homonymes, proximité trompeuse, provinces distinctes, identifiants concordants/conflictuels, opérateurs identiques/distincts et absence de coordonnées. Précision, rappel, taux de faux positifs et taux de faux négatifs sont des métriques techniques du noyau, jamais une validation métier nationale.

## Cas contrôlés et MNO

- CENI ↔ Éducation : `source_id` commun donne un candidat exact prioritaire, sans consolidation.
- FDSU ↔ Administration : proximité et rattachements donnent des candidats classés et expliqués ; un site n'est jamais déclaré identique à une localité.
- `E.P KABAMBA` : le nom seul reste ambigu. `CABANE` reste critique en situation d'homonymie massive. Aucun cas n'est fusionné.
- MNO : le contrat futur sait porter opérateur, identifiant, nom, coordonnées, technologie, province et territoire, puis classer `EXACT_MATCH`, `PROBABLE_MATCH`, `AMBIGUOUS`, `NEW_SITE`, `POSSIBLE_DUPLICATE` ou `CONFLICT`. Aucun fichier MNO réel n'est lu. Les données historiques Orange/Vodacom ne pourront être remplacées logiquement qu'après couverture ou résolution démontrée à 100 %.

## Règles, limites et trajectoire Phase 3

Les stratégies résident dans `nire_candidate_generation_rules_v1.json`. Rayons, top-k, compatibilités et priorités sont évolutifs ; une future version s'ajoute sans écraser v1. Les index restent en mémoire pour cette phase et les adaptateurs DB peuvent nécessiter pagination/streaming à grande échelle.

La Phase 3 ajoutera par contrats : persistance additive avec migrations réversibles, audit trail, API interne, Review Queue, validation humaine, historique des décisions et annulation. Les API dépendront des interfaces, non des implémentations ; les identités sources seront toujours conservées et aucune consolidation NEIL ne sera irréversible.
