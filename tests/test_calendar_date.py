# -*- coding: utf-8 -*-
"""Regression tests for appointment date/time resolution.

Covers the bug where the original code hardcoded "tomorrow" and ignored a
customer-specified date. Also covers service-duration-derived end times and the
demo (no-Google) available-slots logic.
"""
import datetime
from zoneinfo import ZoneInfo

from bookinggpt.tool.available_event import AvailableSlotsTool
from bookinggpt.tool.create_event import CalendarTool, EventInfo, _default_duration


def make_info(**overrides):
    data = {
        "event_name": "Haircut",
        "customer_name": "Alice",
        "customer_phone": "123",
        "start_time": "14:00",
        "end_time": "15:00",
        "customer_service": "Hair cut",
    }
    data.update(overrides)
    return EventInfo(**data)


def test_resolve_start_time_uses_specified_date():
    tool = CalendarTool()
    current = datetime.datetime(2026, 10, 21, 10, 0, tzinfo=ZoneInfo("UTC"))
    info = make_info(date="2026-11-05")
    start = tool._resolve_start_time(info, current)
    assert start.date().isoformat() == "2026-11-05"
    assert (start.hour, start.minute) == (14, 0)


def test_resolve_start_time_falls_back_to_tomorrow_when_no_date():
    tool = CalendarTool()
    current = datetime.datetime(2026, 10, 21, 10, 0, tzinfo=ZoneInfo("UTC"))
    info = make_info(date=None)
    start = tool._resolve_start_time(info, current)
    assert start.date().isoformat() == "2026-10-22"


def test_resolve_end_time_uses_explicit_value():
    tool = CalendarTool()
    start = datetime.datetime(2026, 11, 5, 14, 0, tzinfo=ZoneInfo("UTC"))
    info = make_info(end_time="15:30")
    end = tool._resolve_end_time(info, start)
    assert (end.hour, end.minute) == (15, 30)


def test_resolve_end_time_uses_service_duration():
    tool = CalendarTool()
    start = datetime.datetime(2026, 11, 5, 14, 0, tzinfo=ZoneInfo("UTC"))
    info = make_info(end_time="")  # no explicit end -> hair cut = 30 min
    end = tool._resolve_end_time(info, start)
    assert end == start + datetime.timedelta(minutes=30)


def test_default_duration_mapping():
    assert _default_duration("Hair cut") == 30
    assert _default_duration("hair coloring") == 60
    assert _default_duration("unknown service") == 30


def test_demo_slots_skips_sundays_and_respects_hours():
    tool = AvailableSlotsTool()
    current = datetime.datetime(2026, 10, 21, 10, 0, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
    slots = tool._get_demo_slots(current)
    assert isinstance(slots, dict)
    assert slots  # non-empty
    for day, day_slots in slots.items():
        assert day.weekday() != 6  # Sunday is excluded
        for slot in day_slots:
            assert 9 <= slot.hour < 18
    # On the current day, slots at/before the current time are excluded.
    today_hours = {s.hour for s in slots[current.date()]}
    assert 9 not in today_hours
    assert 10 not in today_hours