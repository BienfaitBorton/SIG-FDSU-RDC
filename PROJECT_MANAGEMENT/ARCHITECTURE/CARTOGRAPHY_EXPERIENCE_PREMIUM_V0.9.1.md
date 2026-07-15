# Rapport UX — Decision Experience Premium · Phase 1 Cartographie

**Version** : 0.9.1  
**Périmètre** : expérience cartographique uniquement (aucun moteur métier modifié)  
**Statut** : livré en working tree — **aucun commit**

## Objectif

Transformer la cartographie SIG-FDSU RDC en expérience institutionnelle utilisable en réunion DG / ministère / bailleurs : carte dominante, barre premium, mode Démonstration, popups intelligents, légende moderne.

## Livrables implémentés

### 1. Occupation de l'espace
- Hauteur carte augmentée (`calc(100vh - 168px)`)
- Marges toolbar réduites
- Panneau latéral limité à 380px max

### 2. Barre cartographique premium
- Nouvelle barre `.cartography-toolbar-premium` avec icônes + libellés + tooltips
- Actions : Vue nationale, Cartographie libre, Recherche, Couches, Légende, Analyse, Impression, Basemap, Mesure, Démonstration, Guidé, Entités, Plein écran

### 3. Mode Démonstration
- Module `dashboard/modules/shared/cartography-experience/cartography-experience.js`
- **Navigation libre** : interface épurée, carte maximisée
- **Parcours guidé** : 11 étapes RDC → Zone → … → Dossier → Recommandation
- Contrôles : Précédent / Pause / Reprise / Suivant / Quitter
- Sortie immédiate (Échap ou Quitter) — **aucune recréation Leaflet**

### 4–6. Popups & infobulles
- Survol : tooltip compact (`sig-map-tooltip--compact`)
- Clic : popup enrichi `SigMapTooltips.bindRichPopup` avec actions fonctionnelles (Analyser, Dossier, TI)
- Auto-pan + keepInView + repositionnement viewport

### 7. Panneaux
- Un seul tiroir ouvert via `closeAllCartographyPanels`
- Animation d'entrée panneau

### 8. Légende
- Catégories : Administratif, Programmes, Télécom, Routes, Autres
- Toggle afficher/masquer + slider transparence par couche

### 9–12. Design, accessibilité, responsive
- Design system dédié `cartography-experience.css`
- Focus visible, Échap (mesure / démo / plein écran)
- Breakpoint 1366px : icônes seules sur petits écrans

## Fichiers touchés (UX uniquement)

| Fichier | Rôle |
|---------|------|
| `dashboard/modules/shared/cartography-experience/cartography-experience.js` | Mode démo, mesure, légende |
| `dashboard/modules/shared/cartography-experience/cartography-experience.css` | Design premium |
| `dashboard/index.html` | Toolbar, demo bar, légende |
| `dashboard/modules/shared/map-tooltips.js` | Popups enrichis |
| `dashboard/app.js` | Branchement expérience + popups |
| `tests/e2e/cartography-experience-premium.spec.js` | Non-régression Playwright |

## Recommandations Phase 2

1. **Parcours guidé narratif** : synchroniser zoom réel sur entités sélectionnées (province/territoire nommés)
2. **Mesure avancée** : surface, périmètre, export PNG annotation
3. **Mode présentation DG** : thème clair optionnel + logo institutionnel discret
4. **Popups métier** : templates Santé/CCN dédiés avec actions API déjà câblées
5. **Performance** : clustering sites 300 en vue nationale

## Validation

Exécuter :
```bash
npx playwright test tests/e2e/cartography-experience-premium.spec.js
```

Captures recommandées : `#map` normal, mode Démonstration, popup enrichi, légende ouverte.
