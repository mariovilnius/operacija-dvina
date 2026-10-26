import json, os, sys, urllib.request, pathlib
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8")
from paths import RAW, CONTENT, DOCS
SOURCES = json.loads((RAW / "sources.json").read_text(encoding="utf-8"))
SOURCE_TEXT = "\n\n".join(f"[{sid}] {s['title']}\n{s['text']}" for sid, s in SOURCES.items())

COMMON = """Kuri turinį questui „Operacija Dvina“ apie buvusią sovietinę požeminę raketų bazę Plokštinėje (dabar Šaltojo karo muziejus, Žemaitijos nacionalinis parkas).
Auditorija – 15–25 m. jaunimas. Tikslas – kad jiems būtų įdomu ir jie norėtų atvažiuoti.

Stilius:
- Gyva, šiuolaikiška lietuvių kalba, kreipinys „tu“. Trumpi sakiniai, ritmas kaip geram podcast'ui ar TikTok pasakojimui.
- Intriga, klausimai, „įsivaizduok…“, kontrastai. Bet be pigių juokelių apie branduolinį karą, be karo romantizavimo ir be „cringe“ slengo.
- Tekstai bus įgarsinti – rašyk taip, kad būtų gera klausytis.

Griežtos faktų taisyklės:
- Naudok TIK faktus iš ŠALTINIŲ. Jokių išgalvotų datų, skaičių, vardų, liudininkų, dialogų ar legendų.
- Galima kurti situacijas antruoju asmeniu („įsivaizduok, kad budi po žeme“), bet jose minimi faktai turi būti iš šaltinių.
- Jei šaltiniai skiriasi, naudok S1.
- Kiekvieno fakto sakinio gale – žyma [S1], [S3] ir t. t.
- Klausimų atsakymai turi būti tiksliai šaltiniuose; pridėk citatą.
"""

EPISODES = COMMON + """
UŽDUOTIS: parašyk 3 NUOTOLINES serijas (klausomas namuose, prieš kelionę). Kiekviena 120–170 žodžių, baigiasi „cliffhangeriu“ – paslaptimi ar klausimu, į kurį atsakymą žmogus gaus tik atvykęs į Plokštinę.
1 serija – „Miškas, kurio nebuvo žemėlapiuose“ (slapta statyba, kodėl čia).
2 serija – „Taikinys: Europa“ (raketos, taikiniai, Kuba).
3 serija – „Diena, kai jie išėjo“ (uždarymas, kas liko, kvietimas atvažiuoti).

Grąžink TIK JSON:
{"episodes": [{"n": 1, "title": "...", "script": "...[S1]...", "cliffhanger": "paskutinis sakinys-kvietimas", "facts_used": [{"source": "S1", "quote": "..."}]}]}
"""

MISSIONS = COMMON + """
UŽDUOTIS: sukurk 7 misijas VIETOJE (GPS stotelės Plokštinėje). Kiekvienai misijai:
- "story": 70–110 žodžių įgarsinamas pasakojimas.
- "task": veiksmas vietoje (rask, suskaičiuok, nufotografuok, įsivaizduok, išmatuok žingsniais). Neteik, kad dabar vietoje matosi tai, ko šaltiniai nemini; jei nesi tikras, rašyk „pabandyk rasti“.
- "quiz": klausimas su 3 atsakymų variantais, teisingas atsakymas ir citata iš šaltinio, įrodanti atsakymą.
- "xp": 50–150.
Misijos: 1 Atvykimas ir kodėl čia; 2 Šešios apsaugos linijos; 3 Karinis miestelis; 4 Šachtos gaubtas ir raketa R-12; 5 Po žeme (valdymo blokas, pamainos); 6 Kuba ir Šateikiai; 7 Finalas – nė viena raketa nepaleista, kas liko, Platelių ežeras.

Grąžink TIK JSON:
{"missions": [{"n": 1, "title": "...", "story": "...[S1]...", "task": "...", "quiz": {"question": "...", "options": ["...", "...", "..."], "answer": "...", "source": "S1", "quote": "..."}, "xp": 100, "facts_used": [{"source": "S1", "quote": "..."}]}]}
"""

key = os.environ["MODEL_API_KEY"]


def ask(prompt):
    body = json.dumps({"model": "muse-wonder-1.0", "max_tokens": 24000,
                       "messages": [{"role": "user", "content": prompt + "\nŠALTINIAI:\n" + SOURCE_TEXT}]}).encode()
    req = urllib.request.Request("https://api.meta.ai/v1/messages", data=body, headers={
        "content-type": "application/json", "anthropic-version": "2023-06-01",
        "x-api-key": key, "authorization": f"Bearer {key}"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=900) as r:
                resp = json.load(r)
            text = "".join(c.get("text", "") for c in resp["content"] if c["type"] == "text")
            print("stop:", resp["stop_reason"], resp["usage"]["output_tokens"])
            return json.loads(text[text.index("{"): text.rindex("}") + 1])
        except Exception as e:
            print("retry", e)
    return {}


