"""Step 1: download the official sources and testimonies into data/raw (not committed).

The texts belong to their publishers, so the repository only stores links and short
verification quotes. Run this before any write_* step or before verify.py.
"""
import html
import re
import sys
import urllib.request

from paths import RAW

sys.stdout.reconfigure(encoding="utf-8")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36"
LRV = "https://zemaitijosnpd.lrv.lt/lt/informacija-atvykstantiems/ekspozicijos/saltojo-karo-ekspozicija-1"
MHT = "https://militaryheritagetourism.info/lt/military/stories/view"

PAGES = {
    "src/znp.txt": "https://zemaitijosnp.lt/veikla/lankytini-objektai/saltojo-karo-ekspozicija/",
    "src/vle.txt": "https://www.vle.lt/straipsnis/saltojo-karo-muziejus/",
    "src/visitplunge.txt": "https://www.visitplunge.lt/lankytinos-vietos/saltojo-karo-ekspozicija/",
    "src/lrv-istorija.txt": f"{LRV}/istorija/",
    "src/lrv-ekskursija-po-buvusi-karini-miesteli.txt": f"{LRV}/ekskursija-po-buvusi-karini-miesteli/",
    "oral/mht360.txt": f"{MHT}/360",
    "oral/mht361.txt": f"{MHT}/361",
    "oral/mht374.txt": f"{MHT}/374",
    "oral/mht381.txt": f"{MHT}/381",
    "oral/lrt.txt": "https://www.lrt.lt/naujienos/lietuvoje/2/2685545/liepdavo-uzsitraukti-uzuolaidas-gyvenimas-prie-branduoliniu-raketu-bazes-salia-plateliu",
}


def page_text(raw: str) -> str:
    match = re.search(r"(?is)<article.*?</article>", raw) or re.search(r"(?is)<main.*?</main>", raw)
    body = re.sub(r"(?is)<(script|style|nav|form|header|footer|aside).*?</\1>", " ", match.group(0) if match else raw)
    text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body))).strip()
    return re.sub(r"^.*?Parko žemėlapis", "", text, count=1).strip()


def story_text(text: str) -> str:
    """militaryheritagetourism.info: story body plus the narrator line."""
    text = re.sub(r"^.*?Paieška\s*", "", text, count=1)
    meta = re.search(r"Pasakotojas:.*?(?=Pridėkite|$)", text)
    return text.split("Įkeliama...")[0] + (" || META: " + meta.group(0)[:400] if meta else "")


for name, url in PAGES.items():
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    raw = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", errors="ignore")
    text = page_text(raw)
    if "/mht" in name:
        text = story_text(text)
    out = RAW / name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"{name:55} {len(text):6} chars")
