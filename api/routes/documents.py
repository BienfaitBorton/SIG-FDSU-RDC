from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas.base import DocumentCreate, DocumentRead
from api.services.document_service import (
    create_document,
    delete_document,
    get_document,
    list_documents,
    update_document,
)

router = APIRouter()


@router.post(
    "/",
    response_model=DocumentRead,
    summary="Créer un document",
)
def create(payload: DocumentCreate, db: Session = Depends(get_db)) -> DocumentRead:
    """Crée un document associé à une mission FDSU."""
    return create_document(db, payload)


@router.get(
    "/",
    response_model=list[DocumentRead],
    summary="Lister les documents",
)
def read_all(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer pour la pagination"),
    limit: int = Query(100, gt=0, description="Nombre maximal d'éléments renvoyés"),
    db: Session = Depends(get_db),
) -> list[DocumentRead]:
    """Retourne la liste des documents avec pagination."""
    return list_documents(db, skip=skip, limit=limit)


@router.get(
    "/{document_id}",
    response_model=DocumentRead,
    summary="Obtenir un document",
)
def read_one(document_id: int, db: Session = Depends(get_db)) -> DocumentRead:
    """Récupère un document par son identifiant."""
    document = get_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    return document


@router.put(
    "/{document_id}",
    response_model=DocumentRead,
    summary="Mettre à jour un document",
)
def update(document_id: int, payload: DocumentCreate, db: Session = Depends(get_db)) -> DocumentRead:
    """Met à jour les informations d'un document existant."""
    document = update_document(db, document_id, payload)
    if document is None:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    return document


@router.delete(
    "/{document_id}",
    summary="Supprimer un document",
)
def delete(document_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    """Supprime un document du référentiel FDSU."""
    success = delete_document(db, document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    return {"deleted": True}
