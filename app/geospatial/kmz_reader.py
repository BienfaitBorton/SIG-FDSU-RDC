from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from zipfile import ZipFile
import xml.etree.ElementTree as ET

KML_NAMESPACE = {
    "kml": "http://www.opengis.net/kml/2.2",
    "gx": "http://www.google.com/kml/ext/2.2",
}


@dataclass(slots=True)
class KMZDocument:
    source_path: Path
    kml_text: str
    document_name: str


class KMZReader:
    """Lit un fichier KMZ sans l'extraire ni le modifier."""

    def read(self, path: str | Path) -> KMZDocument:
        kmz_path = Path(path)
        with ZipFile(kmz_path, "r") as archive:
            kml_name = self._find_kml_name(archive)
            if kml_name is None:
                raise FileNotFoundError("Aucun fichier KML n'a été trouvé dans le KMZ.")
            kml_text = archive.read(kml_name).decode("utf-8", errors="replace")
        return KMZDocument(source_path=kmz_path, kml_text=kml_text, document_name=Path(kml_name).name)

    def _find_kml_name(self, archive: ZipFile) -> Optional[str]:
        for name in archive.namelist():
            if name.lower().endswith(".kml"):
                return name
        return None
