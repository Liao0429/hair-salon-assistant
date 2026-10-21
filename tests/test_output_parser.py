# -*- coding: utf-8 -*-
"""Unit tests for the Pydantic output parser used by the booking tools.

Keeps the OpenAI-compatible model layer (ChatOpenAI) without requiring a live
endpoint: a fake LLM returns canned JSON so the parser logic is exercised.
"""
from datetime import datetime
from typing import Optional

import pytest
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

# Load environment variables (override user/system vars so .env wins)
load_dotenv(override=True)


class EventDetails(BaseModel):
    event_name: str = Field(description="The name of the event or service being booked")
    customer_name: str = Field(description="The name of the customer making the booking")
    customer_phone: Optional[str] = Field(description="The customer's phone number for contact")
    start_time: datetime = Field(description="The starting time of the event")
    end_time: datetime = Field(description="The ending time of the event")
    booking_code: Optional[str] = Field(description="A unique code for this booking, if applicable")
    additional_requests: Optional[str] = Field(description="Any additional requests or preferences from the customer")


class FakeLLM:
    """Minimal stand-in for an OpenAI-compatible chat model.

    Implements only what the Runnable chain needs (invoke) and returns a
    canned completion, so tests never hit a live /v1 endpoint.
    """

    def __init__(self, content: str):
        self.content = content

    def invoke(self, *args, **kwargs):
        from langchain_core.messages import AIMessage
        return AIMessage(content=self.content)


def make_parser() -> PydanticOutputParser:
    return PydanticOutputParser(pydantic_object=EventDetails)


def make_chain():
    parser = make_parser()
    prompt = PromptTemplate(
        template="""Based on the user input, chat history, and current time, extract the following event details:
User Input: {input}

{format_instructions}

Ensure all fields are filled appropriately based on the available information.
If any information is not provided or unclear, leave the field empty or null.
For the start_time and end_time, use the current time as reference if needed.""",
        input_variables=["input"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    return prompt, parser


def test_parser_format_instructions_include_required_fields():
    parser = make_parser()
    instructions = parser.get_format_instructions()
    assert "event_name" in instructions
    assert "customer_name" in instructions
    assert "start_time" in instructions
    assert "end_time" in instructions


def test_parser_parses_canned_json():
    parser = make_parser()
    canned_json = (
        '{"event_name": "Haircut", "customer_name": "Hoang Anh", '
        '"customer_phone": "1234567890", '
        '"start_time": "2026-10-22T15:00:00", '
        '"end_time": "2026-10-22T15:30:00", '
        '"booking_code": null, "additional_requests": null}'
    )
    result = parser.parse(canned_json)
    assert result.event_name == "Haircut"
    assert result.customer_name == "Hoang Anh"
    assert result.customer_phone == "1234567890"
    assert result.start_time.hour == 15
    assert result.end_time.minute == 30
    assert result.booking_code is None


def test_parser_rejects_invalid_json():
    parser = make_parser()
    with pytest.raises(Exception):
        parser.parse("this is not json")


def test_parser_rejects_missing_required_field():
    parser = make_parser()
    invalid_json = '{"event_name": "Haircut"}'  # missing customer_name
    with pytest.raises(Exception):
        parser.parse(invalid_json)


def test_event_details_model_validation():
    with pytest.raises(ValidationError):
        EventDetails(
            event_name="Haircut",
            customer_name="Hoang Anh",
            start_time="not-a-datetime",  # type: ignore[arg-type]
            end_time="2026-10-22T15:30:00",
        )
