# DECISIONS - SIG-FDSU RDC

## 2026-07-04 - Sprint 3.1

- Le dashboard doit suivre strictement le principe `Liste > Selection > Fiche`.
- Aucun compteur ne doit ouvrir directement une fiche.
- Les composants existants du Dashboard doivent etre reutilises avant toute creation de nouveau module.
- Aucune migration PostgreSQL n'est creee dans Sprint 3.1, car le socle de connaissance territoriale est prepare cote UI/API.
- Les donnees absentes doivent etre affichees explicitement comme `Donnée non encore renseignée`.
- Les couleurs Zones FDSU Sprint 3.1 sont: OT jaune, CE rose, SD vert sombre, ND gris olive, ET bleu.
- Le format KMZ est reporte en natif serveur; le navigateur exporte un KML pret a compresser.

