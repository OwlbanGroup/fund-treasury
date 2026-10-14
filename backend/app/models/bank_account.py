"""Bank account owned by an entity, with balances in a given currency."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .entity import Entity
    from .payment import Payment


class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_id: Mapped[int] = mapped_column(
        ForeignKey("entities.id", ondelete="CASCADE"), index=True
    )
    bank_name: Mapped[str] = mapped_column(String(200))
    # Store only a masked account number (never the full PAN) in this demo app.
    account_number_masked: Mapped[str] = mapped_column(String(20))
    account_type: Mapped[str] = mapped_column(String(40))  # e.g. Operating, Payroll
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0.00")
    )
    available_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0.00")
    )
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    entity: Mapped[Entity] = relationship(back_populates="accounts")
    payments: Mapped[list[Payment]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
