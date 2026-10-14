"""Tests for the Kyriba-backed account-balances endpoint (mock mode)."""
from __future__ import annotations

from app.clients import KyribaError, get_kyriba_client
from app.main import app


def _seeded_entity_id(client) -> int:
    entities = client.get("/entities").json()
    return next(e["id"] for e in entities if e["code"] == "RW-CAP")


def test_balances_mock_mode(client):
    entity_id = _seeded_entity_id(client)
    resp = client.get(f"/entities/{entity_id}/balances")
    assert resp.status_code == 200, resp.text
    rows = resp.json()
    assert len(rows) == 2
    assert {r["entity_code"] for r in rows} == {"RW-CAP"}
    first = rows[0]
    assert first["bank_name"] in {"JPMorgan Chase", "Bank of America"}
    assert first["currency"] == "USD"
    # Decimal fields serialise as JSON strings to preserve precision.
    assert isinstance(first["current_balance"], str)
    assert float(first["current_balance"]) > 0
    assert float(first["available_balance"]) <= float(first["current_balance"])


def test_balances_unknown_entity_404(client):
    assert client.get("/entities/999999/balances").status_code == 404


def test_balances_kyriba_failure_returns_502(client):
    """A KyribaError from the client must surface as 502, not a 500."""

    class _FailingKyriba:
        """Stub client whose balance fetch always fails."""

        async def get_account_balances(self, _entity_code: str):
            raise KyribaError("simulated Kyriba outage")

    app.dependency_overrides[get_kyriba_client] = _FailingKyriba
    try:
        entity_id = _seeded_entity_id(client)
        resp = client.get(f"/entities/{entity_id}/balances")
        assert resp.status_code == 502
        assert "simulated Kyriba outage" in resp.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_kyriba_client, None)
