#!/usr/bin/env python3
import pathlib, time, os
from urllib.parse import quote

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
BASE = os.environ.get('SITE_BASE_URL', 'https://verininmutfagi.com').rstrip('/')

def url_for(path: pathlib.Path):
    rel = path.relative_to(SITE).as_posix()
    return f"{BASE}/{quote(rel)}"

def lastmod(path: pathlib.Path):
    try:
        ts = int(path.stat().st_mtime)
        return time.strftime('%Y-%m-%d', time.gmtime(ts))
    except Exception:
        return None

def add(urlset, p):
    lm = lastmod(p)
    url = url_for(p)
    urlset.append((url, lm))

def main():
    urlset = []
    # Top level pages
    for rel in ['index.html', 'blog/index.html', 'bultenler/index.html', 'youtube/index.html', 'contact/index.html']:
        p = SITE / rel
        if p.exists(): add(urlset, p)
    # Blog posts
    for p in sorted((SITE/'blog').glob('*.html')):
        if p.name.lower() == 'index.html':
            continue
        add(urlset, p)
    # Bulletins
    for p in sorted((SITE/'bultenler').glob('*.html')):
        if p.name.lower() == 'index.html':
            continue
        add(urlset, p)

    # Build XML
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    for url, lm in urlset:
        lines.append('<url>')
        lines.append(f'  <loc>{url}</loc>')
        if lm:
            lines.append(f'  <lastmod>{lm}</lastmod>')
        lines.append('</url>')
    lines.append('</urlset>')
    (SITE/'sitemap.xml').write_text('\n'.join(lines), encoding='utf-8')
    print(f"Wrote sitemap with {len(urlset)} urls to {SITE/'sitemap.xml'}")

if __name__ == '__main__':
    main()
