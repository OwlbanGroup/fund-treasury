"""FastAPI application entrypoint for the Fund Treasury backend."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import SessionLocal, init_db
from .routers import accounts, balances, entities, forecast, health, payments
from .seed import seed_demo_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Create tables and seed demo data on startup."""
    logger.info("Initialising database: %s", settings.DATABASE_URL)
    init_db()
    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()
    logger.info(
        "Startup complete (kyriba_mode=%s, bank_mode=%s)",
        settings.KYRIBA_MODE,
        settings.BANK_MODE,
    )
    yield


app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    lifespan=lifespan,
)

# CORS is enabled for the default Vite dev server so the bundled frontend (or a
# locally generated one) can talk to the API during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(entities.router)
app.include_router(accounts.router)
app.include_router(balances.router)
app.include_router(payments.router)
app.include_router(forecast.router)
