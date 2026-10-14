"""Tests for the health/info endpoints."""
from __future__ import annotations


def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["service"] == "Fund Treasury API"
    assert body["docs"] == "/docs"


def test_health_reports_modes(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["kyriba_mode"] == "mock"
    assert body["bank_mode"] == "mock"
