"""Builds the vertical video of the bonus stories episode with burned-in subtitles.

Usage: python make_stories_video.py [lt|en]   → build/clips/stories-<lang>.mp4
Visuals are our own: a title card per story naming its narrator, and the base diagrams.
No third-party photos are used until the museum or LRT give permission.
"""
import asyncio
import base64
import html
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "pipeline"))
from make_audio import VOICES, spoken_form  # noqa: E402
from make_clips import CSS, FPS, H, IMG, OUT, W, run, subtitles, with_punctuation  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

import edge_tts  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
lang = sys.argv[1] if len(sys.argv) > 1 else "lt"
quest = json.loads((ROOT / "app" / "data" / "quest.json").read_text(encoding="utf-8"))
story = next(e for e in quest["episodes"] if e.get("bonus"))["text"][lang]
text = spoken_form(lang, story["script"])
name = f"stories-{lang}"


async def narrate():
    import make_clips  # reuses its retrying narration with this language's voice

    make_clips.VOICE = VOICES[lang][1]
    return with_punctuation(await make_clips.narrate(name, text), text)


def story_starts(words):
    """Paragraph starts in the script mark the stories; find when each one is spoken."""
    # Matched on letters only, so it also works for Chinese and Japanese, which have no spaces
    def letters(s):
        return re.sub(r"[\W_]+", "", s).lower()

    clean = re.sub(r"\s*\[[ST]\d\]", "", story["script"])
    # Stories are separated by blank lines; some translations also break single sentences onto new lines
    paragraphs = [p.strip() for p in clean.split("\n\n") if p.strip()]
    if len(paragraphs) < 3:
        paragraphs = [p.strip() for p in clean.split("\n") if p.strip()]
    spoken, owner = "", []
    for i, w in enumerate(words):
        chunk = letters(w[2])
        spoken += chunk
        owner += [i] * len(chunk)
    starts, cursor = [], 0
    for p in paragraphs:
        head = letters(p)[:6]
        at = spoken.find(head, cursor) if head else -1
        if at >= 0:
            starts.append((words[owner[at]][0], p))
            cursor = at + len(head)
    return starts


def card(page, path, kicker, title, body=""):
    page.set_content(f"<!doctype html><meta charset='utf-8'><style>{CSS} p{{font-size:46px;line-height:1.35;color:#b8c2bb}}</style>"
                     f"<div style='padding:360px 80px 0'><span class='kicker'>{html.escape(kicker)}</span>"
                     f"<h1 style='font-size:92px'>{html.escape(title)}</h1><p>{html.escape(body)}</p></div>"
                     "<div class='brand'>OPERACIJA DVINA</div>", wait_until="networkidle")
    page.screenshot(path=str(path))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    words = asyncio.run(narrate())
    subtitles(words, OUT / f"{name}.ass")
    font = {"zh": "Microsoft YaHei", "ja": "Yu Gothic"}.get(lang)
    if font:
        ass = OUT / f"{name}.ass"
        ass.write_text(ass.read_text(encoding="utf-8").replace("Style: Cap,Arial,", f"Style: Cap,{font},"), encoding="utf-8")
    length = words[-1][1] + 1.2
    starts = story_starts(words)
    # Narrator line = the first sentence of each paragraph ("Pirmąją istoriją pasakoja …")
    segments = [(0.0, "title")] + [(s, p) for s, p in starts[1:]]
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H})
        card(page, OUT / f"{name}-0.png", "OPERACIJA DVINA · BONUS", story["title"])
        for k, (_, para) in enumerate(segments[1:], start=1):
            first = re.split(r"(?<=[.!?])\s|(?<=[。！？])", para)[0]
            card(page, OUT / f"{name}-{k}.png", f"{k:02d}", first[:120])
        diagrams = {}
        for img in ("base-plan", "shaft-section"):
            data = base64.b64encode((IMG / f"{img}.svg").read_bytes()).decode()
            page.set_content(f"<!doctype html><meta charset='utf-8'><style>{CSS}</style><img src='data:image/svg+xml;base64,{data}' "
                             "style='position:absolute;left:40px;top:260px;width:1000px;border-radius:28px'><div class='brand'>OPERACIJA DVINA</div>",
                             wait_until="networkidle")
            diagrams[img] = OUT / f"{name}-{img}.png"
            page.screenshot(path=str(diagrams[img]))
        browser.close()

    # The intro shows the title, then the base plan; each story keeps its narrator card on screen
    timeline = []
    bounds = [s for s, _ in segments] + [length]
    for k in range(len(segments)):
        start, end = bounds[k], bounds[k + 1]
        if k == 0 and end - start > 8:
            timeline += [(OUT / f"{name}-0.png", 6.0), (diagrams["base-plan"], end - start - 6.0)]
        else:
            timeline.append((OUT / f"{name}-{k}.png", end - start))
    inputs, chains = [], []
    for i, (img, seg) in enumerate(timeline):
        inputs += ["-loop", "1", "-t", f"{seg:.3f}", "-i", str(img)]
        chains.append(f"[{i}:v]scale={W}:{H},setsar=1,fps={FPS}[s{i}]")
    n = len(timeline)
    subs = (OUT / f"{name}.ass").as_posix().replace(":", r"\:")
    graph = ";".join(chains) + ";" + "".join(f"[s{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0,subtitles='{subs}'[v]"
    out = OUT / f"{name}.mp4"
    run(*inputs, "-i", str(OUT / f"{name}.mp3"), "-filter_complex", graph, "-map", "[v]", "-map", f"{n}:a",
        "-af", "apad", "-t", f"{length:.2f}", "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out))
    print(f"{out.name}: {length / 60:.1f} min, {len(starts)} stories, {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
