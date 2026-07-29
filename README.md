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
- `status`: `"released"` or `"coming_soon"` (shows a badge; cards without store links are not clickable).
- `privacy`: drives the auto-generated data-processing summary on `/privacy/<id>/`.
  `backend` is `firebase` / `supabase` / `local`; add `extras` for app-specific lines.
- `docs`: which extra legal pages exist, so the privacy page cross-links them.
- `name` / `tagline`: keyed by language code; missing languages fall back to `en`.

## Localization (16 languages)

`en, ko, ja, zh, zh_Hant, es, pt, de, fr, hi, id, ru, vi, tr, it, ar` — default `en`,
Arabic renders right-to-left. All 16 are fully translated, including the legal documents.

- Copy lives in `data/i18n/<lang>.json`; any missing key falls back to `en.json`.
- English is served by `/`; every other language also has a static page at `/<lang>/`
  (`/zh-Hant/` for `zh_Hant`), linked by `hreflang` and listed in `sitemap.xml`.
- On the home page the switcher navigates between those URLs. Elsewhere it swaps text in
  place. A static page declares `data-lang`, which overrides the saved preference.

## Legal pages

Custom per-app documents (`privacy.*`, `docs.*` keys in the i18n files) are rendered into
shells that carry `data-privacy-app` or `data-legal-doc`. **Their URLs are referenced from
app store listings and inside the apps — never change or remove them.**

They are intentionally left out of `sitemap.xml` and have no pre-rendered language variants:
they must stay reachable, but they name apps that have not launched yet, so there is no reason
to invite indexing. For the same reason the generator skips `status: "coming_soon"` apps when
pre-rendering the product grid — `app.js` still shows those cards to visitors.

## Local preview

Serve from the repo root (paths are root-absolute):

```bash
python3 -m http.server 8000
```

## Notes

- The legal documents were drafted in-house — have them reviewed by legal counsel.
- Store "Data Safety" (Google Play) / "App Privacy" (App Store) declarations are filed
  per-app in the store consoles, separately from these pages.
