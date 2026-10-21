#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render multi-scene AI booking demo screenshots for Daisy Hair Salon.

Extends tools/render_demo_screenshots.py with 4 appointment-dialog scenes.
Each conversation is rendered to a full-page PNG (width 800, height adaptive,
color emoji) using Playwright + headless Chromium - the same rendering
approach as the existing screen-chat-long.png.

Generated files (docs/screenshots/):
    demo-booking-confirm.png   user books -> AI confirms (service/time/code)
    demo-booking-cancel.png    user cancels -> AI confirms cancellation
    demo-availability.png      user asks for openings -> AI lists free slots
    demo-multi-turn.png        multi-turn: services -> booking -> confirmation

Usage:
    .venv\\Scripts\\python.exe tools/render_demo_scenes.py
    .venv\\Scripts\\python.exe tools/render_demo_scenes.py --scene booking-confirm
    .venv\\Scripts\\python.exe tools/render_demo_scenes.py --width 900
    .venv\\Scripts\\python.exe tools/render_demo_scenes.py --verify
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from string import Template

try:
    from PIL import Image
    HAVE_PIL = True
except ImportError:  # pragma: no cover - PIL only used for verification
    HAVE_PIL = False

# Reuse the renderer / helpers from the existing screenshot script.
from render_demo_screenshots import esc, image_size, project_root, render


# --------------------------------------------------------------------------- #
# Scene content
# --------------------------------------------------------------------------- #
SCENES = [
    {
        "name": "booking-confirm",
        "out": "demo-booking-confirm.png",
        "messages": [
            ("user", "Hi! I'd like to book a haircut tomorrow at 10am. My name is Li Hua, phone 13800001111."),
            ("bot", "Great choice! 🎉 I've booked your **Hair cut** for **tomorrow at 10:00 AM** ✂️ Your booking code is **AB12CD34**. We'll see you then! 💇♀️✨"),
        ],
    },
    {
        "name": "booking-cancel",
        "out": "demo-booking-cancel.png",
        "messages": [
            ("user", "Hi, I need to cancel my booking AB12CD34 please."),
            ("bot", "No problem! ❌ I've cancelled your booking **AB12CD34** (Hair cut on tomorrow 10:00). Hope to see you another time! 💇"),
        ],
    },
    {
        "name": "availability",
        "out": "demo-availability.png",
        "messages": [
            ("user", "Do you have any openings this Saturday for hair coloring?"),
            ("bot", "Let me check... 📅 Here's what's available this Saturday for **Hair coloring**: 🕘 9:00 AM · 11:30 AM · 2:00 PM · 4:30 PM. Which one works for you? 🎨"),
        ],
    },
    {
        "name": "multi-turn",
        "out": "demo-multi-turn.png",
        "messages": [
            ("user", "What services do you offer?"),
            ("bot", "Here's what we're rocking right now! 💇♀️ Hair wash, ✂️ Hair cut, 💇 Hair styling, 🧔 Beard trim, 🎨 Hair coloring, 💅 Manicure... Which one would you like to book?"),
            ("user", "Great! I'd like a haircut tomorrow at 10am. My name is Amy, phone 13900002222."),
            ("bot", "Perfect! ✅ Your **Hair cut** is booked for **tomorrow at 10:00 AM**. Booking code **EF56GH78**. See you soon! ✂️✨"),
        ],
    },
]


# --------------------------------------------------------------------------- #
# HTML builder
# --------------------------------------------------------------------------- #
def md_bold(text: str) -> str:
    """HTML-escape text, then turn **bold** markers into <strong> tags."""
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", esc(text))


def scene_chat_html(messages: list[tuple[str, str]]) -> str:
    """Build a chat UI HTML document (same look as screen-chat-long.png)."""
    msg_divs = []
    for role, text in messages:
        if role == "user":
            msg_divs.append(f'<div class="msg user">{esc(text)}</div>')
        else:
            msg_divs.append(f'<div class="msg bot">{md_bold(text)}</div>')
    msgs_html = "\n    ".join(msg_divs)

    last_user = ""
    for role, text in reversed(messages):
        if role == "user":
            last_user = text
            break

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
  .msg strong { font-weight:600; }
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
    $msgs
  </div>
  <div class="inputbar">
    <input value="$question" readonly>
    <div class="send">Send</div>
  </div>
</div>
</body>
</html>""")
    return tmpl.substitute(msgs=msgs_html, question=esc(last_user))


# --------------------------------------------------------------------------- #
# Verification helpers
# --------------------------------------------------------------------------- #
def colorful_pixel_ratio(path: Path) -> float:
    """Fraction of clearly colorful (high-saturation) pixels.

    The UI is white/cream/dark-brown, so bright saturated pixels only come from
    color emoji glyphs. A monochrome tofu box contributes ~0 colorful pixels.
    """
    if not HAVE_PIL:
        return -1.0
    with Image.open(path).convert("RGB") as im:
        w, h = im.size
        pixels = im.load()
        colorful = 0
        sampled = 0
        for y in range(0, h, 2):
            for x in range(0, w, 2):
                r, g, b = pixels[x, y]
                mx, mn = max(r, g, b), min(r, g, b)
                if mx - mn >= 60 and mx >= 100:
                    colorful += 1
                sampled += 1
        return colorful / sampled


def analyze_image(path: Path) -> tuple:
    """Return (width, height, bytes, colorful_ratio) for one PNG."""
    if not HAVE_PIL:
        return (0, 0, path.stat().st_size, -1.0)
    with Image.open(path) as im:
        return (im.width, im.height, path.stat().st_size,
               colorful_pixel_ratio(path))


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scene", choices=[s["name"] for s in SCENES],
        help="render only this scene (default: all scenes)",
    )
    parser.add_argument("--width", type=int, default=800,
                        help="screenshot width in px (default: 800)")
    parser.add_argument("--verify", action="store_true",
                        help="verify existing screenshots only (no re-render)")
    args = parser.parse_args()

    root = project_root()
    out_dir = root / "docs" / "screenshots"
    out_dir.mkdir(parents=True, exist_ok=True)

    scenes = SCENES if args.scene is None else [s for s in SCENES if s["name"] == args.scene]

    if not args.verify:
        for scene in scenes:
            out = out_dir / scene["out"]
            print(f"Rendering {scene['name']} -> {out}")
            if render(scene_chat_html(scene["messages"]), out, args.width):
                w, h, size, ratio = analyze_image(out)
                print(f"  OK ({w}x{h}, {size} bytes, colorful={ratio:.4%})")
            else:
                print("  FAILED: neither Playwright nor system Chrome available.")

    if args.verify or args.scene is None:
        print("\nVerification:")
        ok = True
        for scene in SCENES:
            out = out_dir / scene["out"]
            if not out.exists() or out.stat().st_size == 0:
                print(f"  [FAIL] {out.name}: missing or empty")
                ok = False
                continue
            w, h, size, ratio = analyze_image(out)
            status = "OK" if (w == args.width and ratio >= 0.0005) else "CHECK"
            if w != args.width:
                status = "FAIL(width)"
                ok = False
            if ratio < 0.0005:
                status = "FAIL(color)"
                ok = False
            print(f"  [{status}] {out.name}: {w}x{h}, {size} bytes, "
                  f"colorful={ratio:.4%}")
        if not ok:
            sys.exit(1)


if __name__ == "__main__":
    main()