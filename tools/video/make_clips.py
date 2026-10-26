"""Builds short vertical clips (1080x1920) for X into build/clips/, with burned-in subtitles.

Every narrated sentence is taken from the verified quest content: [S1] Žemaitija National Park
Directorate, [T1] Stanislovas Puidokas. Reuses the phone recordings made by make_video.py
(build/video/scene-*.webm), so run that first.
"""
import asyncio
import base64
import html
import json
import pathlib
import subprocess

import edge_tts
import imageio_ffmpeg
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "build" / "clips"
VIDEO = ROOT / "build" / "video"
IMG = ROOT / "app" / "img"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
VOICE = "en-GB-RyanNeural"
W, H, FPS = 1080, 1920, 30

CLIPS = {
    "1-missiles-under-a-forest": {
        "title": ("TOP SECRET · 1962–1978", "Nuclear missiles under a Lithuanian forest"),
        "text": "In 1962, under a forest in Lithuania, the Soviet Union finished a secret underground base. "
                "Four R-12 missiles, each 23 metres tall, stood in shafts 27 metres deep. Their range: up to 2,000 kilometres. "
                "Norway, Britain, West Germany, Turkey and Spain were on the target list. Not one was ever launched. "
                "Today it's a museum, and a game: Operacija Dvina.",
        "visuals": [("card", "title"), ("image", "shaft-section"), ("image", "range-map"), ("phone", "scene-1")],
    },
    "2-legend-or-fact-hangar": {
        "title": ("LEGEND OR FACT?", "The secret hangar in the forest"),
        "text": "Legend or fact? Near Plokštinė, people said a secret hangar in the forest held nuclear warheads. "
                "Local resident Stanislovas Puidokas remembers that nobody knew what was inside. "
                "The park directorate's history confirms that eight warheads were stored in the base's warehouse. "
                "But was it that hangar? The sources don't say. Verdict: partly true. Play the rest in Operacija Dvina.",
        "visuals": [("card", "title"), ("phone", "scene-5")],
    },
    "3-dug-with-shovels": {
        "title": ("PLOKŠTINĖ · 1960–1962", "Dug with shovels"),
        "text": "Ten thousand soldier-builders dug the missile shafts at Plokštinė like wells, with shovels. "
                "Twenty-seven metres deep. They concreted a pit for the control block, covered the roof with liquid glass "
                "and hid everything under a layer of earth. On the 31st of December 1962, at ten in the evening, "
                "the first combat duty began. What waits in the shafts? Find out in Operacija Dvina.",
        "visuals": [("card", "title"), ("image", "base-plan"), ("image", "shaft-section"), ("phone", "scene-3")],
    },
}

FONT = "@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@600&family=Inter:wght@600;800&display=swap');"
CSS = FONT + """
body { margin: 0; width: 1080px; height: 1920px; background: radial-gradient(900px 1200px at 30% 30%, #1a2620, #0b100d);
       color: #e9ece6; font-family: Inter, sans-serif; overflow: hidden; }
.kicker { font: 600 34px 'IBM Plex Mono', monospace; letter-spacing: .18em; color: #ef7d6b; border: 4px solid #ef7d6b;
          display: inline-block; padding: 8px 18px; border-radius: 8px; transform: rotate(-2deg); }
h1 { font-size: 104px; line-height: 1.02; letter-spacing: -.03em; font-weight: 800; margin: 50px 0 0; }
.brand { position: absolute; left: 80px; bottom: 120px; font: 600 34px 'IBM Plex Mono', monospace; color: #d6b25e; letter-spacing: .14em; }
"""


def run(*args: str) -> None:
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", *args], check=True)


async def narrate(name: str, text: str) -> list[tuple[float, float, str]]:
    """Saves the narration and returns word timings (start s, end s, word)."""
    words = []
    with open(OUT / f"{name}.mp3", "wb") as audio:
        async for chunk in edge_tts.Communicate(text, VOICE, boundary="WordBoundary").stream():
            if chunk["type"] == "audio":
                audio.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 1e7
                words.append((start, start + chunk["duration"] / 1e7, chunk["text"]))
    return words


def with_punctuation(words: list[tuple[float, float, str]], text: str) -> list[tuple[float, float, str]]:
    """Word boundaries come without punctuation; take each word as written in the script instead."""
    out, cursor = [], 0
    for start, end, word in words:
        at = text.lower().find(word.lower(), cursor)
        if at < 0:
            out.append((start, end, word))
            continue
        stop = at + len(word)
        while stop < len(text) and not text[stop].isspace():
            stop += 1
        out.append((start, end, text[at:stop]))
        cursor = stop
    return out


def subtitles(words: list[tuple[float, float, str]], path: pathlib.Path) -> None:
    """Groups words into short lines and writes an ASS file with big, high-contrast captions."""
    lines, current = [], []
    for w in words:
        current.append(w)
        if len(" ".join(x[2] for x in current)) > 22 or w[2].endswith((".", ",", "?", ":")):
            lines.append(current)
            current = []
    if current:
        lines.append(current)

    def ts(s: float) -> str:
        return f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:05.2f}"

    events = []
    for i, line in enumerate(lines):
        end = lines[i + 1][0][0] if i + 1 < len(lines) else line[-1][1] + 0.4
        text = " ".join(x[2] for x in line).replace("{", "(").replace("}", ")")
        events.append(f"Dialogue: 0,{ts(line[0][0])},{ts(end)},Cap,,0,0,0,,{text}")
    path.write_text(
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, "
        "StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Cap,Arial,78,&H00FFFFFF,&H00FFFFFF,&H00000000,&H99000000,1,0,0,0,100,100,0,0,3,6,0,2,70,70,250,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n" + "\n".join(events) + "\n",
        encoding="utf-8")


def stills(pw) -> None:
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width": W, "height": H})
    for name, clip in CLIPS.items():
        kicker, title = clip["title"]
        page.set_content(f"<!doctype html><meta charset='utf-8'><style>{CSS}</style><div style='padding:420px 80px 0'>"
                         f"<span class='kicker'>{html.escape(kicker)}</span><h1>{html.escape(title)}</h1></div>"
                         "<div class='brand'>OPERACIJA DVINA</div>", wait_until="networkidle")
        page.screenshot(path=str(OUT / f"{name}-title.png"))
    for img in ("range-map", "shaft-section", "base-plan"):
        data = base64.b64encode((IMG / f"{img}.svg").read_bytes()).decode()
        page.set_content(f"<!doctype html><meta charset='utf-8'><style>{CSS}</style>"
                         f"<img src='data:image/svg+xml;base64,{data}' style='position:absolute;left:40px;top:260px;width:1000px;"
                         "border-radius:28px'><div class='brand'>OPERACIJA DVINA</div>", wait_until="networkidle")
        page.screenshot(path=str(OUT / f"img-{img}.png"))
    browser.close()


def compose(name: str, clip: dict, length: float) -> pathlib.Path:
    visuals = clip["visuals"]
    title_len = 3.0
    each = (length - title_len) / (len(visuals) - 1)
    inputs, chains = [], []
    for i, (kind, ref) in enumerate(visuals):
        seg = title_len if i == 0 else each
        if kind == "card":
            inputs += ["-loop", "1", "-t", f"{seg:.2f}", "-i", str(OUT / f"{name}-title.png")]
            chains.append(f"[{i}:v]scale={W}:{H},setsar=1,fps={FPS}[s{i}]")
        elif kind == "image":
            inputs += ["-i", str(OUT / f"img-{ref}.png")]  # one frame; zoompan makes exactly seg seconds
            # slow push-in keeps a still image alive on a feed
            chains.append(f"[{i}:v]scale={W * 2}:{H * 2},zoompan=z='min(zoom+0.0006,1.08)':d={int(seg * FPS)}:"
                          f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS},setsar=1[s{i}]")
        else:
            inputs += ["-ss", "2", "-t", f"{seg:.2f}", "-i", str(VIDEO / f"{ref}.webm")]
            chains.append(f"[{i}:v]scale=-2:1300,pad={W}:{H}:(ow-iw)/2:110:color=0x0e1411,"
                          f"tpad=stop_mode=clone:stop_duration=30,trim=0:{seg:.2f},setsar=1,fps={FPS}[s{i}]")
    n = len(visuals)
    subs = (OUT / f"{name}.ass").as_posix().replace(":", r"\:")
    graph = ";".join(chains) + ";" + "".join(f"[s{i}]" for i in range(n)) + \
        f"concat=n={n}:v=1:a=0,subtitles='{subs}',fade=t=out:st={length - 0.4:.2f}:d=0.4[v]"
    out = OUT / f"{name}.mp4"
    run(*inputs, "-i", str(OUT / f"{name}.mp3"), "-filter_complex", graph, "-map", "[v]", "-map", f"{n}:a",
        "-af", "apad", "-t", f"{length:.2f}", "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out))
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    timings = {}
    for name, clip in CLIPS.items():
        words = with_punctuation(asyncio.run(narrate(name, clip["text"])), clip["text"])
        subtitles(words, OUT / f"{name}.ass")
        timings[name] = words[-1][1] + 1.0
    with sync_playwright() as pw:
        stills(pw)
    for name, clip in CLIPS.items():
        out = compose(name, clip, timings[name])
        print(f"{out.name}: {timings[name]:.1f}s, {out.stat().st_size // 1024} KB")
    (OUT / "posts.json").write_text(json.dumps({n: c["text"] for n, c in CLIPS.items()}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
