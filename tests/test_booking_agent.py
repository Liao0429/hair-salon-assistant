# -*- coding: utf-8 -*-
"""Unit tests for pure logic in the production booking package.

These tests do NOT call a live LLM or Google Calendar API.
The model layer remains OpenAI-compatible (ChatOpenAI is used in production;
here we only exercise importable helpers and Pydantic models).
"""
import pytest
from pydantic import ValidationError

from bookinggpt.tool.create_event import EventInfo, generate_booking_code


def test_generate_booking_code_length():
    code = generate_booking_code()
    assert isinstance(code, str)
    assert len(code) == 8


def test_generate_booking_code_is_hex():
    code = generate_booking_code()
    int(code, 16)  # raises ValueError if not hexadecimal


def test_generate_booking_code_unique():
    codes = {generate_booking_code() for _ in range(100)}
    assert len(codes) == 100


def test_event_info_required_fields():
    info = EventInfo(
        event_name="Haircut",
        customer_name="Alex",
        customer_phone="555-9876",
        start_time="14:00",
        end_time="15:00",
        customer_service="Hair cut",
        booking_code=None,
    )
    assert info.event_name == "Haircut"
    assert info.start_time == "14:00"
    assert info.booking_code is None


def test_event_info_invalid_time_missing():
    with pytest.raises(ValidationError):
        EventInfo(
            event_name="Haircut",
            customer_name="Alex",
            customer_phone="555-9876",
            start_time="14:00",
            customer_service="Hair cut",
        )
