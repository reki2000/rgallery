#!/usr/bin/env python3
"""Capture seven scenes per live project, advancing through the collection."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
from build import ROOT, external, load_projects

DESKTOP = {'width': 1440, 'height': 900}
MOBILE = {'width': 390, 'height': 844}
SHOTS = tuple(
    (f'desktop-{i}.png', DESKTOP, False,
     {'ja': f'PC・場面{i}', 'en': f'Desktop scene {i}'})
    for i in range(1, 6)
) + tuple(
    (f'mobile-{i}.png', MOBILE, True,
     {'ja': f'スマートフォン・場面{i}', 'en': f'Mobile scene {i}'})
    for i in range(1, 3)
)


def set_initial_window_size(context, page, size):
    """Size the real Chromium window without locking the page's viewport."""
    session = context.new_cdp_session(page)
    try:
        window_id = session.send('Browser.getWindowForTarget')['windowId']
        session.send('Browser.setWindowBounds', {'windowId': window_id, 'bounds': {'windowState': 'normal'}})
        frame = page.evaluate('({width: Math.max(0, outerWidth - innerWidth), height: Math.max(0, outerHeight - innerHeight)})')
        session.send('Browser.setWindowBounds', {'windowId': window_id, 'bounds': {
            'width': size['width'] + frame['width'], 'height': size['height'] + frame['height']}})
    finally:
        session.detach()


def parse_resize_command(answer, current=None):
    match = re.fullmatch(r'r\s+(\d+)\s*[x×]\s*(\d+)', answer)
    if match:
        width, height = map(int, match.groups())
    else:
        percent = re.fullmatch(r'r\s+([+-]?)([wh]?)((?:\d+(?:\.\d+)?|\.\d+))\s*%', answer)
        if not percent or current is None:
            raise ValueError('例: r 1200x800 / r +10% / r +w10% / r -h10%')
        sign, axis, amount = percent.groups()
        number = float(amount)
        scale = 1 + number / 100 if sign == '+' else 1 - number / 100 if sign == '-' else number / 100
        width = current['width'] * scale if axis != 'h' else current['width']
        height = current['height'] * scale if axis != 'w' else current['height']
        if not (239.5 <= width < 7680.5 and 239.5 <= height < 7680.5):
            raise ValueError('変更後の幅・高さは240〜7680になるよう指定してください。')
        width, height = round(width), round(height)
    if not (240 <= width <= 7680 and 240 <= height <= 7680):
        raise ValueError('幅・高さは240〜7680で指定してください。')
    return {'width': width, 'height': height}


def save_manifest(folder, manifest):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def capture(browser, project, override=None, completed=None):
    slug = project['id']
    url = override or project.get('url')
    if not external(url):
        raise ValueError('A live HTTPS URL is required.')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    folder = ROOT / '.captures' / slug / stamp
    manifest = {'project': slug, 'source_url': url, 'captured_at': stamp, 'screenshots': []}
    contexts = []
    current_mobile = None
    try:
        for index, (filename, viewport, mobile, caption) in enumerate(SHOTS):
            if mobile != current_mobile:
                # A fixed emulated viewport would ignore manual window resizing.
                # Mobile shots use a narrow, touch-enabled responsive window.
                context = browser.new_context(no_viewport=True, has_touch=mobile, locale='ja-JP')
                contexts.append(context)
                page = context.new_page()
                set_initial_window_size(context, page, viewport)
                response = page.goto(url, wait_until='domcontentloaded', timeout=90000)
                if response and response.status >= 400:
                    raise ValueError(f'Live site returned HTTP {response.status}: {url}')
                if current_mobile is not None:
                    # Close the desktop window when moving to mobile.
                    contexts.pop(0).close()
                current_mobile = mobile
                page.bring_to_front()
            instruction = 'PCで視点・操作・ページを変えた場面' if not mobile else 'スマホで表示・場面を変える'
            while True:
                answer = input(f'[{index + 1}/{len(SHOTS)}] {instruction} → Enterで撮影 / r 幅x高さ・+10%・+w10%・-h10% / sで次の作品 / qで終了: ').strip().lower()
                if answer == 's':
                    print(f'次の作品に進みます: {slug}')
                    return folder if manifest['screenshots'] else None
                if answer == 'q':
                    raise KeyboardInterrupt
                if answer.startswith('r'):
                    try:
                        current_size = page.evaluate('({width: innerWidth, height: innerHeight})')
                        size = parse_resize_command(answer, current_size)
                    except ValueError as error:
                        print(error)
                        continue
                    set_initial_window_size(context, page, size)
                    page.bring_to_front()
                    actual = page.evaluate('({width: innerWidth, height: innerHeight})')
                    print(f'表示サイズ: {actual["width"]}×{actual["height"]}（指定: {size["width"]}×{size["height"]}）。撮影はEnter。')
                    continue
                if not answer:
                    break
                print('Enter、r 幅x高さ / +10% / +w10% / -h10%、s、q のいずれかを入力してください。')
            if not external(page.url):
                raise ValueError('Only a real HTTPS page can be captured')
            folder.mkdir(parents=True, exist_ok=True)
            image = folder / filename
            page.screenshot(path=str(image), full_page=False)
            actual_size = page.evaluate('({width: innerWidth, height: innerHeight})')
            manifest['screenshots'].append({'src': filename, 'caption': caption,
                'url': page.url, 'viewport': actual_size,
                'sha256': hashlib.sha256(image.read_bytes()).hexdigest()})
            save_manifest(folder, manifest)
            print(f'Saved: {image}')
        return folder
    finally:
        try:
            if manifest['screenshots']:
                save_manifest(folder, manifest)
                if completed is not None:
                    completed.append(folder)
                print(f'Completed: {slug} / {len(manifest["screenshots"]) }枚を保存しました。')
        finally:
            for context in contexts:
                context.close()


def capture_projects(browser, projects, override=None, errors=(ValueError,), completed=None):
    if completed is None:
        completed = []
    for index, project in enumerate(projects):
        print(f'\n=== 作品 {index + 1}/{len(projects)}: {project["title"]["ja"]} ({project["id"]}) ===')
        if not external(override or project.get('url')):
            print('公開URL未登録のためスキップします。')
            continue
        try:
            capture(browser, project, override, completed)
        except errors as error:
            print(f'撮影できませんでした: {error}\n次の作品に進みます。')
    return completed


def select_projects(arguments, projects):
    """Only the basename identifies a project; shell-expanded paths are accepted."""
    by_id = {p['id']: p for p in projects}
    selected = []
    for argument in arguments:
        slug = Path(argument).name
        if slug not in by_id:
            raise ValueError(f'Unknown project: {slug or argument}')
        selected.append(by_id[slug])
    return selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('projects', nargs='*', metavar='DIRECTORY', help='Project directories or IDs in capture order; identified by basename. Example: projects/*')
    parser.add_argument('--url', help='Override the HTTPS demo URL for one selected project')
    parser.add_argument('--list', action='store_true')
    args = parser.parse_args()
    projects = load_projects()
    if args.projects:
        try:
            projects = select_projects(args.projects, projects)
        except ValueError as error:
            parser.error(str(error))
    if args.list:
        for p in projects:
            print(f'{p["id"]:16} {p.get("url", "公開URL未登録")}')
        return
    if not args.projects:
        parser.error('Specify project directories, for example: python3 scripts/capture.py projects/*')
    if args.url and (len(args.projects) != 1 or not external(args.url)):
        parser.error('--url requires exactly one selected project and an HTTPS URL')
    try:
        from playwright.sync_api import sync_playwright, Error
    except ImportError:
        parser.exit(1, 'Install capture dependencies: python3 -m pip install -r requirements-capture.txt\n')
    completed = []
    print('各作品: PC 5枚 → スマホ 2枚 → 自動で次の作品。')
    print('ブラウザで操作し、端末のEnterで撮影。エラーや読み込み中なら s でスキップ。q / Ctrl+C で終了。')
    print('枠をドラッグできない場合は、撮影待ちで r 1200x800 のように入力するとサイズ変更できます。')
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=False)
            try:
                # Keep results even when the user quits midway through the collection.
                capture_projects(browser, projects, args.url, (ValueError, Error), completed)
            finally:
                browser.close()
    except (KeyboardInterrupt, EOFError):
        print('\n撮影を終了しました。完了済みの作品は保存されています。')
    except Error as error:
        parser.exit(1, f'Browser failed: {error}\n')
    finally:
        print(f'\n完了: {len(completed)}作品。画像を確認後、以下で取り込めます。')
        for folder in completed:
            print(f'python3 scripts/import_captures.py {folder}')
        print('project.yaml と公開用 docs/ は撮影だけでは変更していません。')


if __name__ == '__main__':
    main()
