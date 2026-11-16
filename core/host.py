"""Public hosting for media that platforms insist on fetching by URL.

Instagram (reels/carousel) and YouTube thumbnails need a public https URL.
This uploads the file into a GitHub Pages repo and returns the Pages URL, so it
costs nothing and never expires.

Needs: GITHUB_TOKEN (repo scope), GITHUB_REPO (owner/name), GITHUB_BRANCH,
and GITHUB_PAGES_URL (e.g. https://owner.github.io/repo).
"""
import base64
from pathlib import Path

from . import config
from .http import request


def upload(path, remote_dir="media"):
    """Upload a file, return its public URL or None."""
    token = config.env("GITHUB_TOKEN")
    repo = config.env("GITHUB_REPO")
    branch = config.env("GITHUB_BRANCH", "main")
    base = config.env("GITHUB_PAGES_URL")
    if not (token and repo and base):
        return None

    path = Path(path)
    name = f"{path.stem}-{int(path.stat().st_mtime)}-{abs(hash(path.name)) % 10000}{path.suffix}"
    remote = f"{remote_dir.strip('/')}/{name}"
    api = f"https://api.github.com/repos/{repo}/contents/{remote}"
    payload = {
        "message": f"media: {remote}",
        "content": base64.b64encode(path.read_bytes()).decode(),
        "branch": branch,
    }
    status, body = request("PUT", api, json_body=payload,
                           headers={"Authorization": f"Bearer {token}",
                                    "Accept": "application/vnd.github+json"})
    if status in (200, 201):
        # GitHub Pages serves the branch; raw URLs are a reliable fallback.
        return f"{base.rstrip('/')}/{remote}"
    if status == 422:  # already exists, same bytes
        return f"{base.rstrip('/')}/{remote}"
    return None
