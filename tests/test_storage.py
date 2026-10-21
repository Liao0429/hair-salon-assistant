# -*- coding: utf-8 -*-
"""Tests for the SQLite storage layer, isolated to a temporary database.

The production `bookinggpt.storage` module reads `DB_PATH` from its module
globals at call time, so we monkeypatch it to a temp file to keep the real
`booking.db` untouched.
"""
import sqlite3

import pytest

from bookinggpt import storage


@pytest.fixture()
def db(tmp_path, monkeypatch):
    """Point storage at a temporary database and ensure the schema exists."""
    db_path = tmp_path / "bookings.db"
    monkeypatch.setattr(storage, "DB_PATH", str(db_path))
    storage.init_db()
    return storage


def test_create_and_list_booking(db):
    db.create_booking("CODE0001", "Alice", "123", "Hair cut", "2026-11-01 14:00")
    bookings = db.list_bookings()
    assert len(bookings) == 1
    b = bookings[0]
    assert b["booking_code"] == "CODE0001"
    assert b["customer_name"] == "Alice"
    assert b["phone"] == "123"
    assert b["service"] == "Hair cut"
    assert b["event_time"] == "2026-11-01 14:00"
    assert b["status"] == "confirmed"
    assert "created_at" in b


def test_list_bookings_empty(db):
    assert db.list_bookings() == []


def test_list_bookings_filter_by_status(db):
    db.create_booking("CODE0001", "Alice")
    db.cancel_booking("CODE0001")
    assert db.list_bookings("confirmed") == []
    cancelled = db.list_bookings("cancelled")
    assert len(cancelled) == 1
    assert cancelled[0]["status"] == "cancelled"


def test_cancel_booking_returns_rowcount(db):
    db.create_booking("CODE0001", "Alice", "123", "Hair cut", "2026-11-01 14:00")
    affected = db.cancel_booking("CODE0001")
    assert affected == 1
    assert db.list_bookings()[0]["status"] == "cancelled"


def test_cancel_booking_no_match_returns_zero(db):
    assert db.cancel_booking("NOPE") == 0


def test_cancel_booking_requires_phone_match(db):
    db.create_booking("CODE0001", "Alice", "123", "Hair cut", "2026-11-01 14:00")
    # Wrong phone -> no row updated, no false success.
    assert db.cancel_booking("CODE0001", "999") == 0
    assert db.list_bookings()[0]["status"] == "confirmed"
    # Correct phone -> cancelled.
    assert db.cancel_booking("CODE0001", "123") == 1
    assert db.list_bookings()[0]["status"] == "cancelled"


def test_bookings_persist_to_disk(db, tmp_path):
    db.create_booking("CODE0001", "Alice", "123", "Hair cut", "2026-11-01 14:00")
    # Open the same file directly to confirm rows are actually persisted.
    conn = sqlite3.connect(str(tmp_path / "bookings.db"))
    rows = conn.execute("SELECT customer_name, status FROM bookings").fetchall()
    conn.close()
    assert rows == [("Alice", "confirmed")]