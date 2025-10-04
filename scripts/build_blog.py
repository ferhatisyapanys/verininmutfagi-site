#!/usr/bin/env python3
import os
import re
import pathlib
from html import unescape
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Yeni temiz site yapısı
SITE_DIR = ROOT / "site"
TEMPLATE_DIR = SITE_DIR / "templates"
INDEX_TEMPLATE = (TEMPLATE_DIR / "blog_index.html").read_text(encoding="utf-8")
HOME_TEMPLATE = (TEMPLATE_DIR / "home.html").read_text(encoding="utf-8")
BLOG_DIR = SITE_DIR / "blog"
SITE_BASE_URL = os.environ.get("SITE_BASE_URL", "").strip().rstrip('/')

def turkish_to_ascii(s: str) -> str:
    table = str.maketrans({
        "ç":"c","Ç":"c","ğ":"g","Ğ":"g","ı":"i","İ":"i","ö":"o","Ö":"o","ş":"s","Ş":"s","ü":"u","Ü":"u",
        "’":"'","“":"\"","”":"\""
    })
    return s.translate(table)

def slugify_from_title(title: str, fallback: str) -> str:
    base = turkish_to_ascii(title or "").lower().strip()
    if not base:
        base = os.path.splitext(fallback)[0]
    base = re.sub(r"[^a-z0-9\-\s]", "", base)
    base = re.sub(r"\s+", "-", base)
    base = re.sub(r"-+", "-", base).strip("-")
    return base or "post"

def extract_title(html: str) -> str:
    m = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    return unescape(m.group(1).strip()) if m else "Blog Yazısı"

def extract_styles(html: str) -> str:
    # Eski: stil çekme (artık blog sayfalarını olduğu gibi yayınlıyoruz)
    return ""

def extract_body(html: str) -> str:
    # Eski: gövde çıkarımı. Artık gerek yok, postları aynen kopyalayacağız.
    return html

def extract_cover(html: str, base_dir: pathlib.Path, slug: str) -> str:
    # Helper: save data URI to file if too large
    def save_data_uri(data_uri: str) -> str:
        try:
            import base64, re
            m = re.match(r"data:image/(png|jpeg|jpg|webp);base64,(.*)", data_uri, re.IGNORECASE)
            if not m:
                return data_uri
            ext = m.group(1).lower()
            b64 = m.group(2)
            raw = base64.b64decode(b64 + '===')
            # if large, write to file; else keep inline
            if len(raw) < 50_000:
                return data_uri
            covers_dir = SITE_DIR / "assets" / "img" / "covers"
            covers_dir.mkdir(parents=True, exist_ok=True)
            target = covers_dir / f"{slug}.{ 'jpg' if ext=='jpeg' else ext }"
            target.write_bytes(raw)
            return f"assets/img/covers/{target.name}"
        except Exception:
            return data_uri
    # Öncelik: .hero-image CSS kuralı
    m = re.search(r"\.hero-image\s*\{[^}]*background-image\s*:\s*url\(['\"]?([^'\"\)]+)", html, re.IGNORECASE)
    def optimize_copy(src_path: pathlib.Path, target_path: pathlib.Path) -> bool:
        try:
            from PIL import Image
            im = Image.open(src_path)
            w, h = im.size
            maxw = 1280
            if w > maxw:
                nh = int(h * (maxw / float(w)))
                im = im.resize((maxw, nh), Image.LANCZOS)
            im.save(target_path)
            return True
        except Exception:
            try:
                target_path.write_bytes(src_path.read_bytes())
                return True
            except Exception:
                return False

    if m:
        src = m.group(1)
        if src.startswith("data:"):
            return save_data_uri(src)
        img_path = (base_dir / src).resolve() if not os.path.isabs(src) else pathlib.Path(src)
        if img_path.exists():
            ext = img_path.suffix.lower() or ".jpg"
            covers_dir = SITE_DIR / "assets" / "img" / "covers"
            covers_dir.mkdir(parents=True, exist_ok=True)
            target = covers_dir / f"{slug}{ext}"
            if optimize_copy(img_path, target):
                return f"assets/img/covers/{slug}{ext}"

    # İkinci: hero-image sınıfına sahip inline style
    m_inline = re.search(r"class=\"[^\"]*hero-image[^\"]*\"[^>]*style=\"[^\"]*background-image\s*:\s*url\(['\"]?([^'\"\)]+)", html, re.IGNORECASE)
    if m_inline:
        src = m_inline.group(1)
        if src.startswith("data:"):
            return save_data_uri(src)
        img_path = (base_dir / src).resolve() if not os.path.isabs(src) else pathlib.Path(src)
        if img_path.exists():
            ext = img_path.suffix.lower() or ".jpg"
            covers_dir = SITE_DIR / "assets" / "img" / "covers"
            covers_dir.mkdir(parents=True, exist_ok=True)
            target = covers_dir / f"{slug}{ext}"
            if optimize_copy(img_path, target):
                return f"assets/img/covers/{slug}{ext}"

    # Üçüncü: İlk <img>
    m_img = re.search(r"<img[^>]+src=\"([^\"]+)\"", html, re.IGNORECASE)
    if m_img:
        src = m_img.group(1)
        if src.startswith("data:"):
            return save_data_uri(src)
        img_path = (base_dir / src).resolve() if not os.path.isabs(src) else pathlib.Path(src)
        if img_path.exists():
            ext = img_path.suffix.lower() or ".jpg"
            covers_dir = SITE_DIR / "assets" / "img" / "covers"
            covers_dir.mkdir(parents=True, exist_ok=True)
            target = covers_dir / f"{slug}{ext}"
            if optimize_copy(img_path, target):
                return f"assets/img/covers/{slug}{ext}"

    # Dördüncü: Genel background-image
    m_bg = re.search(r"background-image\s*:\s*url\(['\"]?([^'\"\)]+)", html, re.IGNORECASE)
    if m_bg:
        src = m_bg.group(1)
        if src.startswith("data:"):
            return save_data_uri(src)
        img_path = (base_dir / src).resolve() if not os.path.isabs(src) else pathlib.Path(src)
        if img_path.exists():
            ext = img_path.suffix.lower() or ".jpg"
            covers_dir = SITE_DIR / "assets" / "img" / "covers"
            covers_dir.mkdir(parents=True, exist_ok=True)
            target = covers_dir / f"{slug}{ext}"
            if optimize_copy(img_path, target):
                return f"assets/img/covers/{slug}{ext}"

    return "assets/img/covers/default.jpg"

def build_post(input_path: pathlib.Path, out_path: pathlib.Path):
    # Blog yazılarını orijinal formatıyla aynen yayınla
    html = input_path.read_text(encoding="utf-8", errors="ignore")

    # Ortak head assetleri ve preloader kapatma
    def ensure_head_assets(doc: str) -> str:
        # add vendor + site css if missing for consistent header
        head_links = [
            ('favicon-ico', '<link rel="icon" type="image/x-icon" href="../favicon.ico">'),
            ('favicon-32', '<link rel="icon" type="image/png" sizes="32x32" href="../favicon-32x32.png">'),
            ('favicon-16', '<link rel="icon" type="image/png" sizes="16x16" href="../favicon-16x16.png">'),
            ('apple-touch', '<link rel="apple-touch-icon" sizes="180x180" href="../apple-touch-icon.png">'),
            ('font-awesome', '<link rel="stylesheet" href="../vendor/starbelly/css/plugins/font-awesome.min.css">'),
            ('bootstrap', '<link rel="stylesheet" href="../vendor/starbelly/css/plugins/bootstrap.min.css">'),
            ('starbelly-style', '<link rel="stylesheet" href="../vendor/starbelly/css/style.css">'),
            ('site-css', '<link rel="stylesheet" href="../assets/css/site.css?v=4">'),
        ]
        # insert before </head>
        ins = []
        for key, tag in head_links:
            if key == 'site-css':
                # match by href contains assets/css/site.css
                if re.search(r"assets/\s*css/\s*site\.css", doc, flags=re.IGNORECASE):
                    continue
            if 'vendor/starbelly' in tag:
                href = re.search(r'href="([^"]+)"', tag).group(1)
                if href and href in doc:
                    continue
            ins.append(tag)
        # preloader/transition disable
        ins.append('<style>.sb-preloader,.sb-click-effect,.sb-load{display:none!important}</style>')
        if '</head>' in doc:
            return doc.replace('</head>', '\n  ' + '\n  '.join(ins) + '\n</head>')
        return doc

    def extract_plain_text(doc: str, limit: int = 220) -> str:
        # remove scripts/styles and tags to build a short description
        s = re.sub(r"<script[\s\S]*?</script>", " ", doc, flags=re.IGNORECASE)
        s = re.sub(r"<style[\s\S]*?</style>", " ", s, flags=re.IGNORECASE)
        s = re.sub(r"<[^>]+>", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s[:limit]

    def inject_meta(doc: str, title: str, cover_url: str) -> str:
        # remove existing og meta to avoid duplicates
        doc = re.sub(r"<meta[^>]+property=\"og:[^\"]+\"[^>]*>\s*", "", doc, flags=re.IGNORECASE)
        desc = extract_plain_text(doc, 200) or f"{title} - Verinin Mutfağı"
        tags = [
            f'<meta name="description" content="{desc}">',
            f'<meta property="og:title" content="{title} - Verinin Mutfağı">',
            f'<meta property="og:description" content="{desc}">',
            '<meta property="og:type" content="article">',
            f'<meta property="og:image" content="{cover_url}">',
            '<meta name="twitter:card" content="summary_large_image">',
            f'<meta name="twitter:title" content="{title} - Verinin Mutfağı">',
            f'<meta name="twitter:description" content="{desc}">',
            f'<meta name="twitter:image" content="{cover_url}">',
        ]
        if '</head>' in doc:
            return doc.replace('</head>', '\n  ' + '\n  '.join(tags) + '\n</head>')
        return '\n'.join(tags) + doc

    def ensure_body_class(doc: str) -> str:
        # ensure body has blog-page class
        m = re.search(r"<body(.*?)>", doc, flags=re.IGNORECASE|re.DOTALL)
        if not m:
            return doc
        full = m.group(0)
        attrs = m.group(1)
        if re.search(r'class=\"[^\"]*\bblog-page\b', full, flags=re.IGNORECASE):
            return doc
        if 'class=' in attrs:
            new = re.sub(r'class=\"', 'class="blog-page ', full, flags=re.IGNORECASE)
        else:
            new = '<body class="blog-page"' + attrs + '>'
        start, end = m.span(0)
        return doc[:start] + new + doc[end:]

    def inject_top_bar(doc: str) -> str:
        # If no starbelly top bar exists, inject a consistent header at start of body
        if 'sb-top-bar-frame' in doc:
            return doc
        header = (
            '\n  <div class="sb-top-bar-frame">\n'
            '    <div class="sb-top-bar-bg"></div>\n'
            '    <div class="container">\n'
            '      <div class="sb-top-bar">\n'
            '        <a href="../index.html" class="sb-logo-frame">\n'
            '          <img src="../assets/img/logo.png" alt="Verinin Mutfağı">\n'
            '        </a>\n'
            '        <div class="sb-right-side">\n'
            '          <nav class="sb-menu-transition">\n'
            '            <ul class="sb-navigation">\n'
            '              <li><a href="../index.html">Ana Sayfa</a></li>\n'
            '              <li class="sb-active"><a href="index.html">Blog</a></li>\n'
            '              <li><a href="../bultenler/index.html">Haftalık Bültenler</a></li>\n'
            '              <li><a href="../youtube/index.html">YouTube</a></li>\n'
            '              <li><a href="../contact/index.html">İletişim</a></li>\n'
            '            </ul>\n'
            '          </nav>\n'
            '          <div class="sb-buttons-frame">\n'
            '            <div class="sb-menu-btn"><span></span></div>\n'
            '            <div class="sb-info-btn"><span></span></div>\n'
            '          </div>\n'
            '        </div>\n'
            '      </div>\n'
            '    </div>\n'
            '  </div>\n'
        )
        m = re.search(r"<body[^>]*>", doc, flags=re.IGNORECASE)
        if m:
            end = m.end()
            return doc[:end] + header + doc[end:]
        return header + doc

    def inject_footer(doc: str) -> str:
        # If a footer using sb-footer-frame already exists, keep it.
        if 'sb-footer-frame' in doc:
            return doc
        footer = (
            '\n  <footer>\n'
            '    <div class="container">\n'
            '      <div class="sb-footer-frame">\n'
            '        <a href="../index.html" class="sb-logo-frame">\n'
            '          <img src="../assets/img/logo.png" alt="Verinin Mutfağı">\n'
            '        </a>\n'
            '        <div class="sb-copy">&copy; <a href="../index.html">Verinin Mutfağı</a></div>\n'
            '        <nav class="vm-social">\n'
            '          <a href="https://www.linkedin.com/in/ferhatisyapan/" target="_blank" rel="noopener">LinkedIn</a>\n'
            '          <a href="https://github.com/ferhatisyapanys/VerininMutfagi" target="_blank" rel="noopener">GitHub</a>\n'
            '          <a href="https://instagram.com/verininmutfagi" target="_blank" rel="noopener">Instagram</a>\n'
            '        </nav>\n'
            '      </div>\n'
            '    </div>\n'
            '  </footer>\n'
        )
        # insert before </body>
        return doc.replace('</body>', footer + '\n</body>') if '</body>' in doc else (doc + footer)

    # Breadcrumb kaldırma: "Ana Sayfa" ve "Blog" butonlarını/izlerini temizle
    def remove_breadcrumbs(doc: str) -> str:
        # vm-breadcrumbs kapsayıcısını kaldır
        doc = re.sub(r"<div[^>]*class=\"[^\"]*vm-breadcrumbs[^\"]*\"[^>]*>[\s\S]*?</div>", "", doc, flags=re.IGNORECASE)
        # class=breadcrumb olan bağlantıları kaldır (tek tek)
        doc = re.sub(r"<a[^>]*class=\"[^\"]*\bbreadcrumb\b[^\"]*\"[^>]*>[\s\S]*?</a>", "", doc, flags=re.IGNORECASE)
        # Eski tek parça link varsa onu da kaldır
        doc = re.sub(r"<a[^>]*>\s*Ana Sayfa\s*/\s*Blog\s*</a>", "", doc, flags=re.IGNORECASE)
        return doc

    # Navbar'ı tüm blog yazılarında sabitle: Ana Sayfa, Blog, Haftalık Bültenler, YouTube, İletişim
    def inject_fixed_nav(doc: str) -> str:
        nav_fixed = (
            '\n<ul class="sb-navigation">\n'
            '  <li><a href="../index.html">Ana Sayfa</a></li>\n'
            '  <li class="sb-active"><a href="index.html">Blog</a></li>\n'
            '  <li><a href="../bultenler/index.html">Haftalık Bültenler</a></li>\n'
            '  <li><a href="../youtube/index.html">YouTube</a></li>\n'
            '  <li><a href="../contact/index.html">İletişim</a></li>\n'
            '</ul>'
        )
        # Mevcut nav <ul class="sb-navigation"> ... </ul> bloğunu yakalayıp değiştir
        doc2 = re.sub(r"<ul\\s+class=\\\"sb-navigation\\\">[\\s\\S]*?</ul>", nav_fixed, doc, flags=re.IGNORECASE)
        return doc2

    # Optimize inline <img> tags: copy local/data images into assets/img/posts/<slug>/, add lazy/decoding attrs
    def optimize_inline_images(doc: str, slug: str, base_dir: pathlib.Path) -> str:
        posts_dir = SITE_DIR / 'assets' / 'img' / 'posts' / slug
        posts_dir.mkdir(parents=True, exist_ok=True)

        def process_tag(tag: str) -> str:
            try:
                m = re.search(r'src=\"([^\"]+)\"', tag, flags=re.IGNORECASE)
                if not m:
                    return tag
                src = m.group(1)
                src_l = src.lower()
                # Skip site UI assets (logo, favicons, vendor)
                if (
                    'vendor/' in src_l or
                    '/assets/img/logo' in src_l or
                    '/assets/img/logos/' in src_l or
                    'favicon' in src_l or
                    'apple-touch-icon' in src_l or
                    'android-chrome' in src_l
                ):
                    # Ensure lazy for content only; do not touch UI images
                    return tag
                # external image: just ensure lazy attrs
                if src.startswith('http://') or src.startswith('https://'):
                    new = tag
                    if 'loading=' not in new.lower():
                        new = new.replace('<img', '<img loading="lazy"', 1)
                    if 'decoding=' not in new.lower():
                        new = new.replace('<img', '<img decoding="async"', 1)
                    return new
                # data URI or local path
                target_path = None
                if src.startswith('data:image/'):
                    import base64
                    m2 = re.match(r'data:image/(png|jpeg|jpg|webp);base64,(.*)', src, flags=re.IGNORECASE)
                    ext = 'png'
                    raw = None
                    if m2:
                        ext = 'jpg' if m2.group(1).lower() == 'jpeg' else m2.group(1).lower()
                        raw = base64.b64decode(m2.group(2) + '===')
                    else:
                        raw = base64.b64decode(src.split(',', 1)[1])
                    target_path = posts_dir / f"img_{abs(hash(src))}.{ext}"
                    target_path.write_bytes(raw)
                else:
                    ip = (base_dir / src).resolve() if not os.path.isabs(src) else pathlib.Path(src)
                    if ip.exists():
                        target_path = posts_dir / os.path.basename(src)
                        try:
                            from PIL import Image
                            im = Image.open(ip)
                            w, h = im.size
                            maxw = 1280
                            if w > maxw:
                                nh = int(h * (maxw / float(w)))
                                im = im.resize((maxw, nh), Image.LANCZOS)
                            im.save(target_path)
                        except Exception:
                            target_path.write_bytes(ip.read_bytes())
                if target_path and target_path.exists():
                    rel = f"../assets/img/posts/{slug}/{target_path.name}"
                    new = re.sub(r'src=\"[^\"]+\"', f'src="{rel}"', tag, flags=re.IGNORECASE)
                    if 'loading=' not in new.lower():
                        new = new.replace('<img', '<img loading="lazy"', 1)
                    if 'decoding=' not in new.lower():
                        new = new.replace('<img', '<img decoding="async"', 1)
                    # add width/height if absent
                    if ('width=' not in new.lower()) or ('height=' not in new.lower()):
                        try:
                            from PIL import Image
                            im2 = Image.open(target_path)
                            wh = f' width="{im2.width}" height="{im2.height}"'
                            new = new.replace('<img', f'<img{wh}', 1)
                        except Exception:
                            pass
                    return new
                return tag
            except Exception:
                return tag

        return re.sub(r'<img[^>]*?>', lambda m: process_tag(m.group(0)), doc, flags=re.IGNORECASE)

    # Extract title early for meta
    page_title = extract_title(html)
    # Compute a cover candidate from content
    cover_for_meta = extract_cover(html, input_path.parent, input_path.stem)

    html = ensure_head_assets(html)
    html = ensure_body_class(html)
    html = inject_top_bar(html)
    html = remove_breadcrumbs(html)
    html = inject_fixed_nav(html)
    # Optimize images inside content
    try:
        html = optimize_inline_images(html, out_path.stem, input_path.parent)
    except Exception:
        pass
    # Inject meta tags (og + description) using computed cover and canonical if available
    html = inject_meta(html, page_title, cover_for_meta if cover_for_meta.startswith('http') or cover_for_meta.startswith('assets/') else cover_for_meta)
    if SITE_BASE_URL:
        canonical = f"{SITE_BASE_URL}/blog/{out_path.name}"
        if '</head>' in html and 'rel="canonical"' not in html:
            html = html.replace('</head>', f'\n  <link rel="canonical" href="{canonical}">\n</head>')
        # JSON-LD per post: BlogPosting + BreadcrumbList
        from datetime import datetime as _dt
        try:
            ts = int(input_path.stat().st_mtime)
        except Exception:
            ts = int(_dt.utcnow().timestamp())
        published = _dt.utcfromtimestamp(ts).strftime('%Y-%m-%dT%H:%M:%SZ')
        image_abs = cover_for_meta
        if image_abs.startswith('../'):
            image_abs = image_abs[3:]
        if image_abs.startswith('assets/'):
            image_abs = f"{SITE_BASE_URL}/{image_abs}"
        import json as _json
        post_ld = {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": page_title,
            "datePublished": published,
            "image": image_abs,
            "url": canonical,
            "publisher": {"@type": "Organization", "name": "Verinin Mutfağı"}
        }
        bc_ld = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Ana Sayfa", "item": f"{SITE_BASE_URL}/"},
                {"@type": "ListItem", "position": 2, "name": "Blog", "item": f"{SITE_BASE_URL}/blog/"},
                {"@type": "ListItem", "position": 3, "name": page_title, "item": canonical}
            ]
        }
        scripts = (
            "<script type=\\\"application/ld+json\\\">" + _json.dumps(post_ld, ensure_ascii=False) + "</script>\n"
            "<script type=\\\"application/ld+json\\\">" + _json.dumps(bc_ld, ensure_ascii=False) + "</script>"
        )
        if '</head>' in html:
            html = html.replace('</head>', scripts + '\n</head>')
    html = inject_footer(html)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return extract_title(html)

def main():
    posts = []
    BLOG_DIR.mkdir(parents=True, exist_ok=True)
    # Öncelik: site/blog içindeki mevcut .html yazılar (index.html hariç)
    blog_srcs = [p for p in BLOG_DIR.glob("*.html") if p.name.lower() != "index.html"]
    if blog_srcs:
        for src in blog_srcs:
            try:
                # Rebuild in-place to inject consistent header/navigation
                build_post(src, src)
                raw_html = src.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                try:
                    raw_html = src.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
            title = extract_title(raw_html)
            slug = src.stem
            ts = datetime.fromtimestamp(src.stat().st_mtime)
            date_str = ts.strftime("%d %b %Y")
            cover_rel = extract_cover(raw_html, BLOG_DIR, slug)
            posts.append({
                "title": title,
                "slug": slug,
                "date": date_str,
                "cover": cover_rel,
                "ts": int(ts.timestamp()),
            })
    else:
        # Kaynak yazıları: content/*.html (opsiyonel kaynak klasörü)
        content_dir = ROOT / 'content'
        source_files = [p for p in content_dir.glob('*.html')] if content_dir.exists() else []
        for src in source_files:
            # Slug'ı başlıktan üret
            temp_html = src.read_text(encoding="utf-8", errors="ignore")
            title_tmp = extract_title(temp_html)
            slug = slugify_from_title(title_tmp, src.name)
            dst = BLOG_DIR / f"{slug}.html"
            raw_html = src.read_text(encoding="utf-8", errors="ignore")
            title = extract_title(raw_html)
            # Yayınla (aynı format)
            build_post(src, dst)
            ts = datetime.fromtimestamp(src.stat().st_mtime)
            date_str = ts.strftime("%d %b %Y")
            # Kapak görseli: içerikten (img/src veya background-image) çıkar
            cover_rel = extract_cover(raw_html, ROOT, slug)
            posts.append({
                "title": title,
                "slug": slug,
                "date": date_str,
                "cover": cover_rel,
                "ts": int(ts.timestamp()),
            })

    # Yeni: dosya tarihine göre (mtime) azalan sıralama
    try:
        posts.sort(key=lambda p: p.get("ts", 0), reverse=True)
    except Exception:
        pass

    # Build index
    cards = []
    for p in posts:
        cover_url = p['cover']
        cover_attr = cover_url if cover_url.startswith('data:') else f"../{cover_url}"
        cards.append(
            (
                "<article class=\"vm-card\">\n"
                f"  <a href=\"{p['slug']}.html\"><img class=\"vm-card-cover\" loading=\"lazy\" src=\"{cover_attr}\" alt=\"{p['title']}\"></a>\n"
                "  <div class=\"vm-card-body\">\n"
                f"    <div class=\"vm-card-meta\">{p['date']}</div>\n"
                f"    <h3><a href=\"{p['slug']}.html\">{p['title']}</a></h3>\n"
                f"    <p><a href=\"{p['slug']}.html\">Yazıyı oku →</a></p>\n"
                "  </div>\n"
                "</article>\n"
            )
        )
    index_html = INDEX_TEMPLATE.replace("{{POST_CARDS}}", "\n".join(cards))
    (BLOG_DIR / "index.html").write_text(index_html, encoding="utf-8")

    # Build home with latest posts (first 6)
    home_cards = []
    for p in posts[:6]:
        cover_url = p['cover']
        home_cover_attr = cover_url  # home'dan kök göreli
        home_cards.append(
            (
                "<article class=\"vm-card\">\n"
                f"  <a href=\"blog/{p['slug']}.html\"><img class=\"vm-card-cover\" loading=\"lazy\" src=\"{home_cover_attr}\" alt=\"{p['title']}\"></a>\n"
                "  <div class=\"vm-card-body\">\n"
                f"    <div class=\"vm-card-meta\">{p['date']}</div>\n"
                f"    <h3><a href=\"blog/{p['slug']}.html\">{p['title']}</a></h3>\n"
                f"    <p><a href=\"blog/{p['slug']}.html\">Yazıyı oku →</a></p>\n"
                "  </div>\n"
                "</article>\n"
            )
        )
    home_html = HOME_TEMPLATE.replace("{{POST_CARDS}}", "\n".join(home_cards))
    (SITE_DIR / "index.html").write_text(home_html, encoding="utf-8")

    # Build search index
    def strip_html(raw: str) -> str:
        # remove scripts and styles
        raw = re.sub(r"<script[\s\S]*?</script>", " ", raw, flags=re.IGNORECASE)
        raw = re.sub(r"<style[\s\S]*?</style>", " ", raw, flags=re.IGNORECASE)
        # remove tags
        text = re.sub(r"<[^>]+>", " ", raw)
        text = re.sub(r"\s+", " ", text)
        return unescape(text).strip()

    search_items = []
    for p in posts:
        html_path = BLOG_DIR / f"{p['slug']}.html"
        if not html_path.exists():
            continue
        raw = html_path.read_text(encoding="utf-8", errors="ignore")
        # parse mtime to epoch seconds for recency scoring on client
        try:
            ts_epoch = int((html_path).stat().st_mtime)
        except Exception:
            ts_epoch = int(datetime.strptime(p["date"], "%d %b %Y").timestamp())
        search_items.append({
            "title": p["title"],
            "slug": p["slug"],
            "date": p["date"],
            "cover": p["cover"],
            "ts": ts_epoch,
            "content": strip_html(raw)[:60000],
        })

    search_dir = SITE_DIR / "search"
    search_dir.mkdir(parents=True, exist_ok=True)
    import json
    import json
    (search_dir / "index.json").write_text(json.dumps(search_items, ensure_ascii=False), encoding="utf-8")

    # Embed search JSON into blog index to support file:// usage
    search_json_inline = json.dumps(search_items, ensure_ascii=False)
    index_html = index_html.replace("{{SEARCH_JSON}}", search_json_inline)
    # JSON-LD: BreadcrumbList
    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Ana Sayfa", "item": SITE_BASE_URL+"/" if SITE_BASE_URL else "../index.html"},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": SITE_BASE_URL+"/blog/" if SITE_BASE_URL else "index.html"}
        ]
    }
    # JSON-LD: ItemList of posts
    items_ld = []
    for i, p in enumerate(posts, start=1):
        url_path = f"/blog/{p['slug']}.html"
        url = (SITE_BASE_URL + url_path) if SITE_BASE_URL else url_path
        img = p['cover']
        if img.startswith('../'):
            img = img[3:]
        if SITE_BASE_URL and (img.startswith('assets/') or img.startswith('site/assets/')):
            img = SITE_BASE_URL + "/" + img.lstrip('/')
        items_ld.append({
            "@type": "ListItem",
            "position": i,
            "item": {"@id": url, "name": p['title'], "image": img}
        })
    itemlist = {"@context": "https://schema.org", "@type": "ItemList", "itemListElement": items_ld}
    index_html = index_html.replace("{{JSONLD_BREADCRUMB}}", json.dumps(breadcrumb, ensure_ascii=False))
    index_html = index_html.replace("{{JSONLD_INDEX}}", json.dumps(itemlist, ensure_ascii=False))
    (BLOG_DIR / "index.html").write_text(index_html, encoding="utf-8")

    print(f"Generated {len(posts)} posts into {BLOG_DIR}")

if __name__ == "__main__":
    main()
