"""Bank account request/response schemas."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class AccountCreate(BaseModel):
    entity_id: int
    bank_name: str = Field(min_length=1, max_length=200)
    account_number_masked: str = Field(min_length=1, max_length=20)
    account_type: str = Field(default="Operating", max_length=40)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    current_balance: Decimal = Field(default=Decimal("0.00"), ge=0)
    available_balance: Decimal = Field(default=Decimal("0.00"), ge=0)


class AccountUpdate(BaseModel):
    bank_name: str | None = Field(default=None, max_length=200)
    account_type: str | None = Field(default=None, max_length=40)
    current_balance: Decimal | None = Field(default=None)
    available_balance: Decimal | None = Field(default=None)
    status: str | None = Field(default=None, max_length=20)


class BalanceOut(BaseModel):
    """A balance line returned by the Kyriba client (mock or real).

    These come from the TMS, not the local database, so there is no ``id`` or
    ``created_at`` — the shape matches ``KyribaClient.get_account_balances``.
    """

    entity_code: str
    bank_name: str
    currency: str
    current_balance: Decimal
    available_balance: Decimal


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entity_id: int
    bank_name: str
    account_number_masked: str
    account_type: str
    currency: str
    current_balance: Decimal
    available_balance: Decimal
    status: str
    created_at: datetime
