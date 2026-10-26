import json
import pathlib
import sys

from paths import RAW, CONTENT, DOCS
out_dir = DOCS
S = json.loads((RAW / "sources.json").read_text(encoding="utf-8"))
T = json.loads((RAW / "testimonies.json").read_text(encoding="utf-8"))
Q = json.loads((CONTENT / "quest.lt.json").read_text(encoding="utf-8"))
L = json.loads((CONTENT / "legends.lt.json").read_text(encoding="utf-8"))
R = json.loads((CONTENT / "translations.json").read_text(encoding="utf-8"))

UI = {
    "en": {"title": "Plokštinė: “Operacija Dvina” (audio guide and quest), English",
           "intro": ["Draft for the Meta hackathon. Translated from the verified Lithuanian version with `muse-spark-1.3`.",
                     "Checked automatically: every source tag and number matches the Lithuanian original, and every quiz answer is among the options.",
                     "Tags [S1]–[S5] are official sources, [T1]–[T5] are testimonies. Sources are in Lithuanian."],
           "sources": "Sources", "official": "Official", "testimonies": "Testimonies and narrators", "told": "Told by", "rec": "Recorded by",
           "episodes": "Remote episodes (listen before the trip)", "missions": "On-site missions", "mission": "Mission",
           "story": "Story", "task": "Task", "question": "Question", "card": "Legend or fact?", "claim": "Claim", "answer": "Answer"},
    "de": {"title": "Plokštinė: „Operacija Dvina“ (Audioguide und Quest), Deutsch",
           "intro": ["Entwurf für den Meta-Hackathon. Aus der geprüften litauischen Fassung mit `muse-spark-1.3` übersetzt.",
                     "Automatisch geprüft: alle Quellenmarken und Zahlen stimmen mit dem litauischen Original überein, jede Quizantwort steht unter den Optionen.",
                     "Marken [S1]–[S5] sind offizielle Quellen, [T1]–[T5] Zeitzeugenberichte. Die Quellen sind auf Litauisch."],
           "sources": "Quellen", "official": "Offizielle Quellen", "testimonies": "Zeitzeugen und Erzähler", "told": "Erzählt von", "rec": "Aufgezeichnet von",
           "episodes": "Folgen für zu Hause (vor der Reise hören)", "missions": "Missionen vor Ort", "mission": "Mission",
           "story": "Erzählung", "task": "Aufgabe", "question": "Frage", "card": "Legende oder Fakt?", "claim": "Behauptung", "answer": "Antwort"},
}

def ui(title, intro, sources, official, testimonies, told, rec, episodes, missions, mission, story, task, question, card, claim, answer):
    return dict(title=title, intro=intro, sources=sources, official=official, testimonies=testimonies, told=told, rec=rec,
                episodes=episodes, missions=missions, mission=mission, story=story, task=task, question=question, card=card, claim=claim, answer=answer)


CHECK = "`muse-spark-1.3`"
UI.update({
    "es": ui("Plokštinė: «Operacija Dvina» (audioguía y quest), español",
             [f"Borrador para el hackathon de Meta. Traducido de la versión lituana verificada con {CHECK}.",
              "Comprobado automáticamente: etiquetas de fuentes, números y respuestas coinciden con el original lituano.",
              "[S1]–[S5] son fuentes oficiales, [T1]–[T5] testimonios. Las fuentes están en lituano."],
             "Fuentes", "Oficiales", "Testimonios y narradores", "Cuenta", "Recogido por", "Episodios a distancia (escuchar antes del viaje)",
             "Misiones en el lugar", "Misión", "Relato", "Tarea", "Pregunta", "¿Leyenda o hecho?", "Afirmación", "Respuesta"),
    "pt": ui("Plokštinė: «Operacija Dvina» (audioguia e quest), português",
             [f"Rascunho para o hackathon da Meta. Traduzido da versão lituana verificada com {CHECK}.",
              "Verificado automaticamente: etiquetas de fontes, números e respostas coincidem com o original lituano.",
              "[S1]–[S5] são fontes oficiais, [T1]–[T5] testemunhos. As fontes estão em lituano."],
             "Fontes", "Oficiais", "Testemunhos e narradores", "Conta", "Registado por", "Episódios à distância (ouvir antes da viagem)",
             "Missões no local", "Missão", "Relato", "Tarefa", "Pergunta", "Lenda ou facto?", "Afirmação", "Resposta"),
    "pl": ui("Plokštinė: „Operacija Dvina” (audioprzewodnik i quest), polski",
             [f"Szkic na hackathon Meta. Przetłumaczono ze sprawdzonej wersji litewskiej za pomocą {CHECK}.",
              "Sprawdzono automatycznie: oznaczenia źródeł, liczby i odpowiedzi zgadzają się z litewskim oryginałem.",
              "[S1]–[S5] to źródła oficjalne, [T1]–[T5] relacje świadków. Źródła są po litewsku."],
             "Źródła", "Oficjalne", "Relacje i narratorzy", "Opowiada", "Spisał(a)", "Odcinki zdalne (posłuchaj przed podróżą)",
             "Misje na miejscu", "Misja", "Opowieść", "Zadanie", "Pytanie", "Legenda czy fakt?", "Twierdzenie", "Odpowiedź"),
    "lv": ui("Plokštinė: “Operacija Dvina” (audiogids un kvests), latviski",
             [f"Melnraksts Meta hakatonam. Tulkots no pārbaudītās lietuviešu versijas ar {CHECK}.",
              "Automātiski pārbaudīts: avotu atzīmes, skaitļi un atbildes sakrīt ar lietuviešu oriģinālu.",
              "[S1]–[S5] ir oficiālie avoti, [T1]–[T5] liecības. Avoti ir lietuviešu valodā."],
             "Avoti", "Oficiālie", "Liecības un stāstītāji", "Stāsta", "Pierakstīja", "Attālinātās sērijas (klausies pirms brauciena)",
             "Misijas uz vietas", "Misija", "Stāsts", "Uzdevums", "Jautājums", "Leģenda vai fakts?", "Apgalvojums", "Atbilde"),
    "ru": ui("Plokštinė: «Operacija Dvina» (аудиогид и квест), русский",
             [f"Черновик для хакатона Meta. Переведено с проверенной литовской версии с помощью {CHECK}.",
              "Проверено автоматически: метки источников, числа и ответы совпадают с литовским оригиналом.",
              "[S1]–[S5] — официальные источники, [T1]–[T5] — свидетельства. Источники на литовском."],
             "Источники", "Официальные", "Свидетельства и рассказчики", "Рассказывает", "Записал(а)", "Эпизоды на расстоянии (послушай до поездки)",
             "Миссии на месте", "Миссия", "Рассказ", "Задание", "Вопрос", "Легенда или факт?", "Утверждение", "Ответ"),
    "uk": ui("Plokštinė: «Operacija Dvina» (аудіогід і квест), українська",
             [f"Чернетка для хакатону Meta. Перекладено з перевіреної литовської версії за допомогою {CHECK}.",
              "Перевірено автоматично: позначки джерел, числа й відповіді збігаються з литовським оригіналом.",
              "[S1]–[S5] — офіційні джерела, [T1]–[T5] — свідчення. Джерела литовською."],
             "Джерела", "Офіційні", "Свідчення та оповідачі", "Розповідає", "Записав(ла)", "Епізоди на відстані (послухай перед поїздкою)",
             "Місії на місці", "Місія", "Розповідь", "Завдання", "Питання", "Легенда чи факт?", "Твердження", "Відповідь"),
    "zh": ui("Plokštinė：“Operacija Dvina”（语音导览与任务），简体中文",
             [f"Meta 黑客松草稿。由经过核实的立陶宛语版本使用 {CHECK} 翻译。",
              "已自动核对：来源标记、数字和答案均与立陶宛语原文一致。",
              "[S1]–[S5] 为官方来源，[T1]–[T5] 为亲历者证言。来源为立陶宛语。"],
             "来源", "官方来源", "证言与讲述者", "讲述者", "记录者", "远程剧集（出发前收听）",
             "现场任务", "任务", "故事", "挑战", "问题", "传说还是事实？", "说法", "答案"),
    "ja": ui("Plokštinė：「Operacija Dvina」（オーディオガイド＆クエスト）日本語",
             [f"Metaハッカソン用の下書き。検証済みのリトアニア語版から {CHECK} で翻訳。",
              "自動チェック済み：出典タグ・数字・クイズの答えはリトアニア語原文と一致。",
              "[S1]–[S5]は公式資料、[T1]–[T5]は証言。資料はリトアニア語。"],
             "出典", "公式資料", "証言と語り手", "語り手", "記録", "リモートエピソード（旅の前に聴こう）",
             "現地ミッション", "ミッション", "ストーリー", "タスク", "クイズ", "伝説か事実か？", "うわさ", "答え"),
})

ICON = {"FAKTAS": "✅", "LEGENDA": "❌", "LIUDIJIMAS": "🗣️", "ŠALTINIAI NESUTARIA": "⚖️", "IŠ DALIES": "◐", "NEĮRODYTA": "❓"}

for lang in sys.argv[1:] or R.keys():
    u, r = UI[lang], R[lang]
    md = [f"# {u['title']}", "", *u["intro"], "", f"## {u['sources']}", "", f"### {u['official']}", ""]
    md += [f"- **[{k}]** [{s['title']}]({s['url']})" for k, s in S.items()]
    md += ["", f"### {u['testimonies']}", ""]
    md += [f"- **[{k}]** [{t['title']}]({t['url']}). {u['told']}: {t['narrator']}. {u['rec']}: {t['recorded_by']}." for k, t in T.items()]
    md += ["", f"## {u['episodes']}", ""]
    for e in Q["episodes"]:
        tr = r["episodes"][str(e["n"])]
        md += [f"### {e['n']}. {tr['title']}", "", tr["script"], ""]
    md += [f"## {u['missions']}", ""]
    for m in Q["missions"]:
        tr = r["missions"][str(m["n"])]
        md += [f"### {u['mission']} {m['n']}. {tr['title']} (+{m['xp']} XP)", "", f"**{u['story']}:** {tr['story']}", "",
               f"**{u['task']}:** {tr['task']}", "", f"**{u['question']}:** {tr['question']}", ""]
        md += [f"- {'✅ ' if o == tr['answer'] else ''}{o}" for o in tr["options"]]
        md.append("")
        for i, l in enumerate(L):
            if l["mission"] != m["n"]:
                continue
            c = r["legends"][str(i)]
            md += [f"#### 🎴 {u['card']} (+{l.get('xp', 50)} XP)", "", f"**{u['claim']}:** {c['claim']}", "",
                   f"**{u['answer']}:** {ICON[l['verdict']]} {c['verdict']}", "", c["reveal"], "",
                   " ".join(f"[{s}]" for s in l["sources"]), ""]
    (out_dir / f"operacija-dvina.{lang}.md").write_text("\n".join(md), encoding="utf-8", newline="\n")
    print("wrote", lang)

