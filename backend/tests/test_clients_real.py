"""Real-mode integration-client tests, run fully offline.

``httpx.MockTransport`` is injected into ``httpx.AsyncClient`` so the
``KYRIBA_MODE=real`` code paths (OAuth2 token flow, forecast parsing, balance
passthrough) and the ``BANK_MODE=real`` guard are exercised without any
network I/O. Settings are flipped on the shared cached instance and restored
by ``monkeypatch`` after each test.
"""
from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import date
from decimal import Decimal

import httpx
import pytest

from app.clients import BankClient, BankError, KyribaClient, KyribaError
from app.config import get_settings
from app.models.payment import Payment

Handler = Callable[[httpx.Request], httpx.Response]


def _patch_transport(
    monkeypatch: pytest.MonkeyPatch, handler: Handler
) -> None:
    """Route every outbound request made by KyribaClient to ``handler``."""
    transport = httpx.MockTransport(handler)
    real_async_client = httpx.AsyncClient  # captured before the patch below

    def factory(*args, **kwargs):
        kwargs["transport"] = transport
        return real_async_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", factory)


def test_real_forecast_parses_response(monkeypatch):
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/oauth/token"):
            seen.append("token")
            return httpx.Response(200, json={"access_token": "test-token"})
        seen.append("forecast")
        assert request.headers["Authorization"] == "Bearer test-token"
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "asOf": "2026-10-13",
                        "currency": "EUR",
                        "openingBalance": "1000.50",
                        "inflows": "250.00",
                        "outflows": "50.25",
                    },
                    {
                        "asOf": "2026-10-14",
                        "currency": "EUR",
                        "openingBalance": "1200.25",
                        "inflows": "0",
                        "outflows": "10.00",
                    },
                ]
            },
        )

    _patch_transport(monkeypatch, handler)
    monkeypatch.setattr(get_settings(), "KYRIBA_MODE", "real")

    rows = asyncio.run(
        KyribaClient().get_cash_forecast("RW-CAP", as_of=date(2026, 10, 13))
    )

    assert seen == ["token", "forecast"]
    assert len(rows) == 2
    assert rows[0].as_of_date == date(2026, 10, 13)
    assert rows[0].currency == "EUR"
    assert rows[0].opening_balance == Decimal("1000.50")
    assert rows[0].inflows == Decimal("250.00")
    assert rows[1].as_of_date == date(2026, 10, 14)
    assert rows[1].outflows == Decimal("10.00")


def test_real_forecast_http_error_raises_kyriba_error(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/oauth/token"):
            return httpx.Response(200, json={"access_token": "test-token"})
        return httpx.Response(500, text="upstream boom")

    _patch_transport(monkeypatch, handler)
    monkeypatch.setattr(get_settings(), "KYRIBA_MODE", "real")

    with pytest.raises(KyribaError, match="Forecast request failed"):
        asyncio.run(KyribaClient().get_cash_forecast("RW-CAP"))


def test_real_balances_passthrough(monkeypatch):
    payload = [
        {
            "entity_code": "RW-CAP",
            "bank_name": "JPMorgan Chase",
            "currency": "USD",
            "current_balance": "123.45",
            "available_balance": "100.00",
        }
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/oauth/token"):
            return httpx.Response(200, json={"access_token": "test-token"})
        assert request.url.path.endswith("/account-balances")
        return httpx.Response(200, json={"data": payload})

    _patch_transport(monkeypatch, handler)
    monkeypatch.setattr(get_settings(), "KYRIBA_MODE", "real")

    rows = asyncio.run(KyribaClient().get_account_balances("RW-CAP"))
    assert rows == payload


def test_token_missing_access_token_raises(monkeypatch):
    _patch_transport(monkeypatch, lambda request: httpx.Response(200, json={}))
    monkeypatch.setattr(get_settings(), "KYRIBA_MODE", "real")

    with pytest.raises(KyribaError, match="access_token"):
        asyncio.run(KyribaClient().get_cash_forecast("RW-CAP"))


def test_token_http_failure_raises_kyriba_error(monkeypatch):
    _patch_transport(
        monkeypatch, lambda request: httpx.Response(401, text="bad credentials")
    )
    monkeypatch.setattr(get_settings(), "KYRIBA_MODE", "real")

    with pytest.raises(KyribaError, match="Token request failed"):
        asyncio.run(KyribaClient().get_cash_forecast("RW-CAP"))


def test_bank_real_mode_refuses_to_send(monkeypatch):
    """BANK_MODE=real must fail loudly until a transport is implemented."""
    monkeypatch.setattr(get_settings(), "BANK_MODE", "real")
    with pytest.raises(BankError, match="BANK_MODE=real"):
        BankClient().send_payment(Payment())
