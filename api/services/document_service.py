from sqlalchemy.orm import Session

from app.models import Document
from api.schemas.base import DocumentCreate


def create_document(session: Session, payload: DocumentCreate) -> Document:
    document = Document(**payload.model_dump())
    session.add(document)
    session.commit()
    session.refresh(document)
    return document


def get_document(session: Session, document_id: int) -> Document | None:
    return session.get(Document, document_id)


def list_documents(session: Session, skip: int = 0, limit: int = 100) -> list[Document]:
    return session.query(Document).offset(skip).limit(limit).all()


def update_document(session: Session, document_id: int, payload: DocumentCreate) -> Document | None:
    document = session.get(Document, document_id)
    if document is None:
        return None
    for key, value in payload.model_dump().items():
        setattr(document, key, value)
    session.commit()
    session.refresh(document)
    return document


def delete_document(session: Session, document_id: int) -> bool:
    document = session.get(Document, document_id)
    if document is None:
        return False
    session.delete(document)
    session.commit()
    return True
