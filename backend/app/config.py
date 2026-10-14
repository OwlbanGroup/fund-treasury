"""Application configuration.

All external integrations are configurable so the system can run fully
self-contained (mock mode) or against real Kyriba / bank endpoints.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import ClassVar

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Central settings loaded from environment variables."""

    # --- Database ---------------------------------------------------------
    # Defaults to a local SQLite file so the project runs out of the box.
    # Set DATABASE_URL to a Postgres DSN to switch, e.g.:
    #   postgresql+psycopg2://postgres:postgres@localhost:5432/treasury
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "sqlite:///./treasury.db"
    )

    # --- Kyriba (Treasury Management System) ------------------------------
    KYRIBA_MODE: str = os.getenv("KYRIBA_MODE", "mock")  # "mock" | "real"
    KYRIBA_BASE_URL: str = os.getenv("KYRIBA_BASE_URL", "https://api.kyriba.com")
    KYRIBA_CLIENT_ID: str = os.getenv("KYRIBA_CLIENT_ID", "")
    KYRIBA_CLIENT_SECRET: str = os.getenv("KYRIBA_CLIENT_SECRET", "")
    KYRIBA_TOKEN_URL: str = os.getenv(
        "KYRIBA_TOKEN_URL", "https://api.kyriba.com/oauth/token"
    )

    # --- Bank connectivity -------------------------------------------------
    BANK_MODE: str = os.getenv("BANK_MODE", "mock")  # "mock" | "real"
    # Directory where generated payment files (e.g. NACHA/ISO 20022) are written.
    BANK_FILE_OUTBOX: str = os.getenv("BANK_FILE_OUTBOX", "./outbox")

    # --- App ---------------------------------------------------------------
    DEFAULT_CURRENCY: str = os.getenv("DEFAULT_CURRENCY", "USD")
    API_TITLE: str = "Fund Treasury API"
    API_VERSION: str = "1.0.0"
    CORS_ORIGINS: ClassVar[list[str]] = [
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
        if o.strip()
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
