"""Writes the "creepy stories" bonus episode from the witness testimonies with Muse Wonder.

Retells (never copies) the memories in [T1]–[T5], names every narrator, and returns the quote
behind each fact so verify.py can check it. Output: content/stories.lt.json.
"""
import json
import sys

from paths import CONTENT, RAW
from quest_common import ask

sys.stdout.reconfigure(encoding="utf-8")
official = json.loads((RAW / "sources.json").read_text(encoding="utf-8"))
testimonies = json.loads((RAW / "testimonies.json").read_text(encoding="utf-8"))
sources = "\n\n".join(f"[{k}] {v['title']}\n{v['text']}" for k, v in {"S1": official["S1"]}.items())
witnesses = "\n\n".join(f"[{k}] {v['title']}. Pasakoja: {v['narrator']}. Užrašė: {v['recorded_by']}\n{v['text']}"
                        for k, v in testimonies.items())

PROMPT = f"""Parašyk bonusinę audio seriją „Šiurpios istorijos iš už spygliuotos vielos“ jaunimo questui „Operacija Dvina“
(Plokštinės raketų bazė). Ji bus įgarsinta, trukmė 3–4 minutės: 450–550 žodžių lietuviškai.

Turinys – vietinių žmonių ir tarnavusiųjų prisiminimai iš LIUDIJIMŲ: gyvenimas šalia bazės, naktinės kolonos ir užuolaidos,
kareiviai prie langų, nuodingas kuras, studentas su žiūronu, veterinaras po malkomis, slaptas angaras, kareivis ant kelmelio,
pirmasis žingsnis į apleistą bunkerį. Pasirink 5–6 stipriausias istorijas ir sujunk jas į vieną pasakojimą.

Stilius: tamsi, įtaigi atmosfera, kaip geras siaubo podcast'as – tyla, tamsa, šnabždesiai, bet BE išgalvotų detalių.
Kreipinys „tu“. Trumpi sakiniai. Kiekvienos istorijos pradžioje aiškiai pasakyk, kas ją pasakoja (vardas ir kas jis).
Pabaigoje – kvietimas atvykti į Plokštinės muziejų.

Griežtos taisyklės:
- Naudok TIK faktus iš LIUDIJIMŲ ir S1. Jokių išgalvotų vardų, datų, skaičių, dialogų ar įvykių.
- Perpasakok savais žodžiais. Tiesioginės citatos – daugiausia dvi, kiekviena iki 10 žodžių.
- Mirtį (kareivis ant kelmelio) pasakok pagarbiai, be sensacijos.
- Kiekvieno fakto sakinio gale – šaltinio žyma [T5], [T2], [S1] ir t. t.

Grąžink TIK JSON:
{{"title": "...", "script": "...[T5]...", "facts_used": [{{"source": "T5", "quote": "trumpa pažodinė citata iš šaltinio"}}]}}

OFICIALUS ŠALTINIS:
{sources}

LIUDIJIMAI:
{witnesses}
"""

story = ask(PROMPT)
(CONTENT / "stories.lt.json").write_text(json.dumps(story, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(story.get("title"), len(story.get("script", "").split()), "words")
