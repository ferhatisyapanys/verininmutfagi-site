#!/usr/bin/env python3
import os
import pathlib
from datetime import datetime
from html import unescape
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
BLOG = SITE / 'blog'
BASE = os.environ.get('SITE_BASE_URL', 'https://verininmutfagi.com').rstrip('/')

def extract_title(html: str) -> str:
    m = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE|re.DOTALL)
    return unescape(m.group(1).strip()) if m else 'Blog Yazısı'

def extract_summary(html: str, limit=200) -> str:
    s = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
    s = re.sub(r"<style[\s\S]*?</style>", " ", s, flags=re.IGNORECASE)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return unescape(s[:limit])

def main():
    items = []
    for p in BLOG.glob('*.html'):
        if p.name.lower() == 'index.html':
            continue
        try:
            html = p.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        title = extract_title(html)
        summary = extract_summary(html)
        ts = int(p.stat().st_mtime)
        pub = datetime.utcfromtimestamp(ts).strftime('%a, %d %b %Y %H:%M:%S GMT')
        link = f"{BASE}/blog/{p.name}"
        items.append((ts, title, link, summary, pub))
    items.sort(key=lambda x: x[0], reverse=True)
    items = items[:50]
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0">',
        '<channel>',
        f'<title>Verinin Mutfağı Blog</title>',
        f'<link>{BASE}/blog/</link>',
        f'<description>Veri ve yapay zekâ üzerine blog</description>',
    ]
    for _ts, title, link, summary, pub in items:
        lines += [
            '<item>',
            f'<title>{title}</title>',
            f'<link>{link}</link>',
            f'<description>{summary}</description>',
            f'<pubDate>{pub}</pubDate>',
            '</item>'
        ]
    lines += ['</channel>', '</rss>']
    out = BLOG / 'feed.xml'
    out.write_text('\n'.join(lines), encoding='utf-8')
    print('Wrote RSS feed to', out)

if __name__ == '__main__':
    main()

