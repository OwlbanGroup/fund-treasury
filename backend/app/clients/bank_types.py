"""Shared data types used by the integration clients."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class CashForecastRow:
    """A single daily forecast line, mode-independent."""

    as_of_date: date
    currency: str
    opening_balance: Decimal
    inflows: Decimal
    outflows: Decimal


@dataclass(frozen=True)
class SendResult:
    """Outcome of dispatching a payment through the bank client."""

    status: str
    bank_reference: str
    outbox_file: str | None
