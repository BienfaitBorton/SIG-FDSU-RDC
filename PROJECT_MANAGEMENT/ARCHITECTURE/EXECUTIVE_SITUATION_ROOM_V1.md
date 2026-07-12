# Executive Situation Room (ESR) v1.0

## Vision

Transformer la **Salle de Pilotage DG** en véritable **salle de commandement** :

> En moins de cinq minutes, un Directeur Général comprend la situation nationale, identifie les priorités, explore les territoires, comprend les raisons, lance des simulations et prépare les décisions — sans quitter la salle.

Ce n’est plus un tableau de bord : c’est un **parcours décisionnel narratif**.

## Parcours DG

```
Situation nationale
        ↓
    Pourquoi ?
        ↓
      Où ?
        ↓
 Que faut-il faire ?
        ↓
   Quel impact ?
        ↓
     Décider
```

Chaque information est **explicable** (bouton « Pourquoi ? »).

## Architecture

```
Moteurs existants
  EDVS cockpit · NCI · NSME · Decision Scenarios
  Decision Intents · Transport · NDF · TST · TDT · SDG
                    │
                    ▼
     executive_situation_room_service (composition)
                    │
                    ▼
     GET /api/executive/situation-room/*
                    │
                    ▼
     ExecutiveSituationRoom (UI) + Edvs* widgets
                    │
                    ▼
     #salle-pilotage / #edvs-cockpit-root
```

**Aucune duplication métier** — lecture seule, agrégation, navigation.

## Composants

| Bloc | Rôle |
|---|---|
| Executive Briefing | Résumé généré dynamiquement (données sourcées uniquement) |
| Situation nationale | KPI cliquables → Workspace / analyses |
| Carte nationale (TST) | Province → … → Site, contexte partagé |
| Alertes nationales | Critique / Attention / Information |
| Posez votre question | Questions prédéfinies (prêt conversationnel) |
| Simulations stratégiques | Decision Scenarios branchés |
| Actions exécutives | Réelles + Capability Registry |
| Présenter au DG | Déroulé guidé des sections |

## API

| Route | Description |
|---|---|
| `GET /api/executive/situation-room` | Payload agrégé |
| `GET /api/executive/situation-room/briefing` | Briefing seul |
| `GET /api/executive/situation-room/national` | KPI nationaux |
| `GET /api/executive/situation-room/alerts` | Alertes |
| `GET /api/executive/situation-room/questions` | Questions |
| `GET /api/executive/situation-room/scenarios` | Scénarios (catalogue rapide) |
| `GET /api/executive/situation-room/actions` | Actions |

Les routes EDVS historiques (`/cockpit`, `/chart-catalog`) restent disponibles.

## Explicabilité

- Chaque KPI / alerte / recommandation / scénario / carte propose **Pourquoi ?**
- Tiroir latéral `#esr-explain-drawer` (titre, justification, source)
- Aucune donnée inventée ; si non chiffré → libellé honnête

## Présentation DG

Ordre :

1. Executive Briefing  
2. Situation nationale  
3. Carte  
4. Alertes  
5. Priorités  
6. Décisions proposées  

- Transitions fluides, `prefers-reduced-motion` respecté  
- Interruption possible  
- Mode Présentation EDVS (chrome masqué) combinable  

## Performances

- Chargement **progressif** des panneaux  
- `Promise` parallèles + timeouts  
- Résultats **partiels** (panneau en erreur ≠ salle bloquée)  
- Scénarios : catalogue immédiat (`run_limit=0`) pour éviter les timeouts  
- **Une** carte Leaflet (TST) — pas de `#edvs-cockpit-map`  

## Zero Decorative Actions

| Action | Comportement |
|---|---|
| Préparer un dossier DG | → `decision-scenario/dg_dossier` |
| Préparer une mission | masquée (`mission_planning`) |
| Exporter les analyses | → Workspace (Excel réel) |
| Decision Workspace | réel |
| Territorial Digital Twin | réel (contexte TST privilégié) |
| Analyse d’Impact Territorial | réel (SDG) |
| Présenter au DG | réel |

## Fichiers

| Couche | Chemin |
|---|---|
| Service | `api/services/executive_situation_room_service.py` |
| Routes | `api/routes/executive.py` |
| UI | `dashboard/modules/shared/executive-situation-room/` |
| Orchestration | `dashboard/modules/shared/executive-dashboard/executive-dashboard.js` |
| E2E | `tests/e2e/executive-situation-room.spec.js` |

## Feuille de route

| Version | Contenu |
|---|---|
| **v1.0** | Briefing, situation, alertes, questions, scénarios, présentation, actions |
| v1.1 | Moteur conversationnel branché sur le même contrat `questions` |
| v1.2 | Alertes temps réel / acquittement |
| v1.3 | Export briefing PDF quand capacité réelle |
| v1.4 | Twin inline (sans quitter la salle) |
