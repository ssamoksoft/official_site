#!/usr/bin/env python3
"""Pre-render the home page in every supported language.

The site is a static, data-driven page: assets/js/app.js injects translated text
from data/i18n/<lang>.json at runtime. Googlebot renders it in English, so no
localized text ever reaches the index. This script bakes each language into its
own crawlable page (/ko/, /ja/, …) while leaving the root page untouched as the
English + auto-detecting entry point.

Run it after changing copy in data/i18n/*.json or data/apps.json:

    python3 tools/build_lang_pages.py

Output: <lang>/index.html for every non-English language, plus sitemap.xml.
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
            if isinstance(node, str):
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
    """Server-side equivalent of renderApps() in app.js."""
    apps = apps_data.get("apps", [])
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

    # app.js expands {year} at runtime; bake it in so the token never shows without JS.
    doc = doc.replace("{year}", str(datetime.date.today().year))
    return doc


def build_sitemap():
    urls = [f"{SITE}/"] + [f"{SITE}/{slug}/" for _, slug, _, _ in LANGS if slug]
    legal = []
    for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, "privacy")):
        if "index.html" in filenames:
            rel = os.path.relpath(dirpath, ROOT).replace(os.sep, "/")
            legal.append(f"{SITE}/{rel}/")
    urls += sorted(legal)
    body = "\n".join(f"  <url><loc>{u}</loc></url>" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n'


def main():
    with open(os.path.join(ROOT, "index.html"), encoding="utf-8") as f:
        template = f.read()
    if "<body data-home>" not in template:
        sys.exit("index.html must carry <body data-home> — aborting so pages are not generated wrong.")

    base = load(f"data/i18n/{DEFAULT_LANG}.json")
    apps_data = load("data/apps.json")

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

    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(build_sitemap())
    print(f"\n{written} language pages + sitemap.xml written")


if __name__ == "__main__":
    main()
