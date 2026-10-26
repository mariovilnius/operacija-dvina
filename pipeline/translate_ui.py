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
    "missions_hint": "Unlock them with QR codes at the museum",
    "mission_label": "Mission {n}",
    "listen": "Listen",
    "stop": "Stop",
    "back": "Back",
    "scan_title": "Find the QR code on the wall",
    "scan_hint": "Every station in the museum has a QR code. Scan it to unlock that mission.",
    "scan_button": "Scan QR code",
    "scan_camera_hint": "Point your camera at the QR code on the wall",
    "scan_unsupported": "Open your phone's camera app and point it at the QR code on the wall.",
    "bad_code": "This QR code isn't part of the quest.",
    "close": "Close",
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
    "visit_title": "Plan your visit",
    "museum_info": "Opening hours and tickets",
    "museum_photos": "Photos of the museum",
    "museum_page": "The museum on plateliai.lt",
    "nearby_title": "Also around Lake Plateliai",
    "nearby_hint": "Places to visit near Plokštinė, on plateliai.lt",
    "more_places": "All places on plateliai.lt",
    "fig_range": "R-12 range from Plokštinė: the dashed circle is 2,000 km. Highlighted are the countries named as targets, in today's borders (Germany then meant West Germany). Most of Spain lies beyond the circle.",
    "fig_plan": "Schematic plan, not to scale: the control block, 4 shafts, 6 security lines, the military town 500 m away and the 2.5 km water pipe to Lake Plateliai.",
    "fig_section": "A shaft 27 m deep and about 5 m across, with the 23 m R-12 inside (19 m rocket + 4 m warhead) and a 1.8 m person for scale.",
    "video": "Video",
}
LT = {
    "tagline": "Slapta branduolinių raketų bazė po Žemaitijos mišku. Klausyk namie, įmink vietoje.",
    "choose_language": "Pasirink kalbą",
    "episodes": "Serijos",
    "episodes_hint": "Klausyk prieš kelionę",
    "episode_label": "{n} serija",
    "missions": "Misijos",
    "missions_hint": "Atrakinsi QR kodais muziejuje",
    "mission_label": "{n} misija",
    "listen": "Klausyti",
    "stop": "Sustabdyti",
    "back": "Atgal",
    "scan_title": "Surask QR kodą ant sienos",
    "scan_hint": "Kiekvienoje muziejaus stotelėje yra QR kodas. Nuskenuok jį ir atrakinsi tą misiją.",
    "scan_button": "Skenuoti QR kodą",
    "scan_camera_hint": "Nukreipk kamerą į QR kodą ant sienos",
    "scan_unsupported": "Atsidaryk telefono kamerą ir nukreipk ją į QR kodą ant sienos.",
    "bad_code": "Šis QR kodas nepriklauso questui.",
    "close": "Uždaryti",
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
    "visit_title": "Planuok apsilankymą",
    "museum_info": "Darbo laikas ir bilietai",
    "museum_photos": "Muziejaus nuotraukos",
    "museum_page": "Muziejus plateliai.lt",
    "nearby_title": "Dar aplink Platelių ežerą",
    "nearby_hint": "Lankytinos vietos netoli Plokštinės, plateliai.lt",
    "more_places": "Visos vietos plateliai.lt",
    "fig_range": "R-12 nuotolis nuo Plokštinės: punktyrinis apskritimas – 2000 km. Paryškintos šalys, šaltiniuose įvardytos kaip taikiniai, dabartinėmis sienomis (Vokietija tada – Vakarų Vokietija). Didžioji Ispanijos dalis – už apskritimo.",
    "fig_plan": "Schema ne pagal mastelį: valdymo blokas, 4 šachtos, 6 apsaugos linijos, karinis miestelis už 500 m ir 2,5 km vandentiekis iki Platelių ežero.",
    "fig_section": "27 m gylio ir apie 5 m skersmens šachta su 23 m raketa R-12 (19 m raketa nešėja + 4 m galvutė) ir 1,8 m žmogus mastelio palyginimui.",
    "video": "Vaizdo įrašas",
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
