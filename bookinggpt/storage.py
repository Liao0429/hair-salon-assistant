# -*- coding: utf-8 -*-
"""SQLite storage for salon bookings.

Zero-config local persistence. Bookings are stored in <project>/booking.db,
so they survive even when Google Calendar is not configured.
"""
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "booking.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS bookings (
            booking_code TEXT PRIMARY KEY,
            customer_name TEXT NOT NULL,
            phone TEXT,
            service TEXT,
            event_time TEXT,
            status TEXT DEFAULT 'confirmed',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def create_booking(booking_code, customer_name, phone="", service="", event_time=""):
    """Create a new booking record. Returns None."""
    init_db()
    conn = get_connection()
    conn.execute(
        "INSERT INTO bookings (booking_code, customer_name, phone, service, event_time) "
        "VALUES (?, ?, ?, ?, ?)",
        (booking_code, customer_name, phone, service, event_time),
    )
    conn.commit()
    conn.close()


def cancel_booking(booking_code, phone=""):
    """Mark a booking as cancelled (by code and optional phone)."""
    init_db()
    conn = get_connection()
    if phone:
        conn.execute(
            "UPDATE bookings SET status='cancelled' WHERE booking_code=? AND phone=?",
            (booking_code, phone),
        )
    else:
        conn.execute(
            "UPDATE bookings SET status='cancelled' WHERE booking_code=?", (booking_code,)
        )
    conn.commit()
    conn.close()


def list_bookings(status=None):
    """Return all bookings (or only those matching status) as list of dicts."""
    init_db()
    conn = get_connection()
    if status:
        rows = conn.execute(
            "SELECT * FROM bookings WHERE status=? ORDER BY created_at DESC", (status,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM bookings ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]
