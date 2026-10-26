"""Builds the 3-minute demo video (docs/demo-video.md) into build/video/operacija-dvina-demo.mp4.

Needs: pip install playwright edge-tts imageio-ffmpeg soundfile && python -m playwright install chromium
and the app served locally:  python -m http.server 8765 --directory app
"""
import asyncio
import base64
import html
import json
import pathlib
import re
import subprocess
import sys

import edge_tts
import imageio_ffmpeg
import soundfile as sf
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "build" / "video"
APP = "http://localhost:8765/"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
VOICE = "en-GB-RyanNeural"
W, H, FPS = 1920, 1080, 30
PHONE_H = 960  # phone recording height on the 1080p canvas
PHONE_X, PHONE_Y = 1240, 60

NARRATION = {
    1: "In a forest in western Lithuania, under a layer of sand, the Soviet Union hid four nuclear missiles aimed at "
       "Western Europe. Today it's the Cold War Museum. We built a game that makes young people want to go there.",
    2: "AI travel guides have a problem: they invent things. At a site about nuclear weapons and occupation, one "
       "invented fact is one too many. So in Operacija Dvina, every sentence has a source, and you can tap it.",
    3: "It starts at home. Three short audio episodes, each ending on a mystery you can only solve at the museum. "
       "Every fact is tagged: S for official sources, T for named witnesses. Tap one, and you're on the original page.",
    4: "At the museum, every station has a QR code on the wall. Scan it, and the mission unlocks: a story, a task like "
       "pacing out the twenty-three metres of the missile, and a quiz, with the proof shown straight from the source.",
    5: "The best part comes from the neighbours. People who grew up next to the barbed wire tell stories. Some are true, "
       "some are legends. The player decides: fact, legend, testimony, sources disagree, partly true, or unproven. "
       "Then the evidence decides.",
    6: "Under the hood, Meta's Muse Wonder writes only from five official sources and five recorded testimonies, and "
       "returns the exact quote behind every sentence. A verifier fails the build if any quote, number or name can't "
       "be found. Muse Spark then translates everything into ten more languages, and the same checks run again.",
    7: "Eleven languages, with neural-voice narration, even in Lithuanian, which most phones can't speak.",
    8: "Operacija Dvina. Listen at home, crack it on site, and trust what you hear.",
}
LT_SAMPLE_SECONDS = 5.0  # scene 7 ends on a few seconds of the Lithuanian narration

CSS = """
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500;600&family=Inter:wght@400;600;700;800&display=swap');
* { box-sizing: border-box; }
body { margin: 0; width: 1920px; height: 1080px; background: radial-gradient(1200px 800px at 20% 30%, #1a2620, #0b100d);
       color: #e9ece6; font-family: Inter, sans-serif; overflow: hidden; }
.mono { font-family: 'IBM Plex Mono', monospace; }
.kicker { font: 600 22px 'IBM Plex Mono', monospace; letter-spacing: .2em; color: #d6b25e; text-transform: uppercase; }
.stamp { display: inline-block; font: 600 22px 'IBM Plex Mono', monospace; letter-spacing: .2em; color: #ef7d6b;
         border: 3px solid #ef7d6b; padding: 6px 14px; border-radius: 6px; transform: rotate(-2deg); }
h1 { font-size: 96px; line-height: 1.02; margin: 26px 0 22px; letter-spacing: -.03em; font-weight: 800; }
h2 { font-size: 64px; line-height: 1.08; margin: 18px 0; letter-spacing: -.02em; font-weight: 800; }
p.lead { font-size: 34px; line-height: 1.4; color: #b8c2bb; margin: 0; }
.left { position: absolute; left: 140px; top: 0; bottom: 0; width: 980px; display: flex; flex-direction: column; justify-content: center; }
.phone-slot { position: absolute; left: %(px)dpx; top: %(py)dpx; width: %(pw)dpx; height: %(ph)dpx; border-radius: 40px;
              box-shadow: 0 0 0 10px #222c27, 0 0 0 12px #3a4a42, 0 30px 80px rgba(0,0,0,.6); background: #0e1411; }
.tag { display: inline-block; font: 600 20px/1 'IBM Plex Mono', monospace; padding: 5px 8px; border-radius: 6px;
       background: #1d2722; color: #d6b25e; border: 1px solid #2b3832; vertical-align: 4px; margin-left: 4px; }
.tag.t { color: #9cc7ff; }
"""
PHONE_W = round(PHONE_H * 390 / 844)


def page_html(body: str) -> str:
    css = (CSS.replace("%(px)d", str(PHONE_X)).replace("%(py)d", str(PHONE_Y))
           .replace("%(pw)d", str(PHONE_W)).replace("%(ph)d", str(PHONE_H)))
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>{body}</body></html>"


def run(*args: str) -> None:
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", *args], check=True)


def duration(path: pathlib.Path) -> float:
    return sf.info(str(path)).duration


async def narrate() -> dict[int, float]:
    for n, text in NARRATION.items():
        out = OUT / f"narration-{n}.mp3"
        if not out.exists():
            await edge_tts.Communicate(text, VOICE).save(str(out))
    return {n: duration(OUT / f"narration-{n}.mp3") for n in NARRATION}


def cards(pw) -> None:
    quest = json.loads((ROOT / "app" / "data" / "quest.json").read_text(encoding="utf-8"))
    story = next(m for m in quest["missions"] if m["n"] == 4)["text"]["en"]["story"]
    sample = html.escape(" ".join(re.split(r"(?<=\])\s", story)[:4]))
    sample = re.sub(r"\[(S\d)\]", r"<span class='tag'>\1</span>", sample)
    verify = subprocess.run([sys.executable, "verify.py"], cwd=ROOT / "pipeline", capture_output=True, text=True,
                            encoding="utf-8").stdout.strip()

    phone = "<div class='phone-slot'></div>"
    layouts = {
        "bg-1": f"<div class='left'><span class='stamp' style='align-self:flex-start'>TOP SECRET · 1962–1978</span>"
                f"<h1>Operacija<br>Dvina</h1><p class='lead'>A youth audio quest about a Soviet nuclear missile base "
                f"hidden in a Lithuanian forest.</p></div>{phone}",
        "card-2": "<div style='position:absolute;inset:0;display:grid;grid-template-columns:1fr 1fr;gap:80px;padding:140px'>"
                  "<div><div class='kicker'>The problem</div><h2>AI travel guides invent facts.</h2>"
                  "<p class='lead'>At a site about nuclear weapons and occupation, one invented fact is one too many.</p></div>"
                  "<div><div class='kicker'>Operacija Dvina</div><p class='lead' style='color:#e9ece6;font-size:32px;"
                  f"line-height:1.6;margin-top:28px'>{sample}</p><p class='lead' style='margin-top:30px;font-size:26px'>"
                  "Every fact carries its source. Tap the tag to open it.</p></div></div>",
        "bg-3": f"<div class='left'><div class='kicker'>At home</div><h2>Three remote episodes</h2><p class='lead'>Each one ends "
                f"on a mystery you can only solve at the museum. <span class='tag'>S1</span> official source, "
                f"<span class='tag t'>T3</span> named witness.</p></div>{phone}",
        "bg-5": f"<div class='left'><div class='kicker'>Legend or fact?</div><h2>The neighbours' stories</h2><p class='lead'>"
                f"Ten local legends, weighed against five recorded testimonies and the official sources. Six verdicts.</p></div>{phone}",
        "card-6a": "<div style='position:absolute;inset:0;padding:120px 140px'><div class='kicker'>Under the hood</div>"
                   "<h2 style='margin-bottom:70px'>Sources in, verified quest out</h2><div style='display:flex;gap:28px;align-items:center;font-size:30px'>"
                   + "<span style='color:#5d6b63;font-size:44px'>→</span>".join(
                       f"<div style='flex:1;background:#161e1a;border:2px solid {c};border-radius:22px;padding:30px;min-height:250px'>"
                       f"<div class='kicker' style='color:{c};font-size:18px'>{k}</div><div style='font-weight:700;font-size:34px;margin:12px 0'>{t}</div>"
                       f"<div style='color:#9aa69f;font-size:24px;line-height:1.4'>{d}</div></div>"
                       for k, t, d, c in [
                           ("Input", "10 sources", "5 official pages, 5 witness testimonies", "#5d6b63"),
                           ("Meta · Muse Wonder", "Writes & cites", "Every sentence returns its exact quote", "#d6b25e"),
                           ("verify.py", "Checks", "Quotes, numbers, names, quiz answers", "#6fcf8e"),
                           ("Meta · Muse Spark", "Translates", "10 more languages, checked again", "#9cc7ff"),
                       ]) + "</div></div>",
        "card-6b": "<div style='position:absolute;inset:0;padding:120px 140px'><div class='kicker'>Every build</div>"
                   "<h2>The verifier has the last word</h2><pre class='mono' style='margin-top:40px;background:#050806;border:2px solid #2b3832;"
                   "border-radius:18px;padding:40px;font-size:34px;line-height:1.6;color:#b8c2bb'>$ python pipeline/verify.py\n"
                   + html.escape(verify).replace("OK", "<span style='color:#6fcf8e;font-weight:600'>OK</span>") + "</pre></div>",
        "bg-7": f"<div class='left'><div class='kicker'>Every visitor group</div><h2>11 languages</h2><p class='lead'>Lietuvių · English · "
                f"Deutsch · Español · Português · Polski · Latviešu · Русский · Українська · 中文 · 日本語</p>"
                f"<p class='lead' style='margin-top:24px'>Neural-voice narration, even in Lithuanian.</p></div>{phone}",
        "card-8": "<div style='position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center'>"
                  "<span class='stamp'>TOP SECRET · 1962–1978</span><h1>Operacija Dvina</h1><p class='lead'>Listen at home. Crack it on site. "
                  "Trust what you hear.</p><p class='mono' style='font-size:30px;color:#d6b25e;margin-top:60px'>mariovilnius.github.io/operacija-dvina</p>"
                  "<p class='mono' style='font-size:26px;color:#9aa69f'>github.com/mariovilnius/operacija-dvina</p>"
                  "<p style='font-size:26px;color:#9aa69f;margin-top:50px'>Built with Meta Muse Wonder &amp; Muse Spark</p></div>",
    }
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width": W, "height": H})
    for name, body in layouts.items():
        page.set_content(page_html(body), wait_until="networkidle")
        page.screenshot(path=str(OUT / f"{name}.png"))
    # Scene 4 background: the real wall poster next to the phone
    poster = browser.new_page(viewport={"width": 794, "height": 1123})
    poster.goto((ROOT / "docs" / "qr" / "posters.html").as_uri())
    poster.locator(".poster").nth(3).screenshot(path=str(OUT / "poster-4.png"))
    page.set_content(page_html(
        f"<div class='left' style='align-items:flex-start'><div class='kicker'>At the museum</div>"
        f"<img src='data:image/png;base64,{base64.b64encode((OUT / 'poster-4.png').read_bytes()).decode()}' style='height:760px;margin-top:24px;border-radius:12px;"
        f"box-shadow:0 30px 80px rgba(0,0,0,.6);transform:rotate(-1.5deg)'></div>{phone}"), wait_until="networkidle")
    page.screenshot(path=str(OUT / "bg-4.png"))
    browser.close()


def record(pw, name: str, seconds: float, state: dict | None, steps) -> None:
    """Records one phone scene; steps(page, pace) drives the app over roughly `seconds`."""
    browser = pw.chromium.launch()
    # Video capture ignores device_scale_factor, so render a 2x viewport and zoom the page to a 390px phone layout.
    ctx = browser.new_context(viewport={"width": 780, "height": 1688},
                              record_video_dir=str(OUT / f"rec-{name}"), record_video_size={"width": 780, "height": 1688})
    ctx.add_init_script("document.addEventListener('DOMContentLoaded', () => { document.documentElement.style.zoom = '2'; });")
    ctx.add_init_script(f"try {{ if (!sessionStorage.getItem('seeded')) {{ localStorage.clear(); "
                        f"{'' if state is None else 'localStorage.setItem(' + json.dumps('operacija-dvina') + ',' + json.dumps(json.dumps(state)) + ');'}"
                        f"sessionStorage.setItem('seeded','1'); }} }} catch (e) {{}}")
    page = ctx.new_page()
    page.goto(APP + "#/")
    page.wait_for_timeout(1200)  # trimmed away when composing
    steps(page, seconds)
    video = page.video.path()
    ctx.close()
    browser.close()
    pathlib.Path(video).replace(OUT / f"{name}.webm")


def scroll(page, total_px: int, seconds: float) -> None:
    steps = max(1, int(seconds * 10))
    for _ in range(steps):
        page.mouse.wheel(0, total_px / steps)
        page.wait_for_timeout(100)


def recordings(pw, dur: dict[int, float]) -> None:
    en_demo = {"lang": "en", "quizzes": {}, "cards": {}, "opened": {}, "demo": True}

    def s1(page, s):
        page.wait_for_timeout(1500); scroll(page, 900, s - 3); page.wait_for_timeout(1500)

    def s3(page, s):
        page.wait_for_timeout(1200); page.click("[data-lang=en]"); page.wait_for_timeout(1500)
        page.click("a[href='#/episode/1']"); page.wait_for_timeout(1500)
        page.locator(".tag").first.hover(); page.wait_for_timeout(1200)
        scroll(page, 700, s - 7)

    def s4(page, s):
        code = json.loads((ROOT / "content" / "qr_codes.json").read_text())["4"]
        page.wait_for_timeout(800); page.goto(APP + f"#/unlock/{code}"); page.wait_for_timeout(2500)
        scroll(page, 900, (s - 6) / 2)
        page.locator("#quiz").scroll_into_view_if_needed(); page.wait_for_timeout(1200)
        page.locator("#quiz .option", has_text="30").first.click(); page.wait_for_timeout(1000)
        page.locator("#quiz-result").scroll_into_view_if_needed(); page.wait_for_timeout(max(1000, (s - 6) / 2 * 1000))

    def s5(page, s):
        page.goto(APP + "#/mission/4"); page.wait_for_timeout(600)
        card = page.locator("[data-card]").first
        card.scroll_into_view_if_needed(); page.mouse.wheel(0, 250); page.wait_for_timeout(2500)
        card.locator(".option", has_text="FACT").first.click(); page.wait_for_timeout(1200)
        scroll(page, 450, s - 5)

    def s7(page, s):
        for code in ["lt", "ja", "uk", "es", "zh"]:
            page.goto(APP + "#/lang"); page.wait_for_timeout(500)
            page.click(f"[data-lang={code}]"); page.wait_for_timeout(max(900, (s - 3) / 5 * 1000 - 500))

    scenes = {1: (s1, en_demo), 3: (s3, None), 4: (s4, {**en_demo, "demo": False}), 5: (s5, en_demo), 7: (s7, en_demo)}
    for n, (steps, state) in scenes.items():
        if not (OUT / f"scene-{n}.webm").exists():
            record(pw, f"scene-{n}", dur[n] + 1.5, state, steps)


def compose(dur: dict[int, float]) -> pathlib.Path:
    parts = []
    lt_clip = ROOT / "app" / "audio" / "lt" / "episode-1.mp3"
    for n in NARRATION:
        length = dur[n] + 0.9 + (LT_SAMPLE_SECONDS + 0.4 if n == 7 else 0)
        audio = ["-i", str(OUT / f"narration-{n}.mp3")]
        if n == 7:
            audio += ["-t", str(LT_SAMPLE_SECONDS), "-i", str(lt_clip)]
        fade = f"fade=t=in:st=0:d=0.3,fade=t=out:st={length - 0.35:.2f}:d=0.35"
        out = OUT / f"part-{n}.mp4"
        if n in (2, 6, 8):
            stills = ["card-6a", "card-6b"] if n == 6 else [f"card-{n}"]
            each = length / len(stills)
            inputs = sum([["-loop", "1", "-t", f"{each:.2f}", "-i", str(OUT / f"{s}.png")] for s in stills], [])
            vf = "".join(f"[{i}:v]scale={W}:{H},fps={FPS},setsar=1[v{i}];" for i in range(len(stills)))
            vf += "".join(f"[v{i}]" for i in range(len(stills))) + f"concat=n={len(stills)}:v=1:a=0,{fade}[v]"
            a0 = len(stills)
        else:
            inputs = ["-loop", "1", "-t", f"{length:.2f}", "-i", str(OUT / f"bg-{n}.png"),
                      "-ss", "1.2", "-i", str(OUT / f"scene-{n}.webm")]
            vf = (f"[1:v]scale=-2:{PHONE_H},tpad=stop_mode=clone:stop_duration=30[p];"
                  f"[0:v][p]overlay={PHONE_X}:{PHONE_Y}:shortest=0,fps={FPS},setsar=1,trim=0:{length:.2f},{fade}[v]")
            a0 = 2
        if n == 7:
            af = (f"[{a0}:a]aresample=48000,apad=pad_dur=0.4[n];[{a0 + 1}:a]aresample=48000,afade=t=in:d=0.3,"
                  f"afade=t=out:st={LT_SAMPLE_SECONDS - 0.6}:d=0.6[l];[n][l]concat=n=2:v=0:a=1,apad[a]")
        else:
            af = f"[{a0}:a]aresample=48000,apad[a]"
        run(*inputs, *audio, "-filter_complex", f"{vf};{af}", "-map", "[v]", "-map", "[a]", "-t", f"{length:.2f}",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
            "-ar", "48000", str(out))
        parts.append(out)
    listing = OUT / "parts.txt"
    listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
    final = OUT / "operacija-dvina-demo.mp4"
    run("-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", "-movflags", "+faststart", str(final))
    return final


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    dur = asyncio.run(narrate())
    total = sum(dur.values()) + 0.9 * len(dur) + LT_SAMPLE_SECONDS + 0.4
    print("narration", {k: round(v, 1) for k, v in dur.items()}, f"→ video ≈ {total:.0f}s")
    with sync_playwright() as pw:
        cards(pw)
        recordings(pw, dur)
    final = compose(dur)
    print("wrote", final, f"{duration_video(final):.1f}s")


def duration_video(path: pathlib.Path) -> float:
    probe = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True).stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", probe).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


if __name__ == "__main__":
    main()
