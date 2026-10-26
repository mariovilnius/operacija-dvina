import json, os, sys, urllib.request, pathlib
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8")
from paths import RAW, CONTENT, DOCS
oral = RAW / "oral"
OFFICIAL = json.loads((RAW / "sources.json").read_text(encoding="utf-8"))


def text(name, start=None, end=None):
    t = (oral / name).read_text(encoding="utf-8")
    if start and start in t:
        t = t[t.index(start):]
    if end and end in t:
        t = t[:t.index(end)]
    return t.strip()


TESTIMONIES = {
    "T1": {"title": "Apie slaptą branduolinės bazės angarą", "narrator": "Stanislovas Puidokas, vietinis gyventojas",
           "recorded_by": "Aušra Brazdeikytė (ŽNPD archyvas)", "url": "https://militaryheritagetourism.info/lt/military/stories/view/360",
           "text": text("mht360.txt", end=" || META")},
    "T2": {"title": "Slaptas veterinaras", "narrator": "Stanislovas Mikašauskas, buvęs veterinarijos gydytojas, vėliau kolūkio pirmininkas",
           "recorded_by": "Aušra Brazdeikytė", "url": "https://militaryheritagetourism.info/lt/military/stories/view/361",
           "text": text("mht361.txt", end=" || META")},
    "T3": {"title": "K. Meškausko prisiminimai apie Plungės rajono raketų bazes", "narrator": "Kajetonas Meškauskas, statybos dalinio gydytojas",
           "recorded_by": "Eugenijus Bunka, 2005-08-09", "url": "https://militaryheritagetourism.info/lt/military/stories/view/374",
           "text": text("mht374.txt", end=" || META")},
    "T4": {"title": "Branduolinės ginkluotės pėdsakais Šateikių girioje", "narrator": "Silvestras Baumila, buvęs Plungės komendantūros darbuotojas",
           "recorded_by": "laikraštis „Žemaitis“", "url": "https://militaryheritagetourism.info/lt/military/stories/view/381",
           "text": text("mht381.txt", end=" || META")},
    "T5": {"title": "Liepdavo užsitraukti užuolaidas: gyvenimas prie branduolinių raketų bazės šalia Platelių", "narrator": "Judita Šatkauskienė (gidė, užaugusi Beržore) ir Eugenijus Bunka (kraštotyrininkas)",
           "recorded_by": "Simas Prašmantas, LRT.lt, 2025-09-28", "url": "https://www.lrt.lt/naujienos/lietuvoje/2/2685545/liepdavo-uzsitraukti-uzuolaidas-gyvenimas-prie-branduoliniu-raketu-bazes-salia-plateliu",
           "text": text("lrt.txt", "„Grynas Stalkeris", "# Aplink Lietuvą")},
}

# Curated claims: (mission number it belongs to, claim, which sources settle it)
CLAIMS = [
    (1, "Bazę statė tik estai, kad nesusikalbėtų su vietiniais, o lietuvių į statybininkus neėmė", "T3, T5, S3"),
    (1, "Visos keturios šachtos buvo iškastos per 8 mėnesius", "T3, S1"),
    (1, "Kelias į bazę išklotas skylėtomis betono plokštėmis tam, kad pro skyles želianti žolė slėptų jį nuo palydovų", "T5"),
    (2, "Studentas su žiūronu stebėjo paukščius prie bazės ir buvo tardomas tris paras", "T5"),
    (2, "Veterinaras į bazę buvo įvežamas pasislėpęs po malkomis sunkvežimyje", "T2"),
    (3, "Pro kaimus naktimis važiuojant kolonoms gyventojams liepdavo užsitraukti užuolaidas tik tam, kad niekas nepamatytų įrangos", "T3, T5"),
    (4, "Slaptame angare Plokštinės miške buvo laikomos branduolinės raketų galvutės", "T1, S1"),
    (5, "Iš Plokštinės bazės po mišku ėjo ilgi slapti tuneliai", "T2"),
    (6, "Apie Šateikių bazės statybą „Amerikos balsui“ išplepėjo vietos klebonas", "T3"),
    (7, "Kariškiai bazę paliko 1979 metais", "S1, S3, T5"),
]

PROMPT = """Kuri vieną užduotį „Legenda ar faktas?“ jaunimo questui „Operacija Dvina“ (Plokštinės raketų bazė, Šaltojo karo muziejus).
Auditorija – 15–25 m. Kalba – gyva lietuvių, kreipinys „tu“, bet be pigių juokelių ir be karo romantizavimo.

Teiginys, kurį žaidėjas turi įvertinti:
„{claim}“
Šaltiniai, kurie tai išsprendžia: {settle}

Verdiktas – vienas iš:
- "FAKTAS" – patvirtina oficialus šaltinis (S…);
- "LEGENDA" – šaltiniai paneigia arba paaiškina kitaip;
- "LIUDIJIMAS" – taip pasakoja liudininkas, bet oficialiai nepatikrinta;
- "ŠALTINIAI NESUTARIA" – skirtingi šaltiniai sako skirtingai.

Griežtos taisyklės:
- Naudok TIK pateiktus šaltinius. Nieko neišgalvok.
- Pasakotojų žodžius perpasakok savais žodžiais. Tiesioginė citata – daugiausia viena, iki 12 žodžių.
- Paaiškinime aiškiai pasakyk, KAS taip pasakoja (vardas ir kas jis).
- "reveal" – 50–90 žodžių, įgarsinamas tekstas, atskleidžiantis atsakymą; faktų sakinių gale žymos [S1]…[T5].

Grąžink TIK JSON:
{{"claim": "teiginys, kaip jį išgirsta žaidėjas (iki 25 žodžių)", "verdict": "FAKTAS|LEGENDA|LIUDIJIMAS|ŠALTINIAI NESUTARIA",
 "reveal": "...", "sources": ["T3", "S1"], "evidence": [{{"source": "T3", "quote": "trumpa pažodinė citata iš šaltinio"}}], "xp": 50}}

OFICIALŪS ŠALTINIAI:
{official}

LIUDIJIMAI:
{testimonies}
"""

key = os.environ["MODEL_API_KEY"]
official = "\n\n".join(f"[{k}] {v['title']}\n{v['text']}" for k, v in OFFICIAL.items())
testimonies = "\n\n".join(f"[{k}] {v['title']}. Pasakoja: {v['narrator']}. Užrašė: {v['recorded_by']}\n{v['text']}" for k, v in TESTIMONIES.items())


def ask(item):
    mission, claim, settle = item
    prompt = PROMPT.format(claim=claim, settle=settle, official=official, testimonies=testimonies)
    body = json.dumps({"model": "muse-wonder-1.0", "max_tokens": 12000,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.meta.ai/v1/messages", data=body, headers={
        "content-type": "application/json", "anthropic-version": "2023-06-01",
        "x-api-key": key, "authorization": f"Bearer {key}"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                resp = json.load(r)
            raw = "".join(c.get("text", "") for c in resp["content"] if c["type"] == "text")
            out = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
            out["mission"] = mission
            return out
        except Exception as e:
            print("retry", claim[:40], e)
    return None


with ThreadPoolExecutor(5) as pool:
    legends = [x for x in pool.map(ask, CLAIMS) if x]
(RAW / "testimonies.json").write_text(json.dumps(TESTIMONIES, ensure_ascii=False, indent=1), encoding="utf-8")
(CONTENT / "legends.lt.json").write_text(json.dumps(legends, ensure_ascii=False, indent=2), encoding="utf-8")
print(len(legends), "of", len(CLAIMS), "written")
