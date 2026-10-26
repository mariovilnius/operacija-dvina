"""Translates the stories episode (content/stories.lt.json) into all languages with Muse Spark."""
import json
import sys
from concurrent.futures import ThreadPoolExecutor

import translate
from paths import CONTENT

sys.stdout.reconfigure(encoding="utf-8")
story = json.loads((CONTENT / "stories.lt.json").read_text(encoding="utf-8"))
path = CONTENT / "translations.json"
tr = json.loads(path.read_text(encoding="utf-8"))
langs = [lang for lang in translate.ALL_LANGS if lang in tr]
with ThreadPoolExecutor(len(langs)) as pool:
    results = list(pool.map(lambda lang: translate.call(lang, {"title": story["title"], "script": story["script"]}), langs))
for lang, (out, _) in zip(langs, results):
    if out:
        tr[lang].setdefault("stories", {})["1"] = out
    else:
        print("FAILED", lang)
path.write_text(json.dumps(tr, ensure_ascii=False, indent=2), encoding="utf-8")
print("stories translated:", ", ".join(lang for lang in langs if "stories" in tr[lang]))
