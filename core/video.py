"""Turns the day's post into a vertical Short (1080x1920, H.264 + AAC).

No paid service is involved: artwork is free AI, voice is free edge-tts, and
ffmpeg does the assembly. Output plays on YouTube Shorts, Instagram Reels and
Facebook Reels.
"""
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from . import image as image_mod
from . import voice as voice_mod

FONT_BOLD = image_mod.FONT_BOLD
FONT_REG = image_mod.FONT_REG


def _probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True,
    )
    try:
        return float(out.stdout.strip())
    except Exception:
        return 0.0


def _wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def _text_card(post, out_path, cta=False):
    W, H = 1080, 1920
    if cta:
        img = Image.new("RGB", (W, H), image_mod.NAVY)
        d = ImageDraw.Draw(img)
        for y in range(H):
            t = y / H
            col = tuple(int(image_mod.NAVY[i] + (image_mod.TEAL[i] - image_mod.NAVY[i]) * (0.2 + 0.7 * t)) for i in range(3))
            d.line([(0, y), (W, y)], fill=col)
        d.rectangle([0, 0, W, 12], fill=image_mod.AMBER)
        big = ImageFont.truetype(FONT_BOLD, 84)
        mid = ImageFont.truetype(FONT_REG, 46)
        small = ImageFont.truetype(FONT_REG, 38)
        for i, line in enumerate(["Fixed price.", "Fixed date.", "No surprises."]):
            d.text((110, 640 + i * 120), line, font=big, fill=image_mod.INK)
        d.text((110, 1080), "Tell us what you need.", font=mid, fill=(214, 228, 225))
        d.text((110, 1500), "GAHONSH", font=ImageFont.truetype(FONT_BOLD, 66), fill=image_mod.INK)
        d.text((110, 1580), "gahonsh-blip.github.io", font=small, fill=image_mod.AMBER)
        img.save(out_path, "JPEG", quality=90)
        return str(out_path)

    art = image_mod.ai_art(post["image_prompt"], size=(W, H)) or Image.new("RGB", (W, H), image_mod.NAVY)
    img = image_mod._scrim(art, top_alpha=215, bottom_alpha=235)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 12], fill=image_mod.AMBER)
    pad = 90
    size = 92
    font = ImageFont.truetype(FONT_BOLD, size)
    lines = _wrap(d, post["headline"], font, W - 2 * pad)
    while len(lines) > 5 and size > 58:
        size -= 6
        font = ImageFont.truetype(FONT_BOLD, size)
        lines = _wrap(d, post["headline"], font, W - 2 * pad)
    y = 620
    for line in lines:
        d.text((pad, y), line, font=font, fill=image_mod.INK)
        y += int(size * 1.22)
    body_font = ImageFont.truetype(FONT_REG, 44)
    y += 40
    for line in _wrap(d, post["body"], body_font, W - 2 * pad)[:4]:
        d.text((pad, y), line, font=body_font, fill=(214, 228, 225))
        y += 62
    d.text((pad, 1560), "GAHONSH", font=ImageFont.truetype(FONT_BOLD, 62), fill=image_mod.INK)
    d.text((pad, 1640), "gahonsh-blip.github.io", font=ImageFont.truetype(FONT_REG, 36), fill=image_mod.AMBER)
    img.save(out_path, "JPEG", quality=90)
    return str(out_path)


def build(post, out_dir, lang="en", use_ai=True):
    """Render the Short. Returns dict with path, duration and whether audio exists."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    audio = voice_mod.speak(post["voice_script"], out_dir / "voice.mp3", lang=lang) if post.get("voice_script") else None
    dur = _probe_duration(audio) if audio else 0.0
    if dur <= 0:
        dur = 18.0

    main = _text_card(post, out_dir / "frame1.jpg")
    cta = _text_card(post, out_dir / "frame2.jpg", cta=True)
    out_mp4 = out_dir / "short.mp4"

    fps = 30
    half = max(dur * 0.62, 4.0)
    rest = max(dur + 0.8 - half, 3.0)

    filter_complex = (
        f"[0:v]scale=1350:2400,zoompan=z='min(zoom+0.0008,1.12)':d={int(half*fps)}:s=1080x1920:fps={fps},setsar=1[v0];"
        f"[1:v]scale=1350:2400,zoompan=z='min(zoom+0.0008,1.10)':d={int(rest*fps)}:s=1080x1920:fps={fps},setsar=1[v1];"
        f"[v0][v1]concat=n=2:v=1:a=0,fade=t=in:st=0:d=0.6[v]"
    )

    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-loop", "1", "-i", main,
        "-loop", "1", "-i", cta,
    ]
    if audio:
        cmd += ["-i", audio]
    cmd += ["-filter_complex", filter_complex, "-map", "[v]"]
    if audio:
        cmd += ["-map", "2:a", "-c:a", "aac", "-b:a", "128k", "-shortest"]
    cmd += [
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        "-t", f"{dur + 1.0:.2f}", str(out_mp4),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not out_mp4.exists():
        return {"ok": False, "error": (proc.stderr or "ffmpeg failed")[-400:]}

    return {
        "ok": True,
        "path": str(out_mp4),
        "duration": round(_probe_duration(out_mp4), 1),
        "size_kb": round(out_mp4.stat().st_size / 1024),
        "has_voice": bool(audio),
    }
