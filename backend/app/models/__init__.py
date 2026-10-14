"""ORM models package.

Importing this package registers every model on ``Base.metadata`` so that
``Base.metadata.create_all`` in :mod:`app.database` creates all tables.
"""
from __future__ import annotations

from .bank_account import BankAccount
from .cash_forecast import CashForecast
from .entity import Entity
from .payment import Payment

__all__ = ["BankAccount", "CashForecast", "Entity", "Payment"]
