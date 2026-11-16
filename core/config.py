"""Config loading for the GAHONSH social autopilot.

Everything comes from environment variables, optionally seeded from a .env file
next to the project root (or /app/.agents/.env when running inside Base44).
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_CANDIDATES = [
    ROOT / ".env",
    Path("/app/.agents/.env"),
]

# Which platforms are enabled by default (comma separated in CHANNELS).
DEFAULT_CHANNELS = "facebook,instagram,telegram,bluesky,mastodon,devto"

# Platforms this project can publish to.
KNOWN_CHANNELS = [
    "facebook",   # Facebook Page (image or video)
    "instagram",  # Instagram business (image or reel)
    "youtube",    # Shorts via OAuth refresh token
    "linkedin",   # personal profile or company page via OAuth
    "telegram",   # bot channel/group
    "bluesky",    # AT protocol
    "mastodon",   # any instance
    "x",          # X / Twitter API v2
    "devto",      # dev.to article
    "blogger",    # Blogger blog post
]


def load_env():
    for path in ENV_CANDIDATES:
        if not path.exists():
            continue
        for raw in path.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val
    return os.environ


def env(key, default=""):
    return os.environ.get(key, default).strip()


def enabled_channels(only=None):
    if only:
        return [c.strip().lower() for c in only.split(",") if c.strip()]
    return [c.strip().lower() for c in env("CHANNELS", DEFAULT_CHANNELS).split(",") if c.strip()]


def has(*keys):
    return all(env(k) for k in keys)
