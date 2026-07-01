/* SSAMOK SOFT — site runtime
   - Full i18n: UI copy is loaded from data/i18n/<lang>.json (fallback to English).
   - Data-driven apps: portfolio is rendered from data/apps.json.
   - Adding an app = one JSON block in apps.json (no markup changes). */

const LANGUAGES = [
  { code: "en",      label: "English" },
  { code: "ko",      label: "한국어" },
  { code: "ja",      label: "日本語" },
  { code: "zh",      label: "简体中文" },
  { code: "zh_Hant", label: "繁體中文" },
  { code: "es",      label: "Español" },
  { code: "pt",      label: "Português" },
  { code: "de",      label: "Deutsch" },
  { code: "fr",      label: "Français" },
  { code: "hi",      label: "हिन्दी" },
  { code: "id",      label: "Bahasa Indonesia" },
  { code: "ru",      label: "Русский" },
  { code: "vi",      label: "Tiếng Việt" },
  { code: "tr",      label: "Türkçe" },
  { code: "it",      label: "Italiano" },
];
const DEFAULT_LANG = "en";
const STORAGE_KEY = "ssamok.lang";

let strings = {};      // strings for the active language
let fallback = {};     // English strings, always loaded as a safety net
let appsData = { defaultLang: DEFAULT_LANG, apps: [] };
let currentLang = DEFAULT_LANG;

/* ---------- helpers ---------- */
function getPath(obj, path) {
  return path.split(".").reduce((o, k) => (o == null ? undefined : o[k]), obj);
}
function t(key) {
  const v = getPath(strings, key);
  if (v !== undefined) return v;
  const f = getPath(fallback, key);
  return f !== undefined ? f : key;
}
function localize(field) {
  // field is an object keyed by language code, e.g. { en: "Focus", ko: "포커스" }
  if (field == null) return "";
  if (typeof field === "string") return field;
  return field[currentLang] || field[appsData.defaultLang] || field[DEFAULT_LANG] || Object.values(field)[0] || "";
}
async function loadJSON(url) {
  const res = await fetch(url, { cache: "no-cache" });
  if (!res.ok) throw new Error(`Failed to load ${url} (${res.status})`);
  return res.json();
}
function isRTL() { return false; } // none of the 15 supported languages are RTL

/* ---------- i18n apply ---------- */
function applyI18n() {
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = t(el.getAttribute("data-i18n"));
  });
  document.querySelectorAll("[data-i18n-html]").forEach((el) => {
    el.innerHTML = t(el.getAttribute("data-i18n-html"));
  });
  document.querySelectorAll("[data-i18n-attr]").forEach((el) => {
    el.getAttribute("data-i18n-attr").split(";").forEach((pair) => {
      const [attr, key] = pair.split(":").map((s) => s.trim());
      if (attr && key) el.setAttribute(attr, t(key));
    });
  });
  const title = t("meta.title");
  if (title && title !== "meta.title") document.title = title;
  const desc = document.getElementById("meta-description");
  const descText = t("meta.description");
  if (desc && descText !== "meta.description") desc.setAttribute("content", descText);
}

/* ---------- apps ---------- */
function renderApps() {
  const grid = document.getElementById("apps-grid");
  if (!grid) return;
  const apps = appsData.apps || [];
  if (apps.length === 0) {
    grid.innerHTML = `<div class="apps-empty">${t("apps.empty")}</div>`;
    return;
  }
  grid.innerHTML = apps.map((app) => {
    const name = localize(app.name);
    const tagline = localize(app.tagline);
    const accent = app.accent || "var(--accent)";
    const soon = app.status === "coming_soon";
    const catLabel = soon ? t("apps.coming_soon") : t("apps.category." + (app.category || "productivity"));
    const icon = app.icon
      ? `<span class="app-icon"><img src="${app.icon}" alt="" /></span>`
      : `<span class="app-icon">${(name || "?").trim().charAt(0).toUpperCase()}</span>`;
    const links = renderLinks(app.links);
    return `
      <article class="app-card ${soon ? "is-soon" : ""}" style="--card-accent:${accent}">
        <div class="app-card__top">
          ${icon}
          <span class="app-cat">${catLabel}</span>
        </div>
        <h3 class="app-name">${escapeHTML(name)}</h3>
        <p class="app-tagline">${escapeHTML(tagline)}</p>
        ${links}
      </article>`;
  }).join("");
}
function renderLinks(links) {
  if (!links) return "";
  const items = [];
  if (links.play) items.push(`<a href="${links.play}" target="_blank" rel="noopener"><i class="ti ti-brand-google-play" aria-hidden="true"></i>${t("apps.links.play")}</a>`);
  if (links.appstore) items.push(`<a href="${links.appstore}" target="_blank" rel="noopener"><i class="ti ti-brand-apple" aria-hidden="true"></i>${t("apps.links.appstore")}</a>`);
  return items.length ? `<div class="app-links">${items.join("")}</div>` : "";
}
function escapeHTML(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

/* ---------- language chips ---------- */
function renderChips() {
  const wrap = document.getElementById("lang-chips");
  if (!wrap) return;
  wrap.innerHTML = LANGUAGES.map((l) => `<span class="chip">${l.label}</span>`).join("");
}

/* ---------- language switcher ---------- */
function buildLangMenu() {
  const menu = document.getElementById("lang-menu");
  if (!menu) return;
  menu.innerHTML = LANGUAGES.map((l) => `
    <li role="option">
      <button class="lang__item" data-lang="${l.code}" ${l.code === currentLang ? 'aria-current="true"' : ""}>
        <span>${l.label}</span>
        <span class="lang__code">${l.code.replace("_", "-")}</span>
      </button>
    </li>`).join("");
  menu.querySelectorAll("[data-lang]").forEach((btn) => {
    btn.addEventListener("click", () => { setLang(btn.getAttribute("data-lang")); closeLangMenu(); });
  });
}
function updateLangButton() {
  const cur = LANGUAGES.find((l) => l.code === currentLang);
  const label = document.getElementById("lang-current");
  if (label && cur) label.textContent = cur.label;
  document.querySelectorAll("#lang-menu [data-lang]").forEach((btn) => {
    if (btn.getAttribute("data-lang") === currentLang) btn.setAttribute("aria-current", "true");
    else btn.removeAttribute("aria-current");
  });
}
function openLangMenu() { document.getElementById("lang").setAttribute("aria-expanded", "true"); }
function closeLangMenu() { document.getElementById("lang").setAttribute("aria-expanded", "false"); }
function toggleLangMenu() {
  const el = document.getElementById("lang");
  el.getAttribute("aria-expanded") === "true" ? closeLangMenu() : openLangMenu();
}

/* ---------- language selection ---------- */
function detectLang() {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved && LANGUAGES.some((l) => l.code === saved)) return saved;
  const navLangs = navigator.languages || [navigator.language || DEFAULT_LANG];
  for (const raw of navLangs) {
    const low = raw.toLowerCase();
    if (low === "zh-tw" || low === "zh-hk" || low.startsWith("zh-hant")) return "zh_Hant";
    const base = low.split("-")[0];
    const match = LANGUAGES.find((l) => l.code === base);
    if (match) return match.code;
  }
  return DEFAULT_LANG;
}
async function setLang(code) {
  currentLang = LANGUAGES.some((l) => l.code === code) ? code : DEFAULT_LANG;
  try {
    strings = await loadJSON(`/data/i18n/${currentLang}.json`);
  } catch (e) {
    console.warn("i18n load failed, falling back to English:", e);
    strings = fallback;
  }
  localStorage.setItem(STORAGE_KEY, currentLang);
  document.documentElement.setAttribute("lang", currentLang.replace("_", "-"));
  document.documentElement.setAttribute("dir", isRTL() ? "rtl" : "ltr");
  applyI18n();
  renderApps();
  updateLangButton();
}

/* ---------- boot ---------- */
async function init() {
  // English is always loaded as the fallback layer.
  try { fallback = await loadJSON(`/data/i18n/${DEFAULT_LANG}.json`); } catch (e) { console.warn(e); }
  try { appsData = await loadJSON("/data/apps.json"); } catch (e) { console.warn("apps.json load failed:", e); }

  renderChips();
  currentLang = detectLang();
  buildLangMenu();
  await setLang(currentLang);

  // switcher interactions
  const toggle = document.getElementById("lang-toggle");
  if (toggle) toggle.addEventListener("click", (e) => { e.stopPropagation(); toggleLangMenu(); });
  document.addEventListener("click", (e) => {
    const langEl = document.getElementById("lang");
    if (langEl && !langEl.contains(e.target)) closeLangMenu();
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeLangMenu(); });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
