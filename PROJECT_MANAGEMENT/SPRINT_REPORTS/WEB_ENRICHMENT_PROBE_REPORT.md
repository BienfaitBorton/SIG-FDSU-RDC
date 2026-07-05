# SIG-FDSU RDC - Web Enrichment Probe

Date de consultation : 2026-07-05T15:25:17+00:00
Mode insertion : dry-run
Propositions inserees : 0

## Perimetre

- Maximum 5 entites.
- Maximum 10 propositions par entite.
- Maximum 3 sources par entite.
- Aucune ecriture dans `territorial_profiles`, `knowledge`, `localites`, `territoires` ou `provinces`.
- Insertion autorisee uniquement dans `territorial_enrichment_suggestions` lorsque `--commit` est utilise.

## Sources trouvees

### Kinshasa
- Aucune source publique autorisee exploitable trouvee pendant ce probe.

### Haut-Uélé
- Aucune source publique autorisee exploitable trouvee pendant ce probe.

### Dungu
- Aucune source publique autorisee exploitable trouvee pendant ce probe.

### Banalia
- Aucune source publique autorisee exploitable trouvee pendant ce probe.

### Wando
- Aucune source publique autorisee exploitable trouvee pendant ce probe.

## Donnees proposees

### Kinshasa
- Aucune proposition creee sans source exploitable.

### Haut-Uélé
- Aucune proposition creee sans source exploitable.

### Dungu
- Aucune proposition creee sans source exploitable.

### Banalia
- Aucune proposition creee sans source exploitable.

### Wando
- Aucune proposition creee sans source exploitable.

## Donnees non trouvees

- Kinshasa : situation_economique, activites_economiques_principales, activites_economiques_secondaires, particularites, defis, potentiel_agricole, potentiel_minier, potentiel_commercial, potentiel_touristique, services_publics, connectivite, infrastructures
- Haut-Uélé : situation_economique, activites_economiques_principales, activites_economiques_secondaires, particularites, defis, potentiel_agricole, potentiel_minier, potentiel_commercial, potentiel_touristique, services_publics, connectivite, infrastructures
- Dungu : situation_economique, activites_economiques_principales, activites_economiques_secondaires, particularites, defis, potentiel_agricole, potentiel_minier, potentiel_commercial, potentiel_touristique, services_publics, connectivite, infrastructures
- Banalia : situation_economique, activites_economiques_principales, activites_economiques_secondaires, particularites, defis, potentiel_agricole, potentiel_minier, potentiel_commercial, potentiel_touristique, services_publics, connectivite, infrastructures
- Wando : situation_economique, activites_economiques_principales, activites_economiques_secondaires, particularites, defis, potentiel_agricole, potentiel_minier, potentiel_commercial, potentiel_touristique, services_publics, connectivite, infrastructures

## Risques

- Les moteurs de recherche peuvent retourner des pages non officielles ou des miroirs ; le script filtre par domaine autorise.
- Les pages institutionnelles peuvent changer de structure ou etre indisponibles.
- Les extraits textuels ne constituent pas une validation metier.
- OpenStreetMap est limite a l'appui geographique et ne doit pas fonder seul une donnee economique.

## Limites

- Erreurs ou indisponibilites observees :
  - Kinshasa / https://www.caid.cd/index.php/donnees-par-villes/ville-de-kinshasa/domaine=fiche: page generique ou recherche non exploitable
  - Kinshasa / https://caid.cd/index.php/donnees-par-villes/ville-de-kinshasa/domaine=fiche: page generique ou recherche non exploitable
  - Kinshasa / CAID: recherche impossible (<urlopen error timed out>)
  - Haut-Uélé / https://www.caid.cd/index.php/donnees-par-province-administrative/province-de-haut-uele/domaine=fiche: page generique ou recherche non exploitable
  - Haut-Uélé / https://caid.cd/index.php/donnees-par-province-administrative/province-de-haut-uele/domaine=fiche: page generique ou recherche non exploitable
  - Haut-Uélé / CAID: recherche impossible (<urlopen error timed out>)
  - Dungu / https://www.caid.cd/index.php/donnees-par-territoire/territoire-de-dungu/domaine=fiche: page generique ou recherche non exploitable
  - Dungu / https://caid.cd/index.php/donnees-par-territoire/territoire-de-dungu/domaine=fiche: page generique ou recherche non exploitable
  - Dungu / CAID: recherche impossible (<urlopen error timed out>)
  - Banalia / https://www.caid.cd/index.php/donnees-par-territoire/territoire-de-banalia/domaine=fiche: page generique ou recherche non exploitable
  - Banalia / https://caid.cd/index.php/donnees-par-territoire/territoire-de-banalia/domaine=fiche: page generique ou recherche non exploitable
  - Banalia / CAID: recherche impossible (<urlopen error timed out>)
  - Wando / https://www.caid.cd/index.php/donnees-par-territoire/territoire-de-dungu/domaine=fiche: page generique ou recherche non exploitable
  - Wando / CAID: recherche impossible (<urlopen error timed out>)
- Le script ne contourne pas les restrictions reseau de l'environnement Codex.
- Si l'environnement n'a pas acces a Internet, aucune donnee n'est inventee et aucune proposition n'est creee.

## Recommandations

- Executer d'abord sans `--commit` pour relire le rapport.
- Valider manuellement chaque proposition dans l'assistant d'enrichissement.
- Ajouter une liste de pages institutionnelles fixes si CAID, INS ou ARPTC exposent des URL stables.
- Ajouter une extraction PDF controlee lors d'un sprint dedie si les rapports institutionnels sont majoritairement au format PDF.
