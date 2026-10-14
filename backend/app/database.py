"""Database engine, session factory and declarative base."""
from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings

_settings = get_settings()

_connect_args = {}
if _settings.DATABASE_URL.startswith("sqlite"):
    # Needed so SQLite works across FastAPI's threadpool.
    _connect_args = {"check_same_thread": False}

engine = create_engine(
    _settings.DATABASE_URL,
    connect_args=_connect_args,
    future=True,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True
)


class Base(DeclarativeBase):
    """Declarative base shared by all ORM models."""


def get_db() -> Iterator[Session]:
    """FastAPI dependency that yields a scoped database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Importing models registers them on the metadata."""
    from . import models  # noqa: F401 # pylint: disable=unused-import,import-outside-toplevel

    Base.metadata.create_all(bind=engine)
