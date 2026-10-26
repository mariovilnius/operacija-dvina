# Demo video script (3:00)

The video must show only what was built during the hackathon: the quest content, the pipeline, the verifier, the app, the QR unlock and the narration. The plateliai.lt platform was built earlier, so it is not shown.

The narration is in English, voiced by `en-GB-RyanNeural`. Screen scenes are recorded from the live app at phone size (390×844), framed in a dark 16:9 canvas. At about 150 words per minute the narration runs 2:50, which leaves room to breathe.

| # | Time | On screen | Narration |
|---|---|---|---|
| 1 | 0:00–0:15 | Title card: "Operacija Dvina", with the stamp "TOP SECRET · 1962–1978". Then a slow zoom on the app's home screen. | In a forest in western Lithuania, under a layer of sand, the Soviet Union hid four nuclear missiles aimed at Western Europe. Today it's the Cold War Museum. We built a game that makes young people want to go there. |
| 2 | 0:15–0:35 | Split screen: a generic AI chatbot answer with a made-up "fact" crossed out in red, next to an Operacija Dvina paragraph with its [S1] tags highlighted. | AI travel guides have a problem: they invent things. At a site about nuclear weapons and occupation, one invented fact is one too many. So in Operacija Dvina, every sentence has a source, and you can tap it. |
| 3 | 0:35–1:00 | App: language picker, then English. Episode 1 plays with narration, and a tap on a tag opens the park directorate's page. | It starts at home. Three short audio episodes, each ending on a mystery you can only solve on site. Every fact is tagged: S for official sources, T for named witnesses. Tap one and you're on the original page. |
| 4 | 1:00–1:25 | A wall QR poster, a phone scanning it, and Mission 4 unlocking. Then the story, the task ("pace out 23 metres") and the quiz with its proof quote. | At the museum, every station has a QR code on the wall. Scan it and the mission unlocks: a story, a task like pacing out the twenty-three metres of the missile, and a quiz, with the proof shown straight from the source. |
| 5 | 1:25–1:55 | A legend card: "Warheads were stored in the secret hangar". The six verdict buttons appear, the player picks FACT, and the answer turns out to be PARTLY TRUE, with Stanislovas Puidokas named. | The best part comes from the neighbours. People who grew up next to the barbed wire tell stories. Some are true and some are legends. The player decides: fact, legend, testimony, sources disagree, partly true or unproven. Then the evidence decides. |
| 6 | 1:55–2:25 | Pipeline diagram: sources → Muse Wonder writes and cites → verify.py → Muse Spark translates → 11 flags. Then a terminal running `python verify.py` and printing OK. | Under the hood, Meta's Muse Wonder writes only from five official sources and five recorded testimonies, and returns the exact quote behind every sentence. A verifier fails the build if any quote, number or name can't be found. Muse Spark then translates everything into ten more languages, and the same checks run again. |
| 7 | 2:25–2:45 | The app cycling through Lithuanian, Japanese, Ukrainian and Spanish, with the Lithuanian narration audible. | Eleven languages, with neural-voice narration, even in Lithuanian, which most phones can't speak. One small rural museum, every visitor group covered. |
| 8 | 2:45–3:00 | End card with the live link (plateliai.lt/game, or the GitHub Pages link), the GitHub repo, and "Built with Meta Muse Wonder & Muse Spark". | Operacija Dvina. Listen at home, crack it on site, and trust what you hear. |

## Production checklist

- [x] Lithuanian and English narration clips generated (`make_audio.py lt en`)
- [x] Narration for the video itself generated (`tools/video/make_video.py`, en-GB-RyanNeural via edge-tts)
- [x] App scenes recorded at 390×844 (Playwright screen recording)
- [ ] QR scan scene: filmed on a real phone, or shown as the poster plus the unlock screen
- [x] Scene 2 uses a plain statement card instead of a mock chatbot
- [x] Assembled with ffmpeg into a 1920×1080 MP4 (2:05), into `build/video/` (not committed)
- [x] Uploaded to YouTube: https://youtu.be/FxC7kLP3XLo
