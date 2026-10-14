"""Kyriba Treasury Management System client.

Supports two modes controlled by ``KYRIBA_MODE``:

* ``mock`` (default) — returns deterministic synthetic data so the whole app
  runs offline with no external dependencies.
* ``real`` — performs OAuth2 client-credentials against Kyriba and calls the
  REST API with ``httpx``. Only exercised when credentials are configured.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

import httpx

from ..config import get_settings
from .bank_types import CashForecastRow

logger = logging.getLogger(__name__)


class KyribaError(RuntimeError):
    """Raised when a real Kyriba call fails."""


class KyribaClient:
    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def is_mock(self) -> bool:
        return self._settings.KYRIBA_MODE.lower() != "real"

    # --- Public API -------------------------------------------------------
    async def get_cash_forecast(
        self, entity_code: str, as_of: date | None = None
    ) -> list[CashForecastRow]:
        """Return forecast rows for an entity.

        Mock mode returns synthetic data; real mode queries Kyriba. The return
        shape is identical so callers never need to branch on the mode.
        """
        as_of = as_of or date.today()
        if self.is_mock:
            return self._mock_forecast(entity_code, as_of)
        return await self._real_forecast(entity_code, as_of)

    async def get_account_balances(self, entity_code: str) -> list[dict[str, Any]]:
        """Return current balances per bank account (mock or real)."""
        if self.is_mock:
            return self._mock_balances(entity_code)
        return await self._real_balances(entity_code)

    # --- Mock implementations --------------------------------------------
    def _mock_forecast(
        self, entity_code: str, as_of: date
    ) -> list[CashForecastRow]:
        # Deterministic pseudo-random figures keyed off the entity code so
        # repeated calls are stable. Uses a small LCG seeded by the code hash.
        seed = sum(ord(c) for c in entity_code) or 1

        def lcg(n: int) -> int:
            return (1103515245 * n + 12345) % 2147483648

        rows: list[CashForecastRow] = []
        balance = Decimal("500000.00") + Decimal(seed * 1000)
        for day in range(14):
            seed = lcg(seed)
            inflows = Decimal(seed % 400_000) / 100
            seed = lcg(seed)
            outflows = Decimal(seed % 350_000) / 100
            rows.append(
                CashForecastRow(
                    as_of_date=as_of + timedelta(days=day),
                    currency="USD",
                    opening_balance=balance.quantize(Decimal("0.01")),
                    inflows=inflows.quantize(Decimal("0.01")),
                    outflows=outflows.quantize(Decimal("0.01")),
                )
            )
            balance = balance + inflows - outflows
        return rows

    def _mock_balances(self, entity_code: str) -> list[dict[str, Any]]:
        seed = sum(ord(c) for c in entity_code) or 1
        return [
            {
                "entity_code": entity_code,
                "bank_name": "JPMorgan Chase",
                "currency": "USD",
                "current_balance": str(Decimal(1_250_000 + seed * 100).quantize(Decimal("0.01"))),
                "available_balance": str(Decimal(1_200_000 + seed * 100).quantize(Decimal("0.01"))),
            },
            {
                "entity_code": entity_code,
                "bank_name": "Bank of America",
                "currency": "USD",
                "current_balance": str(Decimal(640_000 + seed * 50).quantize(Decimal("0.01"))),
                "available_balance": str(Decimal(640_000 + seed * 50).quantize(Decimal("0.01"))),
            },
        ]

    # --- Real implementations --------------------------------------------
    async def _real_forecast(
        self, entity_code: str, as_of: date
    ) -> list[CashForecastRow]:
        try:
            async with httpx.AsyncClient(base_url=self._settings.KYRIBA_BASE_URL) as client:
                token = await self._get_token(client)
                resp = await client.get(
                    "/api/v1/cash-forecasts",
                    params={"entity": entity_code, "asOf": as_of.isoformat()},
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=30,
                )
                resp.raise_for_status()
                payload = resp.json()
        except httpx.HTTPError as exc:
            raise KyribaError(f"Forecast request failed: {exc}") from exc
        rows: list[CashForecastRow] = []
        for item in payload.get("data", []):
            rows.append(
                CashForecastRow(
                    as_of_date=date.fromisoformat(item["asOf"]),
                    currency=item.get("currency", "USD"),
                    opening_balance=Decimal(str(item["openingBalance"])),
                    inflows=Decimal(str(item["inflows"])),
                    outflows=Decimal(str(item["outflows"])),
                )
            )
        return rows

    async def _real_balances(self, entity_code: str) -> list[dict[str, Any]]:
        try:
            async with httpx.AsyncClient(base_url=self._settings.KYRIBA_BASE_URL) as client:
                token = await self._get_token(client)
                resp = await client.get(
                    "/api/v1/account-balances",
                    params={"entity": entity_code},
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=30,
                )
                resp.raise_for_status()
                return list(resp.json().get("data", []))
        except httpx.HTTPError as exc:
            raise KyribaError(f"Balance request failed: {exc}") from exc

    # --- Token handling (real mode only) ---------------------------------
    async def _get_token(self, client: httpx.AsyncClient) -> str:
        try:
            resp = await client.post(
                self._settings.KYRIBA_TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._settings.KYRIBA_CLIENT_ID,
                    "client_secret": self._settings.KYRIBA_CLIENT_SECRET,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise KyribaError(f"Token request failed: {exc}") from exc
        token = resp.json().get("access_token")
        if not token:
            raise KyribaError("Kyriba token response missing access_token")
        return token


def get_kyriba_client() -> KyribaClient:
    """FastAPI dependency factory."""
    return KyribaClient()
