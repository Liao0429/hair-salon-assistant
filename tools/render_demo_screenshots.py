#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render demo long screenshots for the Daisy Hair Salon assistant.

The old screenshots were drawn with PIL using Arial, which rendered emoji as tofu
(``□□□``). This script renders the same screenshots with real color emoji using
headless Chromium. Primary renderer is Playwright with its bundled Chromium; if
Playwright is not available it falls back to system Google Chrome
``--headless --screenshot`` plus a PIL crop to the content height.

Generated files:
    docs/screenshots/screen-chat-long.png   (chat UI: user question + AI reply)
    docs/screenshots/screen-admin-long.png  (admin appointment table from booking.db)

Setup (one time):
    .venv\\Scripts\\python.exe -m pip install pillow playwright
    .venv\\Scripts\\python.exe -m playwright install chromium

Usage:
    .venv\\Scripts\\python.exe tools/render_demo_screenshots.py
    .venv\\Scripts\\python.exe tools/render_demo_screenshots.py --chat
    .venv\\Scripts\\python.exe tools/render_demo_screenshots.py --admin
    .venv\\Scripts\\python.exe tools/render_demo_screenshots.py --width 900
"""

from __future__ import annotations

import argparse
import html
import os
import sqlite3
import subprocess
import tempfile
from pathlib import Path
from string import Template

try:
    from PIL import Image, ImageChops
    HAVE_PIL = True
except ImportError:  # pragma: no cover - PIL only used by the CLI fallback
    HAVE_PIL = False


# --------------------------------------------------------------------------- #
# Paths / constants
# --------------------------------------------------------------------------- #
def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


CHROME_CANDIDATES = [
    Path(os.environ.get("PROGRAMFILES", r"C:\Program Files"))
    / "Google" / "Chrome" / "Application" / "chrome.exe",
    Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"))
    / "Google" / "Chrome" / "Application" / "chrome.exe",
    Path(os.environ.get("LOCALAPPDATA", ""))
    / "Google" / "Chrome" / "Application" / "chrome.exe",
    Path(os.environ.get("PROGRAMFILES", r"C:\Program Files"))
    / "Microsoft" / "Edge" / "Application" / "msedge.exe",
]


# --------------------------------------------------------------------------- #
# Content
# --------------------------------------------------------------------------- #
USER_QUESTION = "What services do you offer?"

AI_REPLY = """Hey there! 👋 Daisy Hair Salon's got you covered with all sorts of goodies! Here's what we're rocking right now:

💇‍♀️ Hair wash - 20 mins of pure relaxation
✂️ Hair cut - 30 mins for that fresh new look
💇 Hair styling - 30 mins to slay your style
🧔 Beard trim - 15 mins to keep it sharp
🎨 Hair coloring - 60 mins for a bold new vibe
🧖‍♀️ Hair treatment - 45 mins of pampering goodness
💆 Scalp massage - 15 mins of bliss
👁️ Eyebrow shaping - 10 mins to frame that face
🧼 Facial - 45 mins of glow time
💅 Manicure - 30 mins for those perfect nails

Sounds like something you'd be into? 😊 I'd love to help you book an appointment whenever you're ready!"""

DEMO_BOOKINGS = [
    {"code": "AB12CD34", "name": "Li Hua", "phone": "13800001111",
     "service": "Hair cut", "time": "2026-10-22 10:00", "status": "confirmed"},
    {"code": "EF56GH78", "name": "Amy", "phone": "13900002222",
     "service": "Hair coloring", "time": "2026-10-22 14:00", "status": "confirmed"},
    {"code": "IJ90KL12", "name": "Wang Qiang", "phone": "13600003333",
     "service": "Hair styling", "time": "2026-10-23 09:30", "status": "cancelled"},
]


# --------------------------------------------------------------------------- #
# Data access
# --------------------------------------------------------------------------- #
def load_bookings(db_path: Path) -> list[dict]:
    """Read bookings from the project's SQLite database (booking.db)."""
    if not db_path.exists():
        return []
    con = sqlite3.connect(db_path)
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT booking_code, customer_name, phone, service, event_time, status "
            "FROM bookings ORDER BY event_time"
        )
        return [
            {"code": r[0], "name": r[1], "phone": r[2],
             "service": r[3], "time": r[4], "status": r[5]}
            for r in cur.fetchall()
        ]
    finally:
        con.close()


def esc(text) -> str:
    """HTML-escape text (quotes included) for safe embedding."""
    return html.escape(str(text), quote=True)


# --------------------------------------------------------------------------- #
# HTML builders
# --------------------------------------------------------------------------- #
def chat_html() -> str:
    """Build the chat UI HTML document (user question + AI reply)."""
    user_html = f'<div class="msg user">{esc(USER_QUESTION)}</div>'
    bot_html = f'<div class="msg bot">{esc(AI_REPLY)}</div>'

    tmpl = Template("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Daisy Salon AI Assistant - Chat</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  html, body { background:#f5f0eb; }
  body { font-family:'Segoe UI', system-ui, -apple-system, sans-serif; padding:24px 0; display:flex; justify-content:center; }
  .app { width:100%; max-width:752px; background:#fff; border-radius:16px; box-shadow:0 10px 40px rgba(0,0,0,.12); overflow:hidden; }
  header { background:#2d1b14; color:#fff; padding:16px 20px; display:flex; align-items:center; justify-content:space-between; }
  .brand { display:flex; align-items:center; gap:12px; }
  .logo { width:42px; height:42px; background:#e8b89b; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:22px; line-height:1; }
  .brand h1 { font-size:16px; font-weight:600; }
  .brand p { font-size:12px; opacity:.8; }
  .lang { background:#4a2f22; color:#fff; padding:6px 14px; border-radius:20px; font-size:12px; }
  .messages { padding:20px; background:#faf7f4; display:flex; flex-direction:column; gap:14px; }
  .msg { max-width:80%; padding:12px 16px; border-radius:16px; font-size:15px; line-height:1.55; white-space:pre-wrap; overflow-wrap:break-word; }
  .bot { align-self:flex-start; background:#fff; border:1px solid #eee; border-top-left-radius:4px; }
  .user { align-self:flex-end; background:#2d1b14; color:#fff; border-top-right-radius:4px; }
  .inputbar { display:flex; gap:8px; padding:14px; background:#fff; border-top:1px solid #eee; }
  .inputbar input { flex:1; padding:12px 16px; border:1px solid #ddd; border-radius:24px; font-size:14px; outline:none; color:#6b5b50; }
  .send { background:#2d1b14; color:#fff; border:none; border-radius:24px; padding:0 24px; font-size:14px; font-weight:600; }
</style>
</head>
<body>
<div class="app">
  <header>
    <div class="brand">
      <div class="logo">&#128135;&#8205;&#9792;&#65039;</div>
      <div>
        <h1>Daisy Salon AI Assistant</h1>
        <p>Book appointments easily &middot; 24/7</p>
      </div>
    </div>
    <div class="lang">English</div>
  </header>
  <div class="messages">
    $user_html
    $bot_html
  </div>
  <div class="inputbar">
    <input value="$question" readonly>
    <div class="send">Send</div>
  </div>
</div>
</body>
</html>""")
    return tmpl.substitute(
        user_html=user_html,
        bot_html=bot_html,
        question=esc(USER_QUESTION),
    )


def admin_html(bookings: list[dict]) -> str:
    """Build the admin dashboard HTML document from booking records."""
    total = len(bookings)
    confirmed = sum(1 for b in bookings if b["status"] == "confirmed")
    cancelled = sum(1 for b in bookings if b["status"] == "cancelled")
    completed = sum(1 for b in bookings if b["status"] == "completed")

    stat_items = [
        ("Total bookings", str(total)),
        ("Confirmed", str(confirmed)),
        ("Cancelled", str(cancelled)),
        ("Completed", str(completed)),
    ]
    stats_html = "\n".join(
        f'      <div class="stat"><div class="num">{esc(num)}</div>'
        f'<div class="label">{esc(label)}</div></div>'
        for label, num in stat_items
    )

    rows_html = ""
    for b in bookings:
        status = b["status"] or "unknown"
        if status in ("confirmed", "completed"):
            icon, badge_class, label = "\u2705", "confirmed", "Confirmed"
        elif status == "cancelled":
            icon, badge_class, label = "\u274c", "cancelled", "Cancelled"
        else:
            icon, badge_class, label = "\u274c", "cancelled", status.title()
        rows_html += (
            "        <tr>\n"
            f'          <td><span class="badge {badge_class}">{icon} {esc(label)}</span></td>\n'
            f'          <td><span class="code">{esc(b["code"])}</span></td>\n'
            f'          <td>{esc(b["name"])}</td>\n'
            f'          <td>{esc(b["phone"])}</td>\n'
            f'          <td>{esc(b["service"])}</td>\n'
            f'          <td class="time">{esc(b["time"])}</td>\n'
            "        </tr>\n"
        )

    tmpl = Template("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Daisy Salon - Admin Dashboard</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  html, body { background:#f5f0eb; }
  body { font-family:'Segoe UI', system-ui, sans-serif; padding:28px 0; display:flex; justify-content:center; }
  .card { width:100%; max-width:744px; background:#fff; border-radius:16px; box-shadow:0 10px 40px rgba(0,0,0,.10); overflow:hidden; }
  .page-header { background:#2d1b14; color:#fff; padding:20px 24px; display:flex; align-items:center; justify-content:space-between; }
  .page-header h1 { font-size:18px; font-weight:600; }
  .page-header p { font-size:12px; opacity:.8; margin-top:2px; }
  .content { padding:24px; }
  .stats { display:flex; gap:12px; margin-bottom:22px; }
  .stat { flex:1; background:#faf7f4; border:1px solid #eee; border-radius:12px; padding:14px 16px; }
  .stat .num { font-size:24px; font-weight:700; color:#2d1b14; }
  .stat .label { font-size:12px; color:#8a7a6f; margin-top:2px; }
  table { width:100%; border-collapse:collapse; }
  thead th { text-align:left; font-size:12px; text-transform:uppercase; letter-spacing:.04em; color:#8a7a6f; padding:10px 12px; border-bottom:2px solid #eee; }
  tbody td { padding:14px 12px; font-size:14px; border-bottom:1px solid #f0ebe6; }
  tbody tr:last-child td { border-bottom:none; }
  .badge { display:inline-flex; align-items:center; gap:6px; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:600; }
  .badge.confirmed { background:#e7f6ec; color:#1a7f37; }
  .badge.cancelled { background:#fdecec; color:#b42318; }
  .code { font-family:Consolas,'Courier New',monospace; font-size:13px; color:#5b4a40; background:#faf7f4; padding:3px 8px; border-radius:6px; }
  .time { font-variant-numeric:tabular-nums; color:#4a3a30; white-space:nowrap; }
</style>
</head>
<body>
<div class="card">
  <div class="page-header">
    <div>
      <h1>Daisy Salon &middot; Admin Dashboard</h1>
      <p>Appointment management &middot; live from booking.db</p>
    </div>
  </div>
  <div class="content">
    <div class="stats">
$stats
    </div>
    <table>
      <thead>
        <tr><th>Status</th><th>Code</th><th>Customer</th><th>Phone</th><th>Service</th><th>Appointment</th></tr>
      </thead>
      <tbody>
$rows
      </tbody>
    </table>
  </div>
</div>
</body>
</html>""")
    return tmpl.substitute(stats=stats_html, rows=rows_html)


# --------------------------------------------------------------------------- #
# Renderers
# --------------------------------------------------------------------------- #
def render_playwright(html_doc: str, out_path: Path, width: int) -> bool:
    """Render HTML to a full-page PNG using Playwright + bundled Chromium."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            # Keep the viewport height small so full_page captures only the
            # content height (height stays adaptive to the conversation/table).
            page = browser.new_page(viewport={"width": width, "height": 100})
            page.set_content(html_doc, wait_until="load")
            page.screenshot(path=str(out_path), full_page=True)
            browser.close()
        return True
    except Exception as exc:  # pragma: no cover - depends on local browser state
        print(f"  [playwright] {exc}")
        return False


def render_chrome_cli(html_doc: str, out_path: Path, width: int) -> bool:
    """Fallback: system Chrome --headless --screenshot + PIL crop to content."""
    if not HAVE_PIL:
        return False
    chrome = next((c for c in CHROME_CANDIDATES if c.exists()), None)
    if chrome is None:
        return False

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        html_path = tmp / "page.html"
        shot_path = tmp / "shot.png"
        profile = tmp / "profile"
        profile.mkdir(exist_ok=True)
        html_path.write_text(html_doc, encoding="utf-8")

        cmd = [
            str(chrome), "--headless=new", "--disable-gpu", "--hide-scrollbars",
            f"--user-data-dir={profile}",
            f"--window-size={width},3000",
            f"--screenshot={shot_path}",
            html_path.as_uri(),
        ]
        subprocess.run(cmd, check=False, capture_output=True)
        if not shot_path.exists():
            return False

        img = Image.open(shot_path).convert("RGB")
        bg = Image.new("RGB", img.size, (245, 240, 235))  # body background #f5f0eb
        diff = ImageChops.difference(img, bg)
        bbox = diff.getbbox()
        if bbox is not None:
            bottom = min(img.height, bbox[3] + 12)
            img = img.crop((0, 0, img.width, bottom))
        img.save(out_path)
    return True


def render(html_doc: str, out_path: Path, width: int) -> bool:
    if render_playwright(html_doc, out_path, width):
        return True
    print("  [fallback] Playwright unavailable, trying system Chrome...")
    return render_chrome_cli(html_doc, out_path, width)


def image_size(path: Path) -> str:
    if not path.exists():
        return "missing"
    if HAVE_PIL:
        with Image.open(path) as im:
            return f"{im.width}x{im.height}"
    return f"{path.stat().st_size} bytes"


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chat", action="store_true", help="render chat screenshot only")
    parser.add_argument("--admin", action="store_true", help="render admin screenshot only")
    parser.add_argument("--width", type=int, default=800, help="screenshot width in px (default: 800)")
    args = parser.parse_args()

    root = project_root()
    out_dir = root / "docs" / "screenshots"
    out_dir.mkdir(parents=True, exist_ok=True)

    do_chat = args.chat or not args.admin
    do_admin = args.admin or not args.chat

    if do_chat:
        out = out_dir / "screen-chat-long.png"
        print(f"Rendering chat screenshot -> {out}")
        if render(chat_html(), out, args.width):
            print(f"  OK ({image_size(out)})")
        else:
            print("  FAILED: neither Playwright nor system Chrome available.")

    if do_admin:
        bookings = load_bookings(root / "booking.db")
        if not bookings:
            print("  WARNING: booking.db not found or empty; using demo data.")
            bookings = DEMO_BOOKINGS
        out = out_dir / "screen-admin-long.png"
        print(f"Rendering admin screenshot -> {out}")
        if render(admin_html(bookings), out, args.width):
            print(f"  OK ({image_size(out)})")
        else:
            print("  FAILED: neither Playwright nor system Chrome available.")


if __name__ == "__main__":
    main()