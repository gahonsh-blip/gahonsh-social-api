"""Free text-to-speech with edge-tts (no key, no cost)."""
from pathlib import Path

VOICES = {
    "en": "en-IN-NeerjaNeural",
    "hi": "hi-IN-SwaraNeural",
    "en-male": "en-IN-PrabhatNeural",
}


async def _save(text, voice, out_path):
    import edge_tts

    communicate = edge_tts.Communicate(text, voice, rate="+4%")
    await communicate.save(str(out_path))


def speak(text, out_path, lang="en"):
    """Render speech to an mp3. Returns path or None."""
    import asyncio

    out_path = Path(out_path)
    voice = VOICES.get(lang, VOICES["en"])
    try:
        asyncio.run(_save(text, voice, out_path))
    except Exception:
        try:
            asyncio.run(_save(text, voice, out_path))
        except Exception:
            return None
    return str(out_path) if out_path.exists() and out_path.stat().st_size > 2000 else None
