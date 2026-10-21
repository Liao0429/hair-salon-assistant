import datetime
import os
from typing import Optional
from zoneinfo import ZoneInfo

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from langchain.tools import BaseTool
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from bookinggpt.google_auth import get_credentials
from bookinggpt.llm import create_llm
from bookinggpt.storage import create_booking
from bookinggpt.utils import generate_booking_code

# Service name (lowercased) -> default duration in minutes, used when the LLM
# does not provide an explicit end time.
SERVICE_DURATIONS = {
    "hair wash": 20,
    "hair cut": 30,
    "hair styling": 30,
    "beard trim": 15,
    "hair coloring": 60,
    "hair treatment": 45,
    "scalp massage": 15,
    "eyebrow shaping": 10,
    "facial": 45,
    "manicure": 30,
}


def _default_duration(service: str) -> int:
    """Return the default appointment duration for a service (minutes)."""
    key = (service or "").strip().lower()
    return SERVICE_DURATIONS.get(key, 30)


class EventInfo(BaseModel):
    event_name: str = Field(description="Name of the event or service")
    customer_name: str = Field(description="Customer's name")
    customer_phone: str = Field(description="Customer's phone number")
    start_time: str = Field(description="Start time of the event in 24-hour format (HH:MM)")
    end_time: str = Field(description="End time of the event in 24-hour format (HH:MM)")
    booking_code: Optional[str] = Field(default=None, description="Unique booking code")
    customer_service: str = Field(description="Service requested by the customer")
    date: Optional[str] = Field(
        default=None,
        description="Appointment date in YYYY-MM-DD format. Use null if the customer did not specify a date.",
    )


class CalendarTool(BaseTool):
    name = "calendar_tool"
    description = """
    A Google Calendar scheduling tool for creating new events, including hair salon appointments.

    Input: JSON object containing customer information and preferred appointment time.
    Example input: {
        "customer_name": "John Doe",
        "phone": "1234567890",
        "service": "Hair wash",
        "start_time": "14:00",
        "end_time": "15:00",
        "date": "2026-10-25"
    }

    Output: JSON object with booking details.
    Example output: {
        "status": "success",
        "booking_code": "ABC123",
        "event_id": "event123456"
    }
    """

    @staticmethod
    def _resolve_start_time(event_info: EventInfo, current_time: datetime.datetime) -> datetime.datetime:
        """Resolve the appointment start time from the requested date/time.

        Uses `event_info.date` (YYYY-MM-DD) when the customer provided one;
        otherwise falls back to "tomorrow" for backward compatibility.
        """
        hour, minute = (int(x) for x in event_info.start_time.split(":")[:2])
        tz = current_time.tzinfo or ZoneInfo(os.getenv("SALON_TIMEZONE", "Asia/Ho_Chi_Minh"))

        if event_info.date:
            try:
                d = datetime.date.fromisoformat(event_info.date.strip())
                return datetime.datetime(d.year, d.month, d.day, hour, minute, tzinfo=tz)
            except ValueError:
                print(f"Invalid date '{event_info.date}', falling back to tomorrow.")

        day = (current_time + datetime.timedelta(days=1)).date()
        return datetime.datetime(day.year, day.month, day.day, hour, minute, tzinfo=tz)

    @staticmethod
    def _resolve_end_time(event_info: EventInfo, start_time: datetime.datetime) -> datetime.datetime:
        """Resolve the end time from explicit input, or from the service duration."""
        if event_info.end_time and ":" in event_info.end_time:
            hour, minute = (int(x) for x in event_info.end_time.split(":")[:2])
            return start_time.replace(hour=hour, minute=minute)
        return start_time + datetime.timedelta(minutes=_default_duration(event_info.customer_service))

    def create_event(self, event_info: EventInfo, current_time: datetime.datetime):
        # 1) Persist to local SQLite first (zero-config, works without Google credentials)
        try:
            start_time = self._resolve_start_time(event_info, current_time)
            end_time = self._resolve_end_time(event_info, start_time)
            event_time_str = start_time.strftime("%Y-%m-%d %H:%M")
            create_booking(
                booking_code=event_info.booking_code,
                customer_name=event_info.customer_name,
                phone=event_info.customer_phone,
                service=event_info.customer_service,
                event_time=event_time_str,
            )
        except Exception as e:
            return f"Failed to save booking locally: {e}"

        # 2) Try Google Calendar sync (optional; does not block local persistence)
        try:
            creds = get_credentials()
            if not creds:
                return (f"Booking {event_info.booking_code} saved locally. "
                        "Google Calendar sync unavailable (no credentials).")

            service = build("calendar", "v3", credentials=creds)

            timezone = os.getenv("SALON_TIMEZONE", "Asia/Ho_Chi_Minh")
            event = {
                'summary': f"{event_info.customer_name} - {event_info.customer_service}",
                'description': f"Service: {event_info.customer_service}\n"
                               f"Phone: {event_info.customer_phone}\n"
                               f"Booking Code: {event_info.booking_code}",
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': timezone,
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': timezone,
                },
            }

            event = service.events().insert(calendarId='primary', body=event).execute()
            return (f"Booking confirmed. "
                    f"Booking code: {event_info.booking_code}, "
                    f"Event ID: {event.get('id')}")

        except HttpError as error:
            return (f"Booking {event_info.booking_code} saved locally. "
                    f"Google Calendar sync skipped: {error}")

    def _run(self, query: str) -> str:
        parser = PydanticOutputParser(pydantic_object=EventInfo)
        prompt = PromptTemplate(
            template="Extract the following information from the user query. "
                    "If the customer provides a specific date (e.g. 'this Friday', 'tomorrow', "
                    "'2026-10-25'), convert it to YYYY-MM-DD format in the 'date' field. "
                    "If no date is mentioned, leave 'date' as null. "
                    "Convert time to 24-hour format (HH:MM):\n"
                    "{format_instructions}\n"
                    "User query: {query}\n"
                    "Current time: {current_time}\n",
            input_variables=["query", "current_time"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )

        llm = create_llm(temperature=0)
        chain = prompt | llm | parser

        current_time = datetime.datetime.now(ZoneInfo(os.getenv("SALON_TIMEZONE", "Asia/Ho_Chi_Minh")))
        event_info = chain.invoke({
            "query": query,
            "current_time": current_time.isoformat()
        })

        if not event_info.booking_code:
            event_info.booking_code = generate_booking_code()

        return self.create_event(event_info, current_time)