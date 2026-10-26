# Operacija Dvina

A youth audio quest about Plokštinė, a former Soviet underground nuclear missile base in Lithuania that is now the Cold War Museum in Žemaitija National Park. Built for the Meta Global AI Developer Hackathon (Oct 26 – Nov 4, 2026).

AI travel guides make things up. This one doesn't: every sentence comes from an official source or a named witness, and a script checks that before anything is published.

## What's in it

- **3 remote episodes** you listen to at home. Each ends on a mystery you can only solve on site.
- **7 on-site missions** with a short story, a task (find, count, pace out the 23 m missile) and a quiz.
- **10 "Legend or fact?" cards** built from local witnesses' memories, such as "the warheads were kept in the secret hangar" or "no Lithuanians worked on the build". Each card names who tells the story and gives one of six verdicts: fact, legend, testimony, sources disagree, partly true or unproven.
- **11 languages:** Lithuanian, English, German, Spanish, Portuguese, Polish, Latvian, Russian, Ukrainian, Chinese and Japanese.

Read the quest in [English](docs/operacija-dvina.en.md). The Lithuanian original is [operacija-dvina.lt.md](docs/operacija-dvina.lt.md), and the other languages are in [docs/](docs/).

## The app

**Try it: [mariovilnius.github.io/operacija-dvina](https://mariovilnius.github.io/operacija-dvina/)**. Switch on demo mode to open the missions away from the museum.

`app/` is a static mobile web app with no build step:

- **Language picker** for all 11 languages.
- **Episodes** you can read or listen to at home.
- **Missions** unlock by GPS at the Cold War Museum. A demo switch unlocks them anywhere.
- **Quizzes** show a proof quote from the source.
- **Legend cards** let you pick one of six verdicts before the reveal.
- **XP** and progress are saved on the device.
- **Source tags** like [S1] or [T3] in every text open the original source.

Run it locally:

```bash
python -m http.server 8765 --directory app
```

All mission points currently sit on the museum (OSM node 410889888) with a 600 m radius. Per-mission points still need to be surveyed on site. Listening uses the browser's own voices for now.

## How Meta's models are used

| Step | Model | What it does |
|---|---|---|
| Factual script | `muse-wonder-1.0` | Writes 10 stops strictly from the official sources and tags every fact with its source |
| Episodes and missions | `muse-wonder-1.0` | Rewrites the facts for 15–25 year olds: second person, cliffhangers, tasks and quizzes |
| Legend or fact? | `muse-wonder-1.0` | Weighs each local legend against witnesses and official sources and writes the reveal |
| Translations | `muse-spark-1.3` | Translates into 10 languages and keeps tags, numbers and names intact |
| App interface | `muse-spark-1.3` | Translates the app's interface strings and keeps placeholders like `{xp}` intact |

## Verification

`pipeline/verify.py` fails the build when:

- a quote the model cites is not in the cited source,
- a number in a story is not in any source,
- a translation loses a source tag, a number or a Lithuanian name,
- a quiz answer is not among its options.

Two model verdicts were too strong and were corrected by hand: the hangar is "partly true" and the tunnels are "unproven". See `pipeline/fix_legends.py`.

## Sources

Official: [Žemaitija National Park Directorate](https://zemaitijosnpd.lrv.lt/lt/informacija-atvykstantiems/ekspozicijos/saltojo-karo-ekspozicija-1/istorija/), [Visuotinė lietuvių enciklopedija](https://www.vle.lt/straipsnis/saltojo-karo-muziejus/), [zemaitijosnp.lt](https://zemaitijosnp.lt/veikla/lankytini-objektai/saltojo-karo-ekspozicija/) and [Visit Plungė](https://www.visitplunge.lt/lankytinos-vietos/saltojo-karo-ekspozicija/).

Testimonies:
- Stanislovas Puidokas, Stanislovas Mikašauskas and Kajetonas Meškauskas, recorded by Aušra Brazdeikytė and Eugenijus Bunka on [militaryheritagetourism.info](https://militaryheritagetourism.info/lt/military/stories/view/374).
- Judita Šatkauskienė and Eugenijus Bunka in [LRT.lt, 2025](https://www.lrt.lt/naujienos/lietuvoje/2/2685545/liepdavo-uzsitraukti-uzuolaidas-gyvenimas-prie-branduoliniu-raketu-bazes-salia-plateliu).

The source texts belong to their publishers and are not in this repository. Only links and short verification quotes are kept.

## Run the pipeline

Python 3.11+, standard library only.

```bash
export MODEL_API_KEY=...            # Meta Model API key
cd pipeline
python fetch_sources.py             # sources -> data/raw (not committed)
python write_script.py              # factual 10-stop script
python write_episodes.py            # remote episodes
python write_missions.py            # on-site missions
python write_legends.py             # legend-or-fact cards
python fix_legends.py               # editorial corrections
python translate.py en de es pt pl lv ru uk zh ja
python translate_ui.py              # app interface strings
python verify.py                    # must print OK
python build_doc.py && python build_lang_doc.py
python build_app_data.py            # app/data/quest.json
```

Each step calls the API, and Muse models reason at length. Translating one language costs about 55–80k output tokens.

## Next

- Voice: generated audio for all 11 languages instead of browser voices.
- Survey a GPS point for each mission on site.
- Illustrations with Muse Image, clearly labelled as illustrations.

## License

[CC BY 4.0](LICENSE). Source texts and testimonies remain the property of their authors and publishers.
