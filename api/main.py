from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError

from api.middlewares.exceptions import (
    sqlalchemy_integrity_error_handler,
    value_error_handler,
)
from api.routes import (
    provinces,
    territoires,
    collectivites,
    groupements,
    villages,
    sites,
    missions,
    documents,
    photos,
    imports,
)

app = FastAPI(
    title="SIG-FDSU RDC - API SIG",
    description=(
        "API FastAPI de gestion du référentiel administratif et des sites du projet "
        "FDSU en République démocratique du Congo. Fournit des opérations CRUD "
        "pour les provinces, territoires, collectivités, groupements, villages, sites, missions, documents et photos."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(IntegrityError, sqlalchemy_integrity_error_handler)
app.add_exception_handler(ValueError, value_error_handler)

geodata_dir = Path(__file__).resolve().parent.parent / "data" / "generated"
app.mount("/geodata", StaticFiles(directory=geodata_dir), name="geodata")

app.include_router(provinces.router, prefix="/provinces", tags=["Provinces"])
app.include_router(territoires.router, prefix="/territoires", tags=["Territoires"])
app.include_router(collectivites.router, prefix="/collectivites", tags=["Collectivites"])
app.include_router(groupements.router, prefix="/groupements", tags=["Groupements"])
app.include_router(villages.router, prefix="/villages", tags=["Villages"])
app.include_router(sites.router, prefix="/sites", tags=["Sites"])
app.include_router(missions.router, prefix="/missions", tags=["Missions"])
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(photos.router, prefix="/photos", tags=["Photos"])
app.include_router(imports.router, prefix="/imports", tags=["Imports"])

@app.get("/", tags=["Root"])
def read_root() -> dict[str, str]:
    return {"message": "SIG-FDSU RDC API est en cours d'exécution."}
