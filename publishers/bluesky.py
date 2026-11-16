"""Bluesky publisher (AT Protocol). Free, no review, needs an app password."""
import json
import mimetypes
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from core import config
from core.http import request

BASE = "https://bsky.social/xrpc"


def _session():
    handle = config.env("BLUESKY_HANDLE")
    password = config.env("BLUESKY_APP_PASSWORD")
    if not (handle and password):
        return None
    _, body = request("POST", f"{BASE}/com.atproto.server.createSession",
                      json_body={"identifier": handle, "password": password})
    if isinstance(body, dict) and body.get("accessJwt"):
        return {"jwt": body["accessJwt"], "did": body["did"]}
    return None


def _upload_blob(path, jwt, ctype):
    req = urllib.request.Request(
        f"{BASE}/com.atproto.repo.uploadBlob",
        data=Path(path).read_bytes(), method="POST",
        headers={"Authorization": f"Bearer {jwt}", "Content-Type": ctype},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode()).get("blob")
    except Exception:
        return None


def _facets(text):
    out = []
    for m in re.finditer(r"https?://\S+", text):
        out.append({
            "index": {"byteStart": len(text[:m.start()].encode()),
                      "byteEnd": len(text[:m.end()].encode())},
            "features": [{"$type": "app.bsky.richtext.facet#link", "uri": m.group(0)}],
        })
    return out


def post(post, media, dry_run=False):
    session = _session()
    if not session:
        return {"ok": False, "skipped": True,
                "error": "BLUESKY_HANDLE / BLUESKY_APP_PASSWORD missing or not accepted"}
    if dry_run:
        return {"ok": True, "dry_run": True}

    text = media.get("short") or media["caption"]
    if len(text) > 290:
        text = text[:287] + "..."
    text = text.replace("https://gahonsh-blip.github.io", "gahonsh-blip.github.io")

    record = {
        "$type": "app.bsky.feed.post",
        "text": text,
        "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "facets": _facets(text),
    }
    if media.get("image"):
        path = Path(media["image"])
        ctype = mimetypes.guess_type(path.name)[0] or "image/jpeg"
        blob = _upload_blob(path, session["jwt"], ctype)
        if blob:
            record["embed"] = {"$type": "app.bsky.embed.images",
                               "images": [{"alt": post["headline"], "image": blob}]}

    _, body = request("POST", f"{BASE}/com.atproto.repo.createRecord",
                      headers={"Authorization": f"Bearer {session['jwt']}"},
                      json_body={"repo": session["did"],
                                 "collection": "app.bsky.feed.post",
                                 "record": record})
    uri = body.get("uri") if isinstance(body, dict) else None
    if not uri:
        return {"ok": False, "error": str(body)[:250]}
    return {"ok": True, "id": uri,
            "link": f"https://bsky.app/profile/{config.env('BLUESKY_HANDLE')}/post/{uri.rsplit('/', 1)[-1]}"}
