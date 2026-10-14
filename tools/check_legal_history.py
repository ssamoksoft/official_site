#!/usr/bin/env python3
"""Validate edition navigation, locale routing, and frozen archive content."""
import datetime
import html
import json
import subprocess
from urllib.parse import urlsplit

from build_lang_pages import LANGS
from check_legal_pages import Page, check_links, check_body
from legal_history import ROOT, START, END, load_registry, render_history, version_url


def main():
    registry = load_registry()
    assert registry['schemaVersion'] == 1
    assert set(registry['labels']) == {lang for lang, _, _, _ in LANGS}
    checked = set()
    for doc_id, document in registry['documents'].items():
        versions = document['versions']
        assert versions[0]['status'] == 'current'
        assert sum(v['status'] == 'current' for v in versions) == 1
        assert len({v['id'] for v in versions}) == len(versions)
        dates = [v['date'] for v in versions if v['date']]
        assert dates == sorted(dates, reverse=True), doc_id
        for version in versions:
            if version['date']:
                datetime.date.fromisoformat(version['date'])
            assert version['dateKind'] in ('effective', 'document')
            if version['status'] == 'prelaunch':
                assert version['dateKind'] == 'document'
            for lang, _, _, _ in LANGS:
                markup = render_history(registry, doc_id, lang, version['id'])
                parsed = Page(markup)
                assert markup.count('aria-current="true"') == 1
                assert markup.count('<li ') == len(versions)
                path = ROOT / urlsplit(version_url(version, lang)).path.lstrip('/')
                if path.is_dir():
                    path /= 'index.html'
                assert path.is_file(), path
                check_links(path, parsed)
                text = path.read_text()
                assert text.count(START) == text.count(END) == 1, path
                assert f'data-history-doc="{doc_id}"' in text
                assert '/assets/css/legal-history.css' in text
                if version['status'] != 'current':
                    assert 'legal-history__notice' in text
                    assert '/assets/js/app.js' not in text, f'Live content in archive: {path}'
                if version.get('snapshot'):
                    documents = json.loads((ROOT / version['snapshot'] / 'documents.json').read_text())
                    check_body(text, documents[lang])
                checked.add(path)

    # The live renderer and pre-rendered HTML must agree in every UI language.
    # This also catches missing labels, incorrect per-language links, and RTL drift.
    script = r'''
const fs = require('node:fs');
const vm = require('node:vm');
const context = vm.createContext({document: {readyState: 'loading', addEventListener() {}, querySelector() {return null;}}});
vm.runInContext(fs.readFileSync('assets/js/app.js', 'utf8'), context);
context.registry = JSON.parse(fs.readFileSync('data/legal-history.json', 'utf8'));
vm.runInContext('legalHistoryData = registry', context);
const results = [];
for (const id of Object.keys(context.registry.documents)) {
  for (const lang of Object.keys(context.registry.labels)) {
    context.id = id; context.lang = lang;
    results.push([id, lang, vm.runInContext('currentLang = lang; renderLegalHistory(id)', context)]);
  }
}
context.document.querySelector = () => ({querySelector: () => ({outerHTML: '<aside>Static fallback</aside>'})});
if (vm.runInContext('legalHistoryData = null; renderLegalHistory("common_privacy")', context) !== '<aside>Static fallback</aside>') throw Error('Lost static navigation after failed metadata request');
console.log(JSON.stringify(results));
'''
    result = subprocess.run(['node', '-e', script], cwd=ROOT, check=True, capture_output=True, text=True)
    for doc_id, lang, rendered in json.loads(result.stdout):
        static = render_history(registry, doc_id, lang).replace(START, '').replace(END, '')
        assert html.unescape(static) == html.unescape(rendered), (doc_id, lang)

    # Frozen pages must keep their declared language, including an Arabic RTL body.
    snapshot = ROOT / 'privacy/snuumo/archive/before-analytics-2026-10-02'
    for lang, _, bcp, _ in LANGS:
        text = (snapshot / f'{lang}.html').read_text()
        page = Page(text)
        assert page.html_lang == bcp
        assert page.dir == ('rtl' if lang == 'ar' else 'ltr')
        assert '<script' not in text
    print(f'PASS: {len(registry["documents"])} document histories, {len(checked)} edition pages, 240 live/static locale comparisons, immutable Snuumo snapshot and failed-request fallback')


if __name__ == '__main__':
    main()
