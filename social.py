#!/usr/bin/env python3
"""GAHONSH social autopilot - one command, every platform.

  python3 social.py                 today (Asia/Kolkata), all enabled channels
  python3 social.py --date 2026-11-17
  python3 social.py --dry-run       build the post and media, publish nothing
  python3 social.py --only facebook,telegram
  python3 social.py --no-video      image post only (faster)
  python3 social.py --doctor        show which channels have keys
  python3 social.py --ai            let a free AI model rewrite the caption

Prints one JSON line at the end so a workflow or cron job can read the result.
"""
import argparse
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core import config, content, host, image, state, video  # noqa: E402
from publishers import REGISTRY  # noqa: E402

IST = timezone(timedelta(hours=5, minutes=30))
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"

KEYS = {
    "facebook": ["META_PAGE_TOKEN", "META_PAGE_ID"],
    "instagram": ["META_PAGE_TOKEN", "META_IG_ID"],
    "youtube": ["YOUTUBE_REFRESH_TOKEN", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"],
    "linkedin": ["LINKEDIN_ACCESS_TOKEN"],
    "telegram": ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"],
    "bluesky": ["BLUESKY_HANDLE", "BLUESKY_APP_PASSWORD"],
    "mastodon": ["MASTODON_TOKEN"],
    "x": ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET"],
    "devto": ["DEVTO_API_KEY"],
    "blogger": ["BLOGGER_BLOG_ID", "GOOGLE_REFRESH_TOKEN"],
}


def doctor():
    print(f"{'channel':10} {'keys':6} ready")
    for name, keys in KEYS.items():
        ready = config.has(*keys)
        print(f"{name:10} {'ok' if ready else 'MISS':6} {'yes' if ready else 'no'}")
    print(f"\nmedia hosting (needed by Instagram): {'ok' if config.has('GITHUB_TOKEN', 'GITHUB_REPO', 'GITHUB_PAGES_URL') else 'MISS'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date")
    ap.add_argument("--only")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-video", action="store_true")
    ap.add_argument("--no-ai", action="store_true")
    ap.add_argument("--ai", action="store_true", help="let the free AI model rewrite the caption")
    ap.add_argument("--lang", default="en")
    ap.add_argument("--doctor", action="store_true")
    args = ap.parse_args()

    config.load_env()
    if args.doctor:
        doctor()
        return

    day = date.fromisoformat(args.date) if args.date else datetime.now(IST).date()
    day_str = day.isoformat()
    channels = config.enabled_channels(args.only)

    post = content.build_post(day, ai_write=args.ai)
    OUT.mkdir(parents=True, exist_ok=True)
    work = OUT / day_str
    work.mkdir(parents=True, exist_ok=True)

    media = {"caption": post["caption"], "short": post["short"]}
    card_path = image.card(post, out_path=work / "card.jpg", use_ai=not args.no_ai)
    media["image"] = card_path
    print(f"card: {card_path}", file=sys.stderr)

    if not args.no_video:
        clip = video.build(post, work, lang=args.lang, use_ai=not args.no_ai)
        if clip.get("ok"):
            media["video"] = clip["path"]
            print(f"short: {clip['path']} ({clip['duration']}s, {clip['size_kb']} KB)", file=sys.stderr)
        else:
            print(f"short failed: {clip.get('error')}", file=sys.stderr)

    if not args.dry_run:
        url = host.upload(card_path, remote_dir="media")
        if url:
            media["image_url"] = url
        if media.get("video"):
            vurl = host.upload(media["video"], remote_dir="media")
            if vurl:
                media["video_url"] = vurl

    results = {}
    for channel in channels:
        fn = REGISTRY.get(channel)
        if not fn:
            results[channel] = {"ok": False, "error": "unknown channel"}
            continue
        if not args.dry_run and state.already(day_str, channel):
            results[channel] = {"ok": True, "skipped": True, "reason": "already posted today"}
            continue
        try:
            res = fn(post, media, dry_run=args.dry_run)
        except Exception as e:  # a broken channel must never stop the rest
            res = {"ok": False, "error": f"{type(e).__name__}: {e}"}
        results[channel] = res
        if not args.dry_run:
            state.record(day_str, channel, res)

    summary = {
        "date": day_str,
        "headline": post["headline"],
        "dry_run": args.dry_run,
        "channels": results,
        "ok": sum(1 for r in results.values() if r.get("ok")),
        "failed": sum(1 for r in results.values() if not r.get("ok") and not r.get("skipped")),
    }
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
