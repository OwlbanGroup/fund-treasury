"""Cash forecast schemas."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ForecastOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entity_id: int
    as_of_date: date
    currency: str
    opening_balance: Decimal
    inflows: Decimal
    outflows: Decimal
    closing_balance: Decimal
    created_at: datetime


class ForecastPullResponse(BaseModel):
    """Result of a forecast pull from Kyriba."""

    entity_id: int
    rows_imported: int
    as_of_date: date
    source: str
