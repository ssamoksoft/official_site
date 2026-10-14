"""Shared registry and static navigation for legal document editions.

The registry contains navigation metadata only. Archived text stays in its original
HTML or documents.json snapshot; never reconstruct an old edition from live copy.
"""
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

from build_lang_pages import LANGS, esc

ROOT = Path(__file__).resolve().parent.parent
START = '<!-- legal-history:start -->'
END = '<!-- legal-history:end -->'
STYLESHEET = '<link rel="stylesheet" href="/assets/css/legal-history.css" />'


def load_registry():
    return json.loads((ROOT / 'data/legal-history.json').read_text())


def version_url(version, lang):
    return version['url'].replace('{lang}', lang).replace('{slug}', lang.replace('_', '-'))


def render_history(registry, doc_id, lang, viewing='current'):
    document = registry['documents'][doc_id]
    labels = registry['labels'].get(lang, registry['labels']['en'])
    current = next(v for v in document['versions'] if v['status'] == 'current')
    bcp = 'zh-Hans' if lang == 'zh' else lang.replace('_', '-')
    is_current = 'true' if viewing == current['id'] else 'false'
    summary_date = (f'{esc(labels[current["dateKind"]])}: <time datetime="{current["date"]}">{current["date"]}</time>'
                    if current['date'] else esc(labels['current']))
    chevron = '<svg class="legal-history__chevron" width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true" focusable="false"><path d="m4 6 4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    result = [START, f'<aside class="legal-history" lang="{bcp}" dir="{"rtl" if lang == "ar" else "ltr"}" data-history-doc="{doc_id}" data-history-current="{is_current}">']
    if viewing != current['id']:
        result.append(f'<p class="legal-history__notice">{esc(labels["notice"])} '
                      f'<a href="{esc(version_url(current, lang))}" data-fixed-lang="true">{esc(labels["latest"])}</a></p>')
    result.append(f'<details><summary><span>{summary_date}</span>{chevron}</summary><ol>')
    for version in document['versions']:
        selected = version['id'] == viewing
        status = labels[version['status']]
        date = (f'{esc(labels[version["dateKind"]])} · <time datetime="{version["date"]}">{version["date"]}</time>'
                if version['date'] else esc(labels['undated']))
        summary_lang = lang if lang in version['summary'] else 'en'
        summary = version['summary'][summary_lang]
        result.append(f'<li class="legal-history__entry{" is-current" if version["status"] == "current" else ""}">'
                      f'<div class="legal-history__meta"><span class="legal-history__status">{esc(status)}</span><span>{date}</span></div>'
                      f'<p lang="{summary_lang}" dir="{"rtl" if summary_lang == "ar" else "ltr"}">{esc(summary)}</p>')
        if version.get('languages'):
            names = {code: label for code, _, _, label in LANGS}
            result.append(f'<p class="legal-history__languages">{esc(labels["languages"])}: '
                          + ', '.join(esc(names[code]) for code in version['languages']) + '</p>')
        if selected:
            result.append(f'<span class="legal-history__viewing" aria-current="true">{esc(labels["viewing"])}</span>')
        else:
            result.append(f'<a href="{esc(version_url(version, lang))}" data-fixed-lang="true">{esc(labels["read"])}</a>')
        result.append('</li>')
    result.append('</ol>')
    if len(document['versions']) == 1:
        result.append(f'<p class="legal-history__empty">{esc(labels["empty"])}</p>')
    result.extend(['</details></aside>', END])
    return ''.join(result)


def insert_history(page, markup):
    """Idempotently update navigation without rewriting the legal body."""
    page = re.sub(re.escape(START) + r'.*?' + re.escape(END), '', page, flags=re.S)
    if STYLESHEET not in page:
        # Some legacy archives omit <head>; inserting after <title> also works there.
        page = page.replace('</title>', '</title>' + STYLESHEET, 1)
    return re.sub(r'</h1>', lambda _: '</h1>' + markup, page, count=1)


def build_snapshot(directory):
    """Render an immutable multilingual snapshot, with a compatible ?lang= entry."""
    from build_stelleaf_legal import body
    documents = json.loads((directory / 'documents.json').read_text())
    for lang, _, bcp, _ in LANGS:
        doc = documents[lang]
        nav = ' · '.join(f'<a href="{code}.html" hreflang="{language}">{esc(label)}</a>'
                         for code, _, language, label in LANGS)
        page = (f'<!doctype html><html lang="{bcp}" dir="{"rtl" if lang == "ar" else "ltr"}"><head>'
                '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                '<meta name="robots" content="noindex">'
                f'<title>{esc(doc["title"])}</title><link rel="stylesheet" href="/assets/css/styles.css">'
                f'</head><body><main class="container legal"><nav class="doc-links">{nav}</nav>'
                f'{body(doc)}</main></body></html>\n')
        (directory / f'{lang}.html').write_text(page)
        if lang == 'en':
            # Only the compatibility URL detects language. Fixed HTML editions never
            # load live translations or change their language based on preferences.
            redirect = '''<script>
(() => {
  const codes = LANGUAGES;
  const supported = (raw) => codes.find((c) => c.toLowerCase() === String(raw || '').replace('-', '_').toLowerCase());
  let saved;
  try { saved = localStorage.getItem('ssamok.lang'); } catch (_) {}
  const browser = (navigator.languages || [navigator.language]).map((raw) =>
    /^zh-(tw|hk|hant)/i.test(raw) ? 'zh_Hant' : String(raw).split('-')[0]);
  const lang = supported(new URLSearchParams(location.search).get('lang')) || supported(saved) || browser.map(supported).find(Boolean) || 'en';
  location.replace(lang + '.html' + location.search + location.hash);
})();
</script>'''.replace('LANGUAGES', json.dumps([code for code, _, _, _ in LANGS]))
            (directory / 'index.html').write_text(page.replace('</head>', redirect + '</head>'))


def build_history():
    from build_lang_pages import Strings, privacy_body, escape_and_link, localize
    from build_stelleaf_legal import body

    registry = load_registry()
    base = json.loads((ROOT / 'data/i18n/en.json').read_text())
    apps = json.loads((ROOT / 'data/apps.json').read_text())
    for document in registry['documents'].values():
        for version in document['versions']:
            if version.get('snapshot'):
                build_snapshot(ROOT / version['snapshot'])
    handled = set()
    for doc_id, document in registry['documents'].items():
        for version in document['versions']:
            for lang, _, _, _ in LANGS:
                path = ROOT / urlsplit(version_url(version, lang)).path.lstrip('/')
                if path.is_dir():
                    path /= 'index.html'
                if path in handled:
                    continue
                if not path.is_file():
                    raise ValueError(f'Missing legal version: {doc_id} / {path}')
                handled.add(path)
                page = path.read_text()
                # Refresh the English fallback of dynamic-only pages on every build.
                if version['status'] == 'current' and doc_id != 'common_privacy' and not doc_id.startswith('stelleaf_'):
                    if doc_id in base['docs']:
                        content = body(base['docs'][doc_id])
                        root_id = 'legal-root'
                    else:
                        s = Strings('en', base)
                        content = privacy_body(s, include_previous=False)
                        app_id = doc_id.removesuffix('_privacy')
                        app = next(a for a in apps['apps'] if a['id'] == app_id)
                        name = localize(app['name'], 'en', 'en')
                        content = content.replace(esc(s.get('privacy.applies_common')),
                                                  esc(s.get('privacy.applies_app').replace('{app}', name)))
                        p = app['privacy']
                        items = [s.get('privacy.sum_backend_' + p['backend'])]
                        items += [s.get('privacy.sum_' + key + ('_yes' if p[key] else '_no')) for key in ('account', 'ads', 'iap')]
                        items += [s.get('privacy.sum_extra_' + key) for key in p.get('extras', [])]
                        summary = '<div class="privacy-summary"><h2>' + esc(s.get('privacy.summary_title')) + '</h2><ul>'
                        summary += ''.join(f'<li>{escape_and_link(item)}</li>' for item in items) + '</ul></div>'
                        content = content.replace('<h2>', summary + '<h2>', 1)
                        root_id = 'privacy-root'
                    page = re.sub(rf'(<article\b[^>]*id="{root_id}"[^>]*>).*?(</article>)',
                                  lambda match: match[1] + content + match[2], page, count=1, flags=re.S)
                # Single-language and bilingual legacy archives declare their own language.
                declared = re.search(r'<html[^>]*\blang="([^"]+)"', page)
                display_lang = (declared[1].replace('-', '_') if declared else lang)
                if display_lang == 'zh_Hans':
                    display_lang = 'zh'
                if display_lang not in registry['labels']:
                    display_lang = lang
                page = insert_history(page, render_history(registry, doc_id, display_lang, version['id']))
                path.write_text(page)
        # Compatibility index URLs for translated pages must have the same navigation.
        for version in document['versions']:
            if '{lang}.html' not in version['url']:
                continue
            path = ROOT / urlsplit(version_url(version, 'en')).path.lstrip('/')
            index = path.with_name('index.html')
            if index.is_file():
                page = insert_history(index.read_text(), render_history(registry, doc_id, 'en', version['id']))
                index.write_text(page)
    # /privacy/ is the auto-localized compatibility entry for the common policy.
    path = ROOT / 'privacy/index.html'
    path.write_text(insert_history(path.read_text(), render_history(registry, 'common_privacy', 'en')))
    print(f'  Legal history: {len(registry["documents"])} documents; {len(handled)} edition pages')


if __name__ == '__main__':
    build_history()
