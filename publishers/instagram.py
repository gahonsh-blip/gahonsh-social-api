"""Instagram business publisher.

Reels need a public video URL and feed images a public image URL, so
core.host.upload() must be configured (GitHub Pages works and costs nothing).
"""
import time

from core import config
from core.http import request

GRAPH = "https://graph.facebook.com/v23.0"


def _wait(container_id, token, tries=30):
    for _ in range(tries):
        _, body = request("GET", f"{GRAPH}/{container_id}?fields=status_code&access_token={token}")
        code = body.get("status_code") if isinstance(body, dict) else None
        if code == "FINISHED":
            return True
        if code == "ERROR":
            return False
        time.sleep(6)
    return False


def post(post, media, dry_run=False):
    token = config.env("META_PAGE_TOKEN")
    ig_id = config.env("META_IG_ID")
    if not (token and ig_id):
        return {"ok": False, "skipped": True, "error": "META_PAGE_TOKEN / META_IG_ID missing"}
    if dry_run:
        return {"ok": True, "dry_run": True}

    if media.get("video_url"):
        params = {"media_type": "REELS", "video_url": media["video_url"],
                  "caption": media["caption"], "share_to_feed": "true",
                  "access_token": token}
    elif media.get("image_url"):
        params = {"image_url": media["image_url"], "caption": media["caption"],
                  "access_token": token}
    else:
        return {"ok": False, "skipped": True,
                "error": "Instagram needs a public media URL (set GITHUB_TOKEN, GITHUB_REPO, GITHUB_PAGES_URL)"}

    _, body = request("POST", f"{GRAPH}/{ig_id}/media", data=params)
    cid = body.get("id") if isinstance(body, dict) else None
    if not cid:
        return {"ok": False, "error": str(body)[:250]}

    if not _wait(cid, token):
        return {"ok": False, "error": "media container did not finish processing"}

    _, pub = request("POST", f"{GRAPH}/{ig_id}/media_publish",
                     data={"creation_id": cid, "access_token": token})
    mid = pub.get("id") if isinstance(pub, dict) else None
    if not mid:
        return {"ok": False, "error": str(pub)[:250]}

    _, info = request("GET", f"{GRAPH}/{mid}?fields=permalink&access_token={token}")
    link = info.get("permalink") if isinstance(info, dict) else None
    return {"ok": True, "id": mid, "link": link}
