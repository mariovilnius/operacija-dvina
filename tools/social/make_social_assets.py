"""Renders profile pictures and banners for the Operacija Dvina social accounts into build/social/."""
import pathlib

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "build" / "social"
OUT.mkdir(parents=True, exist_ok=True)

CSS = """@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@600&family=Inter:wght@800&display=swap');
body { margin: 0; background: radial-gradient(1200px 800px at 25% 35%, #1a2620, #0b100d); color: #e9ece6; font-family: Inter, sans-serif;
       overflow: hidden; display: flex; align-items: center; justify-content: center; }
.stamp { font: 600 var(--s, 28px) 'IBM Plex Mono', monospace; letter-spacing: .2em; color: #ef7d6b; border: .14em solid #ef7d6b;
         padding: .25em .6em; border-radius: .25em; transform: rotate(-3deg); display: inline-block; }
h1 { font-weight: 800; letter-spacing: -.03em; line-height: 1; margin: .35em 0 0; }
.sub { font: 600 var(--m, 22px) 'IBM Plex Mono', monospace; color: #d6b25e; letter-spacing: .14em; margin-top: .9em; }
"""

ASSETS = {
    # name: (width, height, html)
    "avatar-1080": (1080, 1080, "<div style='text-align:center;--s:62px'><span class='stamp'>TOP SECRET</span>"
                                "<h1 style='font-size:190px'>OD</h1><div class='sub' style='--m:46px'>1962–1978</div></div>"),
    "banner-x-1500x500": (1500, 500, "<div style='--s:30px'><span class='stamp'>TOP SECRET · 1962–1978</span>"
                                     "<h1 style='font-size:120px'>Operacija Dvina</h1>"
                                     "<div class='sub'>A NUCLEAR MISSILE BASE UNDER A LITHUANIAN FOREST</div></div>"),
    "cover-facebook-1640x624": (1640, 624, "<div style='--s:32px'><span class='stamp'>TOP SECRET · 1962–1978</span>"
                                           "<h1 style='font-size:130px'>Operacija Dvina</h1>"
                                           "<div class='sub' style='--m:26px'>LISTEN AT HOME · CRACK IT ON SITE · PLOKŠTINĖ</div></div>"),
    "banner-youtube-2560x1440": (2560, 1440, "<div style='text-align:center;--s:46px'><span class='stamp'>TOP SECRET · 1962–1978</span>"
                                             "<h1 style='font-size:200px'>Operacija Dvina</h1>"
                                             "<div class='sub' style='--m:38px'>THE COLD WAR MUSEUM AT PLOKŠTINĖ, LITHUANIA</div></div>"),
}

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    for name, (w, h, body) in ASSETS.items():
        page = browser.new_page(viewport={"width": w, "height": h})
        page.set_content(f"<!doctype html><meta charset='utf-8'><style>{CSS} body{{width:{w}px;height:{h}px}}</style>{body}",
                         wait_until="networkidle")
        page.screenshot(path=str(OUT / f"{name}.png"))
        page.close()
    browser.close()
print("\n".join(sorted(p.name for p in OUT.glob("*.png"))))
