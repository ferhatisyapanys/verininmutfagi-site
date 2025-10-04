#!/usr/bin/env python3
"""
Static link checker for the built site.

Checks internal links (href/src) under the site/ folder.
Skips external (http/https), mailto:, tel:, data:, javascript: URIs.

Usage:
  python3 scripts/check_links.py --base site --strict

Returns non-zero exit code if --strict and broken links found.
"""
import os
import sys
import argparse
from html.parser import HTMLParser
from urllib.parse import urlparse

class LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []  # (attr_name, url, tag)

    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k in ('href', 'src') and v:
                self.links.append((k, v, tag))

SKIP_SCHEMES = ('http://', 'https://', 'mailto:', 'tel:', 'data:', 'javascript:')

def normalize_target(base_dir, page_rel, ref):
    # Strip fragment and query
    ref = ref.split('#', 1)[0]
    ref = ref.split('?', 1)[0]
    if not ref:
        return None
    if ref.startswith('/'):
        target = os.path.join(base_dir, ref.lstrip('/'))
    else:
        target = os.path.normpath(os.path.join(base_dir, os.path.dirname(page_rel), ref))
    # If directory, assume index.html
    if os.path.isdir(target):
        index_path = os.path.join(target, 'index.html')
        return index_path
    # If no extension and exists as dir with index.html
    if not os.path.splitext(target)[1] and os.path.isdir(target):
        return os.path.join(target, 'index.html')
    # If no extension and file not found, try add index.html
    if not os.path.exists(target) and not os.path.splitext(target)[1]:
        alt = os.path.join(target, 'index.html')
        return alt
    return target

def is_external(url: str) -> bool:
    up = urlparse(url)
    if up.scheme in ('http', 'https', 'mailto', 'tel', 'data', 'javascript'):
        return True
    for s in SKIP_SCHEMES:
        if url.startswith(s):
            return True
    return False

SKIP_DIRS = {'templates'}

def check_site(base_dir: str):
    broken = []
    pages = []
    for root, dirs, files in os.walk(base_dir):
        # skip known template dirs
        relroot = os.path.relpath(root, base_dir)
        parts = relroot.split(os.sep)
        if any(p in SKIP_DIRS for p in parts):
            continue
        for fn in files:
            if not fn.lower().endswith('.html'):
                continue
            rel = os.path.relpath(os.path.join(root, fn), base_dir)
            pages.append(rel)
    for rel in pages:
        p = os.path.join(base_dir, rel)
        try:
            html = open(p, 'r', encoding='utf-8', errors='ignore').read()
        except Exception:
            continue
        parser = LinkCollector()
        try:
            parser.feed(html)
        except Exception:
            # Skip parse errors
            continue
        for attr, url, tag in parser.links:
            if not url or url.strip() == '' or url.startswith('#'):
                continue
            if is_external(url):
                continue
            target = normalize_target(base_dir, rel, url)
            if not target:
                continue
            if not os.path.exists(target):
                broken.append((rel, tag, attr, url))
    return broken

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='site')
    ap.add_argument('--strict', action='store_true', help='Exit 1 if broken links found')
    args = ap.parse_args()
    broken = check_site(args.base)
    if broken:
        print(f"Broken links: {len(broken)}")
        for rel, tag, attr, url in broken:
            print(f"  [{rel}] <{tag} {attr}='{url}'> -> MISSING")
        if args.strict:
            sys.exit(1)
    else:
        print("No broken internal links found.")

if __name__ == '__main__':
    main()
