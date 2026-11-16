"""Facebook Page publisher (Graph API). Photo post, or video post when a Short exists."""
from core import config
from core.http import request

GRAPH = "https://graph.facebook.com/v23.0"


def post(post, media, dry_run=False):
    token = config.env("META_PAGE_TOKEN")
    page_id = config.env("META_PAGE_ID")
    if not (token and page_id):
        return {"ok": False, "skipped": True, "error": "META_PAGE_TOKEN / META_PAGE_ID missing"}
    if dry_run:
        return {"ok": True, "dry_run": True}

    if media.get("video"):
        status, body = request(
            "POST", f"{GRAPH}/{page_id}/videos",
            data={"description": media["caption"], "access_token": token},
            files={"source": media["video"]}, timeout=300,
        )
    elif media.get("image_url"):
        status, body = request(
            "POST", f"{GRAPH}/{page_id}/photos",
            data={"url": media["image_url"], "message": media["caption"], "access_token": token},
        )
    elif media.get("image"):
        status, body = request(
            "POST", f"{GRAPH}/{page_id}/photos",
            data={"message": media["caption"], "access_token": token},
            files={"source": media["image"]}, timeout=180,
        )
    else:
        return {"ok": False, "error": "no media"}

    if not isinstance(body, dict):
        return {"ok": False, "error": str(body)[:200]}
    if body.get("error"):
        return {"ok": False, "error": body["error"].get("message", "graph error")}
    pid = body.get("post_id") or body.get("id")
    return {"ok": bool(pid), "id": pid,
            "link": f"https://www.facebook.com/{pid}" if pid else None}
