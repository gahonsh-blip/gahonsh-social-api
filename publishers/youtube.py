"""YouTube Shorts, the route that actually publishes publicly for free.

The YouTube Data API from an unverified Google Cloud project can only upload
private videos, so this publisher does not touch the API. Instead it uploads the
Short to public hosting and refreshes https://gahonsh-blip.github.io/social/daily.json,
which the owner's own Google Apps Script reads once a day and uploads as a
public Short. Nothing here needs a password.

Needs: GITHUB_TOKEN (repo scope, can write gahonsh-blip.github.io),
      MEDIA_HOST_REPO for the video (defaults to this project's own Pages repo).
"""
import base64
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core import config, host
from core.http import request

MANIFEST_REPO = "gahonsh-blip/gahonsh-blip.github.io"
MANIFEST_PATH = "social/daily.json"
MANIFEST_URL = "https://gahonsh-blip.github.io/social/daily.json"
IST = timezone(timedelta(hours=5, minutes=30))


def _put_manifest(token, payload):
    api = f"https://api.github.com/repos/{MANIFEST_REPO}/contents/{MANIFEST_PATH}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    _, cur = request("GET", api, headers=headers)
    body = dict(payload)
    body["message"] = f"social: daily Short {payload.get('date')}"
    body["content"] = base64.b64encode(
        (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode()
    ).decode()
    if isinstance(cur, dict) and cur.get("sha"):
        body["sha"] = cur["sha"]
    return request("PUT", api, json_body=body, headers=headers)


def post(post, media, dry_run=False):
    if not media.get("video"):
        return {"ok": False, "skipped": True, "error": "no video rendered"}
    if dry_run:
        return {"ok": True, "dry_run": True}

    token = config.env("GITHUB_TOKEN")
    if not token:
        return {"ok": False, "skipped": True, "error": "GITHUB_TOKEN missing (needed to refresh the manifest)"}

    video_url = media.get("video_url") or host.upload(media["video"], remote_dir="media")
    if not video_url:
        return {"ok": False, "error": "could not host the Short publicly (set GITHUB_REPO / GITHUB_PAGES_URL)"}

    manifest = {
        "date": post["date"],
        "title": post["headline"][:95],
        "description": f"{post['body']}\n\n{config.env('SITE_URL', 'https://gahonsh-blip.github.io')}",
        "tags": ["software", "india", "flutter", "nodejs", "freelance"],
        "video_url": video_url,
        "duration_seconds": media.get("duration"),
        "updated": datetime.now(IST).isoformat(timespec="seconds"),
    }
    status, body = _put_manifest(token, manifest)
    if status not in (200, 201):
        return {"ok": False, "error": f"manifest update {status}: {str(body)[:180]}"}
    return {"ok": True, "link": MANIFEST_URL, "note": "queued for the owner's Apps Script upload"}
