"""Telegram publisher: free, unlimited, no review. Sends the Short or the card."""
from core import config
from core.http import request


def post(post, media, dry_run=False):
    token = config.env("TELEGRAM_BOT_TOKEN")
    chat = config.env("TELEGRAM_CHAT_ID")
    if not (token and chat):
        return {"ok": False, "skipped": True, "error": "TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID missing"}
    if dry_run:
        return {"ok": True, "dry_run": True}

    base = f"https://api.telegram.org/bot{token}"
    caption = media["caption"][:1000]

    if media.get("video"):
        status, body = request("POST", f"{base}/sendVideo",
                               data={"chat_id": chat, "caption": caption, "supports_streaming": "true"},
                               files={"video": media["video"]}, timeout=300)
    elif media.get("image"):
        status, body = request("POST", f"{base}/sendPhoto",
                               data={"chat_id": chat, "caption": caption},
                               files={"photo": media["image"]}, timeout=180)
    else:
        status, body = request("POST", f"{base}/sendMessage",
                               data={"chat_id": chat, "text": media["caption"][:4000]})

    ok = isinstance(body, dict) and body.get("ok")
    msg_id = body.get("result", {}).get("message_id") if ok else None
    return {"ok": bool(ok), "id": msg_id,
            "error": None if ok else str(body)[:200]}
