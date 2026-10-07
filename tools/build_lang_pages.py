#!/usr/bin/env python3
"""Pre-render home and common privacy pages in every supported language.

The site runtime loads translated text from data/i18n/<lang>.json. This script
bakes each language into its own crawlable HTML so indexing does not depend on
JavaScript language detection. The root home page and /privacy/ remain
auto-detecting entry points for existing links.

Run it after changing copy in data/i18n/*.json or data/apps.json:

    python3 tools/build_lang_pages.py

Output: localized home pages, <lang>/privacy/index.html (including en),
the compatible /privacy/ entry point, and sitemap.xml.
"""

import datetime
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://www.ssamoksoft.com"
DEFAULT_LANG = "en"

# i18n code -> (url slug, BCP-47 hreflang, menu label)
LANGS = [
    ("en",      "",        "en",      "English"),
    ("ko",      "ko",      "ko",      "한국어"),
    ("ja",      "ja",      "ja",      "日本語"),
    ("zh",      "zh",      "zh-Hans", "简体中文"),
    ("zh_Hant", "zh-Hant", "zh-Hant", "繁體中文"),
    ("es",      "es",      "es",      "Español"),
    ("pt",      "pt",      "pt",      "Português"),
    ("de",      "de",      "de",      "Deutsch"),
    ("fr",      "fr",      "fr",      "Français"),
    ("hi",      "hi",      "hi",      "हिन्दी"),
    ("id",      "id",      "id",      "Bahasa Indonesia"),
    ("ru",      "ru",      "ru",      "Русский"),
    ("vi",      "vi",      "vi",      "Tiếng Việt"),
    ("tr",      "tr",      "tr",      "Türkçe"),
    ("it",      "it",      "it",      "Italiano"),
    ("ar",      "ar",      "ar",      "العربية"),
]
RTL = {"ar"}


def load(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return json.load(f)


def esc(s):
    return html.escape(str(s), quote=True)


class Strings:
    """i18n lookup with per-key fallback to English, mirroring app.js."""

    def __init__(self, lang, base):
        self.d = load(f"data/i18n/{lang}.json")
        self.base = base

    def get(self, key):
        for src in (self.d, self.base):
            node = src
            for part in key.split("."):
                if not isinstance(node, dict) or part not in node:
                    node = None
                    break
                node = node[part]
            if isinstance(node, (str, list)):
                return node
        return key


def localize(field, lang, default_lang):
    """Mirror of localize() in app.js for apps.json name/tagline objects."""
    if field is None:
        return ""
    if isinstance(field, str):
        return field
    for code in (lang, default_lang, DEFAULT_LANG):
        if field.get(code):
            return field[code]
    return next(iter(field.values()), "")


def render_apps(apps_data, lang, s):
    """Server-side equivalent of renderApps() in app.js.

    Unreleased apps are left out on purpose: these pages exist to be crawled, and we
    do not want unannounced app names showing up in search results before launch.
    app.js still renders them for visitors once the page loads.

    Apps marked "hidden" (pulled from the stores) are left out everywhere; their
    entry stays in apps.json only so /privacy/<id>/ keeps rendering.
    """
    apps = [a for a in apps_data.get("apps", [])
            if a.get("status") != "coming_soon" and not a.get("hidden")]
    if not apps:
        return f'<div class="apps-empty">{esc(s.get("apps.empty"))}</div>'

    out = []
    for app in apps:
        name = localize(app.get("name"), lang, apps_data.get("defaultLang", DEFAULT_LANG))
        tagline = localize(app.get("tagline"), lang, apps_data.get("defaultLang", DEFAULT_LANG))
        accent = app.get("accent") or "var(--accent)"
        soon = app.get("status") == "coming_soon"
        cat = s.get("apps.coming_soon") if soon else s.get("apps.category." + (app.get("category") or "productivity"))

        if app.get("icon"):
            icon = f'<span class="app-icon"><img src="{esc(app["icon"])}" alt="" /></span>'
        else:
            first = (name or "?").strip()[:1].upper()
            icon = f'<span class="app-icon">{esc(first)}</span>'

        links = app.get("links") or {}
        badges = []
        if links.get("play"):
            badges.append(
                f'<a href="{esc(links["play"])}" target="_blank" rel="noopener">'
                f'<i class="ti ti-brand-google-play" aria-hidden="true"></i>{esc(s.get("apps.links.play"))}</a>'
            )
        if links.get("appstore"):
            badges.append(
                f'<a href="{esc(links["appstore"])}" target="_blank" rel="noopener">'
                f'<i class="ti ti-brand-apple" aria-hidden="true"></i>{esc(s.get("apps.links.appstore"))}</a>'
            )
        links_html = f'<div class="app-links">{"".join(badges)}</div>' if badges else ""

        # Desktop resolution order; app.js re-resolves per device on load.
        href = links.get("play") or links.get("appstore") or ""
        cls = "app-card" + (" is-soon" if soon else "") + (" is-linked" if href else "")
        attrs = f' data-href="{esc(href)}" role="link" tabindex="0" aria-label="{esc(name)}"' if href else ""

        out.append(
            f'<article class="{cls}" style="--card-accent:{esc(accent)}"{attrs}>'
            f'<div class="app-card__top">{icon}<span class="app-cat">{esc(cat)}</span></div>'
            f'<h3 class="app-name">{esc(name)}</h3>'
            f'<p class="app-tagline">{esc(tagline)}</p>'
            f'{links_html}'
            f'<a class="app-privacy" href="/privacy/{esc(app["id"])}/">{esc(s.get("footer.links.privacy"))}</a>'
            f"</article>"
        )
    return "".join(out)


def privacy_href(code):
    return f"/{code.replace('_', '-')}/privacy/"


def lang_menu_html(current, privacy=False):
    """Mirror of langMenuHTML() in app.js for the home page (real links, not buttons).

    Baking these into the HTML gives every language page an inbound link that crawlers can
    follow without running JavaScript — otherwise the only way in is the sitemap, and Google
    leaves such URLs sitting in "discovered, not indexed".
    """
    items = []
    for code, slug, bcp, label in LANGS:
        href = privacy_href(code) if privacy else ("/" if not slug else f"/{slug}/")
        cur = ' aria-current="true"' if code == current else ""
        inner = f'<span>{esc(label)}</span><span class="lang__code">{esc(code.replace("_", "-"))}</span>'
        items.append(
            f'<li role="option"><a class="lang__item" href="{href}" hreflang="{bcp}" '
            f'data-lang="{code}"{cur}>{inner}</a></li>'
        )
    return "".join(items)


def with_lang_menu(doc, current, privacy=False):
    return re.sub(
        r'(<ul class="lang__menu" id="lang-menu" role="listbox">).*?(</ul>)',
        lambda m: m.group(1) + lang_menu_html(current, privacy) + m.group(2),
        doc,
        count=1,
        flags=re.S,
    )


def build_page(template, lang, slug, bcp, label, s, apps_data):
    page_url = f"{SITE}/" if not slug else f"{SITE}/{slug}/"
    doc = template

    # <html lang> (+ direction for RTL languages)
    direction = ' dir="rtl"' if lang in RTL else ""
    doc = doc.replace('<html lang="en">', f'<html lang="{bcp}"{direction}>', 1)

    # Declare the page language so app.js keeps it instead of auto-detecting.
    doc = doc.replace("<body data-home>", f'<body data-home data-lang="{lang}">', 1)

    title, desc = s.get("meta.title"), s.get("meta.description")
    doc = re.sub(r"<title>.*?</title>", f"<title>{esc(title)}</title>", doc, count=1, flags=re.S)
    doc = re.sub(r'(<meta name="description" id="meta-description" content=")[^"]*(")',
                 lambda m: m.group(1) + esc(desc) + m.group(2), doc, count=1)
    doc = re.sub(r'(<meta property="og:title" content=")[^"]*(")',
                 lambda m: m.group(1) + esc(title) + m.group(2), doc, count=1)
    doc = re.sub(r'(<meta property="og:description" content=")[^"]*(")',
                 lambda m: m.group(1) + esc(desc) + m.group(2), doc, count=1)
    doc = re.sub(r'(<meta property="og:url" content=")[^"]*(")',
                 lambda m: m.group(1) + page_url + m.group(2), doc, count=1)
    doc = re.sub(r'(<link rel="canonical" href=")[^"]*(")',
                 lambda m: m.group(1) + page_url + m.group(2), doc, count=1)

    # Fill every translatable element so the text exists without JavaScript.
    def fill(m):
        tag, attrs, key, _inner = m.group(1), m.group(2), m.group(4), m.group(5)
        value = s.get(key)
        body = value if 'data-i18n-html="' in attrs else esc(value)
        return f"<{tag}{attrs}>{body}</{tag}>"

    doc = re.sub(r'<(\w+)([^>]*\bdata-i18n(-html)?="([^"]+)"[^>]*)>(.*?)</\1>', fill, doc, flags=re.S)

    # Current language shown on the switcher button
    doc = re.sub(r'(<span id="lang-current">).*?(</span>)',
                 lambda m: m.group(1) + esc(label) + m.group(2), doc, count=1, flags=re.S)

    # Pre-render the product grid (this is what puts app names like 별갈피 in the HTML)
    doc = doc.replace(
        '<div class="apps-grid" id="apps-grid" aria-live="polite"></div>',
        f'<div class="apps-grid" id="apps-grid" aria-live="polite">{render_apps(apps_data, lang, s)}</div>',
        1,
    )

    doc = with_lang_menu(doc, lang)
    # Only the common policy moves to a crawlable language URL. Store-linked
    # /privacy/<app>/ documents keep their established destinations.
    doc = doc.replace('href="/privacy/"', f'href="{privacy_href(lang)}"')
    doc = doc.replace('href="/en/privacy/"', f'href="{privacy_href(lang)}"')

    # app.js expands {year} at runtime; bake it in so the token never shows without JS.
    doc = doc.replace("{year}", str(datetime.date.today().year))
    return doc


def escape_and_link(value):
    """Preserve the policy's existing text and clickable URLs (see app.js)."""
    def link(match):
        raw = match.group(0)
        href = raw.rstrip(".,;:!?)]}")
        return f'<a href="{href}" target="_blank" rel="noopener">{href}</a>' + raw[len(href):]
    return re.sub(r"https?://[^\s<]+", link, esc(value))


def privacy_body(s):
    parts = [f'<h1>{esc(s.get("privacy.title"))}</h1>',
             f'<p class="updated">{esc(s.get("privacy.updated"))}</p>',
             f'<p class="applies">{esc(s.get("privacy.applies_common"))}</p>',
             f'<p class="intro">{esc(s.get("privacy.intro"))}</p>']
    for section in ("collect", "purpose", "iap", "thirdparty", "ads", "retention",
                    "storage", "rights", "children", "contact", "representative", "changes", "business"):
        prefix = f"privacy.s_{section}"
        parts.append(f'<h2>{esc(s.get(prefix + "_title"))}</h2>')
        body = s.get(prefix + "_body")
        if body != prefix + "_body":
            parts.append(f"<p>{escape_and_link(body)}</p>")
        items = s.get(prefix + "_items")
        if isinstance(items, list):
            parts.append("<ul>" + "".join(f"<li>{escape_and_link(item)}</li>" for item in items) + "</ul>")
    parts.append(f'<a class="back" href="/"><i class="ti ti-arrow-left" aria-hidden="true"></i> {esc(s.get("privacy.back"))}</a>')
    return "\n".join(parts)


def build_privacy_page(template, lang, bcp, label, s, legacy=False):
    """Static language pages plus the existing auto-localized /privacy/ entry.

    The legacy entry can show any language via ?lang= or saved preferences, so
    app.js creates its canonical after selecting that language. Do not put a
    conflicting English canonical in its source. Fixed pages have static canonicals.
    """
    direction = ' dir="rtl"' if lang in RTL else ""
    doc = template.replace('<html lang="en">', f'<html lang="{bcp}"{direction}>', 1)
    if not legacy:
        doc = doc.replace('<body data-common-privacy>', f'<body data-common-privacy data-lang="{lang}">', 1)
    doc = re.sub(r"<title>.*?</title>", lambda m: f'<title>{esc(s.get("privacy.title"))}</title>', doc, count=1)
    doc = re.sub(r'(<meta name="description" id="privacy-description" content=")[^"]*(")',
                 lambda m: m.group(1) + esc(s.get("privacy.intro")) + m.group(2), doc, count=1)
    seo = [] if legacy else [f'<link rel="canonical" href="{SITE}{privacy_href(lang)}" />']
    seo.append(f'<link rel="alternate" hreflang="x-default" href="{SITE}/en/privacy/" />')
    seo.extend(f'<link rel="alternate" hreflang="{other_bcp}" href="{SITE}{privacy_href(code)}" />'
               for code, _, other_bcp, _ in LANGS)
    doc = doc.replace('<!-- privacy-seo -->', "\n  ".join(seo), 1)
    doc = doc.replace('<article class="container legal" id="privacy-root"></article>',
                      '<article class="container legal" id="privacy-root">\n' + privacy_body(s) + '\n</article>', 1)
    doc = re.sub(r'(<([\w]+)[^>]*\bdata-i18n="([^"]+)"[^>]*>).*?(</\2>)',
                 lambda m: m.group(1) + esc(s.get(m.group(3))) + m.group(4), doc, flags=re.S)
    doc = re.sub(r'(<span id="lang-current">).*?(</span>)',
                 lambda m: m.group(1) + esc(label) + m.group(2), doc, count=1, flags=re.S)
    doc = with_lang_menu(doc, lang, privacy=True)
    home = "/" if lang == DEFAULT_LANG else f"/{lang.replace('_', '-')}/"
    doc = doc.replace('href="/"', f'href="{home}"')
    doc = doc.replace('href="/#', f'href="{home}#')
    doc = doc.replace('href="/privacy/"', f'href="{privacy_href(lang)}"')
    return doc.replace("{year}", str(datetime.date.today().year))


def build_sitemap():
    """Home pages and the common policy's fixed-language pages.

    App-specific /privacy/** documents are deliberately left out. They stay reachable —
    app store listings and shipped apps link straight to them — but listing them here
    would actively invite indexing of pages naming apps that have not launched yet.
    """
    urls = [f"{SITE}/"] + [f"{SITE}/{slug}/" for _, slug, _, _ in LANGS if slug]
    urls += [SITE + privacy_href(code) for code, _, _, _ in LANGS]
    body = "\n".join(f"  <url><loc>{u}</loc></url>" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n'


def main():
    with open(os.path.join(ROOT, "index.html"), encoding="utf-8") as f:
        template = f.read()
    if "<body data-home>" not in template:
        sys.exit("index.html must carry <body data-home> — aborting so pages are not generated wrong.")

    base = load(f"data/i18n/{DEFAULT_LANG}.json")
    apps_data = load("data/apps.json")

    # The root page is English, but it still needs the crawlable links to every other language.
    template = with_lang_menu(template, DEFAULT_LANG)
    template = template.replace('href="/privacy/"', 'href="/en/privacy/"')
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(template)
    print("  index.html            English (language links refreshed)")

    written = 0
    for lang, slug, bcp, label in LANGS:
        if not slug:  # English is served by the root page
            continue
        s = Strings(lang, base)
        page = build_page(template, lang, slug, bcp, label, s, apps_data)
        outdir = os.path.join(ROOT, slug)
        os.makedirs(outdir, exist_ok=True)
        with open(os.path.join(outdir, "index.html"), "w", encoding="utf-8") as f:
            f.write(page)
        written += 1
        print(f"  {slug + '/index.html':22} {label}")

    with open(os.path.join(ROOT, "tools/templates/privacy.html"), encoding="utf-8") as f:
        privacy_template = f.read()
    for lang, _, bcp, label in LANGS:
        page = build_privacy_page(privacy_template, lang, bcp, label, Strings(lang, base))
        outdir = os.path.join(ROOT, privacy_href(lang).strip("/"))
        os.makedirs(outdir, exist_ok=True)
        with open(os.path.join(outdir, "index.html"), "w", encoding="utf-8") as f:
            f.write(page)
    with open(os.path.join(ROOT, "privacy/index.html"), "w", encoding="utf-8") as f:
        f.write(build_privacy_page(privacy_template, "en", "en", "English", Strings("en", base), legacy=True))

    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(build_sitemap())
    print(f"\n{written} home pages + 16 privacy pages + /privacy/ entry + sitemap.xml written")


if __name__ == "__main__":
    main()
