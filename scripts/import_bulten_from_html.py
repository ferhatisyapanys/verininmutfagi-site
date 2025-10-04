#!/usr/bin/env python3
"""
Convert Google Docs "Web Page (.html)" downloads into site-compatible bulletins.

Given a source folder containing one or more exported HTML files (and their
adjacent images), this script:
  - Parses each .html file, extracts <title> and <body>
  - Copies local images to site/bultenler/assets/<slug>/ and rewrites paths
  - Creates data/bultenler/<slug>.json with doc_html set to cleaned body
  - Optionally auto-generates weekly title/slug/date ("Verinin Dünyası <GG Ay>")

Usage:
  python3 scripts/import_bulten_from_html.py --src "/path/to/folder" \
    --auto-week-title --week-start 2025-09-22 --weekly-seq

Then build pages:
  python3 scripts/build_bulten.py
"""
import argparse
import os
import re
import json
import shutil
from datetime import datetime, timedelta

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(ROOT, 'data', 'bultenler')
BULTEN_SITE_DIR = os.path.join(ROOT, 'site', 'bultenler')

TR_MONTHS = {
    1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan', 5: 'Mayıs', 6: 'Haziran',
    7: 'Temmuz', 8: 'Ağustos', 9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'
}

def monday_of(dt: datetime) -> datetime:
    return dt - timedelta(days=dt.weekday())

def title_from_weekstart(dt: datetime) -> str:
    mname = TR_MONTHS.get(dt.month, dt.strftime('%b'))
    return f"Verinin Dünyası {dt.day} {mname}"

def derive_slug(title: str) -> str:
    t = (title or '').lower().strip()
    t = re.sub(r"[^a-z0-9\s-]", "", t)
    t = re.sub(r"\s+", "-", t)
    t = re.sub(r"-+", "-", t).strip('-')
    return t or ('bulten-' + datetime.now().strftime('%Y%m%d'))

def read_file(p: str) -> str:
    return open(p, 'r', encoding='utf-8', errors='ignore').read()

def extract_title_and_body(html: str):
    m = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE|re.DOTALL)
    title = (m.group(1).strip() if m else 'Haftalık Bülten')
    m2 = re.search(r"<body[^>]*>([\s\S]*?)</body>", html, re.IGNORECASE)
    body = m2.group(1) if m2 else html
    # strip inline <style> and comments
    body = re.sub(r"<!--.*?-->", " ", body, flags=re.DOTALL)
    body = re.sub(r"<style[\s\S]*?</style>", " ", body, flags=re.IGNORECASE)
    # light-clean inline style attrs
    body = re.sub(r"\sstyle=\"[^\"]*\"", "", body)
    return title, body.strip()

def rewrite_and_copy_assets(body: str, src_dir: str, slug: str) -> str:
    # Copy local images/links referenced via src/href that are not absolute (http/https/data)
    out_assets = os.path.join(BULTEN_SITE_DIR, 'assets', slug)
    os.makedirs(out_assets, exist_ok=True)

    def replace_url(m):
        attr = m.group(1)
        url = m.group(2)
        if re.match(r"^(https?:|data:|assets/|../|/)", url):
            return m.group(0)  # leave as is (already absolute or site assets)
        # local file next to HTML; copy to assets/slug/
        src_path = os.path.join(src_dir, url)
        base_name = os.path.basename(url)
        dst_path = os.path.join(out_assets, base_name)
        try:
            if os.path.isfile(src_path):
                shutil.copy2(src_path, dst_path)
        except Exception:
            pass
        # new relative path from bulten HTML: assets/slug/filename
        new_url = f"assets/{slug}/{base_name}"
        return f'{attr}="{new_url}"'

    # Rewrite src and href
    body = re.sub(r"(src)=\"([^\"]+)\"", replace_url, body, flags=re.IGNORECASE)
    body = re.sub(r"(href)=\"([^\"]+)\"", replace_url, body, flags=re.IGNORECASE)
    return body

def find_folder_cover(src_dir: str):
    """Pick a cover image from a likely 'image' folder next to the HTML.
    Returns (rel_src_path, base_name) or (None, None) if not found.
    """
    candidates = []
    for name in os.listdir(src_dir):
        p = os.path.join(src_dir, name)
        if os.path.isdir(p) and name.lower() in ('image', 'images', 'res', 'assets'):
            for fn in os.listdir(p):
                if fn.lower().endswith(('.jpg','.jpeg','.png','.webp','.gif')):
                    candidates.append(os.path.join(name, fn))
    if candidates:
        # pick the first
        rel = candidates[0]
        return rel, os.path.basename(rel)
    return None, None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True, help='Folder containing exported .html files from Google Docs')
    ap.add_argument('--auto-week-title', action='store_true')
    ap.add_argument('--week-start', help='YYYY-MM-DD base week start (Monday)')
    ap.add_argument('--weekly-seq', action='store_true', help='Decrement 7 days per file (in alphabetical order)')
    args = ap.parse_args()

    src = os.path.abspath(args.src)
    if not os.path.isdir(src):
        raise SystemExit(f'Source folder not found: {src}')

    # Recursively collect .html files
    files = []
    for root, _dirs, fnames in os.walk(src):
        for fn in fnames:
            if fn.lower().endswith('.html'):
                files.append(os.path.join(root, fn))
    files.sort()
    if not files:
        raise SystemExit('No .html files found in source folder.')

    if args.week_start:
        try:
            base_dt = datetime.fromisoformat(args.week_start)
        except Exception:
            base_dt = monday_of(datetime.now())
    else:
        base_dt = monday_of(datetime.now())

    os.makedirs(DATA_DIR, exist_ok=True)
    # Regex to parse date from parent folder name like "… - 1 Eylül"
    import unicodedata
    def normalize_tr(s):
        return ''.join(c for c in unicodedata.normalize('NFC', s))
    MONTHS_TR = {
        'ocak':1,'subat':2,'şubat':2,'mart':3,'nisan':4,'mayis':5,'mayıs':5,'haziran':6,
        'temmuz':7,'agustos':8,'ağustos':8,'eylul':9,'eylül':9,'ekim':10,'kasim':11,'kasım':11,'aralik':12,'aralık':12
    }

    for i, path in enumerate(files):
        html = read_file(path)
        title_src, body = extract_title_and_body(html)
        # weekly logic or parse from folder name
        parent = os.path.basename(os.path.dirname(path))
        parent_n = normalize_tr(parent).lower()
        # try match "... - <gün> <ay>"
        m = re.search(r"(\d{1,2})\s+([a-zçğıöşü]+)", parent_n)
        wdt = None
        if m:
            try:
                day = int(m.group(1))
                mon_name = m.group(2)
                mon = MONTHS_TR.get(mon_name)
                if mon:
                    year = datetime.now().year
                    # heuristik: Eylül/Ağustos gibi aylar için yakın yıl
                    wdt = datetime(year, mon, day)
                    # haftabaşına çek
                    wdt = monday_of(wdt)
            except Exception:
                wdt = None
        if wdt is None:
            wdt = base_dt - timedelta(days=7*i) if args.weekly_seq else base_dt
        title_auto = title_from_weekstart(wdt) if args.auto_week_title else None
        title = title_auto or title_src
        date_iso = wdt.strftime('%Y-%m-%d')
        slug_auto = f"verinin-dunyasi-{wdt.strftime('%Y-%m-%d')}" if args.auto_week_title else None
        slug = slug_auto or derive_slug(title)

        # asset rewrite/copy (use the file's own folder as src_dir)
        src_dir = os.path.dirname(path)
        body2 = rewrite_and_copy_assets(body, src_dir, slug)
        # pick a cover image from 'image' folder if exists
        cover_rel, cover_base = find_folder_cover(src_dir)
        hero = '../assets/img/covers/default.jpg'
        if cover_rel and cover_base:
            # copy cover into site/bultenler/assets/slug/
            out_assets = os.path.join(BULTEN_SITE_DIR, 'assets', slug)
            os.makedirs(out_assets, exist_ok=True)
            try:
                shutil.copy2(os.path.join(src_dir, cover_rel), os.path.join(out_assets, cover_base))
                hero = f'assets/{slug}/{cover_base}'
            except Exception:
                pass

        rec = {
            'title': title,
            'date': date_iso,
            'slug': slug,
            'hero': hero,
            'intro': '',
            'blog': [],
            'youtube': [],
            'notes': [],
            'doc_html': body2,
        }
        out = os.path.join(DATA_DIR, f'{slug}.json')
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(rec, f, ensure_ascii=False, indent=2)
        print('Wrote', out)

    print('\nNext: python3 scripts/build_bulten.py')

if __name__ == '__main__':
    main()
