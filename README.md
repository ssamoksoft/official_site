# SSAMOK SOFT — official site

Official website for **SSAMOK SOFT (싸목소프트)**, an app studio.
Static site hosted on GitHub Pages at **www.ssamoksoft.com**.

## Stack

Plain static HTML/CSS/JS — no framework, no backend. `assets/js/app.js` renders the
page from JSON data at runtime; a small Python script pre-renders the home page per
language so search engines can read it.

## Structure

```
index.html              Home — English, and the auto-detecting entry point
<lang>/index.html       Pre-rendered home page per language (generated — do not edit)
privacy/index.html      Common privacy policy
privacy/<app>/          Per-app privacy policy, and terms / delete-account where applicable
assets/css/styles.css   Design system (modern dark + violet #6E56F8)
assets/js/app.js        i18n engine, data-driven app cards, legal-doc renderer, language switcher
data/apps.json          App portfolio data (edit this to add/update apps)
data/i18n/<lang>.json   All UI and legal copy, per language
tools/build_lang_pages.py  Generates <lang>/index.html + sitemap.xml
sitemap.xml             Generated
CNAME, robots.txt, app-ads.txt
```

## ⚠️ After changing copy, regenerate

`index.html` holds English fallback text, and `<lang>/index.html` holds the pre-rendered
translations. Both go stale if you edit `data/i18n/*.json` or `data/apps.json` without
regenerating:

```bash
python3 tools/build_lang_pages.py
```

If you change English copy, update the matching fallback text in `index.html` by hand as
well — that is what crawlers read before JavaScript runs.

## Adding or editing an app

Edit **`data/apps.json`** only, then regenerate. Add a block to `apps`:

```json
{
  "id": "my-app",
  "category": "productivity",
  "accent": "#3B82F6",
  "status": "released",
  "icon": "/assets/apps/my-app.png",
  "links": { "play": "https://play.google.com/...", "appstore": "https://apps.apple.com/..." },
  "privacy": { "backend": "firebase", "account": true, "ads": true, "iap": true },
  "docs": ["terms", "delete"],
  "name":    { "en": "My App", "ko": "..." },
  "tagline": { "en": "One-line description.", "ko": "..." }
}
```

- `icon`: path to an image, or `null` to auto-generate a lettered tile from the name.
- `status`: `"released"` or `"coming_soon"` (shows a badge and disables store links until release).
- `hidden`: `true` removes the app from every listing (home page, static language pages)
  after it is pulled from the stores. Keep the entry — `/privacy/<id>/` still renders
  from it, and people who installed the app still need that policy.
- `privacy`: drives the auto-generated data-processing summary on `/privacy/<id>/`.
  `backend` is `firebase` / `supabase` / `local`; add `extras` for app-specific lines.
- `docs`: which extra legal pages exist, so the privacy page cross-links them.
- `name` / `tagline`: keyed by language code; missing languages fall back to `en`.

## Localization (16 languages)

`en, ko, ja, zh, zh_Hant, es, pt, de, fr, hi, id, ru, vi, tr, it, ar` — default `en`,
Arabic renders right-to-left. Existing app documents retain their translations.
Snuumo's privacy policy is available in all 16 languages. Its terms, deletion, support,
and Impressum pages are available in Korean and English; other language choices
display the English document with left-to-right text.

- Copy lives in `data/i18n/<lang>.json`; any missing key falls back to `en.json`.
- English is served by `/`; every other language also has a static page at `/<lang>/`
  (`/zh-Hant/` for `zh_Hant`), linked by `hreflang` and listed in `sitemap.xml`.
- On home and common privacy pages the switcher navigates between language URLs.
  App documents still swap text in place. On existing URLs, a supported `?lang=` query
  takes precedence without replacing a saved preference;
  otherwise a static page declares `data-lang`, which overrides the saved preference.
  Internal document links preserve the current language.

## Legal pages

Custom per-app documents (`privacy.*`, `docs.*` keys in the i18n files) are rendered into
shells that carry `data-privacy-app` or `data-legal-doc`. **Their URLs are referenced from
app store listings and inside the apps — never change or remove them.**

App-specific documents are intentionally left out of `sitemap.xml` and retain their
existing URLs and `?lang=` behavior, including the links registered in the stores.

The **common policy** has pre-rendered pages at `/en/privacy/`, `/ko/privacy/`, etc.
Each includes its translated body, a self-referencing canonical, reciprocal `hreflang`
links, and a sitemap entry. These new fixed URLs always use their declared language,
including when a conflicting query is present. `/privacy/` remains an auto-localized compatibility entry;
it also retains `?lang=` and saved-language behavior, and its runtime creates one
canonical pointing to the displayed language's static page. Its source intentionally
omits an English canonical to avoid conflicting with an explicit language query.
The English policy is present as a no-JavaScript fallback. The template lives in
`tools/templates/privacy.html`; regenerate with `python3 tools/build_lang_pages.py`
after changing the template, translations, or app data. Do not hand-edit generated pages.

The generator skips
`status: "coming_soon"` apps when pre-rendering the product grid so unreleased apps
are not promoted in search results — `app.js` still shows those cards to visitors.

## Released apps

Kairotique and Snuumo are available on both Google Play and the App Store. Their
store links are maintained in `data/apps.json` and shown on their product cards.

## Snuumo pages

Snuumo is listed as released. Its public documents are under `/privacy/snuumo/`:
`terms/`, `delete-account/`, `support/`, `impressum/`, and the preserved policy
`archive/2026-07-25/` and terms `archive/terms-2026-08-12/`. Support contact: **support@ssamoksoft.com**.
The Snuumo document shells use same-origin assets and system fonts.

## Local preview

Serve from the repo root (paths are root-absolute):

```bash
python3 -m http.server 8000
```

## Notes

- The legal documents were drafted in-house — have them reviewed by legal counsel.
- Store "Data Safety" (Google Play) / "App Privacy" (App Store) declarations are filed
  per-app in the store consoles, separately from these pages.
