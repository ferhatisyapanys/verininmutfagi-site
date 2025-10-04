#!/usr/bin/env python3
"""
Watches source blog HTML files and rebuilds the site automatically when new files are
added or existing ones are changed. Uses only stdlib (polling every 2 seconds).

Usage:
  python3 scripts/watch_posts.py

Tip: In another terminal, you can serve the static site directory to preview:
  cd site && python3 -m http.server 9000
  Then open http://localhost:9000
"""
import os
import sys
import time
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
BLOG_DIR = ROOT / 'site' / 'blog'

def snapshot_sources():
    # Source posts are site/blog/*.html (excluding index.html)
    shots = {}
    BLOG_DIR.mkdir(parents=True, exist_ok=True)
    for p in BLOG_DIR.glob('*.html'):
        if p.name.lower() == 'index.html':
            continue
        try:
            shots[p] = p.stat().st_mtime
        except FileNotFoundError:
            pass
    return shots

def rebuild():
    print('[watch] Change detected → rebuilding blog...')
    # Import and call main() from build_blog
    sys.path.insert(0, str(ROOT / 'scripts'))
    import importlib
    mod = importlib.import_module('build_blog')
    mod.main()

def main():
    print('[watch] Watching root HTML posts. Press Ctrl+C to stop.')
    prev = snapshot_sources()
    rebuild()  # initial build
    try:
        while True:
            time.sleep(2)
            cur = snapshot_sources()
            # Detect added/removed/modified files
            changed = False
            if set(cur.keys()) != set(prev.keys()):
                changed = True
            else:
                for p, mt in cur.items():
                    if prev.get(p) != mt:
                        changed = True
                        break
            if changed:
                rebuild()
                prev = cur
    except KeyboardInterrupt:
        print('\n[watch] Stopped.')

if __name__ == '__main__':
    main()
