# National Territorial Intelligence Engine v1.0

## Objet et principes

Le NTIE est la couche analytique territoriale commune du SIG-FDSU RDC. Il assemble les resultats du National FDSU Asset Registry, de l'intelligence territoriale multi-echelle, du Territorial Impact Engine, du Program Lifecycle Engine et du Spatial Decision Graph. Il ne remplace aucun de ces moteurs et ne duplique ni leurs lecteurs de sources ni leurs regles metier.

Principes obligatoires : Data First, valeurs absentes conservees a `null`, provenance par indicateur, calculs explicables, absence de coefficient implicite et extensibilite par ajout d'adaptateurs.

## Architecture

```text
Sources officielles data/raw, data/strategic, data/business
                         |
        moteurs et referentiels existants
   +----------+----------+----------+----------+
   | Registry | Lifecycle| Impact   | SDG / TI |
   +----------+----------+----------+----------+
                         |
       NTIE - federation et normalisation
          |             |             |
        API         Dashboard       futurs moteurs
```

Le service `api/services/national_territorial_intelligence_engine.py` normalise les contrats existants. La route `api/routes/national_territorial_intelligence.py` publie le contrat HTTP. La vue dashboard ne recalcule rien : elle restitue les valeurs, limites et methodes de l'API.

## Flux de donnees

1. L'identifiant territorial est resolu par l'intelligence territoriale multi-echelle.
2. Les agrégats de population et de couverture sont repris avec leurs gardes anti-double comptage.
3. Les actifs sont lus depuis l'instantane en lecture seule du National Asset Registry puis rattaches selon la hierarchie documentee.
4. Chaque dimension est convertie vers un contrat commun.
5. Les valeurs absentes deviennent des indicateurs `unavailable`, jamais des zeros, sauf lorsqu'un comptage exhaustif du Registry retourne reellement zero.
6. Le profil expose score, evolution, qualite et explicabilite sans modifier les sources.

## Niveaux territoriaux

Le moteur accepte Province, Territoire, Secteur, Chefferie, Collectivite, Groupement et Localite. Secteur et Chefferie utilisent le niveau physique `collectivite` du referentiel tout en conservant leur `admin_type`. Cette representation respecte le modele existant et evite une duplication de tables.

## Contrat des indicateurs

Chaque indicateur publie : `id`, `label`, `value`, `unit`, `status`, `source`, `version`, `date`, `confidence`, `quality`, `method` et `explanation`.

Les dimensions v1 couvrent population, couverture mobile, populations couverte et non couverte, localites, sites FDSU, sites operateurs, CCN, sante, education, routes, fibre, energie, services publics, activites et potentiel economiques, contraintes geographiques, vulnerabilite numerique, accessibilite, maturite numerique et developpement territorial. Une dimension non raccordee reste visible avec `value: null` et une methode `not_calculated_no_source`.

## Algorithmes et controles

### Population et couverture

Le NTIE reprend les ensembles NCI couverts et non couverts declares exclusifs. Le nombre total de localites n'est additionne que lorsque les deux compteurs compatibles existent. La population totale, le taux et les compteurs conservent la source et la methode du moteur amont.

### Actifs territoriaux

Les comptes Sites FDSU et CCN proviennent exclusivement du Registry. Le rapprochement utilise les champs territoriaux normalises de l'actif et l'entite resolue. Aucun fichier programme n'est relu dans le NTIE.

### Score territorial

Un score officiel deja calcule par un moteur existant peut etre reference sans recalcul. En son absence, v1 affiche `Score indicatif`, `Confiance limitee` et une valeur `null`. Aucun coefficient officiel NTIE n'etant disponible, aucune moyenne ponderee ou ponderation egale n'est inventee. Les futures pondérations devront etre versionnees, sourcees et exposees dans l'explicabilite avant activation.

### Evolution

Les scenarios `Aujourd'hui`, `Apres 40 sites`, `Apres 300 sites`, `Apres 20 476 sites` et `Apres CCN` exposent les actifs effectivement documentes dans le Registry. Seul l'etat actuel reprend la couverture observee. Les impacts futurs restent `null` tant qu'un scenario valide du Territorial Impact Engine ne les fournit pas.

## API

- `GET /territorial-profile` : catalogue des profils documentes et niveaux supportes.
- `GET /territorial-profile/{id}` : profil complet.
- `GET /territorial-profile/{id}/score` : score et statut de ponderation.
- `GET /territorial-profile/{id}/population` : population et metadonnees.
- `GET /territorial-profile/{id}/coverage` : couverture et localites.
- `GET /territorial-profile/{id}/explainability` : sources, methodes, limites et dependances.
- `GET /territorial-profile/{id}/evolution` : scenarios temporels documentes.

## Dashboard

La vue **National Territorial Intelligence** fournit un selecteur de profil, des indicateurs, le score, la qualite, l'evolution, un resume cartographique et l'explicabilite. Le rendu detaille de carte reste delegue au composant territorial multi-echelle existant.

## Relations avec les moteurs

- National Asset Registry : identites, programmes, actifs et provenance.
- Program Lifecycle Engine : etats et historique des actifs, sans duplication dans le profil.
- Territorial Impact Engine : future source des effets de scenario valides.
- Spatial Decision Graph : relations spatiales et contexte decisionnel.
- Territorial Intelligence multi-echelle : resolution administrative, population, couverture et carte.

## Qualite, tracabilite et securite des calculs

Le profil compte les dimensions disponibles et indisponibles. Un indicateur `null` est exclu de tout score. Les zeros issus d'un comptage de Registry sont distingues des absences de source. Les reponses incluent la version du moteur, la date de generation, les sources, la confiance, la qualite et la methode.

## Extension et roadmap

1. Raccorder les referentiels MNO, energie, education et infrastructures publiques par adaptateurs, sans changer le contrat d'indicateur.
2. Publier une matrice officielle versionnee de pondérations NTIE.
3. Brancher les scenarios valides du Territorial Impact Engine pour les projections.
4. Ajouter des series temporelles datees et des comparaisons entre pairs de meme niveau.
5. Integrer les futurs moteurs CCN et de priorisation de sites via leurs API explicables.
6. Etendre la cartographie aux couches thematiques NTIE sans dupliquer le Spatial Decision Graph.

## Validation

Les tests backend couvrent les sept niveaux fonctionnels avec des entites reelles, le contrat de metadonnees, la population, la couverture, les comptes Registry, l'absence de ponderations inventees et tous les endpoints. Les tests Playwright valident les memes niveaux via l'API isolee et la vue dashboard.
