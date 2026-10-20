# -*- coding: utf-8 -*-
"""
FastAPI web interface for the AI Hair Salon Booking Assistant.
- GET  /            -> chat UI (default English, i18n switch)
- POST /api/chat    -> send message, get assistant reply
- GET  /api/health  -> health check

Run:  uvicorn app:app --host 0.0.0.0 --port 8000
"""
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from bookinggpt.agent.booking_agent import BookingAgent

load_dotenv()

app = FastAPI(title="Daisy AI Booking Assistant")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize the booking agent once (model from .env)
llm = ChatOpenAI(
    model=os.getenv("MODEL_NAME", "u2-flash"),
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    temperature=0.3,
)
booking_agent = BookingAgent(llm)

class ChatMessage(BaseModel):
    message: str
    session_id: str = "default"

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/chat")
async def chat(payload: ChatMessage):
    try:
        reply = booking_agent.call_agent(payload.message)
        return JSONResponse({"reply": reply})
    except Exception as e:
        return JSONResponse({"reply": f"Sorry, an error occurred: {str(e)[:200]}"}, status_code=500)

@app.get("/api/health")
async def health():
    return {"status": "ok"}
