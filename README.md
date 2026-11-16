# GAHONSH social autopilot

One command builds the day's post and publishes it everywhere:

```
content calendar -> free AI artwork -> free AI voice -> 20s vertical Short
                                   -> Facebook, Instagram, LinkedIn, YouTube,
                                      Telegram, Bluesky, Mastodon, X, dev.to, Blogger
```

Nothing is scheduled inside this repo by default: a single daily trigger
(GitHub Actions cron at 03:00 UTC = 08:30 IST, or the Base44 workflow) runs
`social.py` once. A channel that already has the day's post is skipped, so a
retry can never double-post.

## Quick start

```bash
pip install -r requirements.txt          # Pillow, requests, edge-tts
apt-get install -y ffmpeg                # already present on GitHub runners

cp .env.example .env                     # fill the keys you have
python3 social.py --doctor               # which channels are ready
python3 social.py --dry-run              # build the post + Short, publish nothing
python3 social.py                        # publish today
```

Useful flags

```
--date 2026-11-17     a specific day
--only facebook,ig    just these channels
--no-video            image post only (faster, no Short)
--no-ai               skip the free AI artwork, use the branded gradient card
--ai                  let a free text model rewrite the caption
--doctor              show which keys are configured
```

## Layout

```
social.py                entry point and CLI
core/config.py           env loading, channel list
core/content.py          the content calendar (weekday rhythm + content_plan.json)
core/image.py            Pollinations AI art + branded overlay
core/voice.py            edge-tts narration
core/video.py            ffmpeg assembly -> 1080x1920 Short
core/host.py             free public hosting (GitHub Pages) for IG/Reels media
core/state.py            per-day idempotency log
publishers/*.py          one file per platform
auth/oauth_paste.py      one-time LinkedIn / Google OAuth without a server
.github/workflows/daily.yml   the daily trigger
docs/KEYS.md             where every key comes from, with costs
```

## Editing the calendar

`core/content.py` rotates a weekday rhythm. Add a dated override in
`content_plan.json`:

```json
{
  "days": {
    "2026-11-17": {
      "headline": "A property site where enquiries actually arrive",
      "body": "Floor plans, gallery, price list and one WhatsApp button.",
      "prompt": "modern apartment building, golden hour, architectural photo"
    }
  }
}
```

Same date always produces the same post, which is what makes retries safe.

## Cost

Zero. Free AI image model, free TTS, ffmpeg, and free posting endpoints. The
only paid thing anywhere near this project is X's paid tier, which is optional
(the free tier allows 500 posts a month).
