SIG-FDSU-RDC - Module Import/Export (app/io)

But: architecture modulaire pour importer/exporter des formats :
- Excel (.xlsx)
- CSV
- GeoJSON
- KML / KMZ (optionnel, dépendances : fastkml, shapely)
- Shapefile (.shp) (optionnel, dépendances : fiona, shapely)

Principes :
- `IOHandler` abstrait uniformise `import_data`, `export_data`, `validate`.
- Chaque format a son handler réutilisable (ExcelHandler, CSVHandler, ...).
- Utilise `tqdm` pour barre de progression, `logging` pour journalisation.
- Validation et levée d'erreurs via `exceptions.py`.

Intégration :
- Ces handlers sont pensés pour être utilisés depuis `app/referentiel_administratif.py`, `app/importer.py` ou les services de `Sites`/`Missions`.
- Les handlers pour KML et Shapefile nécessitent des dépendances optionnelles ; ils lèvent `DependencyMissing` si absentes.

Exemple rapide :

```python
from app.io.factory import get_handler
from pathlib import Path

handler = get_handler("xlsx")
for row in handler.import_data(Path("/tmp/provinces.xlsx")):
    # traiter row (dict)
    pass

# exporter
records = [{"code": "11", "nom": "Kinshasa"}]
handler.export_data(Path("/tmp/out.xlsx"), records)
```

Prochaine étape : exposer des endpoints FastAPI pour importer via HTTP et ajouter tests d'intégration.
