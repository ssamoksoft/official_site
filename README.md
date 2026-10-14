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
- On home, common privacy and Stelleaf legal pages the switcher navigates between
  language URLs. Other app documents still swap text in place. On existing URLs, a supported `?lang=` query
  takes precedence without replacing a saved preference;
  otherwise a static page declares `data-lang`, which overrides the saved preference.
  Internal document links preserve the current language.

## Legal pages

Custom per-app documents (`privacy.*`, `docs.*` keys in the i18n files) are rendered into
shells that carry `data-privacy-app` or `data-legal-doc`. **Their URLs are referenced from
app store listings and inside the apps — never change or remove them.**

App-specific documents are intentionally left out of `sitemap.xml` and retain their
existing URLs and `?lang=` behavior, including the links registered in the stores.

Stelleaf's three existing URLs contain an English HTML fallback. Each also has
16 fully rendered translations (`ko.html`, `en.html`, `zh_Hant.html`, etc.) in the
same directory. These fixed pages retain their declared language, even without
JavaScript or when translation requests fail. Existing `?lang=` URLs remain valid.
Templates live in `tools/templates/stelleaf-*.html`; `build_lang_pages.py` also
runs `build_stelleaf_legal.py`. Do not edit generated HTML directly.

The 2026-10-11 clarification preserves the 7-day Stelleaf email-deletion deadline,
explains app-policy precedence and map initialization, corrects the KISA link,
and spells out plan benefits and change notices. Security wording describes
verified controls without promising an unverified quarterly audit or six-month
log retention. Previous editions are immutable `documents.json` snapshots with
static translations under `privacy/archive/2026-09-07/` and Stelleaf's
`archive/2026-10-10/`, `archive/terms-2026-07-25/`, `archive/delete-2026-09-20/`.
The earlier Stelleaf `archive/2026-09-20/` is also retained.

### Version history

Every privacy policy, terms page and account-deletion guide has a collapsible
**Version history** near its title. Archived pages show a notice, a link to the
current version, and navigation to other editions. History works without JavaScript;
the existing live language switcher refreshes its labels and links too.

`data/legal-history.json` is the navigation registry for all 15 documents. It holds
the current URL, dated archive URLs, date type, publication status, available
archive languages, and short summaries. UI labels cover all 16 languages; summaries
fall back to explicitly marked English where a translation is unavailable.
Pre-release documents are labeled separately. Do not infer an effective date from
a folder name, fabricate a missing edition, or reuse a common-policy archive as if
it included an app's historical processing summary.

When revising a document:

1. **Before editing live copy**, preserve the outgoing full text and all available
   translations under a new, stable archive URL. Existing archive text and
   `documents.json` snapshots must not be overwritten.
2. Move the outgoing version's date and summary into a new registry entry with a
   stable `id`, an archive `url`, and `status: "previous"`. Keep exactly one first
   entry with `id: "current"`, updating its date and summary. Use `dateKind:
   "document"` for a document date that is not a confirmed effective date, and
   `date: null` if no date is stated. Use `status: "prelaunch"` for preparation copies.
   URL templates accept `{lang}` (such as `zh_Hant`) and `{slug}` (`zh-Hant`).
3. Regenerate with `python3 tools/build_lang_pages.py`. Its final stage,
   `tools/legal_history.py`, adds navigation to current and archived HTML without
   changing archived legal text. Do not run a partial generator as the final build.
4. Run `python3 tools/check_legal_pages.py` and
   `python3 tools/check_legal_history.py` to check content and edition links.

The pre-analytics Snuumo policy is now frozen in
`privacy/snuumo/archive/before-analytics-2026-10-02/documents.json` and 16 static
translations. Its registry entry uses `snapshot` to generate HTML from that file;
the old `?lang=` entry still selects the corresponding frozen translation. The
legacy `docs.snuumo_privacyPrevious` translation keys are no longer its content
source. A `snapshot` directory contains a language-to-document mapping with the
same `title`, `updated`, `applies`, and `sections` schema as other custom documents.

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
