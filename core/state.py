"""Run log so a channel never gets the same day twice."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state" / "posted.json"


def load():
    if STATE.exists():
        try:
            return json.loads(STATE.read_text())
        except Exception:
            return {}
    return {}


def already(day, channel):
    return channel in load().get(day, {}).get("ok", [])


def record(day, channel, result):
    data = load()
    entry = data.setdefault(day, {"ok": [], "results": {}})
    entry["results"][channel] = result
    if result.get("ok"):
        if channel not in entry["ok"]:
            entry["ok"].append(channel)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return data
