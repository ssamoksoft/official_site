#!/usr/bin/env python3
"""Pre-render Stelleaf documents, preserving every shipped URL and old edition."""
import json
import re
from pathlib import Path

from build_lang_pages import LANGS, Strings, esc, escape_and_link, privacy_body

ROOT = Path(__file__).resolve().parent.parent
DOCS = {'privacy': '', 'terms': 'terms/', 'delete': 'delete-account/'}


def href(kind, lang, legacy=False):
    base = '/privacy/stelleaf/' + DOCS[kind]
    return base if legacy else base + lang + '.html'


def body(doc):
    result = [f'<h1>{esc(doc["title"])}</h1>',
              f'<p class="updated">{esc(doc["updated"])}</p>',
              f'<p class="applies">{escape_and_link(doc["applies"])}</p>']
    for section in doc['sections']:
        result.append(f'<h2>{esc(section["t"])}</h2>')
        if section.get('b'):
            result.append(f'<p>{escape_and_link(section["b"])}</p>')
        if section.get('l'):
            result.append('<ul>' + ''.join(f'<li>{escape_and_link(x)}</li>' for x in section['l']) + '</ul>')
    if doc.get('previous'):
        result.append('<div class="doc-links">' + ''.join(
            f'<a href="{esc(x["href"])}" data-fixed-lang="true">{esc(x["label"])}</a>' for x in doc['previous']) + '</div>')
    return '\n'.join(result)


def language_links(kind, lang):
    return ''.join(f'<li role="option"><a class="lang__item" href="{href(kind, code)}" '
                   f'hreflang="{bcp}" data-lang="{code}"' + (' aria-current="true"' if code == lang else '') +
                   f'><span>{esc(label)}</span><span class="lang__code">{esc(code)}</span></a></li>'
                   for code, _, bcp, label in LANGS)


def render_page(template, kind, lang, bcp, label, data, legacy=False):
    doc = data['docs']['stelleaf_' + kind]
    direction = 'rtl' if lang == 'ar' else 'ltr'
    s = Strings(lang, data)
    page = template.replace('<html lang="en">', f'<html lang="{bcp}" dir="{direction}">', 1)
    if not legacy:
        page = page.replace('<body ', f'<body data-legal-static data-lang="{lang}" ', 1)
    page = re.sub(r'<title>.*?</title>', lambda _: f'<title>{esc(doc["title"])} — SSAMOK SOFT</title>', page, count=1)
    page = re.sub(r'(<meta name="description" content=")[^"]*(")',
                  lambda m: m[1] + esc(doc['title']) + m[2], page, count=1)
    # Fixed-language pages have unambiguous canonical URLs. The compatibility
    # URL deliberately has none: ?lang= continues to choose its document.
    if not legacy:
        page = page.replace('</head>', f'<link rel="canonical" href="https://www.ssamoksoft.com{href(kind, lang)}" />\n</head>', 1)
    related = {'privacy':data['privacy']['title'], 'terms':data['privacy']['link_terms'], 'delete':data['privacy']['link_delete']}
    nav = '<div class="doc-links">' + ''.join(f'<a href="{href(k, lang)}">{esc(title)}</a>' for k,title in related.items() if k != kind) + '</div>'
    home = '/' if lang == 'en' else '/' + lang.replace('_','-') + '/'
    nav += f'<a class="back" href="{home}">{esc(data["privacy"]["back"])}</a>'
    article = f'<article class="container legal" id="legal-root" lang="{bcp}" dir="{direction}">\n{body(doc)}\n{nav}\n</article>'
    page = page.replace('<article class="container legal" id="legal-root"></article>', article, 1)
    page = re.sub(r'(<([\w]+)[^>]*\bdata-i18n="([^"]+)"[^>]*>).*?(</\2>)',
                  lambda m: m[1] + esc(s.get(m[3])) + m[4], page, flags=re.S)
    page = re.sub(r'(<span id="lang-current">).*?(</span>)', lambda m: m[1]+esc(label)+m[2], page, count=1)
    page = page.replace('<ul class="lang__menu" id="lang-menu" role="listbox"></ul>',
                        '<ul class="lang__menu" id="lang-menu" role="listbox">'+language_links(kind, lang)+'</ul>')
    nojs = '<noscript><nav class="container doc-links" aria-label="Languages">' + ' · '.join(
        f'<a href="{href(kind, code)}" hreflang="{bcp}">{esc(label)}</a>' for code,_,bcp,label in LANGS) + '</nav></noscript>'
    page = page.replace('<main>', '<main>\n'+nojs, 1)
    page = page.replace('href="/privacy/"', f'href="{href("privacy", lang)}"')
    page = page.replace('href="/"', f'href="{home}"').replace('href="/#', f'href="{home}#')
    return page


def render_archive(directory, kind=None):
    data = json.loads((directory / 'documents.json').read_text())
    for lang, _, bcp, _ in LANGS:
        old = data[lang]
        direction = 'rtl' if lang == 'ar' else 'ltr'
        new = json.loads((ROOT / f'data/i18n/{lang}.json').read_text())
        current = href(kind,lang) if kind else f'/{lang.replace("_","-")}/privacy/'
        if kind:
            content = body(old)
            title = old['title']
        else:
            # An isolated old bundle prevents the current policy being mixed
            # into archived content by the Strings fallback.
            class Archived:
                def get(self, key):
                    return old.get(key.removeprefix('privacy.'), key)
            content = privacy_body(Archived())
            title = old['title']
        links = ' · '.join(f'<a href="{code}.html" hreflang="{bcp}">{esc(label)}</a>' for code,_,bcp,label in LANGS)
        current_label = new['docs']['stelleaf_'+kind]['title'] if kind else new['privacy']['title']
        page = (f'<!doctype html><html lang="{bcp}" dir="{direction}"><head><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">'
                f'<title>{esc(title)} — {directory.name}</title><link rel="stylesheet" href="/assets/css/styles.css"></head>'
                f'<body><main class="container legal"><nav class="doc-links">{links}</nav>{content}'
                f'<p><a href="{current}">{esc(current_label)} · 2026-10-11</a></p></main></body></html>\n')
        (directory / f'{lang}.html').write_text(page)
        if lang == 'en':
            (directory / 'index.html').write_text(page)


def build_stelleaf():
    for kind in DOCS:
        template = (ROOT/f'tools/templates/stelleaf-{kind}.html').read_text()
        directory = ROOT / ('privacy/stelleaf/' + DOCS[kind])
        for lang, _, bcp, label in LANGS:
            data = json.loads((ROOT/f'data/i18n/{lang}.json').read_text())
            (directory/f'{lang}.html').write_text(render_page(template,kind,lang,bcp,label,data))
            if lang == 'en':
                (directory/'index.html').write_text(render_page(template,kind,lang,bcp,label,data,legacy=True))
    for archive,kind in [('2026-10-10','privacy'),('terms-2026-07-25','terms'),('delete-2026-09-20','delete')]:
        render_archive(ROOT/'privacy/stelleaf/archive'/archive,kind)
    render_archive(ROOT/'privacy/archive/2026-09-07')
    print('  Stelleaf: 48 static translations + 3 compatible URLs; 64 archived translations')


if __name__ == '__main__':
    build_stelleaf()
