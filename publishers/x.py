"""X (Twitter) publisher: API v2 text post with OAuth 1.0a user context.

Free tier allows a limited number of writes per month, which is plenty for one
post a day. Media upload needs the v1.1 endpoint, so posts are text plus link.
"""
import base64
import hashlib
import hmac
import time
import urllib.parse

from core import config
from core.http import request


def _oauth_header(method, url, params):
    key = config.env("X_API_KEY")
    secret = config.env("X_API_SECRET")
    token = config.env("X_ACCESS_TOKEN")
    token_secret = config.env("X_ACCESS_SECRET")
    if not all([key, secret, token, token_secret]):
        return None

    oauth = {
        "oauth_consumer_key": key,
        "oauth_nonce": base64.b16encode(str(time.time_ns()).encode()).decode().lower()[:32],
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": token,
        "oauth_version": "1.0",
    }
    encoded = "&".join(
        f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(str(oauth[k]), safe='')}"
        for k in sorted(oauth)
    )
    base = f"{method}&{urllib.parse.quote(url, safe='')}&{urllib.parse.quote(encoded, safe='')}"
    signing_key = f"{urllib.parse.quote(secret, safe='')}&{urllib.parse.quote(token_secret, safe='')}"
    digest = hmac.new(signing_key.encode(), base.encode(), hashlib.sha1).digest()
    oauth["oauth_signature"] = base64.b64encode(digest).decode()
    return "OAuth " + ", ".join(
        f'{urllib.parse.quote(k, safe="")}="{urllib.parse.quote(str(v), safe="")}"'
        for k, v in sorted(oauth.items())
    )


def post(post, media, dry_run=False):
    url = "https://api.twitter.com/2/tweets"
    header = _oauth_header("POST", url, {})
    if not header:
        return {"ok": False, "skipped": True, "error": "X_API_KEY / X_API_SECRET / X_ACCESS_TOKEN / X_ACCESS_SECRET missing"}
    if dry_run:
        return {"ok": True, "dry_run": True}

    text = media.get("short") or media["caption"]
    if len(text) > 275:
        text = text[:272] + "..."
    status, body = request("POST", url, json_body={"text": text},
                           headers={"Authorization": header})
    tid = (body or {}).get("data", {}).get("id") if isinstance(body, dict) else None
    if not tid:
        return {"ok": False, "error": str(body)[:250]}
    return {"ok": True, "id": tid, "link": f"https://x.com/i/web/status/{tid}"}
