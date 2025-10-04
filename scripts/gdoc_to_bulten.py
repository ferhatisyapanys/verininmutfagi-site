#!/usr/bin/env python3
"""
Fetch Google Docs as HTML and generate a bulletin JSON for site/bultenler.

Usage examples:
  # Single
  python3 scripts/gdoc_to_bulten.py \
    --url "https://docs.google.com/document/d/1Hk2LiNvJ1k8OM162uZOMr_W5qWUQrieo4Cx7Pzy0TAg/edit" \
    --slug haftalik-bulten-02 \
    --title "Haftalık Bülten #2 — Yapay Zekâ & Veri" \
    --date 2025-09-24 \
    --intro "Bu hafta öne çıkanlar"

  # Batch by text file (one URL per line). Missing args (title/date/slug) auto-derived.
  python3 scripts/gdoc_to_bulten.py --batch urls.txt

Note: The Google Doc must be shared as "Anyone with the link can view".
"""
import argparse
import os
import re
import json
from datetime import datetime, timedelta
from urllib.parse import urlparse
from urllib.request import urlopen, Request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT_DIR = os.path.join(ROOT, 'data', 'bultenler')


def extract_doc_id(url: str) -> str:
    m = re.search(r"/document/d/([a-zA-Z0-9_-]+)", url)
    if not m:
        raise ValueError('Invalid Docs URL (cannot find /document/d/<ID>)')
    return m.group(1)


def fetch_gdoc_html(url: str) -> str:
    doc_id = extract_doc_id(url)
    export = f"https://docs.google.com/document/d/{doc_id}/export?format=html"
    req = Request(export, headers={'User-Agent':'Mozilla/5.0'})
    with urlopen(req) as r:
        html = r.read().decode('utf-8', errors='ignore')
    return html


def simple_clean(html: str) -> str:
    # remove google doc styles and comments
    html = re.sub(r"<!--.*?-->", " ", html, flags=re.DOTALL)
    html = re.sub(r"<style[\s\S]*?</style>", " ", html, flags=re.IGNORECASE)
    # keep only body inner
    m = re.search(r"<body[^>]*>([\s\S]*?)</body>", html, flags=re.IGNORECASE)
    if m:
        html = m.group(1)
    # trim extra spans with inline styles (light touch)
    html = re.sub(r"\sstyle=\"[^\"]*\"", "", html)
    # collapse spaces
    html = re.sub(r"\s+", " ", html)
    # re-enable paragraphs line breaks for readability
    html = html.replace("</p>", "</p>\n")
    return html.strip()


def derive_slug(title: str) -> str:
    t = title.lower().strip()
    t = re.sub(r"[^a-z0-9\s-]", "", t)
    t = re.sub(r"\s+", "-", t)
    t = re.sub(r"-+", "-", t).strip('-')
    return t or ('bulten-' + datetime.now().strftime('%Y%m%d'))


TR_MONTHS = {
    1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan', 5: 'Mayıs', 6: 'Haziran',
    7: 'Temmuz', 8: 'Ağustos', 9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'
}

def monday_of(dt: datetime) -> datetime:
    return dt - timedelta(days=dt.weekday())  # Monday=0

def title_from_weekstart(dt: datetime) -> str:
    mname = TR_MONTHS.get(dt.month, dt.strftime('%b'))
    return f"Verinin Dünyası {dt.day} {mname}"


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--url')
    p.add_argument('--batch')
    p.add_argument('--slug')
    p.add_argument('--title')
    p.add_argument('--date')
    p.add_argument('--intro', default='')
    p.add_argument('--hero', default='../assets/img/covers/default.jpg')
    # Auto weekly titling for batch or single
    p.add_argument('--auto-week-title', action='store_true', help='Title as "Verinin Dünyası <GG> <Ay>" and slug/date from week start (Monday)')
    p.add_argument('--week-start', help='ISO date (YYYY-MM-DD) to use as first week start (defaults to this week)')
    p.add_argument('--weekly-seq', action='store_true', help='When used with --batch, decrement 7 days per URL')
    args = p.parse_args()

    urls = []
    if args.batch:
        with open(args.batch, 'r', encoding='utf-8') as f:
            for line in f:
                u = line.strip()
                if u and not u.startswith('#'):
                    urls.append(u)
    elif args.url:
        urls = [args.url.strip()]
    else:
        raise SystemExit('Provide --url or --batch file with URLs')

    os.makedirs(OUT_DIR, exist_ok=True)
    base_dt = None
    if args.week_start:
        try:
            base_dt = datetime.fromisoformat(args.week_start)
        except Exception:
            base_dt = None
    if base_dt is None:
        base_dt = monday_of(datetime.now())

    for i, u in enumerate(urls):
        print(f"Fetching {u} ...")
        raw = fetch_gdoc_html(u)
        body = simple_clean(raw)
        # Week sequence control
        wdt = base_dt - timedelta(days=7*i) if (args.batch and args.weekly_seq) else base_dt
        title_auto = title_from_weekstart(wdt) if args.auto_week_title else None
        title_src = (re.search(r"<title>(.*?)</title>", raw, re.IGNORECASE) or [None, 'Haftalık Bülten'])[1]
        title = args.title or title_auto or title_src
        date_iso = args.date or wdt.strftime('%Y-%m-%d')
        slug_auto = f"verinin-dunyasi-{wdt.strftime('%Y-%m-%d')}" if args.auto_week_title else None
        slug = args.slug or slug_auto or derive_slug(title)
        rec = {
            'title': title,
            'date': date_iso,
            'slug': slug,
            'hero': args.hero,
            'intro': args.intro,
            'blog': [],
            'youtube': [],
            'notes': [],
            'doc_html': body,
        }
        out_path = os.path.join(OUT_DIR, f'{slug}.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(rec, f, ensure_ascii=False, indent=2)
        print('Wrote', out_path)

if __name__ == '__main__':
    main()
