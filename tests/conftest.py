import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base
from api.dependencies import get_db
from api.main import app as fastapi_app

TEST_DB_NAME = os.environ.get("TEST_DB_NAME", "sig_fdsu_test")
ADMIN_DB_URL = os.environ.get("ADMIN_DATABASE_URL", "postgresql://postgres:test123@localhost:5432/postgres")
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    f"postgresql://postgres:test123@localhost:5432/{TEST_DB_NAME}",
)


@pytest.fixture(scope="session")
def engine():
    admin_engine = create_engine(ADMIN_DB_URL)
    database_name = TEST_DB_NAME

    with admin_engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        existing = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": database_name},
        ).scalar()
        if not existing:
            conn.execute(text(f'CREATE DATABASE "{database_name}"'))

    test_engine = create_engine(TEST_DATABASE_URL, future=True)
    with test_engine.connect() as conn:
        conn = conn.execution_options(isolation_level="AUTOCOMMIT")
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    with test_engine.connect() as conn:
        Base.metadata.drop_all(bind=test_engine)
        Base.metadata.create_all(bind=test_engine)

    yield test_engine

    with test_engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))


@pytest.fixture(scope="function")
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection, autoflush=False, autocommit=False, future=True)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as client:
        yield client
    fastapi_app.dependency_overrides.clear()
