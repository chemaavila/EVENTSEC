from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app import database, models


@pytest.fixture(autouse=True)
def setup_database(monkeypatch):
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )
    models.Base.metadata.create_all(engine)
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(database, "SessionLocal", TestingSessionLocal)
    import backend.app.main as main_mod

    monkeypatch.setattr(main_mod, "SessionLocal", TestingSessionLocal, raising=False)
    yield
    models.Base.metadata.drop_all(engine)


@pytest.fixture()
def db_session():
    session = database.SessionLocal()
    try:
        yield session
    finally:
        session.close()
