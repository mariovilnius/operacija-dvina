"""Checks every generated text against its sources. Exits 1 if anything fails.

Lithuanian content: every quote the model cites must appear in the cited source, and every
number in a text must appear somewhere in the sources (task step counts are game rules, not facts).
Translations: source tags, numbers, quiz answers and Lithuanian names must survive.
"""
import json
import re
import sys

from paths import CONTENT, RAW

sys.stdout.reconfigure(encoding="utf-8")
TAG = re.compile(r"\[[ST]\d\]")
NAMES = ["Plokštin", "Plateli", "Šateik", "Meškausk", "Šatkausk", "Mikašausk", "Puidok", "Bunk"]


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[„“\"”…–‑\-()\[\]«»]", " ", s)).lower().strip(" .,")


def numbers(s: str) -> set[str]:
    s = re.sub(r"(?<=\d)[   .,](?=\d{3}(?!\d))", "", TAG.sub("", s))
    return {n.replace(",", ".") for n in re.findall(r"\d+(?:[.,]\d+)?", s)}


quest = json.loads((CONTENT / "quest.lt.json").read_text(encoding="utf-8"))
legends = json.loads((CONTENT / "legends.lt.json").read_text(encoding="utf-8"))
stops = json.loads((CONTENT / "factual_stops.lt.json").read_text(encoding="utf-8"))
translations = json.loads((CONTENT / "translations.json").read_text(encoding="utf-8"))
problems: list[str] = []

# Lithuanian content against the fetched sources
if (RAW / "sources.json").exists() and (RAW / "testimonies.json").exists():
    texts = {k: v["text"] for f in ("sources.json", "testimonies.json")
             for k, v in json.loads((RAW / f).read_text(encoding="utf-8")).items()}
    all_numbers = numbers(" ".join(texts.values()))

    def check(label: str, text: str, quotes: list[dict]) -> None:
        for q in quotes:
            if norm(q["quote"]) not in norm(texts.get(q["source"], "")):
                problems.append(f"{label}: quote not in {q['source']}: {q['quote'][:70]}")
        extra = numbers(text) - all_numbers
        if extra:
            problems.append(f"{label}: numbers not in sources {sorted(extra)}")

    for e in quest["episodes"]:
        check(f"episode {e['n']}", e["script"], e.get("facts_used", []))
    for m in quest["missions"]:
        q = m["quiz"]
        check(f"mission {m['n']}", m["story"], m.get("facts_used", []) + [{"source": q["source"], "quote": q["quote"]}])
    for i, card in enumerate(legends):
        check(f"card {i}", card["claim"] + " " + card["reveal"], card["evidence"])
    for s in stops:
        check(f"stop {s['stop']}", s["script"], s.get("facts_used", []))
    print("Lithuanian content checked against", len(texts), "sources")
else:
    print("data/raw missing: run fetch_sources.py and write_script.py / write_legends.py to rebuild source texts; skipping LT check")

# Translations against the Lithuanian original
original = {("episodes", str(e["n"])): e["title"] + " " + e["script"] for e in quest["episodes"]}
original |= {("missions", str(m["n"])): " ".join([m["title"], m["story"], m["task"], m["quiz"]["question"], *m["quiz"]["options"]])
             for m in quest["missions"]}
original |= {("legends", str(i)): c["claim"] + " " + c["reveal"] for i, c in enumerate(legends)}
for lang, groups in translations.items():
    for kind, items in groups.items():
        for key, item in items.items():
            text = " ".join(v if isinstance(v, str) else " ".join(v) for k, v in item.items() if k not in ("answer", "verdict"))
            src = original[(kind, key)]
            label = f"{lang} {kind} {key}"
            if sorted(TAG.findall(text)) != sorted(TAG.findall(src)):
                problems.append(f"{label}: source tags changed")
            if numbers(src) - numbers(text):
                problems.append(f"{label}: numbers lost {sorted(numbers(src) - numbers(text))}")
            if kind == "missions" and item["answer"] not in item["options"]:
                problems.append(f"{label}: answer not among options")
            lost = [n for n in NAMES if n in src and n not in text]
            if lost:
                problems.append(f"{label}: names changed {lost}")
print("Translations checked:", ", ".join(sorted(translations)))

for p in problems:
    print("FAIL", p)
print("OK" if not problems else f"{len(problems)} problem(s)")
sys.exit(1 if problems else 0)
