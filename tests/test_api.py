# -*- coding: utf-8 -*-
"""End-to-end API tests using FastAPI TestClient.

These exercise the HTTP layer without a live LLM or Google Calendar:
- quick booking fallback (POST /api/booking)
- chat guard rails (rate limit 429, message length 400)
- admin dashboard auth (/bookings)
- health check + index page

The rate limiter is in-memory and keyed by session, so each test uses a unique
session id to avoid cross-test interference.
"""
import pytest
from fastapi.testclient import TestClient

import app as app_module
from bookinggpt import storage


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Isolate the database and set a known ADMIN_TOKEN for the app."""
    db_path = tmp_path / "test_booking.db"
    monkeypatch.setattr(storage, "DB_PATH", str(db_path))
    storage.init_db()
    monkeypatch.setattr(app_module, "ADMIN_TOKEN", "test-admin-token")
    with TestClient(app_module.app) as c:
        yield c


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_index_serves_chat_ui(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Daisy Salon" in r.text


def test_quick_booking_success(client):
    r = client.post(
        "/api/booking",
        json={
            "customer_name": "Alice",
            "phone": "123456",
            "service": "Hair cut",
            "date": "2026-11-01",
            "time": "14:30",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "confirmed"
    assert len(data["booking_code"]) == 8


def test_quick_booking_requires_name_and_date(client):
    r = client.post("/api/booking", json={})
    assert r.status_code == 400


def test_quick_booking_requires_date(client):
    r = client.post("/api/booking", json={"customer_name": "Bob"})
    assert r.status_code == 400


def test_quick_booking_invalid_time_format(client):
    r = client.post(
        "/api/booking",
        json={"customer_name": "Carol", "date": "2026-11-01", "time": "2pm"},
    )
    assert r.status_code == 400


def test_chat_message_too_long_returns_400(client):
    r = client.post(
        "/api/chat",
        json={
            "message": "x" * (app_module.MAX_MESSAGE_LENGTH + 1),
            "session_id": "len-test",
        },
    )
    assert r.status_code == 400


def test_chat_rate_limit_returns_429(client):
    sid = "ratelimit-test"
    # Fire CHAT_RATE_LIMIT over-long messages. Each passes validation, increments
    # the limiter, then short-circuits on the length check (no LLM call).
    for _ in range(app_module.CHAT_RATE_LIMIT):
        r = client.post(
            "/api/chat",
            json={"message": "x" * (app_module.MAX_MESSAGE_LENGTH + 1), "session_id": sid},
        )
        assert r.status_code == 400
    # The next request within the same window is rate limited.
    r = client.post(
        "/api/chat",
        json={"message": "x" * (app_module.MAX_MESSAGE_LENGTH + 1), "session_id": sid},
    )
    assert r.status_code == 429


def test_bookings_disabled_without_admin_token(client, monkeypatch):
    monkeypatch.setattr(app_module, "ADMIN_TOKEN", "")
    r = client.get("/bookings")
    assert r.status_code == 503


def test_bookings_requires_token(client):
    r = client.get("/bookings")
    assert r.status_code == 401


def test_bookings_wrong_token_unauthorized(client):
    r = client.get("/bookings", params={"token": "wrong"})
    assert r.status_code == 401


def test_bookings_with_token_serves_admin(client):
    r = client.get("/bookings", params={"token": "test-admin-token"})
    assert r.status_code == 200
    assert "admin" in r.text.lower()