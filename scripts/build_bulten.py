#!/usr/bin/env python3
import json
import pathlib
from datetime import datetime
import re
from html import escape
import os
import json

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
TPL = SITE / 'templates'
BULTEN_DIR = SITE / 'bultenler'
DATA_DIR = ROOT / 'data' / 'bultenler'

TPL_INDEX = (TPL / 'bulten_index.html').read_text(encoding='utf-8')
TPL_PAGE = (TPL / 'bulten.html').read_text(encoding='utf-8')
SITE_BASE_URL = os.environ.get('SITE_BASE_URL', '').strip().rstrip('/')

IMAGE_EXTS = ('.jpg', '.jpeg', '.png', '.webp', '.gif')

def pick_bulletin_hero(slug: str, cur: str) -> str:
    """Prefer per-bulletin asset image: site/bultenler/assets/<slug>/image1.*
    or the first available image. Fallback to current hero.
    """
    assets_dir = SITE / 'bultenler' / 'assets' / slug
    try:
        if assets_dir.exists():
            files = sorted([p for p in assets_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS])
            if not files:
                return cur
            # Prefer image1.* if present
            preferred = [p for p in files if p.stem.lower() == 'image1']
            img = preferred[0] if preferred else files[0]
            # Path from bulletin HTML: assets/<slug>/<file>
            return f"assets/{slug}/{img.name}"
    except Exception:
        pass
    return cur


def fmt_date(d):
    try:
        dt = datetime.fromisoformat(d)
        return dt.strftime('%d %b %Y')
    except Exception:
        return d


def build_cards_blog(items):
    cards = []
    for it in items or []:
        slug = it.get('slug') or ''
        title = it.get('title') or slug.replace('-', ' ').title()
        cover = it.get('cover') or '../assets/img/covers/default.jpg'
        cards.append(
            '\n'.join([
                '<article class="vm-card">',
                f'  <a href="../blog/{escape(slug)}.html"><img class="vm-card-cover" src="{escape(cover)}" alt="{escape(title)}"></a>',
                '  <div class="vm-card-body">',
                f'    <h3><a href="../blog/{escape(slug)}.html">{escape(title)}</a></h3>',
                f'    <p><a href="../blog/{escape(slug)}.html">Yazıyı oku →</a></p>',
                '  </div>',
                '</article>'
            ])
        )
    return '\n'.join(cards)


def build_cards_youtube(items):
    cards = []
    for it in items or []:
        vid = it.get('id') or ''
        title = it.get('title') or 'YouTube Video'
        thumb = f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg'
        href = f'https://www.youtube.com/watch?v={vid}'
        cards.append(
            '\n'.join([
                '<article class="vm-card">',
                f'  <a href="{href}" target="_blank" rel="noopener"><img class="vm-card-cover" src="{thumb}" alt="{escape(title)}"></a>',
                '  <div class="vm-card-body">',
                f'    <h3><a href="{href}" target="_blank" rel="noopener">{escape(title)}</a></h3>',
                f'    <p><a href="{href}" target="_blank" rel="noopener">YouTube\'da izle →</a></p>',
                '  </div>',
                '</article>'
            ])
        )
    return '\n'.join(cards)


def build_notes_html(notes):
    if not notes:
        return '<p class="vm-muted">Not bulunamadı.</p>'
    out = ['<ul>']
    for n in notes:
        out.append(f'<li>{escape(n)}</li>')
    out.append('</ul>')
    return '\n'.join(out)


def build_one(rec):
    slug = rec.get('slug') or 'bulten'
    title = rec.get('title') or 'Haftalık Bülten'
    hero = rec.get('hero') or '../assets/img/covers/default.jpg'
    # Prefer per-bulletin image under site/bultenler/assets/<slug>/
    hero = pick_bulletin_hero(slug, hero)
    date = fmt_date(rec.get('date') or '')
    intro = rec.get('intro') or ''
    page = TPL_PAGE
    page = page.replace('{{TITLE}}', escape(title))
    page = page.replace('{{DATE}}', escape(date))
    page = page.replace('{{HERO}}', escape(hero))
    page = page.replace('{{INTRO}}', escape(intro))
    page = page.replace('{{BLOG_CARDS}}', build_cards_blog(rec.get('blog') or []))
    page = page.replace('{{YT_CARDS}}', build_cards_youtube(rec.get('youtube') or []))
    page = page.replace('{{NOTES_HTML}}', build_notes_html(rec.get('notes') or []))
    doc_html = rec.get('doc_html') or ''
    if doc_html:
        # Add lazy-loading to images in doc_html
        def add_lazy(s: str) -> str:
            return re.sub(r'<img([^>]*?)>', lambda m: (
                ('<img' + ('' if ' loading=' in m.group(1) else ' loading="lazy"') +
                 ('' if ' decoding=' in m.group(1) else ' decoding="async"') + m.group(1) + '>')
            ), s, flags=re.IGNORECASE)
        page = page.replace('{{DOC_HTML}}', f'<article class="vm-article">{add_lazy(doc_html)}</article>')
    else:
        # Eğer doc_html yoksa, blog/youtube/notlar'dan kompakt bir özet gövde oluştur
        body_parts = []
        if rec.get('blog'):
            body_parts.append('<h2>Öne Çıkan Bloglar</h2><div class="vm-grid">'+build_cards_blog(rec.get('blog'))+'</div>')
        if rec.get('youtube'):
            body_parts.append('<h2>Öne Çıkan Videolar</h2><div class="vm-grid">'+build_cards_youtube(rec.get('youtube'))+'</div>')
        if rec.get('notes'):
            body_parts.append('<h2>Notlar</h2>'+build_notes_html(rec.get('notes')))
        page = page.replace('{{DOC_HTML}}', '<article class="vm-article">'+('\n'.join(body_parts) or '<p class="vm-muted">Bu bülten için içerik hazırlanıyor.</p>')+'</article>')
    out = BULTEN_DIR / f'{slug}.html'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding='utf-8')
    # Inject JSON-LD for newsletter article
    try:
        from datetime import datetime as _dt
        published = rec.get('date') or ''
        # normalize iso
        try:
            published_iso = _dt.fromisoformat(published).strftime('%Y-%m-%dT%H:%M:%SZ')
        except Exception:
            published_iso = published
        img = hero
        if img.startswith('../'):
            img = img[3:]
        data = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "datePublished": published_iso,
            "image": img,
            "url": f"/bultenler/{slug}.html",
            "publisher": {
                "@type": "Organization",
                "name": "Verinin Mutfağı"
            }
        }
        import json as _json
        j = _json.dumps(data, ensure_ascii=False)
        page_path = out
        s = page_path.read_text(encoding='utf-8', errors='ignore')
        if '</head>' in s:
            s = s.replace('</head>', f'<script type="application/ld+json">{j}</script>\n</head>')
            page_path.write_text(s, encoding='utf-8')
    except Exception:
        pass
    return {
        'slug': slug,
        'title': title,
        'date': date,
        'hero': hero,
    }


def build_index(items):
    cards = []
    for it in items:
        cards.append(
            '\n'.join([
                '<article class="vm-card">',
                f'  <a href="{escape(it["slug"])}.html"><img class="vm-card-cover" loading="lazy" src="{escape(it["hero"]) }" alt="{escape(it["title"]) }"></a>',
                '  <div class="vm-card-body">',
                f'    <div class="vm-card-meta">{escape(it["date"])}</div>',
                f'    <h3><a href="{escape(it["slug"]) }.html">{escape(it["title"]) }</a></h3>',
                '  </div>',
                '</article>'
            ])
        )
    # Build simple search index (inline JSON)
    def strip_html(raw: str) -> str:
        raw = re.sub(r"<script[\s\S]*?</script>", " ", raw, flags=re.IGNORECASE)
        raw = re.sub(r"<style[\s\S]*?</style>", " ", raw, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", raw)
        text = re.sub(r"\s+", " ", text)
        return text.strip()
    search_items = []
    for it in items:
        # Normalize cover to site root path for search.js logic
        hero = it['hero']
        hero_norm = hero
        if hero_norm.startswith('../assets/'):
            hero_norm = hero_norm[3:]
        # Load page content to provide searchable text (doc_html already injected separately)
        page_path = BULTEN_DIR / f"{it['slug']}.html"
        try:
            raw = page_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            raw = ''
        # strip only main article if present
        content = strip_html(raw)[:60000]
        # approximate timestamp from date
        try:
            ts = int(datetime.strptime(it['date'], '%d %b %Y').timestamp())
        except Exception:
            ts = int(datetime.now().timestamp())
        search_items.append({
            'title': it['title'],
            'slug': it['slug'],
            'date': it['date'],
            'cover': hero_norm,
            'ts': ts,
            'content': content,
        })
    html = TPL_INDEX.replace('{{BULTEN_CARDS}}', '\n'.join(cards))
    html = html.replace('{{SEARCH_JSON}}', json.dumps(search_items, ensure_ascii=False))
    # JSON-LD Breadcrumb
    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Ana Sayfa", "item": SITE_BASE_URL+"/" if SITE_BASE_URL else "../index.html"},
            {"@type": "ListItem", "position": 2, "name": "Haftalık Bültenler", "item": SITE_BASE_URL+"/bultenler/" if SITE_BASE_URL else "index.html"}
        ]
    }
    items_ld = []
    for i, it in enumerate(items, start=1):
        url_path = f"/bultenler/{it['slug']}.html"
        url = SITE_BASE_URL + url_path if SITE_BASE_URL else url_path
        img = it['hero']
        if img.startswith('../'):
            img = img[3:]
        if SITE_BASE_URL and img.startswith('assets/'):
            img = SITE_BASE_URL + "/" + img
        items_ld.append({
            "@type": "ListItem",
            "position": i,
            "item": {"@id": url, "name": it['title'], "image": img}
        })
    itemlist = {"@context": "https://schema.org", "@type": "ItemList", "itemListElement": items_ld}
    html = html.replace('{{JSONLD_BREADCRUMB}}', json.dumps(breadcrumb, ensure_ascii=False))
    html = html.replace('{{JSONLD_INDEX}}', json.dumps(itemlist, ensure_ascii=False))
    (BULTEN_DIR / 'index.html').write_text(html, encoding='utf-8')

def build_rss(items):
    base = SITE_BASE_URL or ''
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0">',
        '<channel>',
        '<title>Verinin Mutfağı — Haftalık Bültenler</title>',
        f'<link>{base}/bultenler/</link>',
        '<description>Verinin Dünyası haftalık bültenleri</description>'
    ]
    for it in items:
        link = (base + f"/bultenler/{it['slug']}.html") if base else f"/bultenler/{it['slug']}.html"
        desc = it['title']
        pub = it.get('date') or ''
        try:
            dt = datetime.strptime(pub, '%d %b %Y')
            pub_rss = dt.strftime('%a, %d %b %Y 00:00:00 GMT')
        except Exception:
            pub_rss = pub
        lines += [
            '<item>',
            f'<title>{it["title"]}</title>',
            f'<link>{link}</link>',
            f'<description>{desc}</description>',
            f'<pubDate>{pub_rss}</pubDate>',
            '</item>'
        ]
    lines += ['</channel>', '</rss>']
    (BULTEN_DIR / 'feed.xml').write_text('\n'.join(lines), encoding='utf-8')


def main():
    items = []
    if DATA_DIR.exists():
        for p in sorted(DATA_DIR.glob('*.json')):
            try:
                rec = json.loads(p.read_text(encoding='utf-8'))
            except Exception:
                continue
            info = build_one(rec)
            items.append(info)
    # son kayıt üstte olacak şekilde ters sırala (tarihe göre yapmadık; basitçe eklenme sırası)
    items = list(reversed(items))
    build_index(items)
    build_rss(items)
    print(f'Generated {len(items)} bulletins into {BULTEN_DIR}')


if __name__ == '__main__':
    main()
