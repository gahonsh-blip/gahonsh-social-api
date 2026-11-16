"""Daily content for every channel.

The post of the day is deterministic: same date always gives the same headline,
so a re-run can never double-post. A dated entry in content_plan.json always
wins over the weekday rhythm.

Optional: AI_WRITE=yes asks a free text model (Pollinations, no key) to rewrite
the caption. If that fails, the built-in copy is used, so a run never breaks.
"""
import json
import random
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path

from . import config

ROOT = Path(__file__).resolve().parent.parent
PLAN_PATH = ROOT / "content_plan.json"

SITE = "https://gahonsh-blip.github.io"
BRAND = "GAHONSH"
TAGS = "#GAHONSH #WebDevelopment #Flutter #NodeJS #Laravel #RESTAPI #FreelanceDeveloperIndia"

# Weekday rhythm: each day leans on one kind of buyer question.
WEEKDAY = {
    0: {  # Monday
        "theme": "Mobile apps",
        "headline": "One Flutter codebase, Android and iOS together",
        "body": "One build, two stores, no duplicated logic. Offline-first storage and real device testing before release.",
        "prompt": "clean minimal workspace with two smartphones showing the same app, teal and white palette, soft daylight, professional product photo",
    },
    1: {  # Tuesday
        "theme": "Backend and APIs",
        "headline": "A REST API your app will not outgrow",
        "body": "Node.js and Express on a real database, JWT auth, validation on every route, and a documented endpoint list at handover.",
        "prompt": "server room abstract, glowing network lines, deep teal and navy, minimal tech aesthetic, wide professional shot",
    },
    2: {  # Wednesday
        "theme": "Websites that convert",
        "headline": "A website that loads in under two seconds",
        "body": "Static first, images compressed, no bloated plugins. Fast pages rank better and turn visitors into enquiries.",
        "prompt": "laptop on a wooden desk showing a clean business website, warm light, shallow depth of field, editorial photo",
    },
    3: {  # Thursday
        "theme": "Dashboards and data",
        "headline": "Dashboards that answer one question fast",
        "body": "Stock, sales, attendance or payments, one screen each, with Excel export for the accountant.",
        "prompt": "financial dashboard on a large monitor, charts in teal and amber, dark office, cinematic light",
    },
    4: {  # Friday
        "theme": "Business automation",
        "headline": "Stop doing the same task every morning",
        "body": "Enquiry replies, follow ups, invoices and reports can run on a schedule while you sleep.",
        "prompt": "calm morning desk with coffee and a phone showing a green checklist, soft sunlight, minimal",
    },
    5: {  # Saturday
        "theme": "Small business tools",
        "headline": "Software sized for a small business",
        "body": "No enterprise licence, no per seat trap. A tool that fits how your shop or office actually works.",
        "prompt": "small indian shop counter with a tablet, warm tones, documentary photography, natural light",
    },
    6: {  # Sunday
        "theme": "Learning and trust",
        "headline": "Clear pricing before any work starts",
        "body": "Fixed scope, fixed price, a written delivery date. You always know what you are paying for.",
        "prompt": "handshake across a desk with documents, soft teal background, professional business photo",
    },
}

# A few 2026 observances worth a greeting post. Extend freely in content_plan.json.
FESTIVALS = {
    "2026-01-01": ("New Year", "A new year, a cleaner way of working."),
    "2026-01-26": ("Republic Day", "Proud to build in India."),
    "2026-03-04": ("Holi", "Happy Holi. May your colours stay bright."),
    "2026-08-15": ("Independence Day", "Freedom to build what we choose."),
    "2026-10-20": ("Diwali", "Wishing you light, prosperity and good work."),
    "2026-12-25": ("Christmas", "Merry Christmas from all of us at GAHONSH."),
}


def _load_plan():
    if PLAN_PATH.exists():
        try:
            return json.loads(PLAN_PATH.read_text())
        except Exception:
            return {}
    return {}


def build_post(day: date, ai_write=False):
    key = day.isoformat()
    plan = _load_plan()
    override = plan.get("days", {}).get(key, {})

    slot = WEEKDAY[day.weekday()].copy()
    slot.update({k: v for k, v in override.items() if v})

    headline = slot["headline"]
    body = slot["body"]
    occasion = None
    if key in FESTIVALS:
        occasion, greeting = FESTIVALS[key]
        headline = f"{greeting}"
        body = f"{occasion} greetings from {BRAND}. We are taking on a few new projects this month."

    caption = f"{headline}.\n\n{body}\n\nTell us what you need and we will scope it honestly.\n\n{SITE}\n\n{TAGS}"

    if ai_write:
        caption = _ai_caption(headline, body) or caption

    voice = f"{headline}. {body} Get a fixed quote in two to four days at gahonsh dot b l i p dot github dot i o."

    return {
        "date": key,
        "theme": slot.get("theme", ""),
        "headline": headline,
        "body": body,
        "caption": caption,
        "short": f"{headline}. {body[:120]} {SITE} {TAGS}",
        "image_prompt": slot.get("prompt", "modern minimal indian software studio, teal palette"),
        "voice_script": voice,
        "occasion": occasion,
    }


def _ai_caption(headline, body):
    """Free text model, no key. Returns None on any problem."""
    prompt = (
        "Write a LinkedIn caption for a small Indian software studio. "
        f"Headline: {headline}. Fact: {body} "
        "Rules: 3 short sentences, no emoji, no hype, end with a plain call to action. "
        "Do not invent prices, clients or numbers."
    )
    url = "https://text.pollinations.ai/" + urllib.parse.quote(prompt, safe="")
    try:
        with urllib.request.urlopen(url, timeout=45) as r:
            text = r.read().decode("utf-8", "ignore").strip()
        text = " ".join(text.split())
        if 80 <= len(text) <= 900 and "pollinations" not in text.lower():
            return f"{headline}.\n\n{text}\n\n{SITE}\n\n{TAGS}"
    except Exception:
        pass
    return None
