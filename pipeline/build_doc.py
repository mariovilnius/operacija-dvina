import json
import pathlib

from paths import RAW, CONTENT, DOCS
out_dir = DOCS
S = json.loads((RAW / "sources.json").read_text(encoding="utf-8"))
T = json.loads((RAW / "testimonies.json").read_text(encoding="utf-8"))
Q = json.loads((CONTENT / "quest.lt.json").read_text(encoding="utf-8"))
L = json.loads((CONTENT / "legends.lt.json").read_text(encoding="utf-8"))
F = sorted(json.loads((CONTENT / "factual_stops.lt.json").read_text(encoding="utf-8")), key=lambda s: int(s["stop"]))

ICON = {"FAKTAS": "✅", "LEGENDA": "❌", "LIUDIJIMAS": "🗣️", "ŠALTINIAI NESUTARIA": "⚖️", "IŠ DALIES": "◐", "NEĮRODYTA": "❓"}

md = [
    "# Plokštinė: „Operacija Dvina“ (audiogidas ir questas)", "",
    "Juodraštis Meta hakatonui. Tekstus parašė `muse-wonder-1.0` tik iš toliau nurodytų šaltinių.",
    "Automatiškai patikrinta: visos modelio citatos ir visi skaičiai rasti šaltiniuose, kiekvieno klausimo atsakymas turi citatą.",
    "Žymos [S1]–[S5] reiškia oficialius šaltinius, [T1]–[T5] – liudijimus.",
    "Vietoje nepatikrinta: ar misijų užduotyse minimi objektai (tvoros pėdsakai, miestelio pastatai, nuorodos) šiandien matomi.", "",
    "## Šaltiniai", "", "### Oficialūs", "",
]
md += [f"- **[{k}]** [{s['title']}]({s['url']})" for k, s in S.items()]
md += ["", "### Liudijimai ir pasakotojai", ""]
md += [f"- **[{k}]** [{t['title']}]({t['url']}). Pasakoja: {t['narrator']}. Užrašė: {t['recorded_by']}." for k, t in T.items()]

md += ["", "## Nuotolinės serijos (klausyti prieš kelionę)", ""]
for e in Q["episodes"]:
    md += [f"### {e['n']}. {e['title']}", "", e["script"], ""]

md += ["## Misijos vietoje", "",
       "Kiekvienoje misijoje yra pasakojimas, užduotis, klausimas ir viena ar kelios „Legenda ar faktas?“ kortelės.",
       "Žaidėjas išgirsta teiginį, pasirenka verdiktą, o tada išgirsta atsakymą su pasakotojo vardu.", "",
       "Verdiktai: ✅ FAKTAS · ❌ LEGENDA · 🗣️ LIUDIJIMAS · ⚖️ ŠALTINIAI NESUTARIA · ◐ IŠ DALIES · ❓ NEĮRODYTA", ""]
for m in Q["missions"]:
    q = m["quiz"]
    md += [f"### Misija {m['n']}. {m['title']} (+{m['xp']} XP)", "", "**Pasakojimas:** " + m["story"], "",
           "**Užduotis:** " + m["task"], "", f"**Klausimas:** {q['question']}", ""]
    md += [f"- {'✅ ' if o == q['answer'] else ''}{o}" for o in q["options"]]
    md += ["", f"> Įrodymas [{q['source']}]: „{q['quote']}“", ""]
    for l in [l for l in L if l["mission"] == m["n"]]:
        mark = " *(pataisyta ranka)*" if l.get("edited_by_hand") else ""
        md += [f"#### 🎴 Legenda ar faktas? (+{l.get('xp', 50)} XP){mark}", "", f"**Teiginys:** „{l['claim']}“", "",
               f"**Atsakymas:** {ICON.get(l['verdict'], '')} {l['verdict']}", "", l["reveal"], "",
               "Šaltiniai: " + ", ".join(f"[{s}]" for s in l["sources"]), ""]

md += ["## Priedas: faktinis scenarijus (10 stotelių)", "", "Dalykiškas variantas, naudotas kaip faktų pagrindas.", ""]
for s in F:
    md += [f"### {s['stop']}. {s['title']}", "", s["script"], ""]

(out_dir / "operacija-dvina.lt.md").write_text("\n".join(md), encoding="utf-8", newline="\n")
data = {"sources": {k: {kk: vv for kk, vv in v.items() if kk != "text"} for k, v in S.items()}, "testimonies": {k: {kk: vv for kk, vv in v.items() if kk != "text"} for k, v in T.items()},
        "episodes": Q["episodes"], "missions": Q["missions"], "legend_or_fact": L, "factual_stops": F}
(out_dir / "operacija-dvina.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
print("ok", len(L), "legend cards")
