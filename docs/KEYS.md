# API keys: where each one comes from, and what it costs

Everything below can be done once, from a phone. Nothing here needs a paid plan.

| Channel | What you need | Where to get it | Cost | Time |
|---|---|---|---|---|
| Telegram | bot token + chat id | Telegram, `@BotFather` -> `/newbot` -> copy token. Then add the bot to your channel/group as admin and read the chat id from `@RawDataBot` or the `getUpdates` URL | free, unlimited | 3 min |
| Bluesky | handle + app password | bsky.app -> Settings -> Privacy and security -> App passwords -> Add | free | 2 min |
| Mastodon | access token | mastodon.social -> Preferences -> Development -> New application -> tick `write:statuses`, `write:media` -> copy access token | free | 5 min |
| dev.to | API key | dev.to -> Settings -> Extensions -> DEV Community API Keys -> Generate | free | 2 min |
| Facebook Page | Page token | already working: `META_PAGE_TOKEN`, `META_PAGE_ID` in `.agents/.env` | free | done |
| Instagram | same Page token | already working: `META_IG_ID` | free | done |
| X / Twitter | API key, secret, access token, access secret | developer.x.com -> Project -> App -> Keys and tokens -> generate (needs a free developer account) | free tier: 500 posts/month | 10 min |
| LinkedIn | access token | linkedin.com/developers -> Create app -> add "Sign In with LinkedIn" + "Share on LinkedIn" products -> put the client id/secret in `.env` -> run `python3 auth/oauth_paste.py linkedin` | free | 10 min |
| YouTube Shorts | Google client id, secret, refresh token | console.cloud.google.com -> project -> enable "YouTube Data API v3" -> OAuth consent screen -> Credentials -> OAuth client (Web) with redirect `http://localhost:8080/callback` -> `python3 auth/oauth_paste.py google` | free | 15 min |
| Blogger | same Google credentials + blog id | enable "Blogger API v3" in the same project; blog id is in the Blogger URL (`blogID=...`) | free | included |
| Media hosting (Instagram needs a public URL) | GitHub token with repo scope | github.com -> Settings -> Developer settings -> Personal access tokens (classic) -> `repo` | free | 3 min |

## Where the free AI video comes from

There is no AI video service that gives 2-3 free videos a day *and* an API, so
this project does the next best thing, which is free and unlimited:

1. artwork: Pollinations free image model, no key (`core/image.py`)
2. voice: Microsoft edge-tts, no key (`core/voice.py`)
3. assembly: ffmpeg zoom + narration (`core/video.py`)

Result: one 1080x1920 Short with an Indian English voice, about 20 seconds,
1.5 MB, built in under 10 seconds. If you ever want a real generative-video
model later, only `core/video.py` needs to change; every publisher already
takes a `video` file or `video_url`.

## Free tier reality check

- X free tier: 500 posts a month (one a day is 30).
- Instagram/Facebook: free, and the Page token we saved never expires.
- YouTube: the API upload itself is free, but while the Google Cloud project is
  unverified, uploads from it are locked to *private*. The owner's own Apps
  Script (Google account) is the only free route that publishes public Shorts.
- LinkedIn: free, no per-post charge.
