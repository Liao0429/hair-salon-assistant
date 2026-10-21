# AI Hair Salon Booking Assistant 💇‍♀️🤖

**English** | [**中文**](README.zh-CN.md)

An AI-powered conversational booking assistant for hair salons. Customers book appointments by chatting naturally — the AI understands intent, checks available slots, creates bookings, and handles cancellations. A zero-config web interface, an SQLite fallback, and a protected admin dashboard make it production-ready for small salons.

## ✨ Key Features

- 🤖 **Conversational booking** — book, check slots, and cancel by natural language
- 🌍 **Trilingual interface** — English (default), 中文, Español, one-click switch
- 🔌 **Model-agnostic** — works with any OpenAI-compatible API (`/v1/chat/completions`)
- 🛡️ **Protected admin dashboard** — view and filter all bookings, secured with `ADMIN_TOKEN`
- ⚡ **No-AI fallback** — if the model is down or rate-limited, a quick-booking form still records the appointment
- 💾 **Zero-config storage** — SQLite, no external database required
- 📅 **Google Calendar** — optional integration for calendar-synced salons

## 📸 Screenshots

All screenshots below are **real browser captures** (no mockups, no AI-rendered images).

### 🤖 AI Booking Conversation

| Screenshot | Description |
|---|---|
| ![Service list](docs/screenshots/real-services.png) | AI replies with the salon's service menu |
| ![Booking in chat](docs/screenshots/real-booking.png) | AI collects details and confirms a booking in chat |
| ![Booking confirmed](docs/screenshots/real-booking-confirmed.png) | Booking confirmed — a booking code is returned |
| ![Cancel request](docs/screenshots/real-cancel.png) | Customer asks to cancel an appointment |
| ![Cancellation processed](docs/screenshots/real-cancel-confirmed.png) | Cancellation completed |

### 🌍 Trilingual Interface

| Screenshot | Description |
|---|---|
| ![English UI](docs/screenshots/real-en.png) | English interface (default) |
| ![中文界面](docs/screenshots/real-zh.png) | 中文界面 (Chinese) |
| ![Interfaz en español](docs/screenshots/real-es.png) | Interfaz en español (Spanish) |

### 🛡️ Resilience & Admin

| Screenshot | Description |
|---|---|
| ![Quick booking](docs/screenshots/real-quickbook.png) | No-AI quick-booking form (fallback) |
| ![Degraded mode](docs/screenshots/real-services-degraded.png) | Degraded mode — service list without AI |
| ![Admin dashboard](docs/screenshots/real-admin-db.png) | Admin dashboard with all bookings |

## 🏗️ Architecture

The project follows a clean four-layer design:

```
┌─────────────────────────────────────────────┐
│  Web Layer — FastAPI + frontend             │
│  /api/chat · /api/booking · /api/health     │
├─────────────────────────────────────────────┤
│  Agent Layer — LangChain Agent              │
│  BookingAgent + 3 tools (create/check/cancel)│
├─────────────────────────────────────────────┤
│  Model Layer — OpenAI-compatible (any /v1)  │
├─────────────────────────────────────────────┤
│  Storage Layer — SQLite (+ optional Google) │
└─────────────────────────────────────────────┘
```

### How a booking works

1. A customer types a message in the web chat (`POST /api/chat`).
2. The LangChain agent calls the LLM to understand intent.
3. The agent invokes a tool:
   - `AvailableSlotsTool` — check free time slots
   - `CalendarTool` — create the appointment
   - `CancelEventTool` — cancel an existing appointment
4. The booking is stored in SQLite; a `booking_code` is returned to the customer.
5. The salon owner views/filters all bookings in the admin dashboard (`/bookings`).

### No-AI fallback

If the model is unavailable or rate-limited, the frontend automatically expands a **quick-booking form**. `POST /api/booking` writes directly to SQLite — no AI needed — so the salon never loses a booking.

## 🧩 Tech Stack

- **Python 3.11+**
- **FastAPI** — web framework
- **LangChain** — agent + tool calling
- **OpenAI-compatible model layer** — any `/v1/chat/completions` endpoint
- **SQLite** — zero-config booking storage
- **Google Calendar API** — optional
- **Vanilla HTML/CSS/JS** — trilingual chat UI + admin dashboard

## 📁 Project Structure

```
hair-salon-assistant/
├── app.py                    # FastAPI entry + all API routes
├── main.py                   # CLI entry
├── view_bookings.py          # CLI: view bookings
├── run_tests.py              # test helper
├── bookinggpt/
│   ├── agent/
│   │   ├── booking_agent.py  # LangChain agent (memory + tools)
│   │   └── prompt.py         # system prompt
│   ├── tool/
│   │   ├── create_event.py   # tool: create appointment
│   │   ├── available_event.py# tool: check available slots
│   │   └── cancel_event.py   # tool: cancel appointment
│   ├── llm.py                # OpenAI-compatible model factory
│   ├── google_auth.py        # Google Calendar OAuth (optional)
│   ├── storage.py            # SQLite storage
│   └── utils.py
├── templates/
│   ├── index.html            # trilingual chat UI
│   └── admin.html            # admin dashboard
├── static/favicon.svg
├── security/                 # Google OAuth templates (.example)
├── tests/                    # 38 unit tests
├── docs/                     # docs + real screenshots
├── .github/workflows/ci.yml  # CI
└── requirements.txt
```

## 🚀 Quick Start

### 1. Clone & install

```bash
git clone https://github.com/Liao0429/hair-salon-assistant.git
cd hair-salon-assistant
pip install -r requirements.txt
```

### 2. Configure `.env`

```bash
# OpenAI-compatible model
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=https://api.openrouter.ai/api/v1   # or DeepSeek / Zhipu / any
MODEL_NAME=gpt-4o-mini                             # change to your model

# Admin dashboard (required to enable /bookings)
ADMIN_TOKEN=your_admin_token
```

Optional: copy `security/credentials.json.example` → `security/credentials.json` and fill in Google OAuth credentials to enable Google Calendar integration.

### 3. Run the web app

```bash
uvicorn app:app --host 127.0.0.1 --port 8000
```

Open http://localhost:8000 in your browser.

### 4. Run tests

```bash
pytest
```

## 🔌 API

| Method | Path | Description | Auth |
|---|---|---|---|
| `GET` | `/` | Chat interface (EN / 中文 / ES) | — |
| `POST` | `/api/chat` | Send a message, get AI reply (rate-limited) | — |
| `POST` | `/api/booking` | Quick booking (no AI, writes to SQLite) | — |
| `GET` | `/api/health` | Health check | — |
| `GET` | `/bookings` | Admin dashboard (booking list) | `ADMIN_TOKEN` |

**Quick booking** `POST /api/booking`

```json
{ "customer_name": "Emily Johnson", "phone": "+1 555-0100", "service": "Hair cut", "date": "2026-10-25", "time": "14:00" }
```

Response:

```json
{ "booking_code": "A1B2C3D4", "status": "confirmed" }
```

**Admin dashboard**: set `ADMIN_TOKEN` before starting, then visit `/bookings?token=<value>`. If `ADMIN_TOKEN` is not set, the endpoint returns 503; a wrong token returns 401.

## 🔒 Security

- `.env`, `security/credentials.json`, `security/token.json`, and `booking.db` are excluded via `.gitignore` and never committed.
- The repo ships only `.env.example` and `security/*.example` templates — no real keys or tokens.
- The admin dashboard is protected by `ADMIN_TOKEN`.

## ⚙️ CI

GitHub Actions runs `pytest` on every push (`.github/workflows/ci.yml`).

## ✅ Verified (2026-10-21)

- **Environment**: Python 3.12 venv, dependencies installed
- **Model**: any OpenAI-compatible endpoint (example uses `gpt-4o-mini`)
- **Result**: the assistant lists services, guides customers through booking, and calls tools to create/check/cancel appointments
- **Tests**: `pytest` — 38 passed

## 📄 License

MIT License. See [LICENSE](LICENSE).
