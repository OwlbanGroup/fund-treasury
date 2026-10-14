"""Health and service-info endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from ..config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness probe plus current integration modes."""
    s = get_settings()
    return {
        "status": "ok",
        "kyriba_mode": s.KYRIBA_MODE,
        "bank_mode": s.BANK_MODE,
        "database": s.DATABASE_URL.split("///")[0],
    }


@router.get("/")
def root() -> dict[str, str]:
    s = get_settings()
    return {
        "service": s.API_TITLE,
        "version": s.API_VERSION,
        "docs": "/docs",
    }
