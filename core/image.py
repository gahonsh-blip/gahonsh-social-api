"""Free AI artwork + branded overlay.

Artwork comes from Pollinations (free, no key, unlimited-ish). If the network
fails we still ship: a clean branded gradient card is drawn instead.
"""
import io
import random
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

TEAL = (18, 119, 106)
AMBER = (201, 146, 46)
NAVY = (22, 42, 54)
INK = (243, 247, 246)

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def ai_art(prompt, size=(1080, 1350), seed=None, out_path=None):
    """Download free AI art. Returns path, or None on failure."""
    w, h = size
    seed = seed if seed is not None else random.randint(1, 999999)
    q = urllib.parse.quote(prompt + ", no text, no words, no letters", safe="")
    url = (
        f"https://image.pollinations.ai/prompt/{q}"
        f"?width={w}&height={h}&nologo=true&model=flux&seed={seed}"
    )
    try:
        with urllib.request.urlopen(url, timeout=120) as r:
            raw = r.read()
        art = Image.open(io.BytesIO(raw)).convert("RGB")
        # the free model stamps a small watermark near the bottom edge; crop it out
        aw, ah = art.size
        art = art.crop((0, 0, aw, int(ah * 0.93)))
        art = art.resize((w, h), Image.LANCZOS)
        if out_path:
            art.save(out_path, "JPEG", quality=92)
            return str(out_path)
        return art
    except Exception:
        return None


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


def _scrim(img, top_alpha=200, bottom_alpha=225):
    w, h = img.size
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    band = int(h * 0.42)
    for y in range(band):
        a = int(top_alpha * (1 - y / band))
        d.line([(0, y), (w, y)], fill=(10, 24, 30, a))
    for y in range(h - band, h):
        a = int(bottom_alpha * ((y - (h - band)) / band))
        d.line([(0, y), (w, y)], fill=(10, 24, 30, a))
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def card(post, size=(1080, 1350), out_path=None, use_ai=True):
    """Branded post image: AI artwork + headline + brand block."""
    w, h = size
    art = ai_art(post["image_prompt"], size=size) if use_ai else None
    if art is None:
        art = Image.new("RGB", size, NAVY)
        d0 = ImageDraw.Draw(art)
        for y in range(h):
            t = y / h
            col = tuple(int(NAVY[i] + (TEAL[i] - NAVY[i]) * (0.15 + 0.6 * t)) for i in range(3))
            d0.line([(0, y), (w, y)], fill=col)
    img = _scrim(art)
    d = ImageDraw.Draw(img)

    d.rectangle([0, 0, w, 10], fill=AMBER)
    d.rectangle([64, h * 0.30, 76, h * 0.30 + 120], fill=AMBER)

    pad = 80
    max_w = w - 2 * pad
    size_px = int(w * 0.082)
    font = ImageFont.truetype(FONT_BOLD, size_px)
    lines = _wrap(d, post["headline"], font, max_w)
    while len(lines) > 4 and size_px > int(w * 0.05):
        size_px -= 4
        font = ImageFont.truetype(FONT_BOLD, size_px)
        lines = _wrap(d, post["headline"], font, max_w)

    y = int(h * 0.30) + 30
    for line in lines:
        d.text((pad + 40, y), line, font=font, fill=INK)
        y += int(size_px * 1.24)

    sub_font = ImageFont.truetype(FONT_REG, int(w * 0.034))
    body_lines = _wrap(d, post["body"], sub_font, max_w)[:3]
    y += 18
    for line in body_lines:
        d.text((pad + 40, y), line, font=sub_font, fill=(214, 228, 225))
        y += int(w * 0.048)

    brand_font = ImageFont.truetype(FONT_BOLD, int(w * 0.046))
    small_font = ImageFont.truetype(FONT_REG, int(w * 0.030))
    d.text((pad, h - 210), "GAHONSH", font=brand_font, fill=INK)
    d.text((pad, h - 148), "gahonsh-blip.github.io", font=small_font, fill=AMBER)
    d.text((pad, h - 100), f"Bundu, Ranchi  ·  {post['date']}", font=small_font, fill=(168, 192, 189))

    if out_path:
        img.save(out_path, "JPEG", quality=90)
        return str(out_path)
    return img


def vertical_frame(post, size=(1080, 1920), use_ai=True):
    """Background artwork for a vertical Short / Reel."""
    w, h = size
    art = ai_art(post["image_prompt"], size=size) if use_ai else None
    if art is None:
        art = Image.new("RGB", size, NAVY)
        d0 = ImageDraw.Draw(art)
        for y in range(h):
            t = y / h
            col = tuple(int(NAVY[i] + (TEAL[i] - NAVY[i]) * (0.1 + 0.6 * t)) for i in range(3))
            d0.line([(0, y), (w, y)], fill=col)
    img = _scrim(art, top_alpha=150, bottom_alpha=200)
    return img.filter(ImageFilter.GaussianBlur(0.4))
