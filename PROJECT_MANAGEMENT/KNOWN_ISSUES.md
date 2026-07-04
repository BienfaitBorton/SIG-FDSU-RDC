# KNOWN ISSUES - SIG-FDSU RDC

## Sprint 3.1

- Le test navigateur automatique n'a pas ete execute car Node et le navigateur integre ne sont pas disponibles dans cette session.
- `fastapi.testclient` n'a pas pu etre utilise car la dependance `httpx2` est absente.
- Le serveur statique fonctionne au premier plan, mais le lancement persistant via `Start-Process` n'a pas tenu dans cette session.
- Le KMZ natif n'est pas compresse cote navigateur; le fichier exporte est un KML pret a compresser.
- La synchronisation cartographique complete des resultats de recherche reste a finaliser.
- Les profils territoriaux ne sont pas encore persistants en PostgreSQL.

