"""Tests for the cash-forecast pull/read flow (mock Kyriba)."""
from __future__ import annotations


def _seeded_entity_id(client) -> int:
    entities = client.get("/entities").json()
    return next(e["id"] for e in entities if e["code"] == "RW-CAP")


def test_forecast_pull_and_read(client):
    entity_id = _seeded_entity_id(client)

    # Pull from (mock) Kyriba.
    pull = client.post(f"/entities/{entity_id}/forecast/pull")
    assert pull.status_code == 200, pull.text
    body = pull.json()
    assert body["entity_id"] == entity_id
    assert body["source"] == "kyriba"
    assert body["rows_imported"] == 14  # mock returns a 14-day horizon

    # Read stored forecast back; verify closing_balance math is exposed.
    # Note: Decimal fields are serialised as JSON strings by Pydantic v2 to
    # preserve precision, so parse them with float() before comparing.
    rows = client.get(f"/entities/{entity_id}/forecast").json()
    assert len(rows) == 14
    first = rows[0]
    expected_close = (
        float(first["opening_balance"])
        + float(first["inflows"])
        - float(first["outflows"])
    )
    assert abs(float(first["closing_balance"]) - expected_close) < 0.01


def test_forecast_pull_repeated_is_idempotent(client):
    entity_id = _seeded_entity_id(client)
    assert client.post(f"/entities/{entity_id}/forecast/pull").status_code == 200
    assert client.post(f"/entities/{entity_id}/forecast/pull").status_code == 200
    rows = client.get(f"/entities/{entity_id}/forecast").json()
    assert len(rows) == 14


def test_forecast_unknown_entity_404(client):
    assert client.post("/entities/999999/forecast/pull").status_code == 404
    assert client.get("/entities/999999/forecast").status_code == 404
