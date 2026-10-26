import json, os, sys, urllib.request, pathlib
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8")
from paths import RAW, CONTENT, DOCS
Q = json.loads((CONTENT / "quest.lt.json").read_text(encoding="utf-8"))
L = json.loads((CONTENT / "legends.lt.json").read_text(encoding="utf-8"))

ALL_LANGS = {
    "en": ("English", "you"), "de": ("German (Deutsch)", "du"),
    "es": ("Spanish (Spain)", "tú"), "pt": ("European Portuguese", "tu"), "pl": ("Polish", "ty"),
    "lv": ("Latvian", "tu"), "ru": ("Russian", "ты"), "uk": ("Ukrainian", "ти"),
    "zh": ("Simplified Chinese (zh-CN)", "你"), "ja": ("Japanese (friendly casual style for young people)", "plain form, no keigo"),
}
LANGS = dict(ALL_LANGS)  # narrowed to the command-line languages in main()
VERDICTS = {
    "en": {"FAKTAS": "FACT", "LEGENDA": "LEGEND", "LIUDIJIMAS": "TESTIMONY", "ŠALTINIAI NESUTARIA": "SOURCES DISAGREE",
           "IŠ DALIES": "PARTLY TRUE", "NEĮRODYTA": "UNPROVEN"},
    "de": {"FAKTAS": "FAKT", "LEGENDA": "LEGENDE", "LIUDIJIMAS": "ZEITZEUGENBERICHT", "ŠALTINIAI NESUTARIA": "QUELLEN WIDERSPRECHEN SICH",
           "IŠ DALIES": "TEILWEISE WAHR", "NEĮRODYTA": "NICHT BELEGT"},
    "es": {"FAKTAS": "HECHO", "LEGENDA": "LEYENDA", "LIUDIJIMAS": "TESTIMONIO", "ŠALTINIAI NESUTARIA": "LAS FUENTES NO COINCIDEN",
           "IŠ DALIES": "EN PARTE CIERTO", "NEĮRODYTA": "SIN PRUEBAS"},
    "pt": {"FAKTAS": "FACTO", "LEGENDA": "LENDA", "LIUDIJIMAS": "TESTEMUNHO", "ŠALTINIAI NESUTARIA": "AS FONTES DIVERGEM",
           "IŠ DALIES": "EM PARTE VERDADE", "NEĮRODYTA": "NÃO PROVADO"},
    "pl": {"FAKTAS": "FAKT", "LEGENDA": "LEGENDA", "LIUDIJIMAS": "RELACJA ŚWIADKA", "ŠALTINIAI NESUTARIA": "ŹRÓDŁA SIĘ RÓŻNIĄ",
           "IŠ DALIES": "CZĘŚCIOWO PRAWDA", "NEĮRODYTA": "NIEUDOWODNIONE"},
    "lv": {"FAKTAS": "FAKTS", "LEGENDA": "LEĢENDA", "LIUDIJIMAS": "LIECĪBA", "ŠALTINIAI NESUTARIA": "AVOTI NESAKRĪT",
           "IŠ DALIES": "DAĻĒJI TAISNĪBA", "NEĮRODYTA": "NAV PIERĀDĪTS"},
    "ru": {"FAKTAS": "ФАКТ", "LEGENDA": "ЛЕГЕНДА", "LIUDIJIMAS": "СВИДЕТЕЛЬСТВО", "ŠALTINIAI NESUTARIA": "ИСТОЧНИКИ РАСХОДЯТСЯ",
           "IŠ DALIES": "ОТЧАСТИ ПРАВДА", "NEĮRODYTA": "НЕ ДОКАЗАНО"},
    "uk": {"FAKTAS": "ФАКТ", "LEGENDA": "ЛЕГЕНДА", "LIUDIJIMAS": "СВІДЧЕННЯ", "ŠALTINIAI NESUTARIA": "ДЖЕРЕЛА РОЗХОДЯТЬСЯ",
           "IŠ DALIES": "ЧАСТКОВО ПРАВДА", "NEĮRODYTA": "НЕ ДОВЕДЕНО"},
    "zh": {"FAKTAS": "事实", "LEGENDA": "传说", "LIUDIJIMAS": "亲历者证言", "ŠALTINIAI NESUTARIA": "说法不一",
           "IŠ DALIES": "部分属实", "NEĮRODYTA": "未经证实"},
    "ja": {"FAKTAS": "事実", "LEGENDA": "伝説", "LIUDIJIMAS": "証言", "ŠALTINIAI NESUTARIA": "資料で食い違い",
           "IŠ DALIES": "一部本当", "NEĮRODYTA": "未確認"},
}

PROMPT = """Translate this Lithuanian content of the youth audio quest "Operacija Dvina" (former Soviet underground missile base at Plokštinė, now the Cold War Museum in Žemaitija National Park, Lithuania) into {lang}.

Rules:
- Audience 15–25, informal address ({you}). Keep the lively spoken style: it will be voiced by text-to-speech.
- Translate meaning, not word by word. Do NOT add, drop or change any fact, number, date, name or place.
- Keep every source tag like [S1] or [T3] exactly, at the end of the same sentence.
- Keep Lithuanian place and person names in Latin script as they are (Plokštinė, Plateliai, Šateikiai, Beržoras, Judita Šatkauskienė…), also in Cyrillic, Chinese and Japanese text. Do not translate "Operacija Dvina".
- Every number that is written with digits in the original (dates, years, measurements, counts) stays in Arabic digits with the same value (no 万, no 千).
- Words like "one", "a", "none", "first" that are words in the original stay natural words in the translation (e.g. 一个, 第一, ни одной, ningún) – never turn them into digits.
- Military terms: R-12, SS-4, megaton, regiment ("79-asis raketinis pulkas" = 79th Missile Regiment).
- Translate only the string values listed in the JSON below. Return ONLY the same JSON structure with translated values, nothing else.

{payload}"""

key = os.environ.get("MODEL_API_KEY", "")


def call(lang, payload):
    prompt = PROMPT.format(lang=LANGS[lang][0], you=LANGS[lang][1],
                           payload=json.dumps(payload, ensure_ascii=False, indent=1))
    body = json.dumps({"model": "muse-spark-1.3", "max_tokens": 12000,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.meta.ai/v1/messages", data=body, headers={
        "content-type": "application/json", "anthropic-version": "2023-06-01",
        "x-api-key": key, "authorization": f"Bearer {key}"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                resp = json.load(r)
            raw = "".join(c.get("text", "") for c in resp["content"] if c["type"] == "text")
            return json.loads(raw[raw.index("{"): raw.rindex("}") + 1]), resp["usage"]["output_tokens"]
        except Exception as e:
            print("retry", lang, str(payload)[:50], e)
    return None, 0



def main():
    global LANGS
    LANGS = {k: ALL_LANGS[k] for k in (sys.argv[1:] or ["en", "de"])}
    jobs = []
    for lang in LANGS:
        for e in Q["episodes"]:
            jobs.append((lang, "episode", e["n"], {"title": e["title"], "script": e["script"]}))
        for m in Q["missions"]:
            jobs.append((lang, "mission", m["n"], {"title": m["title"], "story": m["story"], "task": m["task"],
                                                   "question": m["quiz"]["question"], "options": m["quiz"]["options"],
                                                   "answer": m["quiz"]["answer"]}))
        for i, l in enumerate(L):
            jobs.append((lang, "legend", i, {"claim": l["claim"], "reveal": l["reveal"]}))

    results, tokens = {lang: {"episodes": {}, "missions": {}, "legends": {}} for lang in LANGS}, 0
    previous = json.loads((CONTENT / "translations.json").read_text(encoding="utf-8")) if (CONTENT / "translations.json").exists() else {}
    with ThreadPoolExecutor(12) as pool:
        for (lang, kind, idx, payload), (out, used) in zip(jobs, pool.map(lambda j: call(j[0], j[3]), jobs)):
            tokens += used
            if out:
                results[lang][kind + "s"][str(idx)] = out
            else:
                print("FAILED", lang, kind, idx)

    for lang in LANGS:
        for i, l in enumerate(L):
            if str(i) in results[lang]["legends"]:
                results[lang]["legends"][str(i)]["verdict"] = VERDICTS[lang][l["verdict"]]
    previous.update(results)
    (CONTENT / "translations.json").write_text(json.dumps(previous, ensure_ascii=False, indent=2), encoding="utf-8")
    print("jobs:", len(jobs), "output tokens:", tokens,
          {lang: {k: len(v) for k, v in r.items()} for lang, r in results.items()})


if __name__ == "__main__":
    main()
