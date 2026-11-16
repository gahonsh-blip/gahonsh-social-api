"""Publisher registry. Each module exposes post(post, media, dry_run)."""
from . import (blogger, bluesky, devto, facebook, instagram, linkedin,
               mastodon, telegram, x, youtube)

REGISTRY = {
    "facebook": facebook.post,
    "instagram": instagram.post,
    "youtube": youtube.post,
    "linkedin": linkedin.post,
    "telegram": telegram.post,
    "bluesky": bluesky.post,
    "mastodon": mastodon.post,
    "x": x.post,
    "devto": devto.post,
    "blogger": blogger.post,
}
