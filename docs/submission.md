# Hackathon submission texts

Draft answers for the Cerebral Valley submission form. Only describe what actually works at submission time, and update the bracketed items before submitting.

## Theme

Build for Your World

## Project Description

Operacija Dvina turns Plokštinė into a game for 15–25 year olds. Plokštinė is a Soviet underground nuclear missile base hidden in a Lithuanian forest, and today it is the Cold War Museum. The game starts with remote audio episodes that hook you at home. At the museum you play missions with quizzes and "Legend or fact?" cards, built from the memories of locals who lived next to the barbed wire.

The problem: AI travel guides invent facts, and at a site about nuclear weapons and occupation, invented facts are unacceptable. In Operacija Dvina, Meta's Muse models write every sentence only from official sources and named witnesses, and every fact is tagged with its source ([S1], [T3]). A verifier fails the build if any quote, number, name or quiz answer can't be found in its source.

The quest is available in 11 languages: Lithuanian, English, German, Spanish, Portuguese, Polish, Latvian, Russian, Ukrainian, Chinese and Japanese.

Live: https://mariovilnius.github.io/operacija-dvina/

## Public GitHub Repository

https://github.com/mariovilnius/operacija-dvina

## 3-Minute Demo Video

https://youtu.be/FxC7kLP3XLo

## Describe your use of Meta products to build the submitted project

- **muse-wonder-1.0** (Meta Model API) is the author. It wrote a 10-stop factual script strictly from 5 official sources (Žemaitija National Park Directorate, the Lithuanian national encyclopedia and others), then rewrote those facts as 3 remote episodes and 7 on-site missions with tasks and quizzes. For every sentence it returns the exact supporting quote, so the pipeline can check it.
- **muse-wonder-1.0** also weighed 10 local legends against 5 recorded testimonies and the official sources, and gave each card one of six verdicts: fact, legend, testimony, sources disagree, partly true or unproven. Each card names the narrator.
- **muse-spark-1.3** translated the whole quest and the app interface into 10 languages, keeping source tags, numbers and Lithuanian names intact. 160+ translation calls were checked automatically.
- The Meta Model API's Anthropic-compatible endpoint let us drive everything from a plain Python pipeline with no SDK.

## Why are Meta's models important to your solution?

Lithuanian is a small language, and a youth audience notices clumsy text immediately. Muse Wonder writes natural, lively Lithuanian, and it reliably returns verbatim evidence quotes that we can check mechanically, which is what makes "no invented facts" enforceable rather than a promise. Muse Spark is fast enough to translate the quest into 10 languages in minutes, so one small team can serve every visitor group of a rural museum. Using one model family for writing, translating and checking keeps style and terminology consistent across all 11 languages.

## Feedback on Meta products

- The Anthropic-compatible Messages endpoint made integration trivial, and tool calling worked on the first try.
- Reasoning budgets are very large: about 3,000–4,000 thinking tokens for a 150-word text. When we batched 16 items into one request, the whole budget went to thinking and the JSON came back cut off. A reasoning-effort setting would help a lot.
- Occasional HTTP 500 errors; a simple retry fixed them.
- When told "keep numbers as digits", Spark also turned "one" and "none" into digits, which sounded unnatural in Russian, Chinese and Japanese. More specific wording fixed it.
- Model verdicts were sometimes too confident: 2 of 10 legend verdicts needed a human correction.
- There's no text-to-speech endpoint in the Model API. A voice model for small languages would complete the stack for audio guides.

## Feedback on partner technologies

[Fill in only if Baseten, Modal or Fireworks gets used; otherwise leave blank.]

## Permission checkbox

The user decides on this. It allows Meta and Cerebral Valley to use and promote the submitted materials.
