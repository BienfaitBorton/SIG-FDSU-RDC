from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
)

app = FastAPI(
    title="SIG-FDSU RDC API",
    description="API FastAPI pour le référentiel administratif et les sites FDSU RDC.",
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

app.include_router(provinces.router, prefix="/provinces", tags=["Provinces"])
app.include_router(territoires.router, prefix="/territoires", tags=["Territoires"])
app.include_router(collectivites.router, prefix="/collectivites", tags=["Collectivites"])
app.include_router(groupements.router, prefix="/groupements", tags=["Groupements"])
app.include_router(villages.router, prefix="/villages", tags=["Villages"])
app.include_router(sites.router, prefix="/sites", tags=["Sites"])
app.include_router(missions.router, prefix="/missions", tags=["Missions"])
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(photos.router, prefix="/photos", tags=["Photos"])

@app.get("/", tags=["Root"])
def read_root() -> dict[str, str]:
    return {"message": "SIG-FDSU RDC API est en cours d'exécution."}
