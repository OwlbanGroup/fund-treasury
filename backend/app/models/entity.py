"""Legal / organizational entity that owns bank accounts and cash positions."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .bank_account import BankAccount


class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    base_currency: Mapped[str] = mapped_column(String(3), default="USD")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships are referenced by class name; SQLAlchemy resolves them from
    # the declarative registry once every model module has been imported.
    accounts: Mapped[list[BankAccount]] = relationship(
        back_populates="entity", cascade="all, delete-orphan"
    )
