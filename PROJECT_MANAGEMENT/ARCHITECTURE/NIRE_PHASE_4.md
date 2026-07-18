# NIRE Phase 4 — Operator Review Workspace & MNO Audit Readiness

## Architecture et lazy loading

Le workspace opérateur est un module autonome accessible par `#nire-workspace` sous le libellé métier « Résolution d’identité ». Le Dashboard initial ne charge ni son JavaScript, ni sa feuille de style, ni ses endpoints. `app.js` injecte les deux ressources uniquement lors de l’ouverture explicite de la route. Le panneau HTML initial reste un conteneur vide sans données NIRE.

L’API interne complète Phase 3 par des agrégats légers, des listes paginées, des dossiers et l’historique. Les accès restent fondés sur `NireRepository`; aucune classe UI ne dépend du stockage PostgreSQL. Les réponses sont compactes et les limites sont bornées à 100 lignes.

## Vue opérateur

La vue d’ensemble présente huit KPI agrégés sans charger la file complète. Les Resolution Runs sont paginés et filtrables, avec version moteur/règles, statut et compteurs disponibles. Le détail distingue explicitement les métriques absentes : aucune durée, réduction ou progression n’est inventée.

La Review Queue est paginée et filtrable par statut, source, cible, domaine, score, confiance, ambiguïté, décision et besoin de revue. Le dossier affiche les identités sources côte à côte, conserve les valeurs originales et qualifie égalités, différences et informations manquantes.

## Géographie, preuves et décisions

La carte n’est créée que si au moins une coordonnée valide existe. `(0,0)` est toujours rejeté. Deux points déclenchent une emprise commune et une liaison visuelle; un seul point est affiché seul; aucun point produit un message professionnel sans carte vide.

Les preuves sont séparées en positives, négatives, conflits bloquants et compléments. Type, valeur, méthode, poids, confiance, fiabilité, contribution et version sont restitués depuis les données persistées. L’explication affichée est exclusivement celle de la décision ou du candidat persistant.

## Actions, historique et rôles

Validation, rejet, correction, report et annulation passent uniquement par l’API NIRE. Une justification est obligatoire; validation et annulation demandent confirmation. La correction porte sur la décision NIRE et crée une nouvelle décision liée à l’ancienne. L’historique chronologique ne propose aucune suppression.

Les rôles `ANALYST`, `REVIEWER`, `APPROVER` et `ADMIN` utilisent le contrat Phase 3. L’interface masque les actions non annoncées, mais l’API reste l’autorité de sécurité. Cette matrice est versionnée et pourra être remplacée par l’IAM institutionnel.

## Observabilité

La vue compacte expose statut, progression disponible, batch, `batch_size`, `max_candidates`, timeout, erreurs et métriques de génération persistées. Les temps client d’ouverture, KPI, file et dossier sont mesurés avec `performance.now()`. Aucun dispositif de monitoring lourd n’est ajouté.

## Audit MNO — préparation uniquement

L’onglet Audit MNO n’ingère aucune source. Orange, Vodacom, Airtel et Africell restent affichés avec « Non calculé ». Aucun nombre synthétique n’est présenté comme réel.

Un remplacement logique Orange/Vodacom ne pourra être proposé qu’après couverture ou résolution de 100 % de l’ancien référentiel, traitement de tous les conflits bloquants, absence de perte d’information et validation humaine/institutionnelle. Sinon, seule une fusion contrôlée conservant toutes les sources sera envisageable. Aucune suppression physique ni remplacement automatique n’est autorisé.

## Limites et Phase 5

Le workspace n’est pas un IAM et les tables Phase 3 ne possèdent pas encore toutes les colonnes d’observabilité avancée. Phase 5 couvrira l’ingestion contrôlée d’un fichier MNO réel authentifié, sa mise en quarantaine, la comparaison NIRE, le rapport de couverture par opérateur, la décision remplacement/fusion et la mise à jour contrôlée du référentiel Télécom après validation humaine.
