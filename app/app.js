/* Operacija Dvina: static mobile web app. All content comes from data/quest.json. */
(() => {
  "use strict";

  const view = document.getElementById("view");
  const xpEl = document.getElementById("xp");
  const langBtn = document.getElementById("lang-btn");
  let data = null;

  // Per-device progress. Storage can be unavailable (private mode), so every access is guarded.
  const STORE_KEY = "operacija-dvina";
  const state = Object.assign(
    { lang: null, quizzes: {}, cards: {}, unlocked: false, demo: false },
    (() => { try { return JSON.parse(localStorage.getItem(STORE_KEY)) || {}; } catch { return {}; } })()
  );
  const save = () => { try { localStorage.setItem(STORE_KEY, JSON.stringify(state)); } catch { /* not persisted */ } };

  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const lang = () => state.lang || "en";
  const t = (key, vars = {}) => (data.ui[lang()][key] ?? data.ui.en[key]).replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? "");
  const tx = (item) => item.text[lang()] || item.text.en;
  const isOpen = () => state.unlocked || state.demo;
  const QUOTES = { lt: ["„", "“"], de: ["„", "“"], pl: ["„", "”"], lv: ["“", "”"], ru: ["«", "»"], uk: ["«", "»"],
    es: ["«", "»"], pt: ["«", "»"], zh: ["“", "”"], ja: ["「", "」"] };
  const quoted = (s) => { const [a, b] = QUOTES[lang()] || ["“", "”"]; return a + esc(s) + b; };

  function totalXp() {
    let xp = 0;
    for (const m of data.missions) if (state.quizzes[m.n]?.right) xp += m.xp;
    for (const c of data.cards) if (state.cards[c.id] === c.verdict) xp += c.xp;
    return xp;
  }

  /** Renders text with [S1]/[T3] tags as tappable source links. */
  function withTags(text) {
    const link = (id) => {
      const src = data.sources[id];
      if (!src) return "";
      return `<a class="tag ${id[0] === "T" ? "t" : ""}" href="${esc(src.url)}" target="_blank" rel="noopener" title="${esc(src.title)}">${id}</a>`;
    };
    // Tags go in front of the sentence's closing punctuation and stay on one line with it:
    // "fact. [S1] Next" reads "fact[S1]. Next".
    return esc(text.trim())
      .replace(/([.!?。！？])\s*((?:\[[ST]\d\]\s*)+)/g, (_, p, tags) => {
        const ids = tags.match(/[ST]\d/g);
        const gap = /[。！？]/.test(p) ? "" : " ";
        return `<span class="nw">${ids.map(link).join("")}${p}</span>${gap}`;
      })
      .replace(/\[([ST]\d)\]/g, (_, id) => link(id))
      .trim();
  }
  const plain = (text) => text.replace(/\s*\[[ST]\d\]/g, "");

  // Speech: browser voices for now, until the generated audio is in place.
  let speaking = null;
  function speak(text, button) {
    const synth = window.speechSynthesis;
    if (!synth) return alert(t("no_voice"));
    if (speaking === button) { synth.cancel(); return; }
    synth.cancel();
    const code = data.languages.find((l) => l.code === lang()).speech;
    const utter = new SpeechSynthesisUtterance(plain(text));
    utter.lang = code;
    const voice = synth.getVoices().find((v) => v.lang.replace("_", "-").toLowerCase().startsWith(lang()));
    if (voice) utter.voice = voice;
    else button.insertAdjacentHTML("afterend", `<span class="note">${esc(t("no_voice"))}</span>`);
    const label = button.textContent;
    utter.onend = utter.onerror = () => { speaking = null; button.textContent = label; };
    speaking = button;
    button.textContent = "■ " + t("stop");
    synth.speak(utter);
  }

  function distanceKm(a, b) {
    const rad = (d) => (d * Math.PI) / 180;
    const h = Math.sin(rad(b.lat - a.lat) / 2) ** 2 +
      Math.cos(rad(a.lat)) * Math.cos(rad(b.lat)) * Math.sin(rad(b.lng - a.lng) / 2) ** 2;
    return 6371 * 2 * Math.asin(Math.sqrt(h));
  }

  function checkLocation(statusEl) {
    if (!navigator.geolocation) { statusEl.textContent = t("location_off"); return; }
    statusEl.textContent = t("locating");
    navigator.geolocation.getCurrentPosition((pos) => {
      const here = { lat: pos.coords.latitude, lng: pos.coords.longitude };
      const target = data.missions[0].location;
      const km = distanceKm(here, target);
      if (km * 1000 <= target.radius_m) {
        state.unlocked = true; save(); render();
      } else {
        statusEl.textContent = t("too_far", { km: km < 10 ? km.toFixed(1) : Math.round(km) });
      }
    }, () => { statusEl.textContent = t("location_off"); }, { enableHighAccuracy: true, timeout: 15000 });
  }

  // Views
  function home() {
    const missionCards = data.missions.map((m) => {
      const done = state.quizzes[m.n] !== undefined;
      const cls = `card ${isOpen() ? "" : "locked"} ${done ? "done" : ""}`;
      const inner = `<div class="kicker">${esc(t("mission_label", { n: m.n }))} · +${m.xp} XP</div><div class="title">${esc(tx(m).title)}</div>`;
      return `<li>${isOpen() ? `<a class="${cls}" href="#/mission/${m.n}">${inner}</a>` : `<div class="${cls}">${inner}</div>`}</li>`;
    }).join("");
    view.innerHTML = `
      <section class="hero">
        <span class="stamp">TOP SECRET · 1962–1978</span>
        <h1>Operacija Dvina</h1>
        <p class="lead">${esc(t("tagline"))}</p>
      </section>
      <h3>${esc(t("episodes"))} · ${esc(t("episodes_hint"))}</h3>
      <ul class="list">${data.episodes.map((e) => `
        <li><a class="card" href="#/episode/${e.n}">
          <div class="kicker">${esc(t("episode_label", { n: e.n }))}</div>
          <div class="title">${esc(tx(e).title)}</div></a></li>`).join("")}
      </ul>
      <h3>${esc(t("missions"))} · ${esc(t("missions_hint"))}</h3>
      ${isOpen() ? "" : `<div class="panel"><p class="note">${esc(t("locked"))}</p>
        <div class="row"><button class="btn" id="locate">${esc(t("check_location"))}</button></div>
        <p class="status" id="status" aria-live="polite"></p></div>`}
      <ul class="list" style="margin-top:12px">${missionCards}</ul>
      <label class="toggle"><input type="checkbox" id="demo" ${state.demo ? "checked" : ""}> ${esc(t("demo_mode"))}</label>
      <h3>${esc(t("sources"))}</h3>
      <p class="note">${esc(t("source_note"))}</p>
      <ul class="sources">${Object.entries(data.sources).map(([id, s]) =>
        `<li><a class="tag ${id[0] === "T" ? "t" : ""}" href="${esc(s.url)}" target="_blank" rel="noopener">${id}</a> ${esc(s.title)}${s.narrator ? ` · ${esc(s.narrator)}` : ""}</li>`).join("")}</ul>`;
    document.getElementById("locate")?.addEventListener("click", () => checkLocation(document.getElementById("status")));
    document.getElementById("demo").addEventListener("change", (e) => { state.demo = e.target.checked; save(); render(); });
  }

  function episode(n) {
    const e = data.episodes.find((x) => x.n === n);
    if (!e) return home();
    const { title, script } = tx(e);
    view.innerHTML = `
      <a class="back" href="#/">← ${esc(t("back"))}</a>
      <div class="kicker" style="font:600 11px var(--mono);letter-spacing:.14em;color:var(--accent)">${esc(t("episode_label", { n }))}</div>
      <h2>${esc(title)}</h2>
      <div class="row"><button class="btn" id="listen">▶ ${esc(t("listen"))}</button></div>
      <div class="prose panel"><p>${withTags(script)}</p></div>`;
    const btn = document.getElementById("listen");
    btn.addEventListener("click", () => speak(script, btn));
  }

  function mission(n) {
    const m = data.missions.find((x) => x.n === n);
    if (!m || !isOpen()) return home();
    const text = tx(m);
    const answered = state.quizzes[n];
    const cards = data.cards.filter((c) => c.mission === n);
    view.innerHTML = `
      <a class="back" href="#/">← ${esc(t("back"))}</a>
      <div class="kicker" style="font:600 11px var(--mono);letter-spacing:.14em;color:var(--accent)">${esc(t("mission_label", { n }))} · +${m.xp} XP</div>
      <h2>${esc(text.title)}</h2>
      <h3>${esc(t("story"))}</h3>
      <div class="row"><button class="btn" id="listen">▶ ${esc(t("listen"))}</button></div>
      <div class="prose panel"><p>${withTags(text.story)}</p></div>
      <h3>${esc(t("task"))}</h3>
      <div class="panel"><p style="margin:0">${withTags(text.task)}</p></div>
      <h3>${esc(t("quiz"))}</h3>
      <div class="panel" id="quiz">
        <p style="margin:0;font-weight:600">${esc(text.question)}</p>
        <div class="options">${text.options.map((o, i) => `<button class="option" data-i="${i}">${esc(o)}</button>`).join("")}</div>
        <div id="quiz-result"></div>
      </div>
      ${cards.map((c) => cardHtml(c)).join("")}`;
    const btn = document.getElementById("listen");
    btn.addEventListener("click", () => speak(text.story, btn));
    view.querySelectorAll("#quiz .option").forEach((b) => b.addEventListener("click", () => {
      const i = +b.dataset.i;
      // Store the option index so the answer survives a language switch.
      state.quizzes[n] = { i, right: text.options[i] === text.answer }; save(); mission(n); updateXp();
    }));
    if (answered !== undefined) showQuiz(m, text, answered.i);
    cards.forEach((c) => {
      view.querySelectorAll(`[data-card="${c.id}"] .option`).forEach((b) => b.addEventListener("click", () => {
        state.cards[c.id] = b.dataset.v; save(); mission(n); updateXp();
        document.querySelector(`[data-card="${c.id}"]`).scrollIntoView({ block: "center" });
      }));
    });
  }

  function showQuiz(m, text, chosen) {
    const right = text.options[chosen] === text.answer;
    view.querySelectorAll("#quiz .option").forEach((b) => {
      const i = +b.dataset.i;
      b.disabled = true;
      if (text.options[i] === text.answer) b.classList.add("right");
      else if (i === chosen) b.classList.add("wrong");
    });
    const src = data.sources[m.proof.source];
    document.getElementById("quiz-result").innerHTML = `
      <p class="result ${right ? "good" : "bad"}">${esc(right ? t("correct", { xp: m.xp }) : t("wrong", { answer: text.answer }))}</p>
      <p class="quote">${esc(t("proof"))}: „${esc(m.proof.quote)}“
        <a class="tag" href="${esc(src.url)}" target="_blank" rel="noopener" title="${esc(src.title)}">${m.proof.source}</a></p>`;
  }

  function cardHtml(c) {
    const text = tx(c);
    const chosen = state.cards[c.id];
    const labels = data.verdicts[lang()] || data.verdicts.en;
    const buttons = data.verdict_order.map((v) => {
      const cls = chosen === undefined ? "" : v === c.verdict ? "right" : v === chosen ? "wrong" : "";
      return `<button class="option ${cls}" data-v="${v}" ${chosen !== undefined ? "disabled" : ""}>${esc(labels[v])}</button>`;
    }).join("");
    const reveal = chosen === undefined ? "" : `
      <p class="result ${chosen === c.verdict ? "good" : "bad"}">${esc(chosen === c.verdict ? t("card_right", { xp: c.xp }) : t("card_wrong", { verdict: labels[c.verdict] }))}</p>
      <div class="prose"><p>${withTags(text.reveal)}</p></div>`;
    return `
      <h3>🎴 ${esc(t("card_title"))} · +${c.xp} XP</h3>
      <div class="panel legend-card" data-card="${c.id}">
        <p class="claim">${quoted(text.claim)}</p>
        <p class="note" style="margin:0">${esc(t("card_prompt"))}</p>
        <div class="options verdicts">${buttons}</div>
        ${reveal}
      </div>`;
  }

  function languages() {
    view.innerHTML = `
      <section class="hero"><span class="stamp">TOP SECRET · 1962–1978</span><h1>Operacija Dvina</h1>
      <p class="lead">${data.languages.map((l) => esc(data.ui[l.code].choose_language)).slice(0, 3).join(" · ")}</p></section>
      <div class="langs">${data.languages.map((l) =>
        `<button class="option ${l.code === state.lang ? "active" : ""}" data-lang="${l.code}" lang="${l.code}">${esc(l.name)}</button>`).join("")}</div>`;
    view.querySelectorAll("[data-lang]").forEach((b) => b.addEventListener("click", () => {
      state.lang = b.dataset.lang; save();
      // On first visit the hash is already "#/", so no hashchange fires.
      if (location.hash === "#/") render(); else location.hash = "#/";
    }));
  }

  function updateXp() {
    xpEl.textContent = t("xp_total", { xp: totalXp() });
  }

  function render() {
    window.speechSynthesis?.cancel();
    const route = location.hash.replace(/^#\/?/, "").split("/");
    if (!state.lang || route[0] === "lang") languages();
    else if (route[0] === "episode") episode(+route[1]);
    else if (route[0] === "mission") mission(+route[1]);
    else home();
    document.documentElement.lang = lang();
    langBtn.textContent = lang();
    updateXp();
    view.focus({ preventScroll: true });
    window.scrollTo(0, 0);
  }

  fetch("data/quest.json")
    .then((r) => r.json())
    .then((json) => { data = json; window.addEventListener("hashchange", render); render(); })
    .catch(() => { view.innerHTML = "<p>Could not load the quest. Please reload.</p>"; });
})();
