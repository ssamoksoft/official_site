#!/usr/bin/env python3
"""Check shipped links, static readability, translations and historical copies."""
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
from build_lang_pages import LANGS, esc, escape_and_link

ROOT = Path(__file__).resolve().parent.parent
KINDS = {'privacy':'', 'terms':'terms/', 'delete':'delete-account/'}

class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.links = []
        self.headings = 0
        self.html_lang = None
        self.dir = None
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'a':
            self.links.append(a.get('href', ''))
        if tag == 'h2':
            self.headings += 1
        if tag == 'html':
            self.html_lang, self.dir = a.get('lang'), a.get('dir','ltr')

def check_links(path, page):
    for link in page.links:
        parts = urlsplit(link)
        if parts.scheme or parts.netloc or not parts.path:
            continue
        target = ROOT / parts.path.lstrip('/') if parts.path.startswith('/') else path.parent / unquote(parts.path)
        if target.is_dir():
            target = target / 'index.html'
        assert target.is_file(), (path, link)

def check_body(text, document):
    assert escape_and_link(document['applies']) in text
    for section in document['sections']:
        for value in ([section['b']] if section.get('b') else []) + section.get('l', []):
            assert escape_and_link(value) in text, value

def main():
    checked = 0
    for lang,_,bcp,_ in LANGS:
        data = json.loads((ROOT/f'data/i18n/{lang}.json').read_text())
        assert isinstance(data['footer']['links']['privacy'], str)
        assert '2026-10-11' in data['privacy']['updated']
        for kind,directory in KINDS.items():
            doc = data['docs']['stelleaf_'+kind]
            assert '2026-10-11' in doc['updated']
            if kind == 'privacy':
                assert 'https://privacy.kisa.or.kr/' in json.dumps(doc,ensure_ascii=False)
                assert 'privacy.kr' not in json.dumps(doc,ensure_ascii=False)
            path = ROOT/f'privacy/stelleaf/{directory}{lang}.html'
            text = path.read_text()
            page = Page(text)
            assert page.headings == len(doc['sections']), path
            assert page.html_lang == bcp, path
            assert page.dir == ('rtl' if lang == 'ar' else 'ltr'), path
            assert '<noscript>' in text and 'id="legal-root"' in text
            assert f'href="/privacy/stelleaf/{lang}.html"' in text
            check_body(text,doc)
            check_links(path,page)
            checked += 1
        common = ROOT/f'{lang.replace("_","-")}/privacy/index.html'
        text = common.read_text()
        assert escape_and_link(data['privacy']['s_retention_body']) in text
        assert escape_and_link(data['privacy']['s_storage_body']) in text
        check_links(common,Page(text))
    for directory in KINDS.values():
        path = ROOT/f'privacy/stelleaf/{directory}index.html'
        page = Page(path.read_text())
        assert page.headings > 0 and page.html_lang == 'en'
        check_links(path,page)
    archives = [(ROOT/'privacy/stelleaf/archive'/x,k) for x,k in [
        ('2026-10-10','privacy'),('terms-2026-07-25','terms'),('delete-2026-09-20','delete')]]
    for directory,kind in archives:
        old = json.loads((directory/'documents.json').read_text())
        for lang in old:
            path=directory/f'{lang}.html'
            text=path.read_text()
            assert '<script' not in text and 'noindex' in text
            assert esc(old[lang]['updated']) in text, (kind, lang)
            check_body(text,old[lang])
            check_links(path,Page(text))
    print(f'PASS: {checked} localized app pages, 3 legacy URLs, 16 common pages, 48 app archive bodies and their links')

if __name__ == '__main__':
    main()
