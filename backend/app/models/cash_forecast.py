"""Cash forecast lines pulled from Kyriba and stored locally for reporting."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class CashForecast(Base):
    __tablename__ = "cash_forecasts"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_id: Mapped[int] = mapped_column(
        ForeignKey("entities.id", ondelete="CASCADE"), index=True
    )
    as_of_date: Mapped[date] = mapped_column(Date, index=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    opening_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0.00")
    )
    inflows: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"))
    outflows: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"))
    # Net closing balance = opening + inflows - outflows (computed on read).
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    @property
    def closing_balance(self) -> Decimal:
        return self.opening_balance + self.inflows - self.outflows
