"""A payment instruction routed to a bank (mock writes a file to the outbox)."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .bank_account import BankAccount

# Payment lifecycle states.
PENDING = "pending"
SENT = "sent"
SETTLED = "settled"
FAILED = "failed"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("bank_accounts.id", ondelete="CASCADE"), index=True
    )
    # Denormalised currency for reporting; defaults to the account currency.
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    counterparty: Mapped[str] = mapped_column(String(200))
    reference: Mapped[str] = mapped_column(String(100), index=True)
    payment_method: Mapped[str] = mapped_column(String(20), default="ACH")
    status: Mapped[str] = mapped_column(String(20), default=PENDING, index=True)
    # Relative path to the generated payment file inside BANK_FILE_OUTBOX.
    outbox_file: Mapped[str | None] = mapped_column(String(400), nullable=True)
    # Bank-assigned id once acknowledged (real mode). Null in mock mode.
    bank_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    account: Mapped[BankAccount] = relationship(back_populates="payments")
