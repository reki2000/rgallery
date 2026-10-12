#!/usr/bin/env python3
"""Build a bilingual static gallery from projects/*/project.yaml. No network."""
from pathlib import Path, PurePosixPath
from html import escape
from urllib.parse import urlsplit
import argparse
import hashlib
import json
import re
import shutil
import struct
import yaml
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
LANGS = ('ja', 'en')
TAGS = ('game', 'demo', 'text')
COPY = {
    'ja': dict(intro='小さな実験、動くかたち。', description='ブラウザで動くデモやゲーム、対話で読む教材。\nつくったものを、ここに集めています。', all='すべて', works='作品', details='紹介とスクリーンショット', launch='作品を開く', read='読んでみる', source='ソースコード', back='一覧に戻る', shots='スクリーンショット', no_shots='スクリーンショットは準備中です。', search='作品を探す', search_hint='名前・説明・技術で検索', empty='該当する作品がありません。', clear='検索をクリア', enlarge='画像を拡大', close='閉じる', previous='前の画像', next='次の画像', cover='画像準備中', footer='好奇心からつくった、デモ・ゲーム・読みもの。', language='表示言語', index='作品一覧'),
    'en': dict(intro='Small experiments. Moving ideas.', description='Demos and games for the browser.\nIdeas explored through conversation. A collection of things I make.', all='All', works='works', details='About & screenshots', launch='Open project', read='Read the texts', source='Source code', back='Back to the collection', shots='Screenshots', no_shots='Screenshots are being prepared.', search='Find a project', search_hint='Search names, descriptions or technology', empty='No matching projects.', clear='Clear search', enlarge='Enlarge image', close='Close', previous='Previous image', next='Next image', cover='Preview coming soon', footer='Demos, games and readings, made out of curiosity.', language='Language', index='Collection'),
}

def h(value):
    return escape(str(value), quote=True)

def external(value):
    return isinstance(value, str) and urlsplit(value).scheme == 'https' and bool(urlsplit(value).netloc)

def bilingual(value, label):
    if not isinstance(value, dict) or any(not isinstance(value.get(lang), str) or not value[lang].strip() for lang in LANGS):
        raise ValueError(f'{label}: both ja and en text are required')

def load_projects(directory=ROOT / 'projects'):
    projects = []
    for folder in sorted(directory.iterdir()):
        if not folder.is_dir() or folder.name.startswith('.'):
            continue
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', folder.name):
            raise ValueError(f'Invalid directory slug: {folder.name}')
        metadata = folder / 'project.yaml'
        if not metadata.is_file():
            raise ValueError(f'{folder.name}: project.yaml is missing')
        p = yaml.safe_load(metadata.read_text(encoding='utf-8'))
        if not isinstance(p, dict):
            raise ValueError(f'{metadata}: expected a mapping')
        for field in ('title', 'summary'):
            bilingual(p.get(field), f'{folder.name}.{field}')
        if 'note' in p:
            bilingual(p['note'], f'{folder.name}.note')
        if not isinstance(p.get('tags'), list) or not p['tags'] or any(tag not in TAGS for tag in p['tags']):
            raise ValueError(f'{folder.name}: tags must contain game, demo or text')
        for field in ('url', 'repository'):
            if p.get(field) and not external(p[field]):
                raise ValueError(f'{folder.name}.{field}: an HTTPS URL is required')
        if not isinstance(p.get('technology', []), list) or any(not isinstance(v, str) for v in p.get('technology', [])):
            raise ValueError(f'{folder.name}.technology: expected a list of strings')
        if not isinstance(p.get('screenshots', []), list):
            raise ValueError(f'{folder.name}.screenshots: expected a list')
        for shot in p.get('screenshots', []):
            if not isinstance(shot, dict):
                raise ValueError(f'{folder.name}: invalid screenshot')
            bilingual(shot.get('caption'), f'{folder.name}.screenshot.caption')
            src = shot.get('src')
            if not isinstance(src, str) or not src:
                raise ValueError(f'{folder.name}: screenshot src is required')
            if external(src):
                if shot.get('crop'):
                    raise ValueError(f'{folder.name}: crop requires a local PNG')
                continue
            path = PurePosixPath(src)
            if path.is_absolute() or '..' in path.parts or path.suffix.lower() not in ('.png', '.jpg', '.jpeg', '.webp', '.avif'):
                raise ValueError(f'{folder.name}: invalid screenshot path {src}')
            if not (folder / src).resolve().is_relative_to(folder.resolve()) or not (folder / src).is_file():
                raise ValueError(f'{folder.name}: missing screenshot {src}')
            if 'crop' in shot:
                crop = shot['crop']
                if not isinstance(crop, dict) or set(crop) != {'x', 'y', 'width', 'height'} or any(type(v) is not int for v in crop.values()):
                    raise ValueError(f'{folder.name}: crop requires integer x, y, width and height')
                data = (folder / src).read_bytes()
                if not data.startswith(b'\x89PNG\r\n\x1a\n'):
                    raise ValueError(f'{folder.name}: crop requires a local PNG')
                width, height = struct.unpack('>II', data[16:24])
                if crop['x'] < 0 or crop['y'] < 0 or crop['width'] <= 0 or crop['height'] <= 0 or crop['x'] + crop['width'] > width or crop['y'] + crop['height'] > height:
                    raise ValueError(f'{folder.name}: crop exceeds image bounds')
        order = p.get('order', 100)
        if not isinstance(order, int):
            raise ValueError(f'{folder.name}.order: expected an integer')
        projects.append(dict(p, id=folder.name, screenshots=p.get('screenshots', []), technology=p.get('technology', []), order=order))
    return sorted(projects, key=lambda p: (p['order'], p['id']))

def image_path(shot):
    key = hashlib.sha256(json.dumps({'src': shot['src'], 'crop': shot.get('crop')}, sort_keys=True).encode()).hexdigest()[:20]
    return f'images/{key}.jpg'


def render_image(source, target, shot):
    with Image.open(source) as original:
        image = ImageOps.exif_transpose(original)
        if shot.get('crop'):
            c = shot['crop']
            image = image.crop((c['x'], c['y'], c['x'] + c['width'], c['y'] + c['height']))
        image.thumbnail((1280, 1280), Image.Resampling.LANCZOS)
        if 'A' in image.getbands() or 'transparency' in image.info:
            rgba = image.convert('RGBA')
            image = Image.new('RGB', rgba.size, (22, 23, 29))
            image.paste(rgba, mask=rgba.getchannel('A'))
        else:
            image = image.convert('RGB')
        target.parent.mkdir(parents=True, exist_ok=True)
        image.save(target, 'JPEG', quality=82, optimize=True, progressive=True)


def shot_url(p, shot, prefix):
    return shot['src'] if external(shot['src']) else prefix + f"assets/projects/{p['id']}/{image_path(shot)}"

def badges(p):
    return ''.join(f'<span class="tag tag-{h(t)}">{h(t)}</span>' for t in p['tags'])

def cover(p, lang):
    if 'text' in p['tags']:
        return f'<div class="text-cover"><span class="mono">TEXT / DIALOGUE</span><strong>{h(p["title"][lang])}</strong><span>{"問いからはじまる、学び。" if lang == "ja" else "Learning begins with a question."}</span></div>'
    return f'<div class="missing-cover"><span class="mono">{h(p["id"].upper())}</span><span>{h(COPY[lang]["cover"])}</span></div>'

def github_link(url, label, class_name='repository-link'):
    icon = '<svg viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path fill="currentColor" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82A7.65 7.65 0 0 1 8 3.86c.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z"/></svg>'
    return f'<a class="{class_name} icon-link" href="{h(url)}" target="_blank" rel="noopener noreferrer" aria-label="{h(label)}" title="{h(label)}">{icon}</a>'


def project_row(p, lang, prefix, number):
    c = COPY[lang]
    photos = ''
    if p['screenshots']:
        for index, shot in enumerate(p['screenshots']):
            url = h(shot_url(p, shot, prefix))
            caption = h(shot['caption'][lang])
            visible = index < 5
            image = f'<img src="{url}" alt="{caption}" loading="lazy" decoding="async">' if visible else ''
            photos += f'<a href="{url}" class="preview-shot screenshot-link shot-{index}" data-gallery="{h(p["id"])}" data-caption="{caption}" aria-label="{h(c["enlarge"])}: {caption}" {"hidden" if not visible else ""}>{image}</a>'
    else:
        photos = cover(p, lang)
    action = f'<a class="open-link" href="{h(p["url"])}" target="_blank" rel="noopener noreferrer">{h(c["read"] if "text" in p["tags"] else c["launch"])} <span aria-hidden="true">↗</span></a>' if p.get('url') else ''
    source = github_link(p['repository'], p['title'][lang] + ' · GitHub') if p.get('repository') else ''
    note = f'<p class="project-note">{h(p["note"][lang])}</p>' if p.get('note') else ''
    search = ' '.join([p['title'][lang], p['summary'][lang], *p['technology'], *p['tags']])
    return f'''<article id="project-{h(p['id'])}" class="project" data-tags="{h(' '.join(p['tags']))}" data-search="{h(search.lower())}">
      <div class="project-info"><div class="project-meta"><span class="number mono">{number:02d}</span>{badges(p)}</div>
      <h2>{h(p['title'][lang])}</h2><p>{h(p['summary'][lang])}</p>{note}
      <div class="technologies mono">{h(' · '.join(p['technology']))}</div><div class="project-links">{action}{source}</div></div>
      <div class="project-preview">{photos}</div></article>'''

def shell(body, lang, prefix, counterpart, title, description, canonical, site):
    c = COPY[lang]
    english = lang == 'en'
    ja_link, en_link = (counterpart, '') if english else ('', counterpart)
    switch = ''.join(f'<span aria-current="page" class="active" lang="{code}" aria-label="{name}">{label}</span>' if code == lang else f'<a href="{h(link)}" lang="{code}" hreflang="{code}" aria-label="{name}">{label}</a>' for code, label, name, link in [('en', 'En', 'English', en_link), ('ja', 'Jp', '日本語', ja_link)])
    return f'''<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{h(title)} — {h(site['name'])}</title><meta name="description" content="{h(description)}">
<meta name="theme-color" content="#16171d"><link rel="canonical" href="{h(site['url'] + canonical)}">
<link rel="alternate" hreflang="{'ja' if english else 'en'}" href="{h(site['url'] + (canonical.removeprefix('en/') if english else 'en/' + canonical))}">
<meta property="og:type" content="website"><meta property="og:title" content="{h(title)}"><meta property="og:description" content="{h(description)}"><meta property="og:url" content="{h(site['url'] + canonical)}">
<link rel="stylesheet" href="{prefix}assets/style.css"><script src="{prefix}assets/site.js" defer></script></head>
<body><a class="skip-link" href="#main">{'本文へ' if lang == 'ja' else 'Skip to content'}</a><div class="page">
<header class="site-header"><a class="wordmark" href="index.html">{h(site['name'])}</a>
<div class="header-right">{github_link(site["repository"], site["name"] + " · GitHub", "github-link")}<nav class="languages" aria-label="{h(c['language'])}">{switch}</nav></div></header>
<main id="main">{body}</main><footer><span class="mono">© {h(site['author'])}</span></footer></div>
<dialog class="lightbox" aria-label="{h(c['shots'])}"><div class="lightbox-top"><span class="lightbox-caption"></span><button class="close-lightbox" aria-label="{h(c['close'])}">×</button></div><img alt=""><div class="lightbox-bottom"><button class="previous-shot" aria-label="{h(c['previous'])}">←</button><span class="lightbox-count mono"></span><button class="next-shot" aria-label="{h(c['next'])}">→</button></div></dialog>
</body></html>'''

def build(output=ROOT / 'docs'):
    site = yaml.safe_load((ROOT / 'site.yaml').read_text(encoding='utf-8'))
    if not external(site.get('url')) or not re.fullmatch(r'[\w-]+', site.get('author', '')):
        raise ValueError('site.yaml: invalid site url or author')
    site['url'] = site['url'].rstrip('/') + '/'
    projects = load_projects()
    # Validate every input before replacing the build output.
    if output.exists():
        shutil.rmtree(output)
    (output / 'assets').mkdir(parents=True)
    for file in (ROOT / 'static').iterdir():
        if file.is_file():
            shutil.copy2(file, output / 'assets' / file.name)
    for p in projects:
        for shot in p['screenshots']:
            if not external(shot['src']):
                target = output / 'assets' / 'projects' / p['id'] / image_path(shot)
                render_image(ROOT / 'projects' / p['id'] / shot['src'], target, shot)
    urls = []
    for lang in LANGS:
        c = COPY[lang]
        folder = output if lang == 'ja' else output / 'en'
        folder.mkdir(exist_ok=True)
        prefix = '' if lang == 'ja' else '../'
        for tag in (None, *TAGS):
            filename = f'{tag}.html' if tag else 'index.html'
            shown = [p for p in projects if tag is None or tag in p['tags']]
            tabs = ''.join(f'<a href="{t + ".html" if t else "index.html"}" data-filter="{t or "all"}" class="filter {"selected" if t == tag else ""}" {"aria-current=\"page\"" if t == tag else ""}>{h(t or c["all"])} <span class="mono">{len([p for p in projects if not t or t in p["tags"]])}</span></a>' for t in (None, *TAGS))
            body = f'''<h1 class="sr-only">{h(c['index'])}</h1><section class="collection" aria-label="{h(c['index'])}"><div class="collection-tools"><nav class="filters" aria-label="{'種類' if lang == 'ja' else 'Category'}">{tabs}</nav>
<div class="search" hidden><label class="sr-only" for="search">{h(c['search'])}</label><span aria-hidden="true">⌕</span><input id="search" type="search" placeholder="{h(c['search'])}" title="{h(c['search_hint'])}"><button class="clear-search" hidden aria-label="{h(c['clear'])}">×</button></div></div>
<div class="collection-heading"><span class="mono">{'SELECTED WORKS' if not tag else tag.upper()}</span><span class="result-count mono" role="status" aria-live="polite">{len(shown)} {h(c['works'])}</span></div>
<div class="project-list" data-category="{tag or 'all'}" data-works="{h(c['works'])}">{''.join(project_row(p, lang, prefix, projects.index(p) + 1) for p in shown)}</div><p class="empty-state" hidden>{h(c['empty'])}</p></section>'''
            canonical = ('' if lang == 'ja' else 'en/') + filename
            counterpart = ('en/' if lang == 'ja' else '../') + filename
            (folder / filename).write_text(shell(body, lang, prefix, counterpart, c['index'], c['description'].replace('\n', ' '), canonical, site), encoding='utf-8')
            urls.append(canonical)
    (output / '.nojekyll').touch()
    sitemap = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{h(site["url"] + u)}</loc></url>' for u in urls) + '</urlset>'
    (output / 'sitemap.xml').write_text(sitemap, encoding='utf-8')
    (output / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {site["url"]}sitemap.xml\n', encoding='utf-8')
    print(f'Built {len(projects)} projects / {len(urls)} HTML pages → {output}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Validate project metadata without writing files')
    args = parser.parse_args()
    try:
        if args.check:
            print(f'Validated {len(load_projects())} projects')
        else:
            build()
    except (ValueError, yaml.YAMLError) as error:
        parser.exit(1, f'Build failed: {error}\n')
