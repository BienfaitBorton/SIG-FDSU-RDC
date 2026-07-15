# Harmonisation terminologique institutionnelle v1

**Objectif :** présenter le SIG-FDSU comme plateforme nationale du Service Universel, sans personnalisation excessive autour d’un profil individuel.

**Périmètre :** libellés UI, tooltips, titres, menus, documentation utilisateur.  
**Hors périmètre :** identifiants techniques (`salle_pilotage`, `dg_dossier`, routes API, moteurs métier).

## Correspondances officielles (UI)

| Ancien libellé | Libellé institutionnel |
|----------------|------------------------|
| Salle de Pilotage DG | **Salle de Pilotage** / **Salle de Pilotage National** |
| Présenter au DG | **Présentation guidée** |
| Préparer un dossier DG | **Préparer un dossier de décision** |
| Executive Briefing | **Synthèse Exécutive** |
| Executive Situation Room | **Centre National de Pilotage** |
| Decision Workspace | **Espace de Décision** |
| Territorial Digital Twin | **Jumeau Numérique Territorial** |
| Mode Présentation DG | **Mode Présentation** |
| Recommandations DG | **Recommandations de pilotage** |

## Implémentation frontend

- Fichier central : `dashboard/modules/shared/institutional-labels.js` (`FdsuLabels.harmonize`)
- Appliqué aux textes codés en dur et aux libellés renvoyés par l’API lors de l’affichage (actions ESR, scénarios, etc.)

## Occurrences « DG » conservées

- Commentaires développeur (non visibles)
- Identifiants techniques (`dg_dossier`, `prepare_dg_dossier`)
- Documentation métier décrivant le rôle du Directeur Général comme **fonction administrative** (livre blanc, principes de design)

## Vérification

Rechercher dans `dashboard/` les chaînes `DG`, `Executive Briefing`, `Digital Twin`, etc. — seules les références techniques ou métier explicites doivent subsister.
