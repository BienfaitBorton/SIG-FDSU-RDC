# Referentiels officiels - architecture

## Objectif de cette phase

Preparer le SIG-FDSU a integrer les referentiels officiels, sans telechargement de donnees et sans modification de PostgreSQL ou des API existantes.

## Sources officielles preparees

Le projet reserve les emplacements suivants:

- data/sources/ceni/
- data/sources/caid/
- data/sources/ins/
- data/sources/fdsu/

## Roles des sources

- CENI: referentiel administratif
- CAID: indicateurs statistiques
- INS: nomenclatures officielles
- KMZ: geometrie
- FDSU: donnees metier

## Module applicatif cree

Le module app/referentials/ contient les composants d architecture suivants:

- source_manager.py: registre des sources officielles, role par source, chemins de stockage
- validator.py: point d entree pour validations schema/contenu/coherence
- comparator.py: structure de comparaison entre versions (ajouts, suppressions, modifications)
- publisher.py: workflow Import -> Analyze -> Validate -> Publish
- quality.py: structure d evaluation qualite (completeness, consistency, geometry, duplicates, global)

## Portee

- Architecture uniquement
- Aucune logique metier definitive
- Aucune synchronisation executee
- Aucune donnee importee

## Prochaine etape recommandee

Brancher progressivement chaque composant sur des endpoints dedies, en conservant la regle: seules les donnees publiees sont consommees par le SIG.
