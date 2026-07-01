# SSAMOK SOFT — official site

Official website for **SSAMOK SOFT**, a studio crafting productivity apps.
Static site hosted on GitHub Pages at **www.ssamoksoft.com**.

> Games are a separate brand/site: `games.ssamoksoft.com` (built later). This site is productivity-focused.

## Stack

Plain static HTML/CSS/JS — no build step, no backend. Deployed via GitHub Pages.

## Structure

```
index.html            Home (hero, apps, languages, contact)
privacy/index.html    Common privacy policy (/privacy)
assets/css/styles.css Design system (modern dark + violet #6E56F8)
assets/js/app.js      i18n engine + data-driven app rendering + language switcher
data/apps.json        App portfolio data (edit this to add/update apps)
data/i18n/<lang>.json UI strings per language (15 languages)
CNAME                 Custom domain (www.ssamoksoft.com)
app-ads.txt           AdMob authorized sellers
```

## Adding or editing an app

Edit **`data/apps.json`** only — no HTML changes needed. Add a block to `apps`:

```json
{
  "id": "my-app",
  "category": "productivity",
  "accent": "#3B82F6",
  "status": "released",
  "icon": "/assets/apps/my-app.png",
  "links": { "play": "https://play.google.com/...", "appstore": "https://apps.apple.com/..." },
  "name":    { "en": "My App", "ko": "..." },
  "tagline": { "en": "One-line description.", "ko": "..." }
}
```

- `icon`: path to an icon image, or `null` to auto-generate a lettered tile from the name.
- `status`: `"released"` or `"coming_soon"` (shows a badge).
- `name` / `tagline`: keyed by language code; missing languages fall back to `en`.

## Localization (15 languages)

Supported: `en, ko, ja, zh, zh_Hant, es, pt, de, fr, hi, id, ru, vi, tr, it` (default `en`).

- UI strings live in `data/i18n/<lang>.json`. Any missing key falls back to `en.json`.
- `en.json` and `ko.json` are translated; the other 13 files are English copies awaiting translation — translate them in place.
- Language is auto-detected from the browser on first visit and remembered in `localStorage`.

## Local preview

Serve from the repo root (paths are root-absolute):

```
python3 -m http.server 8000
# open http://localhost:8000
```

## Notes

- The privacy policy is a **draft template** — have it reviewed by legal counsel before relying on it.
- Store "Data Safety" (Google Play) / "App Privacy" (App Store) declarations are done per-app in the store consoles, separately from this page.
