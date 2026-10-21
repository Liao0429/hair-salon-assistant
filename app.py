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
    streaming=False,
)
# Per-session agents: each session_id gets its own agent with isolated memory.
# Fixes H2 (previously all web visitors shared one global conversation memory).
agents: dict[str, BookingAgent] = {}

def get_agent(session_id: str) -> BookingAgent:
    if session_id not in agents:
        agents[session_id] = BookingAgent(llm)
    return agents[session_id]

class ChatMessage(BaseModel):
    message: str
    session_id: str = "default"

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/chat")
async def chat(payload: ChatMessage):
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

@app.get("/api/health")
async def health():
    return {"status": "ok"}


# ===== 预约管理后台页面（管理者查看 booking.db 数据） =====
from fastapi.responses import HTMLResponse
from bookinggpt.storage import list_bookings

@app.get("/bookings", response_class=HTMLResponse)
def bookings_page():
    bookings = list_bookings()
    rows_html = ""
    if not bookings:
        rows_html = '<tr><td colspan="6" style="text-align:center;color:#888;padding:24px">No bookings yet</td></tr>'
    for b in bookings:
        status_cls = "confirmed" if b["status"] == "confirmed" else "cancelled"
        status_label = "✅ Confirmed" if b["status"] == "confirmed" else "❌ Cancelled"
        rows_html += f"""<tr>
            <td class="mono">{b['booking_code']}</td>
            <td>{b['customer_name']}</td>
            <td>{b['phone']}</td>
            <td>{b['service']}</td>
            <td>{b['event_time']}</td>
            <td><span class="badge {status_cls}">{status_label}</span></td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>Daisy Salon - 预约管理后台</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif; background: #f5f6fa; padding: 32px; }}
  .card {{ max-width: 960px; margin: 0 auto; background: #fff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,.08); overflow: hidden; }}
  .header {{ background: linear-gradient(135deg, #6a11cb, #2575fc); color: #fff; padding: 24px 32px; }}
  .header h1 {{ font-size: 22px; }}
  .header p {{ opacity: .85; margin-top: 6px; font-size: 13px; }}
  .stats {{ display: flex; gap: 16px; padding: 20px 32px; background: #fafbfc; border-bottom: 1px solid #eee; }}
  .stat {{ flex: 1; }}
  .stat .num {{ font-size: 28px; font-weight: 700; color: #2575fc; }}
  .stat .label {{ font-size: 12px; color: #888; }}
  table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
  th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #f0f0f0; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
  th {{ background: #fafbfc; color: #666; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: .5px; }}
  .mono {{ font-family: Consolas, monospace; color: #2575fc; font-weight: 600; }}
  .badge {{ padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }}
  .badge.confirmed {{ background: #e6f7ec; color: #1a8f4a; }}
  .badge.cancelled {{ background: #fdeaea; color: #d93b3b; }}
  .footer {{ padding: 16px 32px; color: #aaa; font-size: 12px; text-align: center; }}
</style>
</head>
<body>
  <div class="card">
    <div class="header">
      <h1>💇 Daisy Salon · Booking Admin Dashboard</h1>
      <p>Manager view · All customer bookings (local SQLite booking.db)</p>
    </div>
    <div class="stats">
      <div class="stat"><div class="num">{len(bookings)}</div><div class="label">Total Bookings</div></div>
      <div class="stat"><div class="num">{sum(1 for b in bookings if b['status']=='confirmed')}</div><div class="label">Confirmed</div></div>
      <div class="stat"><div class="num">{sum(1 for b in bookings if b['status']=='cancelled')}</div><div class="label">Cancelled</div></div>
    </div>
    <table>
      <thead><tr><th>Booking Code</th><th>Customer</th><th>Phone</th><th>Service</th><th>Time</th><th>Status</th></tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
    <div class="footer">Daisy Salon AI Booking Assistant · Data from booking.db</div>
  </div>
</body>
</html>"""
    return HTMLResponse(html)


# ===== 无模型保底预约接口（模型限速/不可用时，Customer直接表单预约，写入 booking.db） =====
import random
import string
from bookinggpt.storage import create_booking as storage_create_booking

class BookingForm(BaseModel):
    customer_name: str
    phone: str
    service: str
    date: str  # YYYY-MM-DD
    time: str  # HH:MM

@app.post("/api/booking")
async def create_booking_api(payload: BookingForm):
    try:
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        event_time = f"{payload.date} {payload.time}"
        storage_create_booking(
            booking_code=code,
            customer_name=payload.customer_name,
            phone=payload.phone,
            service=payload.service,
            event_time=event_time,
        )
        return {"booking_code": code, "status": "confirmed", "message": f"Booking {code} created."}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
