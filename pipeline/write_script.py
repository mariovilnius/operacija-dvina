import json, os, re, sys, urllib.request, pathlib
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8")
from paths import RAW, CONTENT, DOCS
src = RAW / "src"


def read(name, start=None, end=None):
    t = (src / name).read_text(encoding="utf-8")
    if start:
        t = t[t.index(start):]
    if end and end in t:
        t = t[:t.index(end)]
    return t.strip()


SOURCES = {
    "S1": {
        "title": "Šaltojo karo ekspozicija. Istorija – Žemaitijos nacionalinio parko direkcija",
        "url": "https://zemaitijosnpd.lrv.lt/lt/informacija-atvykstantiems/ekspozicijos/saltojo-karo-ekspozicija-1/istorija/",
        "text": read("lrv-istorija.txt", "Šaltojo karo ekspozicija įsikūrusi", "Atnaujinimo data"),
    },
    "S2": {
        "title": "Ekskursija po buvusį karinį miestelį – Žemaitijos nacionalinio parko direkcija",
        "url": "https://zemaitijosnpd.lrv.lt/lt/informacija-atvykstantiems/ekspozicijos/saltojo-karo-ekspozicija-1/ekskursija-po-buvusi-karini-miesteli/",
        "text": read("lrv-ekskursija-po-buvusi-karini-miesteli.txt", "Buvusios raketinės bazės", "Atstumas"),
    },
    "S3": {
        "title": "Šaltojo karo muziejus – Visuotinė lietuvių enciklopedija",
        "url": "https://www.vle.lt/straipsnis/saltojo-karo-muziejus/",
        "text": read("vle.txt", "Šáltojo", "Plokštinės raketų bazė Kiti šaltiniai"),
    },
    "S4": {
        "title": "Šaltojo karo ekspozicija – Žemaitijos nacionalinis parkas",
        "url": "https://zemaitijosnp.lt/veikla/lankytini-objektai/saltojo-karo-ekspozicija/",
        "text": read("znp.txt", "Tai vienintelė", "Adresas"),
    },
    "S5": {
        "title": "Šaltojo karo ekspozicija – Visit Plungė",
        "url": "https://www.visitplunge.lt/lankytinos-vietos/saltojo-karo-ekspozicija/",
        "text": read("visitplunge.txt", "Tai vienintelė", "360°"),
    },
}

STOPS = [
    ("1", "Kodėl būtent Plokštinė", "Atvykimas į Plokštinės mišką: kodėl ši vieta tiko bazei (aukštis, gruntas, mažai gyventojų, Europa pasiekiama), kelias, pilamas iš šachtų iškasto grunto."),
    ("2", "Bazės gimimas", "Šaltojo karo kontekstas ir statybos pradžia 1960 m. rugsėjį: pirmoji SSRS požeminė raketų bazė, kas ją statė ir kaip kasė šachtas."),
    ("3", "Šešios tvoros", "Saugumas ir slaptumas: 6 apsauginės linijos, teritorijos dydis, spygliuota viela, signalizacija, aukšta įtampa."),
    ("4", "Karinis miestelis", "Karinis miestelis šalia aikštelės: atstumas, pastatai, kiek žmonių gyveno, budėjimo pamainos ir kasdienybė."),
    ("5", "Raketa R-12", "Šachtų gaubtai ir pačios raketos R-12 (SS-4): matmenys, galingumas, nuotolis, kuras, taikiniai ir jų keitimas."),
    ("6", "Po žeme", "Požeminis technologinis (valdymo) blokas: kaip jis įrengtas, kas jame buvo, pamainos po žeme, pirmasis kovinis budėjimas 1962 m. gruodžio 31 d."),
    ("7", "Kuba ir Šateikiai", "79-asis raketinis pulkas, Šateikių bazė, pulko vadai ir dalyvavimas 1962 m. Kubos įvykiuose."),
    ("8", "Uždarymas", "1968 m. parengtis, bazės uždarymas 1978 m., įrangos demontavimas, faktas, kad nė viena raketa nebuvo paleista, nuniokojimas po kariškių pasitraukimo."),
    ("9", "Nuo griuvėsių iki muziejaus", "1992 m. bazė atitenka parkui, Militarizmo ekspozicija, rekonstrukcija ir Šaltojo karo muziejus, kas šiandien matoma ekspozicijoje."),
    ("10", "Vanduo iš Platelių ežero", "Baigiamoji stotelė: 2,5 km vandentiekio tranšėja iki Platelių ežero ir siurbliai, kvietimas tęsti kelionę Platelių apylinkėse."),
]

STYLE_RULES = """Rašai lietuvišką audiogido tekstą Plokštinės (Šaltojo karo) bazės lankytojams. Tekstas bus įgarsintas.

Taisyklės:
- 130–200 žodžių, gyva šnekamoji kalba, kreipiniai „jūs“, trumpi sakiniai, lengvai skaitomi balsu.
- Naudok TIK faktus iš pateiktų šaltinių. Nieko neišgalvok: jokių papildomų datų, skaičių, vardų, legendų ar emocingų „liudininkų“ istorijų.
- Jei šaltiniai skiriasi (pvz., šachtų gylis, galvutės galingumas), naudok S1 duomenis arba pasakyk intervalą.
- Kiekvieno sakinio, kuriame yra faktas, gale įrašyk šaltinio žymą, pvz. [S1] arba [S1][S3].
- Tonas – pagarbus ir dalykiškas; tai karo istorija, ne nuotykių parkas.
- Skaičius rašyk skaitmenimis, kaip šaltinyje.

Grąžink TIK JSON objektą be jokio kito teksto:
{"stop": "...", "title": "...", "script": "tekstas su [S#] žymomis",
 "facts_used": [{"source": "S1", "quote": "trumpa pažodinė citata iš šaltinio"}]}
"""

key = os.environ["MODEL_API_KEY"]


def ask(stop):
    number, title, brief = stop
    sources = "\n\n".join(f"[{sid}] {s['title']}\n{s['text']}" for sid, s in SOURCES.items())
    prompt = f"{STYLE_RULES}\nStotelė {number}: „{title}“\nApie ką: {brief}\nNekartok to, kas priklauso kitoms stotelėms.\n\nŠALTINIAI:\n{sources}"
    body = json.dumps({"model": "muse-wonder-1.0", "max_tokens": 12000,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.meta.ai/v1/messages", data=body, headers={
        "content-type": "application/json", "anthropic-version": "2023-06-01",
        "x-api-key": key, "authorization": f"Bearer {key}"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                resp = json.load(r)
            text = "".join(c.get("text", "") for c in resp["content"] if c["type"] == "text")
            out = json.loads(text[text.index("{"): text.rindex("}") + 1])
            out["stop"], out["title"] = number, title
            return out
        except Exception as e:
            print("retry", number, e)
    return None


with ThreadPoolExecutor(5) as pool:
    stops = [s for s in pool.map(ask, STOPS) if s]
(RAW / "sources.json").write_text(json.dumps(SOURCES, ensure_ascii=False, indent=1), encoding="utf-8")
(CONTENT / "factual_stops.lt.json").write_text(json.dumps(stops, ensure_ascii=False, indent=2), encoding="utf-8")
print(len(stops), "stops written")
