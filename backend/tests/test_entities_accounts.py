"""Tests for entity and account CRUD, plus seeded demo data."""
from __future__ import annotations


def test_seed_created_entity_and_accounts(client):
    entities = client.get("/entities").json()
    assert any(e["code"] == "RW-CAP" for e in entities)

    entity_id = next(e["id"] for e in entities if e["code"] == "RW-CAP")
    accounts = client.get("/accounts", params={"entity_id": entity_id}).json()
    assert len(accounts) == 2
    assert {a["bank_name"] for a in accounts} == {
        "JPMorgan Chase",
        "Bank of America",
    }


def test_entity_crud(client):
    # Create
    resp = client.post(
        "/entities",
        json={"name": "Test Co", "code": "TEST-CO", "base_currency": "EUR"},
    )
    assert resp.status_code == 201, resp.text
    entity = resp.json()
    eid = entity["id"]
    assert entity["base_currency"] == "EUR"

    # Duplicate code -> 409
    dup = client.post("/entities", json={"name": "Dup", "code": "TEST-CO"})
    assert dup.status_code == 409

    # Read one
    got = client.get(f"/entities/{eid}")
    assert got.status_code == 200
    assert got.json()["code"] == "TEST-CO"

    # Update
    upd = client.patch(f"/entities/{eid}", json={"base_currency": "GBP"})
    assert upd.status_code == 200
    assert upd.json()["base_currency"] == "GBP"

    # Delete
    dele = client.delete(f"/entities/{eid}")
    assert dele.status_code == 204
    assert client.get(f"/entities/{eid}").status_code == 404


def test_account_create_requires_existing_entity(client):
    resp = client.post(
        "/accounts",
        json={
            "entity_id": 999999,
            "bank_name": "Nowhere Bank",
            "account_number_masked": "****0000",
        },
    )
    assert resp.status_code == 404


def test_get_missing_entity_404(client):
    assert client.get("/entities/999999").status_code == 404
