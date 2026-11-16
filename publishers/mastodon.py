"""Mastodon publisher. Free, no review, works on any instance."""
from pathlib import Path

from core import config
from core.http import request


def post(post, media, dry_run=False):
    base = config.env("MASTODON_BASE_URL", "https://mastodon.social").rstrip("/")
    token = config.env("MASTODON_TOKEN")
    if not token:
        return {"ok": False, "skipped": True, "error": "MASTODON_TOKEN missing"}
    if dry_run:
        return {"ok": True, "dry_run": True}

    headers = {"Authorization": f"Bearer {token}"}
    text = media["caption"]
    if len(text) > 480:
        text = (media.get("short") or text)[:480]

    media_ids = []
    if media.get("image") and Path(media["image"]).exists():
        _, body = request("POST", f"{base}/api/v2/media", headers=headers,
                          files={"file": media["image"]},
                          data={"description": post["headline"]}, timeout=180)
        mid = body.get("id") if isinstance(body, dict) else None
        if mid:
            media_ids.append(mid)

    payload = {"status": text, "visibility": "public"}
    if media_ids:
        payload["media_ids[]"] = media_ids[0]

    _, body = request("POST", f"{base}/api/v1/statuses", headers=headers, data=payload)
    sid = body.get("id") if isinstance(body, dict) else None
    if not sid:
        return {"ok": False, "error": str(body)[:250]}
    return {"ok": True, "id": sid, "link": body.get("url")}
