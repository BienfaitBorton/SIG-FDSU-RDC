# Règle UX — Aucune impasse de navigation

**Portée :** SIG-FDSU RDC (toute l’interface)  
**Statut :** Obligatoire  
**Date :** 10 juillet 2026

## Principe

Aucune action de l’interface ne doit laisser l’utilisateur **sans moyen visible et immédiat de revenir** à l’état précédent.

## Interdit

- Plein écran natif du navigateur (`requestFullscreen`) lorsqu’il masque les contrôles de l’application
- Modes immersifs sans barre de sortie visible
- Modales / overlays sans bouton Fermer / Retour clairement affiché
- États où seul ESC (non documenté) permet de sortir

## Obligatoire

- Tout mode immersif (ex. **Mode Focus** cartographique) expose une barre persistante avec :
  - **← Retour**
  - titre du mode
  - **Quitter …**
- ESC peut compléter la sortie, jamais la remplacer comme seul moyen
- La sortie restaure l’interface précédente sans perte de contexte utile (ex. zoom / position carte)

## Référence d’implémentation

Cartographie → **Mode Focus** (`#carto-focus-btn`, `#cartography-focus-bar`) — immersion dans l’application, pas de fullscreen navigateur.
