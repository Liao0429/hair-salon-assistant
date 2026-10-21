# -*- coding: utf-8 -*-
"""
FastAPI web interface for the AI Hair Salon Booking Assistant.
- GET  /               -> chat UI (default English, i18n switch)
- POST /api/chat       -> send message, get assistant reply (rate-limited)
- POST /api/booking    -> quick booking fallback (no AI required)
- GET  /api/health     -> health check
- GET  /bookings       -> admin dashboard (protected by ADMIN_TOKEN)

Run:  uvicorn app:app --host 0.0.0.0 --port 8000
"""
import os
import re
import time
from collections import OrderedDict, defaultdict, deque

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from bookinggpt.agent.booking_agent import BookingAgent
from bookinggpt.llm import create_llm
from bookinggpt.storage import create_booking, list_bookings
from bookinggpt.utils import generate_booking_code

load_dotenv()

app = FastAPI(title="Daisy AI Booking Assistant")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Model layer (config via .env)
llm = create_llm()

# ---- Per-session agents with LRU capacity bound (prevents unbounded memory growth) ----
MAX_AGENTS = int(os.getenv("MAX_AGENTS", "100"))
agents: "OrderedDict[str, BookingAgent]" = OrderedDict()


def get_agent(session_id: str) -> BookingAgent:
    agent = agents.pop(session_id, None)
    if agent is None:
        if len(agents) >= MAX_AGENTS:
            agents.popitem(last=False)  # evict least-recently-used session
        agent = BookingAgent(llm)
    agents[session_id] = agent  # move to end (most recently used)
    return agent


# ---- Simple in-memory rate limiter (per session, fixed window) ----
CHAT_RATE_LIMIT = int(os.getenv("CHAT_RATE_LIMIT", "20"))
CHAT_WINDOW_SECONDS = 60
MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", "2000"))
_hits: "defaultdict[str, deque]" = defaultdict(deque)


def _rate_limited(session_id: str) -> bool:
    now = time.monotonic()
    q = _hits[session_id]
    while q and now - q[0] > CHAT_WINDOW_SECONDS:
        q.popleft()
    if len(q) >= CHAT_RATE_LIMIT:
        return True
    q.append(now)
    return False


class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: str = "default"


class BookingRequest(BaseModel):
    customer_name: str = ""
    phone: str = ""
    service: str = ""
    date: str = ""
    time: str = ""


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/chat")
async def chat(payload: ChatMessage):
    if _rate_limited(payload.session_id):
        return JSONResponse(
            {"reply": "Too many messages. Please wait a moment and try again.", "degraded": True},
            status_code=429,
        )
    if len(payload.message) > MAX_MESSAGE_LENGTH:
        return JSONResponse(
            {"reply": f"Message too long (max {MAX_MESSAGE_LENGTH} chars).", "degraded": True},
            status_code=400,
        )
    try:
        agent = get_agent(payload.session_id)
        reply = agent.call_agent(payload.message)
        return JSONResponse({"reply": reply})
    except Exception as e:
        # Degraded mode: tell frontend AI is unavailable (rate limit / error) so it can offer fallback form.
        return JSONResponse(
            {"reply": f"Sorry, an error occurred: {str(e)[:200]}", "degraded": True},
            status_code=500,
        )


@app.post("/api/booking")
async def quick_booking(payload: BookingRequest):
    """Quick booking fallback that works without the AI layer."""
    name = (payload.customer_name or "").strip()
    phone = (payload.phone or "").strip()
    service = (payload.service or "").strip()
    date = (payload.date or "").strip()
    time = (payload.time or "").strip()

    if not name or not date:
        return JSONResponse({"error": "Name and date are required."}, status_code=400)
    if time and not re.fullmatch(r"\d{2}:\d{2}", time):
        return JSONResponse({"error": "Time must be in HH:MM format."}, status_code=400)

    booking_code = generate_booking_code()
    event_time = f"{date} {time}".strip()
    try:
        create_booking(booking_code, name, phone, service, event_time)
    except Exception as e:
        return JSONResponse({"error": f"Failed to save booking: {e}"}, status_code=500)
    return JSONResponse({"booking_code": booking_code, "status": "confirmed"})


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# ===== 预约管理后台页面（受 ADMIN_TOKEN 保护） =====
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")


@app.get("/bookings", response_class=HTMLResponse)
def bookings_page(request: Request):
    token = request.query_params.get("token", "") or request.cookies.get("admin_token", "")
    if not ADMIN_TOKEN:
        return HTMLResponse(
            "<h2>Admin dashboard is disabled.</h2>"
            "<p>Set the ADMIN_TOKEN environment variable to enable it.</p>",
            status_code=503,
        )
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    bookings = list_bookings()
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "bookings": bookings,
            "total": len(bookings),
            "confirmed": sum(1 for b in bookings if b["status"] == "confirmed"),
            "cancelled": sum(1 for b in bookings if b["status"] == "cancelled"),
        },
    )