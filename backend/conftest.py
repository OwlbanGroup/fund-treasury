"""Pytest configuration and shared fixtures for the backend test-suite.

Environment variables must be set **before** any ``app`` module is imported,
because ``app.config.Settings`` reads them at class-definition time.
"""
from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

# Isolated, throwaway database + outbox for the whole test session.
_TMP = Path(tempfile.mkdtemp(prefix="fund-treasury-test-"))
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP / 'test.db'}"
os.environ["BANK_FILE_OUTBOX"] = str(_TMP / "outbox")
os.environ["KYRIBA_MODE"] = "mock"
os.environ["BANK_MODE"] = "mock"

# The imports below must run after the environment setup above; the Pylint
# directive applies from this point to the end of the module.
# pylint: disable=wrong-import-position
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import SessionLocal, init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import seed_demo_data  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _prepare_db():
    """Create tables and seed once for the session."""
    init_db()
    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()
    yield


@pytest.fixture()
def client() -> Iterator[TestClient]:
    """A TestClient whose lifespan runs init + seed against the temp DB."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
