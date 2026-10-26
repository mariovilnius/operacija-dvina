"""Bundles the verified content into app/data/quest.json for the web app."""
import json
import sys

from paths import CONTENT, RAW, ROOT

sys.stdout.reconfigure(encoding="utf-8")
from translate import VERDICTS  # noqa: E402  (reuses the verdict labels)

APP_DATA = ROOT / "app" / "data"

LANGUAGES = [
    ("lt", "Lietuvių", "lt-LT"), ("en", "English", "en-GB"), ("de", "Deutsch", "de-DE"),
    ("es", "Español", "es-ES"), ("pt", "Português", "pt-PT"), ("pl", "Polski", "pl-PL"),
    ("lv", "Latviešu", "lv-LV"), ("ru", "Русский", "ru-RU"), ("uk", "Українська", "uk-UA"),
    ("zh", "中文", "zh-CN"), ("ja", "日本語", "ja-JP"),
]

# Each mission is unlocked by the QR code on the wall at its station: …#/unlock/<code>.
QR_CODES = json.loads((CONTENT / "qr_codes.json").read_text(encoding="utf-8"))

quest = json.loads((CONTENT / "quest.lt.json").read_text(encoding="utf-8"))
legends = json.loads((CONTENT / "legends.lt.json").read_text(encoding="utf-8"))
translations = json.loads((CONTENT / "translations.json").read_text(encoding="utf-8"))
ui = json.loads((CONTENT / "ui.json").read_text(encoding="utf-8"))


def strip_text(meta: dict) -> dict:
    return {k: v for k, v in meta.items() if k != "text"}


sources = {k: strip_text(v) for k, v in json.loads((RAW / "sources.json").read_text(encoding="utf-8")).items()}
sources |= {k: strip_text(v) for k, v in json.loads((RAW / "testimonies.json").read_text(encoding="utf-8")).items()}

episodes = []
for e in quest["episodes"]:
    text = {"lt": {"title": e["title"], "script": e["script"]}}
    text |= {lang: tr["episodes"][str(e["n"])] for lang, tr in translations.items()}
    episodes.append({"n": e["n"], "text": text})

missions = []
for m in quest["missions"]:
    q = m["quiz"]
    text = {"lt": {"title": m["title"], "story": m["story"], "task": m["task"],
                   "question": q["question"], "options": q["options"], "answer": q["answer"]}}
    text |= {lang: tr["missions"][str(m["n"])] for lang, tr in translations.items()}
    missions.append({"n": m["n"], "xp": m["xp"], "code": QR_CODES[str(m["n"])],
                     "proof": {"source": q["source"], "quote": q["quote"]}, "text": text})

cards = []
for i, card in enumerate(legends):
    text = {"lt": {"claim": card["claim"], "reveal": card["reveal"]}}
    text |= {lang: {"claim": tr["legends"][str(i)]["claim"], "reveal": tr["legends"][str(i)]["reveal"]}
             for lang, tr in translations.items()}
    cards.append({"id": i, "mission": card["mission"], "verdict": card["verdict"], "xp": card.get("xp", 50),
                  "sources": card["sources"], "text": text})

verdicts = {"lt": {k: k for k in VERDICTS["en"]}} | {lang: VERDICTS[lang] for lang in translations}

# Pre-generated narration (pipeline/make_audio.py); the app falls back to browser voices.
AUDIO = ROOT / "app" / "audio"
audio = {d.name: sorted(f.stem for f in d.glob("*.mp3")) for d in AUDIO.glob("*") if d.is_dir()} if AUDIO.exists() else {}

# Cross-links: the museum's own pages and the plateliai.lt places around it.
PLATELIAI = "https://plateliai.lt/vietos/{slug}?utm_source=operacija-dvina&utm_medium=game"
LINKS = {
    "museum": [
        {"key": "museum_info", "url": "https://zemaitijosnpd.lrv.lt/lt/informacija-atvykstantiems/ekspozicijos/saltojo-karo-ekspozicija-1/"},
        {"key": "museum_photos", "url": "https://zemaitijosnp.lt/veikla/lankytini-objektai/saltojo-karo-ekspozicija/"},
        {"key": "museum_page", "url": PLATELIAI.format(slug="saltojo-karo-ekspozicija")},
    ],
    "nearby": [{"name": name, "url": PLATELIAI.format(slug=slug)} for slug, name in [
        ("plateliai", "Plateliai"), ("plateliu-ezeras", "Platelių ežeras"), ("plateliu-dvaro-parkas", "Platelių dvaro parkas"),
        ("plateliu-dvaro-sodyba", "Platelių dvaro sodyba"), ("uzgaveniu-ekspozicija", "Užgavėnių ekspozicija"),
        ("siberijos-apzvalgos-bokstas", "Siberijos apžvalgos bokštas"), ("berzoras", "Beržoras"),
    ]],
    "more": "https://plateliai.lt/vietos?utm_source=operacija-dvina&utm_medium=game",
}

bundle = {
    "audio": audio,
    "links": LINKS,
    "languages": [{"code": c, "name": n, "speech": s} for c, n, s in LANGUAGES],
    "ui": ui, "verdicts": verdicts, "verdict_order": list(VERDICTS["en"]),
    "sources": sources, "episodes": episodes, "missions": missions, "cards": cards,
}
if __name__ == "__main__":
    APP_DATA.mkdir(parents=True, exist_ok=True)
    (APP_DATA / "quest.json").write_text(json.dumps(bundle, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{len(episodes)} episodes, {len(missions)} missions, {len(cards)} cards, {len(LANGUAGES)} languages")
