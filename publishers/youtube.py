"""YouTube Shorts upload with a saved OAuth refresh token.

Create the token once with auth/youtube_oauth.py. Note the Google rule: while
the Cloud project is unverified, uploads from it stay PRIVATE. The owner's own
App Script route (in the previous setup) avoids that, so this publisher is
optional and reports the visibility it asked for.
"""
import json
from pathlib import Path

from core import config
from core.http import request

TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"


def access_token():
    refresh = config.env("YOUTUBE_REFRESH_TOKEN")
    cid = config.env("GOOGLE_CLIENT_ID")
    secret = config.env("GOOGLE_CLIENT_SECRET")
    if not (refresh and cid and secret):
        return None
    status, body = request("POST", TOKEN_URL, data={
        "client_id": cid, "client_secret": secret,
        "refresh_token": refresh, "grant_type": "refresh_token"})
    return (body or {}).get("access_token") if isinstance(body, dict) else None


def post(post, media, dry_run=False):
    if not media.get("video"):
        return {"ok": False, "skipped": True, "error": "no video for YouTube"}
    if dry_run:
        return {"ok": True, "dry_run": True}

    token = access_token()
    if not token:
        return {"ok": False, "skipped": True,
                "error": "YOUTUBE_REFRESH_TOKEN / GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET missing"}

    privacy = config.env("YOUTUBE_PRIVACY", "public")
    meta = {
        "snippet": {
            "title": post["headline"][:95],
            "description": f"{post['body']}\n\n{config.env('SITE_URL', 'https://gahonsh-blip.github.io')}",
            "tags": ["software", "india", "flutter", "nodejs", "freelance"],
            "categoryId": "28",
        },
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False},
    }
    status, res = request(
        "POST", UPLOAD_URL, json_body=meta,
        headers={
            "Authorization": f"Bearer {token}",
            "X-Upload-Content-Type": "video/mp4",
            "X-Upload-Content-Length": str(Path(media["video"]).stat().st_size),
        },
    )
    return {"ok": False, "error": f"resumable init returned {status}; use the Apps Script route or complete OAuth"}


def upload_file(session_uri, video_path, token):
    """PUT the bytes into the resumable session (used once init succeeds)."""
    import urllib.request

    data = Path(video_path).read_bytes()
    req = urllib.request.Request(
        session_uri, data=data, method="PUT",
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "video/mp4",
                 "Content-Length": str(len(data))},
    )
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.loads(r.read().decode())
