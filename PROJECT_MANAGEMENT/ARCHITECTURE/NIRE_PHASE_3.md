# NIRE Phase 3 — Persistence, Audit Trail & Review Queue

## Doctrine et persistance

Phase 3 rend NIRE opérationnel sans modifier ni fusionner les référentiels sources. Toutes les opérations sont additives, explicites, traçables et réversibles. Les sources restent référencées uniquement par `source_name` et `source_entity_id`.

La migration réversible `0006_nire_operational` crée le schéma PostgreSQL `nire` et huit tables : `resolution_runs`, `resolution_candidates`, `resolution_evidences`, `resolution_decisions`, `review_queue`, `review_actions`, `rule_versions` et `decision_history`. `downgrade()` retire exclusivement ces objets. Aucun DDL ne vise une table source.

Le contrat `NireRepository` découple l'orchestration du stockage. `PostgresNireRepository` est différé jusqu'à une requête explicite ; `InMemoryNireRepository` porte les workflows contrôlés et les tests.

## Audit, décisions et Review Queue

Une décision conserve moteur, versions, score, explication, décision précédente et date d'annulation. Chaque création, correction ou annulation ajoute une entrée immuable dans `decision_history`. Une preuve ou décision validée ne disparaît jamais silencieusement.

La file propose `PENDING`, `IN_REVIEW`, `VALIDATED`, `REJECTED`, `CORRECTED`, `DEFERRED` et `CANCELLED`. Chaque action conserve auteur, rôle, justification, preuves consultées, ancien/nouveau statut et date. Correction et annulation créent une nouvelle décision liée à l'ancienne.

Les rôles contractuels `ANALYST`, `REVIEWER`, `APPROVER`, `ADMIN` préparent un futur IAM. Ils n'en constituent pas un. Le nom seul et toute action sans traçabilité sont insuffisants.

## API interne, workflow et performance

L'API versionnée `/api/nire` est masquée du schéma public. Elle expose runs, candidats, décisions, génération explicite, file paginée/filtrée et actions. Ses dépendances ciblent le service et le repository, jamais les tables concrètes.

Les runs sont explicites et bornés par `batch_size`, `max_candidates` et `timeout_seconds`. Aucun repository, index ou accès DB NIRE n'est initialisé au démarrage du Dashboard.

Le workflow contrôlé est : Source Adapter → Candidate Generation → Evidence Extraction → Evidence Fusion → Resolution Decision → Persistence → Review Queue. Il utilise des entités injectées et n'écrit jamais dans leur source. La capacité de placer les 38 candidats CENI en file est testée : ils restent `AMBIGUOUS` ou `INSUFFICIENT_EVIDENCE`, avec revue humaine obligatoire.

## Phase 4

La migration est définie mais non appliquée ici. Phase 4 couvrira l'interface opérateur, la visualisation comparative des preuves, la revue humaine, la comparaison multi-source et la préparation contrôlée du premier audit MNO réel, sans remplacement automatique des données historiques.
