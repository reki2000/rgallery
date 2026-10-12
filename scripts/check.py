#!/usr/bin/env python3
"""Check generated pages, relative links, locale switches and screenshot assets."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from build import ROOT, load_projects

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
        self.lang = None
        self.articles = 0
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'html':
            self.lang = attrs.get('lang')
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        if tag == 'article':
            self.articles += 1
        for key in ('href', 'src'):
            if attrs.get(key):
                self.links.append(attrs[key])
        if tag == 'img' and attrs.get('src') and not attrs.get('alt'):
            raise AssertionError('Image has no alternative text')

docs = ROOT / 'docs'
projects = load_projects()
pages = {}
for file in docs.rglob('*.html'):
    page = Page()
    page.feed(file.read_text(encoding='utf-8'))
    assert page.lang == ('en' if file.relative_to(docs).parts[0] == 'en' else 'ja'), file
    assert 'main' in page.ids, file
    pages[file.resolve()] = page
for file, page in pages.items():
    for link in page.links:
        url = urlsplit(link)
        if url.scheme or url.netloc:
            continue
        assert not url.path.startswith('/'), f'Absolute URL would break a project Pages path: {file}: {link}'
        target = (file.parent / unquote(url.path)).resolve() if url.path else file
        assert target.is_relative_to(docs.resolve()), f'Link escapes docs: {link}'
        assert target.is_file(), f'Broken link: {file}: {link}'
        if url.fragment and target in pages:
            assert url.fragment in pages[target].ids, f'Missing anchor: {link}'
for lang in ('ja', 'en'):
    folder = docs if lang == 'ja' else docs / 'en'
    assert pages[(folder / 'index.html').resolve()].articles == len(projects)
    for tag in ('game', 'demo', 'text'):
        assert pages[(folder / f'{tag}.html').resolve()].articles == sum(tag in p['tags'] for p in projects)
    for p in projects:
        assert f'project-{p["id"]}' in pages[(folder / 'index.html').resolve()].ids
    assert not (folder / 'projects').exists(), 'Detail pages must not be generated'
assert len(pages) == 8
assert (docs / '.nojekyll').is_file()
print(f'Checked {len(pages)} HTML pages: locale, links, assets, category counts and inline project sections OK')
