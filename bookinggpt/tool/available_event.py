import datetime
import os
from zoneinfo import ZoneInfo

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from langchain.tools import BaseTool

from bookinggpt.google_auth import get_credentials


def _timezone():
    return ZoneInfo(os.getenv("SALON_TIMEZONE", "Asia/Ho_Chi_Minh"))


class AvailableSlotsTool(BaseTool):
    name = "available_slots_tool"
    description = """
    A tool for showing available slots on Google Calendar for the current week, excluding Sundays.

    Input: No input required. The tool will automatically use the current time and date.

    Output: A string listing available time slots for each day of the current week (excluding Sunday),
    starting from the current day until Saturday.

    Note: This tool checks for available slots between 9:00 AM and 6:00 PM on weekdays and Saturdays.
    """

    slot_duration: int = 60  # Set slot duration as a class attribute

    def get_busy_slots(self, service, start_time, end_time):
        try:
            events_result = service.events().list(
                calendarId='primary',
                timeMin=start_time.isoformat(),
                timeMax=end_time.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])
            busy_slots = [(datetime.datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date'))),
                           datetime.datetime.fromisoformat(event['end'].get('dateTime', event['end'].get('date'))))
                          for event in events]
            return busy_slots
        except HttpError as error:
            print(f"An error occurred while fetching events: {error}")
            return []

    def _get_demo_slots(self, current_time):
        """Return demo available slots without Google Calendar (local/demo use)."""
        available_slots = {}
        current_date = current_time.date()
        end_date = current_date + datetime.timedelta(days=(6 - current_date.weekday()))
        while current_date <= end_date:
            if current_date.weekday() != 6:  # Skip Sunday
                slots = []
                for hour in range(9, 18):
                    slot = datetime.datetime.combine(current_date, datetime.time(hour, 0)).replace(tzinfo=_timezone())
                    if current_date == current_time.date() and slot <= current_time:
                        continue
                    slots.append(slot)
                available_slots[current_date] = slots
            current_date += datetime.timedelta(days=1)
        return available_slots

    def get_available_slots(self, current_time):
        try:
            creds = get_credentials()
            if not creds:
                return self._get_demo_slots(current_time)

            service = build("calendar", "v3", credentials=creds)

            start_time = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = start_time + datetime.timedelta(days=(6 - start_time.weekday()))

            busy_slots = self.get_busy_slots(service, start_time, end_time)

            available_slots = {}
            current_date = start_time.date()
            while current_date <= end_time.date():
                if current_date.weekday() != 6:  # Skip Sunday
                    day_start = datetime.datetime.combine(current_date, datetime.time(9, 0)).replace(tzinfo=_timezone())
                    day_end = datetime.datetime.combine(current_date, datetime.time(18, 0)).replace(tzinfo=_timezone())

                    if current_date == current_time.date():
                        day_start = max(day_start, current_time)

                    available_slots[current_date] = []
                    current_slot = day_start
                    while current_slot < day_end:
                        slot_end = current_slot + datetime.timedelta(minutes=self.slot_duration)
                        if all(slot_end <= busy_start or current_slot >= busy_end for busy_start, busy_end in busy_slots):
                            available_slots[current_date].append(current_slot)
                        current_slot += datetime.timedelta(minutes=self.slot_duration)

                current_date += datetime.timedelta(days=1)

            return available_slots

        except HttpError as error:
            return f"An error occurred: {error}"

    def _run(self, *args, **kwargs) -> str:
        current_time = datetime.datetime.now(_timezone())
        available_slots = self.get_available_slots(current_time)

        if isinstance(available_slots, dict):
            result = "Available slots for the current week:\n"
            for date, slots in available_slots.items():
                result += f"\n{date.strftime('%A, %B %d')}: "
                if slots:
                    result += ", ".join([slot.strftime('%I:%M %p') for slot in slots])
                else:
                    result += "No available slots"
                result += "\n"
            return result.strip()  # Remove trailing newline
        else:
            return available_slots