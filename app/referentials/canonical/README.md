# Couche Canonique SIG-FDSU

Ce package definit le modele canonique national pour representer toute entite administrative de la RDC avant toute integration de source.

## Portee

- Aucune modification PostgreSQL.
- Aucune modification des API existantes.
- Aucun branchement actif de source.
- Definitions declaratives uniquement (schema, modele, mapping, registres).

## Fichiers

- `canonical_schema.py` : enums et regles de base (niveaux administratifs, sources, statuts).
- `canonical_entity.py` : modele unique `CanonicalAdministrativeEntity` et objets associes.
- `mapping_registry.py` : registre de profils de mapping source -> canonique.
- `canonical_mapper.py` : conversion d'un enregistrement source vers une entite canonique.
- `source_registry.py` : registre des sources connues et de leurs metadonnees.

## Sources declarees

Le mapping registry et le source registry declarent:

- HDX
- CENI
- CAID
- KMZ
- Excel FDSU

Ces declarations sont extensibles pour de futures sources via `SourceKey.CUSTOM` et l'enregistrement de nouveaux profils.

## Extension future

1. Ajouter une nouvelle source dans `SourceKey`.
2. Declarer sa `SourceDefinition` dans `SourceRegistry`.
3. Enregistrer un `SourceMappingProfile` dans `MappingRegistry`.
4. Utiliser `CanonicalMapper` pour produire des `CanonicalAdministrativeEntity`.
