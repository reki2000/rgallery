#!/usr/bin/env python3
"""Import reviewed captures, skipping missing files."""
import argparse
import hashlib
import json
from pathlib import Path
import yaml
from build import ROOT, bilingual, external, load_projects

def import_captures(folder):
    try:
        manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    except FileNotFoundError:
        print(f'Skipped: {folder} (manifest.json is missing)')
        return
    projects = {p['id']: p for p in load_projects()}
    slug = manifest['project']
    if slug not in projects or not external(manifest.get('source_url')):
        raise ValueError('Invalid project or source URL')
    shots = manifest['screenshots']
    expected = {f'desktop-{i}.png' for i in range(1, 6)} | {f'mobile-{i}.png' for i in range(1, 3)}
    names = [s['src'] for s in shots]
    if len(names) != len(set(names)) or not set(names).issubset(expected):
        raise ValueError('Invalid or duplicate screenshot filenames')
    # Validate all available files before changing the project.
    available = []
    for shot in shots:
        try:
            data = (folder / shot['src']).read_bytes()
        except FileNotFoundError:
            print(f'Skipped: {folder / shot["src"]} (file is missing)')
            continue
        bilingual(shot.get('caption'), 'caption')
        if not external(shot.get('url')):
            raise ValueError('Invalid capture URL')
        if not data.startswith(b'\x89PNG\r\n\x1a\n') or hashlib.sha256(data).hexdigest() != shot.get('sha256'):
            raise ValueError(f'Invalid or changed capture: {shot["src"]}')
        available.append((shot, data))
    if not available:
        print(f'Skipped: {folder} (no images available; project metadata unchanged)')
        return
    project_folder = ROOT / 'projects' / slug
    # Stable per-capture directory: separate runs never overwrite older images.
    capture_key = hashlib.sha256(json.dumps(manifest, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()[:20]
    destination = project_folder / 'screenshots' / capture_key
    destination.mkdir(parents=True, exist_ok=True)
    metadata = project_folder / 'project.yaml'
    p = yaml.safe_load(metadata.read_text(encoding='utf-8'))
    shots = [shot for shot, _ in available]
    for shot, data in available:
        (destination / shot['src']).write_bytes(data)
    provenance = destination / 'capture.json'
    previous_shots = json.loads(provenance.read_text(encoding='utf-8'))['screenshots'] if provenance.is_file() else []
    combined_shots = {s['src']: s for s in previous_shots}
    combined_shots.update({s['src']: s for s in shots})
    imported_manifest = dict(manifest, screenshots=list(combined_shots.values()))
    (destination / 'capture.json').write_text(json.dumps(imported_manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    existing = p.setdefault('screenshots', [])
    registered = {s['src'] for s in existing}
    additions = [{'src': f'screenshots/{capture_key}/{s["src"]}', 'caption': s['caption']} for s in shots
                 if f'screenshots/{capture_key}/{s["src"]}' not in registered]
    existing.extend(additions)
    metadata.write_text(yaml.safe_dump(p, allow_unicode=True, sort_keys=False, width=110), encoding='utf-8')
    print(f'Added {len(additions)} screenshots into projects/{slug}/ ({len(existing)} total)')
    print('Build for local preview / GitHub Pages: python3 scripts/build.py')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    try:
        import_captures(args.directory)
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1, f'Import failed: {error}\n')
