# Executive Presentation Mode — Phase 2.1

**Statut :** UX Dossier de Décision — reconception  
**Date :** 14 juillet 2026  
**Contrainte :** aucun moteur métier / aucun commit

---

## Architecture UX retenue

```text
Dossier de Décision (#decision-case)
        │
        ▼
┌─────────────────────────────────────────┐
│  #sdg-shell (même Leaflet #dxl-map)     │
│                                         │
│  [Mode Présentation]  ← entrée       │
│                                         │
│  body.executive-presentation-mode       │
│  ┌─ #epm-root (chrome overlay) ──────┐  │
│  │ topbar (marque / site / prio)     │  │
│  │ KPI strip (10 indicateurs)        │  │
│  │ narrative + compteur guidé        │  │
│  │ carte dominante (85–92 % utile)   │  │
│  │ dock icônes (bas)                 │  │
│  │ panneaux Relations/Détail on-demand│ │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### Principes

1. **Immersion réelle** — viewport fixe + Fullscreen API si disponible, fallback CSS.
2. **Carte unique** — réutilisation de l’instance Leaflet SDG ; `invalidateSize()` à l’entrée/sortie.
3. **Chrome minimal** — topbar + KPI + dock ; pas de barre textuelle lourde.
4. **Panneaux à la demande** — masqués au démarrage ; ouverts à la sélection ou via dock.
5. **Guidé sans étape vide** — les catégories à count = 0 sont sautées.
6. **Restauration d’état** — snapshot centre/zoom/filtres/scroll avant entrée.

---

## Fichiers

| Fichier | Rôle |
|---------|------|
| `dashboard/modules/shared/decision-cartography-experience/decision-cartography-experience.js` | Reconception EPM |
| `dashboard/modules/shared/decision-cartography-experience/decision-cartography-experience.css` | Immersion / dock / KPI |
| `dashboard/modules/decision-experience/dxl-core.js` | Store `map.__sigBasemapManager` (UX basemap) |
| `dashboard/modules/decision-experience/spatial-impact-controller.js` | `attach()` après montage SDG (existant) |
| `tests/e2e/decision-cartography-experience.spec.js` | Sites 14/16/26/29/34 + responsive |
| `PROJECT_MANAGEMENT/ARCHITECTURE/captures/executive-presentation-mode/` | Captures |

---

## Actions réellement fonctionnelles

| Action | Statut |
|--------|--------|
| Mode Présentation | ✅ |
| Quitter / Échap | ✅ |
| Plein écran navigateur (si API) | ✅ + fallback CSS |
| Présentation guidée / libre | ✅ |
| Précédent / Suivant / Pause | ✅ |
| Réinitialiser | ✅ |
| Basemap (cycle fournisseurs) | ✅ |
| Légende / Couches / Détail | ✅ |
| Imprimer | ✅ |
| Export PNG/PDF / Partager | ❌ masqué « À venir » (Zero Decorative Actions) |

---

## Limites restantes

- Fullscreen API peut être bloquée par le navigateur (fallback viewport OK).
- Étape « Fibre » s’appuie sur le domaine télécom (pas de catégorie fibre séparée côté SDG).
- Export PNG/PDF volontairement différés (Phase 3).
- Ratio carte mesuré vs shell (~72 %+ selon chrome) — objectif 85–92 % de la surface utile sous le chrome.

## Recommandations Phase 3

1. Export PNG/PDF natifs (canvas Leaflet + branding FDSU).
2. Scénarios guidés paramétrables par programme (Sites 40 / 300 / CCN).
3. Ancrage Design System institutionnel FDSU (couleurs / logo officiels).
4. Partage de session présentation (URL deep-link étape).
5. Mode double écran (carte + notes orateur).
