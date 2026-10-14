"""Account-balances endpoint backed by the Kyriba client (mock or real)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..clients import KyribaClient, KyribaError, get_kyriba_client
from ..database import get_db
from ..models.entity import Entity
from ..schemas import BalanceOut

router = APIRouter(tags=["balances"])


@router.get("/entities/{entity_id}/balances", response_model=list[BalanceOut])
async def get_entity_balances(
    entity_id: int,
    db: Session = Depends(get_db),
    kyriba: KyribaClient = Depends(get_kyriba_client),
) -> list[BalanceOut]:
    """Fetch live account balances for an entity from Kyriba (mock or real)."""
    entity = db.get(Entity, entity_id)
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity {entity_id} not found",
        )
    try:
        rows = await kyriba.get_account_balances(entity.code)
    except KyribaError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Kyriba balance fetch failed: {exc}",
        ) from exc
    return [BalanceOut.model_validate(row) for row in rows]
