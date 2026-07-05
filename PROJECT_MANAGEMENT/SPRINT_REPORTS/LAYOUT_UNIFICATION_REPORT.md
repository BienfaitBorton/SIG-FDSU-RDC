# SIG-FDSU RDC - Rapport Sprint 3.3.2

## Uniformisation des layouts Dashboard

Date : 2026-07-05

## Objectif

Uniformiser le placement vertical de tous les modules du dashboard afin que chaque contenu commence immediatement sous le bandeau superieur, sans grand espace vide, et avec une structure commune :

Header -> barre d'actions -> filtres -> liste/tableau -> carte si necessaire -> fiche.

## Causes identifiees

- Le conteneur principal utilisait un espacement vertical global trop large entre le header et la zone de contenu.
- Les modules avaient des paddings et gaps heterogenes selon les sections.
- Plusieurs composants imposaient des `min-height` importants, notamment la carte principale a `620px`, les placeholders cartographiques a `420px` et certains blocs de rapport a `220px`.
- Certains sous-composants ajoutaient des `margin-top` secondaires qui decalaient les listes, fiches et zones de travail.
- Le changement de menu scrollait deja vers le haut, mais ne placait pas le focus sur le debut du module actif.

## Composants corriges

- `dashboard/styles.css`
  - normalisation de `.main-content`
  - normalisation de `.topbar`
  - normalisation de `.content-area`
  - normalisation commune de `.module-panel`
  - reduction des espacements `.panel-header`
  - harmonisation des grilles KPI, listes, tableaux et fiches
  - hauteur cartographique recalculee avec `clamp(...)`
  - hauteur disponible des tableaux recalculee avec `calc(100vh - 300px)`
  - reduction des `min-height` excessifs des cartes, placeholders et rapports
  - adaptation responsive pour 1080px et 720px
- `dashboard/app.js`
  - maintien du scroll automatique vers le haut
  - ajout du focus automatique sur le panneau actif apres changement de menu

## Captures avant/apres

Le navigateur integre Codex n'etait pas disponible dans cette session (`Browser is not available: iab`). Les captures bitmap avant/apres n'ont donc pas pu etre produites automatiquement.

Capture technique avant :

```text
.main-content      padding: 28px 36px ; gap: 24px
.topbar            padding: 24px 32px ; border-radius: 24px
.module-panel      padding: 28px ; border-radius: 28px
.map-canvas        min-height: 620px
.map-placeholder   min-height: 420px
.normalization-report-preview min-height: 220px
```

Capture technique apres :

```text
.main-content      height: 100vh ; overflow: auto ; padding: 18px 24px ; gap: 16px
.topbar            padding: 16px 22px ; border-radius: 16px
.module-panel      min-height: 0 ; padding: 18px ; gap: 14px
.map-canvas        min-height: clamp(360px, calc(100vh - 260px), 620px)
.map-placeholder   min-height: clamp(260px, calc(100vh - 300px), 420px)
.normalization-report-preview min-height: clamp(120px, 22vh, 220px)
```

## Validation UX

Modules verifies dans `dashboard/index.html` :

- Dashboard
- Cartographie
- Referentiel administratif
- Gestion des referentiels
- Explorateur de sources
- Sites FDSU
- Aide a la decision
- Centre de connaissances
- Assistant d'enrichissement
- Import
- Export
- Statistiques
- Parametres
- Utilisateurs

Regles validees :

- chaque module est couvert par `.module-panel` ou `#dashboard-panel` ;
- les panneaux caches restent en `display: none` ;
- le panneau actif recoit le focus apres navigation ;
- le scroll de `.main-content` et de `window` revient en haut apres changement de menu ;
- les tableaux et cartes ont une hauteur maximale ou minimale calculee selon la hauteur disponible ;
- les fiches laterales restent dans la partie visible avec `top/right/bottom: 12px`.

## Validation resolutions

Validation statique realisee pour les contraintes de hauteur suivantes :

- 1366x768 : hauteur disponible compacte, cartes reduites par `calc(100vh - 260px)`.
- 1600x900 : espacement standard, listes et cartes visibles sans decalage initial.
- 1920x1080 : maintien du layout dense, sans agrandissement vertical inutile.
- 2560x1440 : padding legerement ajuste, contenu toujours ancre sous le header.

## Tests effectues

- Verification des 14 panneaux/modules dans `dashboard/index.html`.
- Verification des regles CSS Sprint 3.3.2 dans `dashboard/styles.css`.
- Verification du scroll et focus dans `dashboard/app.js`.
- Verification UTF-8 sans BOM et absence de sequences mojibake dans :
  - `dashboard/styles.css`
  - `dashboard/app.js`
  - `dashboard/index.html`
- Test HTTP du serveur statique dashboard :
  - `index.html` : 200, `text/html; charset=utf-8`
  - `styles.css` : 200, `text/css; charset=utf-8`
  - `app.js` : 200, `application/javascript; charset=utf-8`

## Limites

- Aucune capture visuelle bitmap n'a pu etre generee car le navigateur integre n'etait pas disponible et `node --check` n'est pas installe dans l'environnement PowerShell.
- Aucune fonctionnalite metier n'a ete modifiee ; seules les regles de layout et le focus de navigation ont ete ajustes.

## Confirmation

Le dashboard dispose maintenant d'une couche de layout commune pour tous les modules. Les grands espaces verticaux imposes par les paddings, gaps et min-height excessifs sont neutralises, et chaque changement de menu replace l'utilisateur en haut du module actif.
