#!/usr/bin/env python3
"""One-time OAuth helper for LinkedIn and Google (YouTube / Blogger).

Both providers have no free server to receive the callback, so this uses the
"out of band" trick: you approve in a browser, the browser lands on a link that
does not open, and you paste that whole link back here. The code is inside it.

  python3 auth/oauth_paste.py linkedin
  python3 auth/oauth_paste.py google

On success the tokens are appended to .env (and printed for reference).
LinkedIn tokens last 60 days; the script also writes LINKEDIN_REFRESH_TOKEN when
LinkedIn returns one. Google refresh tokens do not expire while the app stays
in production.
"""
import base64
import hashlib
import json
import os
import secrets
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"

PROVIDERS = {
    "linkedin": {
        "auth": "https://www.linkedin.com/oauth/v2/authorization",
        "token": "https://www.linkedin.com/oauth/v2/accessToken",
        "scopes": "openid profile w_member_social w_organization_social r_organization_admin",
        "client_id": "LINKEDIN_CLIENT_ID",
        "client_secret": "LINKEDIN_CLIENT_SECRET",
        "redirect": "LINKEDIN_REDIRECT_URI",
        "default_redirect": "http://localhost:8080/callback",
        "env_key": "LINKEDIN_ACCESS_TOKEN",
        "pkce": False,
    },
    "google": {
        "auth": "https://accounts.google.com/o/oauth2/v2/auth",
        "token": "https://oauth2.googleapis.com/token",
        "scopes": ("https://www.googleapis.com/auth/youtube.upload "
                   "https://www.googleapis.com/auth/blogger"),
        "client_id": "GOOGLE_CLIENT_ID",
        "client_secret": "GOOGLE_CLIENT_SECRET",
        "redirect": "GOOGLE_REDIRECT_URI",
        "default_redirect": "http://localhost:8080/callback",
        "env_key": "GOOGLE_REFRESH_TOKEN",
        "pkce": True,
    },
}


def load_env():
    if not ENV_PATH.exists():
        return
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def save_env(pairs):
    lines = ENV_PATH.read_text().splitlines() if ENV_PATH.exists() else []
    existing = {l.split("=", 1)[0].strip() for l in lines if "=" in l and not l.strip().startswith("#")}
    for k, v in pairs.items():
        line = f"{k}={v}"
        if k in existing:
            lines = [line if (l.split("=", 1)[0].strip() == k and "=" in l) else l for l in lines]
        else:
            lines.append(line)
    ENV_PATH.write_text("\n".join(lines) + "\n")


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "linkedin"
    provider = PROVIDERS.get(name)
    if not provider:
        print("usage: python3 auth/oauth_paste.py [linkedin|google]")
        return

    load_env()
    client_id = os.environ.get(provider["client_id"], "").strip()
    client_secret = os.environ.get(provider["client_secret"], "").strip()
    redirect = os.environ.get(provider["redirect"], provider["default_redirect"]).strip()
    if not client_id:
        print(f"Set {provider['client_id']} in .env first.")
        return

    state = secrets.token_urlsafe(12)
    params = {
        "client_id": client_id,
        "redirect_uri": redirect,
        "response_type": "code",
        "scope": provider["scopes"],
        "state": state,
    }
    extra = {}
    if provider["pkce"]:
        verifier = secrets.token_urlsafe(64)
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode()).digest()
        ).decode().rstrip("=")
        params.update({"code_challenge": challenge, "code_challenge_method": "S256",
                       "access_type": "offline", "prompt": "consent"})
        extra["code_verifier"] = verifier

    url = provider["auth"] + "?" + urllib.parse.urlencode(params)
    print("\n1. Open this in a browser where you are logged in:\n")
    print(url)
    print("\n2. Approve. The browser will try to open a localhost link and fail. That is expected.")
    print("3. Copy that whole failing link and paste it here.\n")
    pasted = input("redirect link: ").strip()
    if not pasted:
        print("nothing pasted, stopping.")
        return

    query = urllib.parse.parse_qs(urllib.parse.urlparse(pasted).query)
    if "code" not in query:
        print("no code in that link. Raw query was:", query)
        return
    if query.get("state", [state])[0] != state:
        print("state mismatch, stopping for safety.")
        return

    data = {
        "grant_type": "authorization_code",
        "code": query["code"][0],
        "redirect_uri": redirect,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    if extra.get("code_verifier"):
        data["code_verifier"] = extra["code_verifier"]

    req = urllib.request.Request(
        provider["token"],
        data=urllib.parse.urlencode(data).encode(),
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        body = json.loads(r.read().decode())

    pairs = {}
    if name == "linkedin":
        if body.get("access_token"):
            pairs["LINKEDIN_ACCESS_TOKEN"] = body["access_token"]
        if body.get("refresh_token"):
            pairs["LINKEDIN_REFRESH_TOKEN"] = body["refresh_token"]
    else:
        if body.get("refresh_token"):
            pairs["GOOGLE_REFRESH_TOKEN"] = body["refresh_token"]
        for key in ("YOUTUBE_REFRESH_TOKEN",):
            if body.get("refresh_token"):
                pairs[key] = body["refresh_token"]

    if not pairs:
        print("token exchange did not return what we needed:", body)
        return
    save_env(pairs)
    print("\nsaved:", ", ".join(pairs))
    print("expires_in:", body.get("expires_in"))


if __name__ == "__main__":
    main()
