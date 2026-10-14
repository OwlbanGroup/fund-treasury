"""Seed demo data so the app has something to show on first run."""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models.bank_account import BankAccount
from .models.entity import Entity


def seed_demo_data(db: Session) -> None:
    """Insert one entity with two bank accounts if the DB is empty.

    Idempotent: it only seeds when there are no entities yet.
    """
    if db.scalar(select(Entity.id).limit(1)) is not None:
        return

    entity = Entity(
        name="RiseWorth Capital Holdings", code="RW-CAP", base_currency="USD"
    )
    db.add(entity)
    db.flush()  # assign entity.id

    db.add_all(
        [
            BankAccount(
                entity_id=entity.id,
                bank_name="JPMorgan Chase",
                account_number_masked="****4291",
                account_type="Operating",
                currency="USD",
                current_balance=Decimal("1250000.00"),
                available_balance=Decimal("1200000.00"),
            ),
            BankAccount(
                entity_id=entity.id,
                bank_name="Bank of America",
                account_number_masked="****8845",
                account_type="Payroll",
                currency="USD",
                current_balance=Decimal("640000.00"),
                available_balance=Decimal("640000.00"),
            ),
        ]
    )
    db.commit()
