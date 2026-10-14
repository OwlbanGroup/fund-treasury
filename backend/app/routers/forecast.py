"""Cash forecast endpoints: pull from Kyriba and read stored forecasts."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..clients import KyribaClient, get_kyriba_client
from ..database import get_db
from ..models.cash_forecast import CashForecast
from ..models.entity import Entity
from ..schemas import ForecastOut, ForecastPullResponse

router = APIRouter(tags=["forecast"])


@router.post("/entities/{entity_id}/forecast/pull", response_model=ForecastPullResponse)
async def pull_forecast(
    entity_id: int,
    as_of: date | None = None,
    db: Session = Depends(get_db),
    kyriba: KyribaClient = Depends(get_kyriba_client),
) -> ForecastPullResponse:
    """Pull a fresh cash forecast from Kyriba and persist it locally."""
    entity = db.get(Entity, entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    rows = await kyriba.get_cash_forecast(entity.code, as_of)
    if not rows:
        return ForecastPullResponse(
            entity_id=entity_id,
            rows_imported=0,
            as_of_date=as_of or date.today(),
            source="kyriba",
        )

    # Replace any prior rows for the same as_of dates to keep the table tidy.
    first_day = min(r.as_of_date for r in rows)
    db.query(CashForecast).filter(
        CashForecast.entity_id == entity_id,
        CashForecast.as_of_date >= first_day,
    ).delete(synchronize_session=False)

    for r in rows:
        db.add(
            CashForecast(
                entity_id=entity_id,
                as_of_date=r.as_of_date,
                currency=r.currency,
                opening_balance=r.opening_balance,
                inflows=r.inflows,
                outflows=r.outflows,
            )
        )
    db.commit()
    return ForecastPullResponse(
        entity_id=entity_id,
        rows_imported=len(rows),
        as_of_date=first_day,
        source="kyriba",
    )


@router.get("/entities/{entity_id}/forecast", response_model=list[ForecastOut])
def list_forecast(
    entity_id: int, db: Session = Depends(get_db)
) -> list[ForecastOut]:
    if not db.get(Entity, entity_id):
        raise HTTPException(status_code=404, detail="Entity not found")
    rows = db.scalars(
        select(CashForecast)
        .where(CashForecast.entity_id == entity_id)
        .order_by(CashForecast.as_of_date)
    ).all()
    # Attach the computed closing_balance property for serialisation.
    return [
        ForecastOut(
            id=r.id,
            entity_id=r.entity_id,
            as_of_date=r.as_of_date,
            currency=r.currency,
            opening_balance=r.opening_balance,
            inflows=r.inflows,
            outflows=r.outflows,
            closing_balance=r.closing_balance,
            created_at=r.created_at,
        )
        for r in rows
    ]
