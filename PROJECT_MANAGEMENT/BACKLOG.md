# BACKLOG - SIG-FDSU RDC

## Version courante

- Version projet: 0.8.4-sprint-3.1
- Date de mise a jour: 2026-07-04
- Cadre officiel: Phase 3 - plateforme nationale SIG, aide a la decision et connaissance territoriale.

## Priorite Sprint 3.2

- Synchroniser completement carte, table, fiche et recherche.
- Brancher l'autocomplete universel sur l'API `/entities/search`.
- Uniformiser les endpoints de listes avec enveloppe `{items,total,skip,limit}`.
- Persister les profils territoriaux dans les tables PostgreSQL prevues par le Master Data Model.
- Produire des exports KMZ natifs compresses et des PDF serveur.

## Fonctionnel

- Consolider le parcours Zone FDSU > Province > Territoire > Collectivite > Groupement > Localite > Site > Mission.
- Ajouter des filtres metier avances: activite economique, defis, services publics, potentiel et connectivite.
- Ajouter les vues de comparaison territoriale.
- Ajouter la gestion documentaire et photo reliee aux fiches metier.

## Technique

- Ajouter des tests Dashboard automatises des interactions liste-selection-fiche-carte.
- Ajouter des tests API pour `/entities/search` et les routes detail.
- Normaliser les exports volumineux avec pagination et streaming.
- Documenter les migrations PostgreSQL liees aux profils territoriaux.

