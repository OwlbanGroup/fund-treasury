"""Payment request/response schemas."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreate(BaseModel):
    account_id: int
    amount: Decimal = Field(gt=0)
    counterparty: str = Field(min_length=1, max_length=200)
    reference: str = Field(min_length=1, max_length=100)
    payment_method: str = Field(default="ACH", max_length=20)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    note: str | None = None


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    currency: str
    amount: Decimal
    counterparty: str
    reference: str
    payment_method: str
    status: str
    outbox_file: str | None
    bank_reference: str | None
    note: str | None
    created_at: datetime
    sent_at: datetime | None


class PaymentSendResponse(BaseModel):
    """Result of dispatching a payment through the bank client."""

    payment: PaymentOut
    bank_reference: str
    outbox_file: str | None
