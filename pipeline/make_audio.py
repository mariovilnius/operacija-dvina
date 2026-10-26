"""Generates narration MP3s with Microsoft neural voices into app/audio/<lang>/.

Two backends with the same voices:
- Azure AI Speech (official) when AZURE_SPEECH_KEY and AZURE_SPEECH_REGION are set;
- otherwise edge-tts (pip install edge-tts), the Edge read-aloud service. No account is needed,
  but it is meant for the browser: fine for the hackathon demo, not for production.

Usage: python make_audio.py lt en        (no arguments: all languages)
Existing files are skipped, so a rerun only fills gaps. Run build_app_data.py afterwards.
"""
import asyncio
import os
import re
import sys
import time
import urllib.error
import urllib.request
from xml.sax.saxutils import escape

from build_app_data import cards, episodes, missions
from paths import ROOT

sys.stdout.reconfigure(encoding="utf-8")

VOICES = {
    "lt": ("lt-LT", "lt-LT-LeonasNeural"), "en": ("en-GB", "en-GB-RyanNeural"), "de": ("de-DE", "de-DE-ConradNeural"),
    "es": ("es-ES", "es-ES-AlvaroNeural"), "pt": ("pt-PT", "pt-PT-DuarteNeural"), "pl": ("pl-PL", "pl-PL-MarekNeural"),
    "lv": ("lv-LV", "lv-LV-NilsNeural"), "ru": ("ru-RU", "ru-RU-DmitryNeural"), "uk": ("uk-UA", "uk-UA-OstapNeural"),
    "zh": ("zh-CN", "zh-CN-YunxiNeural"), "ja": ("ja-JP", "ja-JP-KeitaNeural"),
}
AUDIO = ROOT / "app" / "audio"
CONTENT = ROOT / "content"


def spoken_form(lang: str, text: str) -> str:
    """Drops source tags and applies the language's pronunciation rules (content/speech.<lang>.json)."""
    text = re.sub(r"\s*\[[ST]\d\]", "", text)
    rules = CONTENT / f"speech.{lang}.json"
    if rules.exists():
        import json
        for pattern, repl in json.loads(rules.read_text(encoding="utf-8"))["rules"]:
            text = re.sub(pattern, repl, text)
    return text
AZURE_KEY, AZURE_REGION = os.environ.get("AZURE_SPEECH_KEY"), os.environ.get("AZURE_SPEECH_REGION")


def clips(lang: str):
    """Every narrated text: episode scripts, mission stories and card reveals."""
    for e in episodes:
        yield f"episode-{e['n']}", e["text"][lang]["script"]
    for m in missions:
        yield f"mission-{m['n']}", m["text"][lang]["story"]
    for c in cards:
        yield f"card-{c['id']}", c["text"][lang]["reveal"]


def azure(lang: str, text: str) -> bytes:
    locale, voice = VOICES[lang]
    ssml = f'<speak version="1.0" xml:lang="{locale}"><voice name="{voice}">{escape(text)}</voice></speak>'
    req = urllib.request.Request(f"https://{AZURE_REGION}.tts.speech.microsoft.com/cognitiveservices/v1",
                                 data=ssml.encode("utf-8"), headers={
        "Ocp-Apim-Subscription-Key": AZURE_KEY,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3",
        "User-Agent": "operacija-dvina",
    })
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code != 429:  # anything but the free tier's rate limit is fatal
                raise
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("rate limited")


async def edge(lang: str, text: str) -> bytes:
    import edge_tts

    chunks = []
    async for chunk in edge_tts.Communicate(text, VOICES[lang][1]).stream():
        if chunk["type"] == "audio":
            chunks.append(chunk["data"])
    return b"".join(chunks)


async def main(langs: list[str]) -> None:
    backend = "Azure AI Speech" if AZURE_KEY and AZURE_REGION else "edge-tts"
    gate = asyncio.Semaphore(4)
    made, chars = 0, 0

    async def one(lang: str, name: str, text: str) -> None:
        nonlocal made, chars
        out = AUDIO / lang / f"{name}.mp3"
        if out.exists():
            return
        spoken = spoken_form(lang, text)
        async with gate:
            for attempt in range(3):
                try:
                    audio = await (asyncio.to_thread(azure, lang, spoken) if backend == "Azure AI Speech" else edge(lang, spoken))
                    if not audio:
                        raise RuntimeError("empty audio")
                    out.parent.mkdir(parents=True, exist_ok=True)
                    out.write_bytes(audio)
                    made, chars = made + 1, chars + len(spoken)
                    return
                except Exception as e:  # network hiccups: retry, then report and move on
                    if attempt == 2:
                        print("FAILED", lang, name, e)
                    await asyncio.sleep(2 * (attempt + 1))

    await asyncio.gather(*(one(lang, name, text) for lang in langs for name, text in clips(lang)))
    print(f"{backend}: {made} new clips, {chars} characters, languages {', '.join(langs)}")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:] or list(VOICES)))
