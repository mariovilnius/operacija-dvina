import json, sys, pathlib, re
from concurrent.futures import ThreadPoolExecutor
from paths import RAW, CONTENT, DOCS
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from quest_common import COMMON, ask

TOPICS = ["Atvykimas ir kodėl čia", "Šešios apsaugos linijos", "Karinis miestelis", "Šachtos gaubtas ir raketa R-12",
          "Po žeme (valdymo blokas, pamainos)", "Kuba ir Šateikiai", "Finalas – nė viena raketa nepaleista, kas liko, Platelių ežeras"]

def mission(i):
    prompt = COMMON + f"""
UŽDUOTIS: sukurk VIENĄ misiją vietoje (GPS stotelė Plokštinėje): misija {i+1} iš 7 – „{TOPICS[i]}“.
- "story": 70–110 žodžių įgarsinamas pasakojimas.
- "task": veiksmas vietoje (rask, suskaičiuok, nufotografuok, įsivaizduok, išmatuok žingsniais). Netvirtink, kad dabar vietoje matosi tai, ko šaltiniai nemini; tada rašyk „pabandyk rasti“.
- "quiz": klausimas su 3 variantais, teisingas atsakymas ir pažodinė citata iš šaltinio.
- "xp": 50–150.
Būk glaustas mąstydamas.
Grąžink TIK JSON:
{{"n": {i+1}, "title": "...", "story": "...[S1]...", "task": "...", "quiz": {{"question": "...", "options": ["...","...","..."], "answer": "...", "source": "S1", "quote": "..."}}, "xp": 100, "facts_used": [{{"source": "S1", "quote": "..."}}]}}
"""
    return ask(prompt)

with ThreadPoolExecutor(7) as pool:
    missions = [m for m in pool.map(mission, range(7)) if m]
quest = json.loads((CONTENT / "episodes.lt.json").read_text(encoding="utf-8"))
quest["missions"] = sorted(missions, key=lambda m: m["n"])
(CONTENT / "quest.lt.json").write_text(json.dumps(quest, ensure_ascii=False, indent=2), encoding="utf-8")
print(len(quest["episodes"]), "episodes,", len(quest["missions"]), "missions")
