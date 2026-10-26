"""Generates narration MP3s with Azure AI Speech neural voices into app/audio/<lang>/.

Needs AZURE_SPEECH_KEY and AZURE_SPEECH_REGION in the environment (never in the repo).
Usage: python make_audio.py lt lv        (no arguments: all languages)
Existing files are skipped, so a rerun only fills gaps. Run build_app_data.py afterwards.
"""
import os
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
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
key, region = os.environ.get("AZURE_SPEECH_KEY"), os.environ.get("AZURE_SPEECH_REGION")
if not key or not region:
    sys.exit("Set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION first.")


def clips(lang: str):
    """Every narrated text: episode scripts, mission stories and card reveals."""
    for e in episodes:
        yield f"episode-{e['n']}", e["text"][lang]["script"]
    for m in missions:
        yield f"mission-{m['n']}", m["text"][lang]["story"]
    for c in cards:
        yield f"card-{c['id']}", c["text"][lang]["reveal"]


def synthesize(job):
    lang, name, text = job
    out = AUDIO / lang / f"{name}.mp3"
    if out.exists():
        return 0
    locale, voice = VOICES[lang]
    spoken = re.sub(r"\s*\[[ST]\d\]", "", text)
    ssml = (f'<speak version="1.0" xml:lang="{locale}"><voice name="{voice}">'
            f"{escape(spoken)}</voice></speak>").encode("utf-8")
    req = urllib.request.Request(f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1", data=ssml, headers={
        "Ocp-Apim-Subscription-Key": key,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3",
        "User-Agent": "operacija-dvina",
    })
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                audio = r.read()
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(audio)
            return len(spoken)
        except urllib.error.HTTPError as e:
            if e.code == 429:  # free tier rate limit
                time.sleep(5 * (attempt + 1))
                continue
            print("FAILED", lang, name, e.code, e.read()[:200])
            return 0
    print("FAILED", lang, name, "rate limited")
    return 0


langs = sys.argv[1:] or list(VOICES)
jobs = [(lang, name, text) for lang in langs for name, text in clips(lang)]
with ThreadPoolExecutor(4) as pool:
    chars = sum(pool.map(synthesize, jobs))
print(f"{len(jobs)} clips checked, {chars} characters synthesized for {', '.join(langs)}")
