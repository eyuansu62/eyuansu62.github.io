const STORAGE_KEY = "sentence_cards_v1";

const TARGET_LANG_GOOGLE = "zh-CN"; // Simplified Chinese
const TARGET_LANG_BING = "zh-Hans"; // Bing uses BCP-47-ish tags like zh-Hans / zh-Hant

const MYMEMORY_ENDPOINT = "https://api.mymemory.translated.net/get";

const STOPWORDS = new Set([
  "a",
  "about",
  "above",
  "after",
  "again",
  "against",
  "all",
  "am",
  "an",
  "and",
  "any",
  "are",
  "aren't",
  "as",
  "at",
  "be",
  "because",
  "been",
  "before",
  "being",
  "below",
  "between",
  "both",
  "but",
  "by",
  "can",
  "can't",
  "cannot",
  "could",
  "couldn't",
  "did",
  "didn't",
  "do",
  "does",
  "doesn't",
  "doing",
  "don't",
  "down",
  "during",
  "each",
  "few",
  "for",
  "from",
  "further",
  "had",
  "hadn't",
  "has",
  "hasn't",
  "have",
  "haven't",
  "having",
  "he",
  "he'd",
  "he'll",
  "he's",
  "her",
  "here",
  "here's",
  "hers",
  "herself",
  "him",
  "himself",
  "his",
  "how",
  "how's",
  "i",
  "i'd",
  "i'll",
  "i'm",
  "i've",
  "if",
  "in",
  "into",
  "is",
  "isn't",
  "it",
  "it's",
  "its",
  "itself",
  "let's",
  "me",
  "more",
  "most",
  "mustn't",
  "my",
  "myself",
  "no",
  "nor",
  "not",
  "of",
  "off",
  "on",
  "once",
  "only",
  "or",
  "other",
  "ought",
  "our",
  "ours",
  "ourselves",
  "out",
  "over",
  "own",
  "same",
  "shan't",
  "she",
  "she'd",
  "she'll",
  "she's",
  "should",
  "shouldn't",
  "so",
  "some",
  "such",
  "than",
  "that",
  "that's",
  "the",
  "their",
  "theirs",
  "them",
  "themselves",
  "then",
  "there",
  "there's",
  "these",
  "they",
  "they'd",
  "they'll",
  "they're",
  "they've",
  "this",
  "those",
  "through",
  "to",
  "too",
  "under",
  "until",
  "up",
  "very",
  "was",
  "wasn't",
  "we",
  "we'd",
  "we'll",
  "we're",
  "we've",
  "were",
  "weren't",
  "what",
  "what's",
  "when",
  "when's",
  "where",
  "where's",
  "which",
  "while",
  "who",
  "who's",
  "whom",
  "why",
  "why's",
  "will",
  "won't",
  "with",
  "would",
  "wouldn't",
  "you",
  "you'd",
  "you'll",
  "you're",
  "you've",
  "your",
  "yours",
  "yourself",
  "yourselves",
]);

const DAY_MS = 24 * 60 * 60 * 1000;
const MAX_SUGGESTED_WORDS = 40;

const $ = (sel) => document.querySelector(sel);

const SAMPLE_SENTENCES_INTERMEDIATE_V1 = [
  "I kept putting it off until the deadline forced my hand.",
  "She took it personally, even though it wasn't about her.",
  "The plan sounds good on paper, but it might fall apart in practice.",
  "I ran into an old friend on the subway, and we talked for an hour.",
  "Once you get the hang of it, the process is pretty straightforward.",
  "I don't want to jump to conclusions without the full context.",
  "Let's break the problem down into smaller, manageable steps.",
  "He apologized, but his tone made it feel half-hearted.",
  "I backed up my files just in case something went wrong.",
  "The meeting dragged on because no one wanted to make a decision.",
  "This feature is useful, but it comes with a trade-off in performance.",
  "She is meticulous about details, which saves us from painful mistakes.",
  "I tried to cut corners, and it ended up costing me more time.",
  "The instructions were vague, so I figured it out by trial and error.",
  "We should prioritize what matters instead of reacting to every message.",
  "If you can spare five minutes, I would appreciate your feedback.",
  "He raised a valid concern, so we adjusted the timeline.",
  "The data points to a trend, but the sample size is still small.",
  "I was tempted to quit, but I decided to stick with it.",
  "By and large, people respond well when you set clear expectations.",
  "I don't agree with the approach, but I understand the reasoning behind it.",
  "The new policy is meant to reduce friction, not add bureaucracy.",
  "She handled the criticism with grace and a sense of humor.",
  "I made a mental note to follow up after the call.",
  "The result was unexpected, but it makes sense in hindsight.",
  "We reached a compromise that everyone could live with.",
  "He tends to overpromise, which puts the team in a tough spot.",
  "I couldn't focus until I cleared my desk and my mind.",
  "The app is simple to use, yet powerful enough for daily study.",
  "I want to sound natural, not perfect.",
  "The explanation was clear, but the example made it click.",
  "I keep a list of phrases that I want to borrow in my own writing.",
  "If I had started earlier, I wouldn't be rushing right now.",
  "She asked for help, which took a lot of courage.",
  "The more you listen, the more nuances you start to notice.",
  "I learned to say \"I don't know\" without feeling embarrassed.",
  "This habit is hard to build, but easy to lose.",
  "The idea is compelling, but we should test it before we commit.",
  "I don't want to waste your time, so I'll get straight to the point.",
  "When something feels off, it's worth investigating instead of ignoring it.",
  "I came across a phrase that perfectly captured what I meant.",
  "He toned down his opinion after hearing the other side.",
  "Don't take it for granted that people know what you want.",
  "I had to put up with a few glitches before it stabilized.",
  "She stepped up when things got messy.",
  "I don't want to settle for \"good enough\" if we can do better.",
  "The sooner we align on goals, the smoother the project will go.",
  "I rewrote the sentence until it sounded like something I'd actually say.",
  "I prefer to learn in context rather than memorize isolated vocabulary.",
  "It took a few tries, but eventually it worked out.",
];

function now() {
  return Date.now();
}

const translationCache = new Map();
let translateBusy = false;

async function myMemoryTranslate(text, { from = "en", to = TARGET_LANG_GOOGLE } = {}) {
  const q = stableTrim(text);
  if (!q) return "";
  const key = `${from}|${to}|${q}`;
  if (translationCache.has(key)) return translationCache.get(key);

  const url = `${MYMEMORY_ENDPOINT}?q=${encodeURIComponent(q)}&langpair=${encodeURIComponent(from)}|${encodeURIComponent(to)}`;
  const res = await fetch(url, { method: "GET" });
  if (!res.ok) throw new Error(`Translate failed (HTTP ${res.status})`);
  const data = await res.json();

  const translatedText = data?.responseData?.translatedText;
  if (typeof translatedText !== "string") throw new Error("Translate failed (no text)");
  const out = stableTrim(translatedText);
  if (!out) throw new Error("Translate failed (empty)");

  // MyMemory sometimes returns warnings/limits as "translations".
  if (/REQUEST LIMIT/i.test(out) || /MYMEMORY WARNING/i.test(out)) {
    throw new Error(out);
  }

  translationCache.set(key, out);
  return out;
}

async function runTranslateTask(fn) {
  if (translateBusy) {
    setStatus("Translation already running... please wait.");
    return;
  }
  translateBusy = true;
  try {
    await fn();
  } finally {
    translateBusy = false;
  }
}

function clamp(n, lo, hi) {
  return Math.max(lo, Math.min(hi, n));
}

function stableTrim(s) {
  return String(s ?? "").replace(/\r\n/g, "\n").trim();
}

function normalizeApostrophes(s) {
  // Normalize common curly apostrophes to ASCII.
  return String(s ?? "").replace(/[\u2018\u2019]/g, "'");
}

function normalizeWord(w) {
  let s = normalizeApostrophes(w).toLowerCase();
  s = s.replace(/^'+|'+$/g, "");
  return s;
}

function extractWords(text) {
  const s = normalizeApostrophes(text);
  const m = s.match(/[A-Za-z]+(?:'[A-Za-z]+)*/g) || [];
  return m.map(normalizeWord).filter(Boolean);
}

function guessPos(word) {
  if (word.endsWith("ly")) return "adv?";
  if (/(tion|ment|ness|ity|ship|ism|ance|ence)$/.test(word)) return "noun?";
  if (/(ous|ful|able|ible|ive|al|ic|less)$/.test(word)) return "adj?";
  if (/(ate|ify|ise|ize|en)$/.test(word)) return "verb?";
  return "";
}

function suggestWords(sentence) {
  const words = extractWords(sentence);
  const seen = new Set();
  const out = [];
  for (const w of words) {
    if (seen.has(w)) continue;
    seen.add(w);
    if (STOPWORDS.has(w)) continue;
    if (w.length < 4) continue;
    out.push(w);
    if (out.length >= MAX_SUGGESTED_WORDS) break;
  }
  return out;
}

function formatDate(ts) {
  const d = new Date(ts);
  const fmt = new Intl.DateTimeFormat(undefined, { year: "numeric", month: "short", day: "2-digit" });
  return fmt.format(d);
}

function relDays(ts) {
  const diff = ts - now();
  return Math.round(diff / DAY_MS);
}

function buildGoogleTranslateUrl(text, { sl = "en", tl = TARGET_LANG_GOOGLE } = {}) {
  const q = encodeURIComponent(String(text ?? ""));
  return `https://translate.google.com/?sl=${encodeURIComponent(sl)}&tl=${encodeURIComponent(tl)}&text=${q}&op=translate`;
}

function buildBingTranslateUrl(text, { from = "en", to = TARGET_LANG_BING } = {}) {
  const q = encodeURIComponent(String(text ?? ""));
  return `https://www.bing.com/translator?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}&text=${q}`;
}

function buildCambridgeEnZhUrl(word) {
  // Cambridge English -> Chinese (Simplified) dictionary.
  return `https://dictionary.cambridge.org/dictionary/english-chinese-simplified/${encodeURIComponent(String(word ?? ""))}`;
}

function openExternal(url) {
  try {
    window.open(url, "_blank", "noopener,noreferrer");
  } catch {
    // Fallback
    location.href = url;
  }
}

function fmtDue(ts) {
  const days = relDays(ts);
  if (days === 0) return `today (${formatDate(ts)})`;
  if (days === 1) return `tomorrow (${formatDate(ts)})`;
  if (days === -1) return `yesterday (${formatDate(ts)})`;
  if (days < 0) return `${Math.abs(days)}d overdue (${formatDate(ts)})`;
  return `in ${days}d (${formatDate(ts)})`;
}

function shuffleInPlace(arr) {
  for (let i = arr.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
}

function newId() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
  return `id_${Math.random().toString(16).slice(2)}_${Date.now().toString(16)}`;
}

function defaultSrs() {
  return {
    dueAt: now(),
    intervalDays: 0,
    ease: 2.5,
    reps: 0,
    lapses: 0,
    lastReviewedAt: 0,
    lastQuality: 0,
  };
}

function updateSm2(srs, quality) {
  let ease = typeof srs.ease === "number" ? srs.ease : 2.5;
  let reps = typeof srs.reps === "number" ? srs.reps : 0;
  let intervalDays = typeof srs.intervalDays === "number" ? srs.intervalDays : 0;
  let lapses = typeof srs.lapses === "number" ? srs.lapses : 0;

  if (quality < 3) {
    reps = 0;
    intervalDays = 1;
    lapses += 1;
  } else {
    reps += 1;
    if (reps === 1) intervalDays = 1;
    else if (reps === 2) intervalDays = 6;
    else intervalDays = Math.max(1, Math.round(intervalDays * ease));
  }

  ease = ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02));
  ease = Math.max(1.3, ease);

  return {
    dueAt: now() + intervalDays * DAY_MS,
    intervalDays,
    ease,
    reps,
    lapses,
    lastReviewedAt: now(),
    lastQuality: quality,
  };
}

function emptyState() {
  return {
    version: 1,
    cards: [],
    lexicon: {},
  };
}

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return emptyState();
    const obj = JSON.parse(raw);
    if (!obj || typeof obj !== "object") return emptyState();
    const cards = Array.isArray(obj.cards) ? obj.cards : [];
    const lexicon = obj.lexicon && typeof obj.lexicon === "object" ? obj.lexicon : {};
    return {
      version: 1,
      cards: cards.filter((c) => c && typeof c === "object").map(normalizeCard),
      lexicon: normalizeLexicon(lexicon),
    };
  } catch {
    return emptyState();
  }
}

function saveState() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    setStatus(`Saved. Cards: ${state.cards.length}. Words: ${Object.keys(state.lexicon).length}.`);
  } catch (e) {
    console.error(e);
    setStatus("Save failed (localStorage quota?). Export a backup and clear space.", "danger");
  }
}

function normalizeLexicon(lexicon) {
  const out = {};
  for (const [k, v] of Object.entries(lexicon)) {
    const w = normalizeWord(k);
    if (!w) continue;
    if (!v || typeof v !== "object") continue;
    const t = stableTrim(v.translation ?? v.t ?? "");
    const n = stableTrim(v.notes ?? v.n ?? "");
    const updatedAt = Number(v.updatedAt ?? v.u ?? 0) || 0;
    out[w] = { translation: t, notes: n, updatedAt };
  }
  return out;
}

function normalizeCard(card) {
  const id = typeof card.id === "string" && card.id ? card.id : newId();
  const sentence = stableTrim(card.sentence ?? card.s ?? "");
  const source = stableTrim(card.source ?? "");
  const translation = stableTrim(card.translation ?? card.tr ?? "");
  const notes = stableTrim(card.notes ?? "");
  const targets = Array.isArray(card.targets) ? card.targets : Array.isArray(card.words) ? card.words : [];
  const cleanedTargets = [];
  const seen = new Set();
  for (const w of targets) {
    const nw = normalizeWord(w);
    if (!nw || seen.has(nw)) continue;
    seen.add(nw);
    cleanedTargets.push(nw);
  }
  const createdAt = Number(card.createdAt ?? card.c ?? 0) || now();
  const updatedAt = Number(card.updatedAt ?? card.u ?? 0) || createdAt;
  const srsRaw = card.srs && typeof card.srs === "object" ? card.srs : defaultSrs();
  const srs = {
    ...defaultSrs(),
    ...srsRaw,
    dueAt: Number(srsRaw.dueAt ?? srsRaw.d ?? now()) || now(),
    intervalDays: Number(srsRaw.intervalDays ?? srsRaw.i ?? 0) || 0,
    ease: Number(srsRaw.ease ?? srsRaw.e ?? 2.5) || 2.5,
    reps: Number(srsRaw.reps ?? srsRaw.r ?? 0) || 0,
    lapses: Number(srsRaw.lapses ?? srsRaw.l ?? 0) || 0,
    lastReviewedAt: Number(srsRaw.lastReviewedAt ?? srsRaw.lr ?? 0) || 0,
    lastQuality: Number(srsRaw.lastQuality ?? srsRaw.lq ?? 0) || 0,
  };

  return {
    id,
    sentence,
    source,
    translation,
    notes,
    targets: cleanedTargets,
    createdAt,
    updatedAt,
    srs,
  };
}

function byId(id) {
  return state.cards.find((c) => c.id === id) || null;
}

function upsertLexicon(word, translation, notes = "") {
  const w = normalizeWord(word);
  if (!w) return;
  const t = stableTrim(translation);
  const n = stableTrim(notes);
  if (!t && !n) return;
  const prev = state.lexicon[w] || { translation: "", notes: "", updatedAt: 0 };
  state.lexicon[w] = {
    translation: t || prev.translation,
    notes: n || prev.notes,
    updatedAt: now(),
  };
}

function getDueCards() {
  return state.cards.filter((c) => (c.srs?.dueAt ?? 0) <= now()).sort((a, b) => a.srs.dueAt - b.srs.dueAt);
}

function domainFromUrl(url) {
  try {
    const u = new URL(url);
    return u.hostname.replace(/^www\./, "");
  } catch {
    return "";
  }
}

function setStatus(msg, tone = "normal") {
  const el = $("#footerStatus");
  if (!el) return;
  el.textContent = msg;
  el.style.color = tone === "danger" ? "#7a271a" : "";
}

function setRoute(route, pushHash = true) {
  const safe = ROUTES.includes(route) ? route : "capture";
  for (const v of document.querySelectorAll(".view")) {
    v.classList.toggle("active", v.dataset.view === safe);
  }
  for (const t of document.querySelectorAll(".tab")) {
    t.classList.toggle("active", t.dataset.route === safe);
  }
  if (pushHash) {
    location.hash = safe;
  }
  if (safe === "deck") {
    renderDeck();
    renderLexicon();
  } else if (safe === "review") {
    renderReviewStats();
    renderReview();
  }
}

function currentRoute() {
  const h = (location.hash || "").replace(/^#/, "");
  return ROUTES.includes(h) ? h : "capture";
}

function splitLines(text) {
  return stableTrim(text)
    .split("\n")
    .map((s) => s.trim())
    .filter(Boolean);
}

const ROUTES = ["capture", "review", "deck", "io", "about"];

let state = loadState();

// Capture draft word state: word -> { checked, translation, manual }
let captureDraft = {};
let captureManualOrder = [];

let deckDueOnly = false;

let reviewSession = null;
// { queue: [cardId...], idx: 0, revealed: false, shuffled: false }

function resetCaptureDraft() {
  captureDraft = {};
  captureManualOrder = [];
  renderSuggestedWords();
}

function setCaptureWord(word, patch) {
  const w = normalizeWord(word);
  if (!w) return;
  const prev = captureDraft[w] || { checked: true, translation: "", manual: false };
  captureDraft[w] = { ...prev, ...patch };
}

function rebuildSuggestionsFromSentence({ keepTranslations = true } = {}) {
  const sentence = stableTrim($("#captureSentence").value);
  const auto = suggestWords(sentence);

  // Delete old auto words that are no longer present.
  for (const [w, v] of Object.entries(captureDraft)) {
    if (v.manual) continue;
    if (!auto.includes(w)) delete captureDraft[w];
  }

  for (const w of auto) {
    const existing = captureDraft[w];
    const lexT = state.lexicon[w]?.translation || "";
    if (!existing) {
      captureDraft[w] = {
        checked: true,
        translation: lexT,
        manual: false,
      };
      continue;
    }
    if (!keepTranslations) continue;
    if (!existing.translation && lexT) existing.translation = lexT;
  }

  renderSuggestedWords();
}

function renderSuggestedWords() {
  const container = $("#suggestedWords");
  container.textContent = "";

  const sentence = stableTrim($("#captureSentence").value);
  const autoOrder = suggestWords(sentence);
  const words = [...autoOrder, ...captureManualOrder.filter((w) => captureDraft[w]?.manual)];

  if (words.length === 0) {
    const empty = document.createElement("div");
    empty.className = "panel-sub";
    empty.textContent = "Type a sentence to see suggested words.";
    container.appendChild(empty);
    return;
  }

  for (const w of words) {
    const d = captureDraft[w] || { checked: true, translation: "", manual: false };
    const row = document.createElement("div");
    row.className = "word-row";

    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.checked = !!d.checked;
    cb.dataset.word = w;
    cb.className = "word-check";

    const left = document.createElement("div");
    const wEl = document.createElement("div");
    wEl.className = "w";
    wEl.textContent = w;
    const meta = document.createElement("div");
    meta.className = "meta";
    const pos = guessPos(w);
    const inLex = state.lexicon[w]?.translation ? "lex" : "";
    const flags = [pos, inLex, d.manual ? "manual" : ""].filter(Boolean).join(" ");
    meta.textContent = flags ? flags : " ";

    const links = document.createElement("div");
    links.className = "mini-links";
    const aDict = document.createElement("a");
    aDict.className = "mini-link";
    aDict.href = buildCambridgeEnZhUrl(w);
    aDict.target = "_blank";
    aDict.rel = "noopener noreferrer";
    aDict.textContent = "Cambridge";
    const aTr = document.createElement("a");
    aTr.className = "mini-link";
    aTr.href = buildGoogleTranslateUrl(w, { sl: "en", tl: TARGET_LANG_GOOGLE });
    aTr.target = "_blank";
    aTr.rel = "noopener noreferrer";
    aTr.textContent = "Translate";
    links.appendChild(aDict);
    links.appendChild(aTr);
    left.appendChild(wEl);
    left.appendChild(meta);
    left.appendChild(links);

    const tr = document.createElement("input");
    tr.type = "text";
    tr.placeholder = "translation (optional)";
    tr.value = d.translation || "";
    tr.dataset.word = w;
    tr.className = "word-translation";

    row.appendChild(cb);
    row.appendChild(left);
    row.appendChild(tr);

    container.appendChild(row);
  }
}

function collectCaptureTargets() {
  const out = [];
  for (const [w, d] of Object.entries(captureDraft)) {
    if (!d.checked) continue;
    out.push(w);
  }
  // Keep capture rendering order (auto first, then manual).
  const sentence = stableTrim($("#captureSentence").value);
  const order = [...suggestWords(sentence), ...captureManualOrder];
  return order.filter((w) => out.includes(w));
}

function createCard({ sentence, source, translation, notes, targets }) {
  const t = Array.isArray(targets) ? targets.map(normalizeWord).filter(Boolean) : [];
  const seen = new Set();
  const uniq = [];
  for (const w of t) {
    if (seen.has(w)) continue;
    seen.add(w);
    uniq.push(w);
  }
  return normalizeCard({
    id: newId(),
    sentence,
    source,
    translation,
    notes,
    targets: uniq,
    createdAt: now(),
    updatedAt: now(),
    srs: defaultSrs(),
  });
}

function loadSampleDeckIntermediate() {
  const ok = confirm(
    "Load 50 sample cards (intermediate) into your deck? This will not delete existing cards."
  );
  if (!ok) return;

  const existing = new Set(
    state.cards.map((c) => stableTrim(normalizeApostrophes(c.sentence)).toLowerCase())
  );

  let added = 0;
  let skipped = 0;
  for (let i = SAMPLE_SENTENCES_INTERMEDIATE_V1.length - 1; i >= 0; i -= 1) {
    const s = SAMPLE_SENTENCES_INTERMEDIATE_V1[i];
    const key = stableTrim(normalizeApostrophes(s)).toLowerCase();
    if (!key) continue;
    if (existing.has(key)) {
      skipped += 1;
      continue;
    }
    const card = createCard({
      sentence: s,
      source: "",
      translation: "",
      notes: "",
      targets: suggestWords(s),
    });
    state.cards.unshift(card);
    existing.add(key);
    added += 1;
  }

  saveState();
  renderAll();
  setStatus(`Loaded sample deck. Added ${added}, skipped ${skipped}.`);
}

function captureSaveCards(e) {
  e.preventDefault();

  const text = stableTrim($("#captureSentence").value);
  const source = stableTrim($("#captureSource").value);
  const translation = stableTrim($("#captureTranslation").value);
  const notes = stableTrim($("#captureNotes").value);
  const bulk = !!$("#captureBulk").checked;

  if (!text) {
    setStatus("Nothing to save. Paste a sentence first.", "danger");
    return;
  }

  if (bulk) {
    const lines = splitLines(text);
    if (lines.length === 0) {
      setStatus("Nothing to save.", "danger");
      return;
    }

    let added = 0;
    for (const line of lines) {
      const targets = suggestWords(line);
      const card = createCard({
        sentence: line,
        source,
        translation: "",
        notes: "",
        targets,
      });
      state.cards.unshift(card);
      added += 1;
    }
    saveState();
    setStatus(`Saved ${added} cards (one per line).`);
    clearCaptureForm();
    return;
  }

  const targets = collectCaptureTargets();
  for (const w of targets) {
    const draftT = stableTrim(captureDraft[w]?.translation || "");
    if (draftT) upsertLexicon(w, draftT);
  }

  const card = createCard({
    sentence: text,
    source,
    translation,
    notes,
    targets,
  });
  state.cards.unshift(card);
  saveState();
  setStatus(`Saved 1 card. Target words: ${targets.length}.`);
  clearCaptureForm();
}

function clearCaptureForm() {
  $("#captureSentence").value = "";
  $("#captureSource").value = "";
  $("#captureTranslation").value = "";
  $("#captureNotes").value = "";
  $("#captureBulk").checked = false;
  resetCaptureDraft();
}

function renderReviewStats() {
  const due = getDueCards();
  const total = state.cards.length;
  const nextDue = state.cards
    .slice()
    .sort((a, b) => a.srs.dueAt - b.srs.dueAt)
    .find((c) => c.srs.dueAt > now());
  const lines = [];
  lines.push(`Due now: ${due.length} / ${total}`);
  if (nextDue) lines.push(`Next due: ${fmtDue(nextDue.srs.dueAt)} (${nextDue.sentence.slice(0, 60)}${nextDue.sentence.length > 60 ? "..." : ""})`);
  $("#reviewStats").textContent = lines.join("\n");
}

function startReview({ shuffle = false } = {}) {
  const due = getDueCards();
  if (due.length === 0) {
    reviewSession = null;
    renderReview();
    setStatus("No cards due. Capture more, or wait until something is due.");
    return;
  }

  const queue = due.map((c) => c.id);
  if (shuffle) shuffleInPlace(queue);
  reviewSession = { queue, idx: 0, revealed: false, shuffled: shuffle };
  renderReview();
}

function currentReviewCard() {
  if (!reviewSession) return null;
  const id = reviewSession.queue[reviewSession.idx];
  return byId(id);
}

function renderReview() {
  const sentenceEl = $("#reviewSentence");
  const metaEl = $("#reviewMeta");
  const ansEl = $("#reviewAnswer");
  const gradeEl = $("#reviewGrade");
  const progressEl = $("#reviewProgress");

  const revealBtn = $("#reviewReveal");
  revealBtn.disabled = true;

  ansEl.classList.add("hidden");
  gradeEl.classList.add("hidden");

  const card = currentReviewCard();
  if (!card) {
    sentenceEl.textContent = "No card loaded.";
    metaEl.textContent = "";
    progressEl.textContent = reviewSession ? "Review finished." : "Press Start Review to begin.";
    return;
  }

  sentenceEl.textContent = card.sentence || "(empty)";
  const srcDom = card.source ? domainFromUrl(card.source) : "";
  metaEl.textContent = [
    `due: ${fmtDue(card.srs.dueAt)}`,
    `interval: ${card.srs.intervalDays}d`,
    `ease: ${card.srs.ease.toFixed(2)}`,
    `targets: ${card.targets.length}`,
    srcDom ? `source: ${srcDom}` : "",
  ]
    .filter(Boolean)
    .join("  |  ");

  $("#reviewTranslationBlock").style.display = card.translation ? "" : "none";
  $("#reviewNotesBlock").style.display = card.notes ? "" : "none";
  $("#reviewWordsBlock").style.display = card.targets.length ? "" : "none";

  $("#reviewTranslation").textContent = card.translation || "";
  $("#reviewNotes").textContent = card.notes || "";

  const wordsBox = $("#reviewWords");
  wordsBox.textContent = "";
  for (const w of card.targets) {
    const item = document.createElement("div");
    item.className = "worditem";
    const left = document.createElement("div");
    left.className = "left";
    left.textContent = w;
    const right = document.createElement("div");
    right.className = "right";
    const t = state.lexicon[w]?.translation || "";
    const tr = document.createElement("div");
    tr.textContent = t || "(no translation yet)";

    const links = document.createElement("div");
    links.className = "mini-links";
    const aDict = document.createElement("a");
    aDict.className = "mini-link";
    aDict.href = buildCambridgeEnZhUrl(w);
    aDict.target = "_blank";
    aDict.rel = "noopener noreferrer";
    aDict.textContent = "Cambridge";
    const aTr = document.createElement("a");
    aTr.className = "mini-link";
    aTr.href = buildGoogleTranslateUrl(w, { sl: "en", tl: TARGET_LANG_GOOGLE });
    aTr.target = "_blank";
    aTr.rel = "noopener noreferrer";
    aTr.textContent = "Translate";
    links.appendChild(aDict);
    links.appendChild(aTr);

    right.appendChild(tr);
    right.appendChild(links);
    item.appendChild(left);
    item.appendChild(right);
    wordsBox.appendChild(item);
  }

  revealBtn.disabled = false;
  progressEl.textContent = `Card ${reviewSession.idx + 1} / ${reviewSession.queue.length}`;

  if (reviewSession?.revealed) {
    ansEl.classList.remove("hidden");
    gradeEl.classList.remove("hidden");
  }
}

function revealAnswer() {
  if (!reviewSession) return;
  const card = currentReviewCard();
  if (!card) return;
  reviewSession.revealed = true;
  $("#reviewAnswer").classList.remove("hidden");
  $("#reviewGrade").classList.remove("hidden");
}

function gradeCurrent(kind) {
  const card = currentReviewCard();
  if (!reviewSession || !card) return;
  if (!reviewSession.revealed) return;

  const map = { again: 2, hard: 3, good: 4, easy: 5 };
  const q = map[kind];
  if (!q) return;

  card.srs = updateSm2(card.srs, q);
  card.updatedAt = now();
  saveState();

  // Next card.
  reviewSession.idx += 1;
  reviewSession.revealed = false;
  if (reviewSession.idx >= reviewSession.queue.length) {
    reviewSession = null;
    renderReviewStats();
    renderReview();
    setStatus("Review finished.");
    return;
  }
  renderReviewStats();
  renderReview();
}

function setDeckDueOnly(on) {
  deckDueOnly = !!on;
  renderDeck();
}

function renderDeck() {
  const list = $("#deckList");
  list.textContent = "";

  const q = stableTrim($("#deckSearch").value).toLowerCase();
  const dueOnly = deckDueOnly;
  const cards = state.cards
    .slice()
    .sort((a, b) => a.srs.dueAt - b.srs.dueAt)
    .filter((c) => {
      if (dueOnly && c.srs.dueAt > now()) return false;
      if (!q) return true;
      const hay = `${c.sentence}\n${c.translation}\n${c.notes}\n${c.source}`.toLowerCase();
      return hay.includes(q);
    });

  if (cards.length === 0) {
    const empty = document.createElement("div");
    empty.className = "panel-sub";
    empty.textContent = dueOnly ? "No due cards match your filter." : "No cards match your filter.";
    list.appendChild(empty);
    return;
  }

  for (const c of cards) {
    const item = document.createElement("div");
    item.className = "deck-item";
    item.dataset.id = c.id;

    const s = document.createElement("div");
    s.className = "sentence";
    s.textContent = c.sentence || "(empty)";

    const meta = document.createElement("div");
    meta.className = "meta";
    const srcDom = c.source ? domainFromUrl(c.source) : "";
    meta.textContent = [
      `due: ${fmtDue(c.srs.dueAt)}`,
      `int: ${c.srs.intervalDays}d`,
      `ease: ${c.srs.ease.toFixed(2)}`,
      `targets: ${c.targets.length}`,
      srcDom ? `src: ${srcDom}` : "",
    ]
      .filter(Boolean)
      .join("  |  ");

    const acts = document.createElement("div");
    acts.className = "actions";

    const bEdit = document.createElement("button");
    bEdit.className = "btn";
    bEdit.type = "button";
    bEdit.dataset.action = "edit";
    bEdit.textContent = "Edit";

    const bReview = document.createElement("button");
    bReview.className = "btn primary";
    bReview.type = "button";
    bReview.dataset.action = "reviewNow";
    bReview.textContent = "Review Now";

    const bDel = document.createElement("button");
    bDel.className = "btn danger";
    bDel.type = "button";
    bDel.dataset.action = "delete";
    bDel.textContent = "Delete";

    acts.appendChild(bEdit);
    acts.appendChild(bReview);
    acts.appendChild(bDel);

    item.appendChild(s);
    item.appendChild(meta);
    item.appendChild(acts);
    list.appendChild(item);
  }
}

function renderLexicon() {
  const box = $("#lexList");
  box.textContent = "";

  const q = stableTrim($("#lexSearch").value).toLowerCase();
  const entries = Object.entries(state.lexicon)
    .map(([w, v]) => ({ w, ...v }))
    .filter((e) => {
      if (!q) return true;
      return e.w.includes(q) || (e.translation || "").toLowerCase().includes(q);
    })
    .sort((a, b) => a.w.localeCompare(b.w));

  if (entries.length === 0) {
    const empty = document.createElement("div");
    empty.className = "panel-sub";
    empty.textContent = "No saved words yet. Add translations in Capture or Edit.";
    box.appendChild(empty);
    return;
  }

  for (const e of entries) {
    const item = document.createElement("div");
    item.className = "lex-item";

    const w = document.createElement("div");
    w.className = "w";
    w.textContent = e.w;

    const t = document.createElement("div");
    t.className = "t";
    t.textContent = e.translation || "";

    item.appendChild(w);
    item.appendChild(t);
    box.appendChild(item);
  }
}

function download(filename, content, mime = "application/octet-stream") {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function exportJson() {
  const payload = {
    exportedAt: now(),
    version: 1,
    cards: state.cards,
    lexicon: state.lexicon,
  };
  const stamp = new Date(now()).toISOString().slice(0, 10);
  download(`sentence-cards-backup-${stamp}.json`, JSON.stringify(payload, null, 2), "application/json");
  setStatus("Exported backup JSON.");
}

function exportLexiconCsv() {
  const rows = [["word", "translation"]];
  const entries = Object.entries(state.lexicon).sort((a, b) => a[0].localeCompare(b[0]));
  for (const [w, v] of entries) {
    rows.push([w, v.translation || ""]);
  }
  const csv = rows
    .map((r) =>
      r
        .map((x) => {
          const s = String(x ?? "");
          if (/[,"\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
          return s;
        })
        .join(",")
    )
    .join("\n");
  download("lexicon.csv", csv, "text/csv");
  setStatus("Exported lexicon CSV.");
}

function importJsonRun() {
  const file = $("#importFile").files?.[0];
  if (!file) {
    setStatus("Choose a JSON file first.", "danger");
    return;
  }

  const mode = document.querySelector('input[name="importMode"]:checked')?.value || "merge";
  const reader = new FileReader();
  reader.onerror = () => setStatus("Failed to read file.", "danger");
  reader.onload = () => {
    try {
      const obj = JSON.parse(String(reader.result || ""));
      const importedCards = Array.isArray(obj.cards) ? obj.cards.map(normalizeCard) : [];
      const importedLex = normalizeLexicon(obj.lexicon || {});

      if (mode === "replace") {
        state = { version: 1, cards: importedCards, lexicon: importedLex };
      } else {
        // Merge
        const byExisting = new Set(state.cards.map((c) => c.id));
        for (const c of importedCards) {
          if (byExisting.has(c.id)) c.id = newId();
          state.cards.push(c);
          byExisting.add(c.id);
        }
        // Prefer existing non-empty translations; otherwise import.
        for (const [w, v] of Object.entries(importedLex)) {
          const cur = state.lexicon[w];
          if (!cur) {
            state.lexicon[w] = v;
            continue;
          }
          if (!stableTrim(cur.translation) && stableTrim(v.translation)) {
            state.lexicon[w] = { ...cur, translation: v.translation, updatedAt: now() };
          }
        }
      }

      saveState();
      renderAll();
      setStatus(`Imported. Cards: ${state.cards.length}. Words: ${Object.keys(state.lexicon).length}.`);
    } catch (e) {
      console.error(e);
      setStatus("Import failed: invalid JSON format.", "danger");
    }
  };
  reader.readAsText(file);
}

function resetAll() {
  const ok = confirm("Delete all local Sentence Cards data in this browser?");
  if (!ok) return;
  localStorage.removeItem(STORAGE_KEY);
  state = emptyState();
  reviewSession = null;
  resetCaptureDraft();
  renderAll();
  setStatus("Local data cleared.");
}

function openEditDialog(cardId) {
  const card = byId(cardId);
  if (!card) return;
  const dlg = $("#editDialog");
  $("#editId").value = card.id;
  $("#editSentence").value = card.sentence;
  $("#editSource").value = card.source;
  $("#editTranslation").value = card.translation;
  $("#editNotes").value = card.notes;

  renderEditWords(card);
  if (typeof dlg.showModal === "function") dlg.showModal();
  else dlg.setAttribute("open", "open");
}

function closeEditDialog() {
  const dlg = $("#editDialog");
  if (typeof dlg.close === "function") dlg.close();
  else dlg.removeAttribute("open");
}

function buildEditWordList(sentence, existingTargets) {
  const sug = suggestWords(sentence);
  const set = new Set(existingTargets);
  const merged = [...existingTargets];
  for (const w of sug) {
    if (set.has(w)) continue;
    merged.push(w);
    set.add(w);
  }
  return merged;
}

function renderEditWords(card) {
  const box = $("#editWords");
  box.textContent = "";

  const words = buildEditWordList(card.sentence, card.targets);
  if (words.length === 0) {
    const empty = document.createElement("div");
    empty.className = "panel-sub";
    empty.textContent = "No target words. Add some below.";
    box.appendChild(empty);
    return;
  }

  for (const w of words) {
    const row = document.createElement("div");
    row.className = "word-row";
    row.dataset.word = w;

    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.checked = card.targets.includes(w);
    cb.dataset.word = w;
    cb.className = "edit-word-check";

    const left = document.createElement("div");
    const wEl = document.createElement("div");
    wEl.className = "w";
    wEl.textContent = w;
    const meta = document.createElement("div");
    meta.className = "meta";
    const pos = guessPos(w);
    const inLex = state.lexicon[w]?.translation ? "lex" : "";
    meta.textContent = [pos, inLex].filter(Boolean).join(" ") || " ";

    const links = document.createElement("div");
    links.className = "mini-links";
    const aDict = document.createElement("a");
    aDict.className = "mini-link";
    aDict.href = buildCambridgeEnZhUrl(w);
    aDict.target = "_blank";
    aDict.rel = "noopener noreferrer";
    aDict.textContent = "Cambridge";
    const aTr = document.createElement("a");
    aTr.className = "mini-link";
    aTr.href = buildGoogleTranslateUrl(w, { sl: "en", tl: TARGET_LANG_GOOGLE });
    aTr.target = "_blank";
    aTr.rel = "noopener noreferrer";
    aTr.textContent = "Translate";
    links.appendChild(aDict);
    links.appendChild(aTr);
    left.appendChild(wEl);
    left.appendChild(meta);
    left.appendChild(links);

    const tr = document.createElement("input");
    tr.type = "text";
    tr.placeholder = "translation (optional)";
    tr.value = state.lexicon[w]?.translation || "";
    tr.dataset.word = w;
    tr.className = "edit-word-translation";

    row.appendChild(cb);
    row.appendChild(left);
    row.appendChild(tr);
    box.appendChild(row);
  }
}

function editSave() {
  const id = $("#editId").value;
  const card = byId(id);
  if (!card) return;

  card.sentence = stableTrim($("#editSentence").value);
  card.source = stableTrim($("#editSource").value);
  card.translation = stableTrim($("#editTranslation").value);
  card.notes = stableTrim($("#editNotes").value);
  card.updatedAt = now();

  const targets = [];
  for (const row of document.querySelectorAll("#editWords .word-row")) {
    const w = row.dataset.word;
    const cb = row.querySelector('input[type="checkbox"]');
    const tr = row.querySelector('input[type="text"]');
    if (cb?.checked) targets.push(w);
    const t = stableTrim(tr?.value || "");
    if (t) upsertLexicon(w, t);
  }
  card.targets = targets.map(normalizeWord).filter(Boolean);

  saveState();
  closeEditDialog();
  renderAll();
  setStatus("Card updated.");
}

function editDelete() {
  const id = $("#editId").value;
  const card = byId(id);
  if (!card) return;
  const ok = confirm("Delete this card?");
  if (!ok) return;
  state.cards = state.cards.filter((c) => c.id !== id);
  saveState();
  closeEditDialog();
  renderAll();
  setStatus("Card deleted.");
}

function editReviewNow() {
  const id = $("#editId").value;
  const card = byId(id);
  if (!card) return;
  card.srs.dueAt = now() - 1;
  card.updatedAt = now();
  saveState();
  closeEditDialog();
  setRoute("review");
  startReview();
}

function addWordToCapture(e) {
  e.preventDefault();
  const wRaw = stableTrim($("#addWordText").value);
  const tRaw = stableTrim($("#addWordTrans").value);
  const w = normalizeWord(wRaw);
  if (!w || !/^[a-z]+(?:'[a-z]+)*$/.test(w)) {
    setStatus("Invalid word. Use letters and apostrophe only.", "danger");
    return;
  }
  if (!captureDraft[w]) captureManualOrder.push(w);
  setCaptureWord(w, { manual: true, checked: true, translation: tRaw || state.lexicon[w]?.translation || "" });
  $("#addWordText").value = "";
  $("#addWordTrans").value = "";
  renderSuggestedWords();
}

function addWordToEdit(e) {
  e.preventDefault();
  const wRaw = stableTrim($("#editAddWordText").value);
  const tRaw = stableTrim($("#editAddWordTrans").value);
  const w = normalizeWord(wRaw);
  if (!w || !/^[a-z]+(?:'[a-z]+)*$/.test(w)) {
    setStatus("Invalid word. Use letters and apostrophe only.", "danger");
    return;
  }
  if (tRaw) upsertLexicon(w, tRaw);
  $("#editAddWordText").value = "";
  $("#editAddWordTrans").value = "";

  const id = $("#editId").value;
  const card = byId(id);
  if (!card) return;
  if (!card.targets.includes(w)) card.targets.push(w);
  renderEditWords(card);
  saveState();
  renderAll();
}

function renderAll() {
  rebuildSuggestionsFromSentence();
  renderReviewStats();
  renderReview();
  renderDeck();
  renderLexicon();
  updateFooter();
}

function updateFooter() {
  const due = getDueCards().length;
  const total = state.cards.length;
  setStatus(`Cards: ${total}. Due: ${due}. Words: ${Object.keys(state.lexicon).length}.`);
}

function wireEvents() {
  for (const btn of document.querySelectorAll(".tab")) {
    btn.addEventListener("click", () => setRoute(btn.dataset.route));
  }
  window.addEventListener("hashchange", () => setRoute(currentRoute(), false));

  $("#captureForm").addEventListener("submit", captureSaveCards);
  $("#captureClear").addEventListener("click", clearCaptureForm);
  $("#captureSentence").addEventListener("input", () => rebuildSuggestionsFromSentence({ keepTranslations: true }));
  $("#captureSentence").addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") captureSaveCards(e);
  });

  $("#suggestedWords").addEventListener("change", (e) => {
    const t = e.target;
    if (!(t instanceof HTMLElement)) return;
    if (t.classList.contains("word-check")) {
      const w = t.dataset.word;
      setCaptureWord(w, { checked: t.checked });
    }
  });
  $("#suggestedWords").addEventListener("input", (e) => {
    const t = e.target;
    if (!(t instanceof HTMLElement)) return;
    if (t.classList.contains("word-translation")) {
      const w = t.dataset.word;
      setCaptureWord(w, { translation: t.value });
    }
  });

  $("#wordsSelectAll").addEventListener("click", () => {
    for (const w of Object.keys(captureDraft)) setCaptureWord(w, { checked: true });
    renderSuggestedWords();
  });
  $("#wordsSelectNone").addEventListener("click", () => {
    for (const w of Object.keys(captureDraft)) setCaptureWord(w, { checked: false });
    renderSuggestedWords();
  });
  $("#wordsFromLexicon").addEventListener("click", () => rebuildSuggestionsFromSentence({ keepTranslations: true }));
  $("#wordsAutoTranslate")?.addEventListener("click", () => {
    void runTranslateTask(async () => {
      const targets = collectCaptureTargets();
      if (targets.length === 0) {
        setStatus("No selected words to translate.", "danger");
        return;
      }
      setStatus(`Auto-translating ${targets.length} words (online)...`);
      let done = 0;
      let skipped = 0;
      for (const w of targets) {
        const cur = stableTrim(captureDraft[w]?.translation || "");
        if (cur) {
          skipped += 1;
          continue;
        }
        try {
          const t = await myMemoryTranslate(w, { from: "en", to: TARGET_LANG_GOOGLE });
          setCaptureWord(w, { translation: t });
          upsertLexicon(w, t);
          done += 1;
        } catch (e) {
          console.warn(e);
        }
      }
      saveState();
      renderSuggestedWords();
      setStatus(`Auto-translate done. Added ${done}, skipped ${skipped}.`);
    });
  });

  $("#addWordForm").addEventListener("submit", addWordToCapture);

  $("#loadSampleDeck")?.addEventListener("click", loadSampleDeckIntermediate);

  $("#captureAutoTranslateSentence")?.addEventListener("click", () => {
    void runTranslateTask(async () => {
      const s = stableTrim($("#captureSentence").value);
      if (!s) {
        setStatus("Paste a sentence first, then translate.", "danger");
        return;
      }
      setStatus("Auto-translating sentence (online)...");
      try {
        const t = await myMemoryTranslate(s, { from: "en", to: TARGET_LANG_GOOGLE });
        $("#captureTranslation").value = t;
        setStatus("Sentence translation filled.");
      } catch (e) {
        console.warn(e);
        setStatus("Auto-translate failed. Opening Google Translate instead.", "danger");
        openExternal(buildGoogleTranslateUrl(s, { sl: "en", tl: TARGET_LANG_GOOGLE }));
      }
    });
  });

  $("#openTranslateSentenceGoogle")?.addEventListener("click", () => {
    const s = stableTrim($("#captureSentence").value);
    if (!s) {
      setStatus("Paste a sentence first, then translate.", "danger");
      return;
    }
    openExternal(buildGoogleTranslateUrl(s, { sl: "en", tl: TARGET_LANG_GOOGLE }));
  });

  $("#openTranslateSentenceBing")?.addEventListener("click", () => {
    const s = stableTrim($("#captureSentence").value);
    if (!s) {
      setStatus("Paste a sentence first, then translate.", "danger");
      return;
    }
    openExternal(buildBingTranslateUrl(s, { from: "en", to: TARGET_LANG_BING }));
  });

  $("#reviewStart").addEventListener("click", () => startReview({ shuffle: false }));
  $("#reviewShuffle").addEventListener("click", () => startReview({ shuffle: true }));
  $("#reviewReveal").addEventListener("click", revealAnswer);
  $("#reviewTranslateGoogle")?.addEventListener("click", () => {
    const c = currentReviewCard();
    const s = stableTrim(c?.sentence || "");
    if (!s) {
      setStatus("No card loaded to translate.", "danger");
      return;
    }
    openExternal(buildGoogleTranslateUrl(s, { sl: "en", tl: TARGET_LANG_GOOGLE }));
  });
  $("#reviewTranslateBing")?.addEventListener("click", () => {
    const c = currentReviewCard();
    const s = stableTrim(c?.sentence || "");
    if (!s) {
      setStatus("No card loaded to translate.", "danger");
      return;
    }
    openExternal(buildBingTranslateUrl(s, { from: "en", to: TARGET_LANG_BING }));
  });
  $("#reviewEditCard")?.addEventListener("click", () => {
    const c = currentReviewCard();
    if (!c) {
      setStatus("No card loaded to edit.", "danger");
      return;
    }
    openEditDialog(c.id);
  });
  $("#reviewAutoSentence")?.addEventListener("click", () => {
    void runTranslateTask(async () => {
      const c = currentReviewCard();
      if (!c) {
        setStatus("No card loaded to translate.", "danger");
        return;
      }
      const s = stableTrim(c.sentence);
      if (!s) {
        setStatus("This card has no sentence.", "danger");
        return;
      }
      setStatus("Auto-translating sentence (online)...");
      try {
        const t = await myMemoryTranslate(s, { from: "en", to: TARGET_LANG_GOOGLE });
        c.translation = t;
        c.updatedAt = now();
        saveState();
        renderReview();
        setStatus("Sentence translation saved to this card.");
      } catch (e) {
        console.warn(e);
        setStatus("Auto-translate failed. Use 'Translate sentence' to open Google Translate.", "danger");
      }
    });
  });
  $("#reviewAutoWords")?.addEventListener("click", () => {
    void runTranslateTask(async () => {
      const c = currentReviewCard();
      if (!c) {
        setStatus("No card loaded to translate.", "danger");
        return;
      }
      const targets = Array.isArray(c.targets) ? c.targets : [];
      if (targets.length === 0) {
        setStatus("This card has no target words.", "danger");
        return;
      }
      const missing = targets.filter((w) => !stableTrim(state.lexicon[w]?.translation || ""));
      if (missing.length === 0) {
        setStatus("All target words already have translations.");
        return;
      }
      setStatus(`Auto-translating ${missing.length} words (online)...`);
      let done = 0;
      for (const w of missing) {
        try {
          const t = await myMemoryTranslate(w, { from: "en", to: TARGET_LANG_GOOGLE });
          upsertLexicon(w, t);
          done += 1;
        } catch (e) {
          console.warn(e);
        }
      }
      saveState();
      renderReview();
      setStatus(`Saved ${done} word translations to Lexicon.`);
    });
  });

  $("#reviewGrade").addEventListener("click", (e) => {
    const t = e.target;
    if (!(t instanceof HTMLElement)) return;
    const g = t.dataset.grade;
    if (!g) return;
    gradeCurrent(g);
  });

  document.addEventListener("keydown", (e) => {
    if (currentRoute() !== "review") return;
    if (e.key === " " || e.code === "Space") {
      e.preventDefault();
      if (!reviewSession) return;
      if (!reviewSession.revealed) revealAnswer();
      return;
    }
    if (!reviewSession?.revealed) return;
    if (e.key === "1") gradeCurrent("again");
    if (e.key === "2") gradeCurrent("hard");
    if (e.key === "3") gradeCurrent("good");
    if (e.key === "4") gradeCurrent("easy");
  });

  $("#deckSearch").addEventListener("input", renderDeck);
  $("#deckDueOnly").addEventListener("click", () => setDeckDueOnly(true));
  $("#deckAll").addEventListener("click", () => setDeckDueOnly(false));

  $("#deckList").addEventListener("click", (e) => {
    const t = e.target;
    if (!(t instanceof HTMLElement)) return;
    const action = t.dataset.action;
    if (!action) return;
    const root = t.closest(".deck-item");
    const id = root?.dataset.id;
    if (!id) return;
    if (action === "edit") openEditDialog(id);
    if (action === "delete") {
      const ok = confirm("Delete this card?");
      if (!ok) return;
      state.cards = state.cards.filter((c) => c.id !== id);
      saveState();
      renderAll();
    }
    if (action === "reviewNow") {
      const c = byId(id);
      if (!c) return;
      c.srs.dueAt = now() - 1;
      c.updatedAt = now();
      saveState();
      setRoute("review");
      startReview();
    }
  });

  $("#lexSearch").addEventListener("input", renderLexicon);
  $("#lexExport").addEventListener("click", exportLexiconCsv);

  $("#exportJson").addEventListener("click", exportJson);
  $("#importRun").addEventListener("click", importJsonRun);
  $("#resetAll").addEventListener("click", resetAll);

  $("#editSave").addEventListener("click", editSave);
  $("#editDelete").addEventListener("click", editDelete);
  $("#editReviewNow").addEventListener("click", editReviewNow);

  $("#editWords").addEventListener("change", (e) => {
    const t = e.target;
    if (!(t instanceof HTMLElement)) return;
    if (!t.classList.contains("edit-word-translation")) return;
    const w = t.dataset.word;
    const v = stableTrim(t.value);
    if (v) upsertLexicon(w, v);
    saveState();
    renderLexicon();
  });

  $("#editAddWordForm").addEventListener("submit", addWordToEdit);

  $("#gotoToday").addEventListener("click", () => {
    setRoute("review");
    startReview({ shuffle: false });
  });
}

function boot() {
  wireEvents();
  setRoute(currentRoute(), false);
  rebuildSuggestionsFromSentence();
  renderAll();

  // PWA: register service worker for offline cache + installability.
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("./sw.js", { scope: "./" }).catch((e) => {
      console.warn("serviceWorker registration failed", e);
    });
  }
}

boot();
