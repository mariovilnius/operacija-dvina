"""Translates the app's interface strings from English with Muse Spark into content/ui.json."""
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor

import translate
from paths import CONTENT

sys.stdout.reconfigure(encoding="utf-8")

EN = {
    "tagline": "A secret nuclear missile base under a Lithuanian forest. Listen at home, crack it on site.",
    "choose_language": "Choose your language",
    "episodes": "Episodes",
    "episodes_hint": "Listen before the trip",
    "episode_label": "Episode {n}",
    "missions": "Missions",
    "missions_hint": "Unlock them on site at Plokštinė",
    "mission_label": "Mission {n}",
    "listen": "Listen",
    "stop": "Stop",
    "back": "Back",
    "locked": "Locked. Come to Plokštinė to unlock it.",
    "check_location": "Check my location",
    "locating": "Checking your location…",
    "too_far": "You're {km} km away. Missions unlock at the Cold War Museum.",
    "location_off": "Location is off. Turn it on to unlock missions.",
    "unlocked": "You're here. Missions unlocked!",
    "demo_mode": "Demo mode: unlock everything",
    "story": "Story",
    "task": "Your task",
    "quiz": "Quiz",
    "correct": "Correct! +{xp} XP",
    "wrong": "Not quite. The answer is: {answer}",
    "proof": "Proof",
    "card_title": "Legend or fact?",
    "card_prompt": "What do you think?",
    "card_right": "You got it! +{xp} XP",
    "card_wrong": "The verdict: {verdict}",
    "sources": "Sources",
    "source_note": "Every fact comes from a source. Tap a tag to see it.",
    "no_voice": "Your device has no voice for this language.",
    "xp_total": "{xp} XP",
}
LT = {
    "tagline": "Slapta branduolinių raketų bazė po Žemaitijos mišku. Klausyk namie, įmink vietoje.",
    "choose_language": "Pasirink kalbą",
    "episodes": "Serijos",
    "episodes_hint": "Klausyk prieš kelionę",
    "episode_label": "{n} serija",
    "missions": "Misijos",
    "missions_hint": "Atrakinsi vietoje, Plokštinėje",
    "mission_label": "{n} misija",
    "listen": "Klausyti",
    "stop": "Sustabdyti",
    "back": "Atgal",
    "locked": "Užrakinta. Atvyk į Plokštinę, kad atrakintum.",
    "check_location": "Patikrinti mano vietą",
    "locating": "Tikrinama tavo vieta…",
    "too_far": "Esi už {km} km. Misijos atsirakina Šaltojo karo muziejuje.",
    "location_off": "Vietos nustatymas išjungtas. Įjunk jį, kad atrakintum misijas.",
    "unlocked": "Tu vietoje. Misijos atrakintos!",
    "demo_mode": "Demo režimas: atrakinti viską",
    "story": "Pasakojimas",
    "task": "Tavo užduotis",
    "quiz": "Klausimas",
    "correct": "Teisingai! +{xp} XP",
    "wrong": "Ne visai. Teisingas atsakymas: {answer}",
    "proof": "Įrodymas",
    "card_title": "Legenda ar faktas?",
    "card_prompt": "Kaip manai?",
    "card_right": "Atspėjai! +{xp} XP",
    "card_wrong": "Verdiktas: {verdict}",
    "sources": "Šaltiniai",
    "source_note": "Kiekvienas faktas turi šaltinį. Paliesk žymą ir pamatysi.",
    "no_voice": "Tavo įrenginyje nėra balso šiai kalbai.",
    "xp_total": "{xp} XP",
}

translate.LANGS = translate.ALL_LANGS
targets = [lang for lang in translate.ALL_LANGS if lang != "en"]
placeholders = {k: set(re.findall(r"\{\w+\}", v)) for k, v in EN.items()}
ui = {"lt": LT, "en": EN}
with ThreadPoolExecutor(len(targets)) as pool:
    for lang, (out, _) in zip(targets, pool.map(lambda lang: translate.call(lang, EN), targets)):
        bad = [k for k in EN if k not in (out or {}) or set(re.findall(r"\{\w+\}", out[k])) != placeholders[k]]
        if bad:
            print("FAILED", lang, bad)
            out = {**EN, **{k: v for k, v in (out or {}).items() if k not in bad}}
        ui[lang] = out
(CONTENT / "ui.json").write_text(json.dumps(ui, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
print("ui strings:", len(EN), "languages:", ", ".join(ui))
