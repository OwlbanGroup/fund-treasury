"""End-to-end payment tests: create a pending payment, then send it."""
from __future__ import annotations

from pathlib import Path


def _first_account_id(client) -> int:
    accounts = client.get("/accounts").json()
    assert accounts, "expected seeded accounts"
    return accounts[0]["id"]


def test_payment_lifecycle(client):
    account_id = _first_account_id(client)

    # Create a pending payment.
    create = client.post(
        "/payments",
        json={
            "account_id": account_id,
            "amount": "1500.00",
            "counterparty": "Acme Supplies",
            "reference": "INV-2026-0001",
            "payment_method": "ACH",
        },
    )
    assert create.status_code == 201, create.text
    payment = create.json()
    pid = payment["id"]
    assert payment["status"] == "pending"
    assert payment["bank_reference"] is None

    # Send it -> becomes 'sent' with a bank reference + outbox file.
    send = client.post(f"/payments/{pid}/send")
    assert send.status_code == 200, send.text
    body = send.json()
    assert body["payment"]["status"] == "sent"
    assert body["payment"]["sent_at"] is not None
    assert body["bank_reference"].startswith("MOCK-")

    # The mock bank must have written a file that exists on disk.
    outbox_file = body["outbox_file"]
    assert outbox_file and Path(outbox_file).exists()
    assert "PAYMENT|INV-2026-0001|" in Path(outbox_file).read_text(encoding="utf-8")

    # Sending twice is rejected.
    again = client.post(f"/payments/{pid}/send")
    assert again.status_code == 409


def test_duplicate_reference_rejected(client):
    account_id = _first_account_id(client)
    payload = {
        "account_id": account_id,
        "amount": "10.00",
        "counterparty": "Dup Payee",
        "reference": "DUP-REF-1",
    }
    assert client.post("/payments", json=payload).status_code == 201
    assert client.post("/payments", json=payload).status_code == 409


def test_payment_requires_valid_account(client):
    resp = client.post(
        "/payments",
        json={
            "account_id": 999999,
            "amount": "5.00",
            "counterparty": "Ghost",
            "reference": "GHOST-1",
        },
    )
    assert resp.status_code == 404


def test_amount_must_be_positive(client):
    account_id = _first_account_id(client)
    resp = client.post(
        "/payments",
        json={
            "account_id": account_id,
            "amount": "0",
            "counterparty": "Zero",
            "reference": "ZERO-1",
        },
    )
    assert resp.status_code == 422
