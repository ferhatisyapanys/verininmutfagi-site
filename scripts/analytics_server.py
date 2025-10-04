#!/usr/bin/env python3
"""
Lightweight open-source analytics + events collector using only Python stdlib + SQLite.

Endpoints:
  POST /api/collect         -> JSON event body, writes to sqlite (events.db)
  GET  /api/stats/summary   -> basic counters (24h, 7d), top pages/searches
  GET  /admin               -> simple dashboard UI (static HTML)

Auth: optional shared token via header X-Analytics-Token (set ANALYTICS_TOKEN env).

Run:
  python3 scripts/analytics_server.py --host 127.0.0.1 --port 8787 --db analytics.db

This server is tiny and file-based; suitable for local and low-traffic usage.
"""
import json
import threading
import time as _time
import shutil
import os
import sqlite3
import time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Default DB under data/runtime to keep repo root clean
DB_PATH = os.environ.get("ANALYTICS_DB", os.path.join(ROOT, "data", "runtime", "analytics.db"))
TOKEN = os.environ.get("ANALYTICS_TOKEN", "")

ADMIN_HTML = """<!DOCTYPE html><html lang=tr><meta charset=utf-8><title>Analytics Dashboard</title>
<meta name=viewport content="width=device-width, initial-scale=1">
<style>
  body{font:14px/1.5 -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Arial,sans-serif;margin:0;background:#fafafa;color:#222}
  header{position:sticky;top:0;background:#fff;border-bottom:1px solid #eee;padding:10px 16px}
  main{max-width:1000px;margin:0 auto;padding:16px}
  .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin:12px 0}
  .card{background:#fff;border:1px solid #eee;border-radius:10px;padding:12px}
  h1{font-size:18px;margin:0}
  h2{font-size:16px;margin:8px 0}
  table{width:100%;border-collapse:collapse}
  th,td{padding:6px 8px;border-bottom:1px solid #f0f0f0;text-align:left}
  .muted{color:#777}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
  canvas{width:100%;height:220px;background:#fff;border:1px solid #eee;border-radius:10px}
  @media (max-width: 800px){ .grid2{grid-template-columns:1fr} }
</style>
<header><h1>Analytics Dashboard</h1></header>
<main>
  <div class=cards>
    <div class=card>
      <h2>Özet (24s)</h2>
      <div id=last24 class=muted>Yükleniyor…</div>
    </div>
    <div class=card>
      <h2>Özet (7g)</h2>
      <div id=last7 class=muted>Yükleniyor…</div>
    </div>
    <div class=card>
      <h2>Özet (30g)</h2>
      <div id=last30 class=muted>Yükleniyor…</div>
    </div>
  </div>
  <div class=grid2>
    <div>
      <h2>Randevular ve E‑postalar (14 gün)
        <a href="/api/export/timeseries?days=14" target="_blank" class="muted" style="font-size:12px; float:right">CSV indir</a>
      </h2>
      <canvas id=tsCanvas></canvas>
    </div>
    <div>
      <h2>Blog Aramaları (Top 10)
        <a href="/api/export/top_searches?days=7" target="_blank" class="muted" style="font-size:12px; float:right">CSV indir</a>
      </h2>
      <table id=topSearches><thead><tr><th>Sorgu</th><th>Adet</th></tr></thead><tbody></tbody></table>
    </div>
  </div>
  <div class=grid2 style="margin-top:12px">
    <div>
      <h2>En Çok Okunan Bloglar (7 gün)
        <a href="/api/export/top_blogs?days=7" target="_blank" class="muted" style="font-size:12px; float:right">CSV indir</a>
      </h2>
      <table id=topBlogs><thead><tr><th>Sayfa</th><th>Görüntüleme</th></tr></thead><tbody></tbody></table>
    </div>
    <div>
      <h2>Abonelik Tıklamaları
        <a href="/api/export/sub_clicks?days=7" target="_blank" class="muted" style="font-size:12px; float:right">CSV indir</a>
      </h2>
      <table id=subClicks><thead><tr><th>Kaynak</th><th>Adet</th></tr></thead><tbody></tbody></table>
    </div>
  </div>
  <div class=cards>
    <div class=card>
      <h2>Randevu Saat Dağılımı
        <a href="/api/export/appointment_hours?days=30" target="_blank" class="muted" style="font-size:12px; float:right">CSV indir</a>
      </h2>
      <canvas id=hourCanvas></canvas>
    </div>
    <div class=card>
      <h2>Tüm Olaylar
        <a href="/api/export/events?limit=10000" target="_blank" class="muted" style="font-size:12px; float:right">CSV indir</a>
      </h2>
      <div class=muted>Son olayları CSV olarak indirebilirsiniz (varsayılan 10.000 satır).</div>
    </div>
  </div>
</main>
<script>
const token = localStorage.getItem('AN_TOKEN')||'';
function q(id){return document.getElementById(id)}
function fillTable(el, rows){
  const tb = el.querySelector('tbody'); tb.innerHTML='';
  rows.forEach(r=>{ const tr=document.createElement('tr'); tr.innerHTML=`<td>${r.k||r.page||r.q||''}</td><td>${r.c}</td>`; tb.appendChild(tr); });
}
function drawLine(canvas, series){
  const ctx=canvas.getContext('2d'); const W=canvas.width=canvas.clientWidth, H=canvas.height=canvas.clientHeight;
  ctx.clearRect(0,0,W,H); ctx.strokeStyle='#eee'; for(let y=0;y<H;y+=H/4){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke();}
  const max = Math.max(1, ...series.map(s=>Math.max(...s.y)));
  const colors=['#0b5ed7','#999'];
  series.forEach((s,si)=>{ ctx.strokeStyle=colors[si%colors.length]; ctx.beginPath(); s.y.forEach((v,i)=>{ const x=i*(W/(s.y.length-1||1)); const y=H - (v/max)*H*0.9; i? ctx.lineTo(x,y): ctx.moveTo(x,y); }); ctx.stroke(); });
}
function drawBars(canvas, labels, values){
  const ctx=canvas.getContext('2d'); const W=canvas.width=canvas.clientWidth, H=canvas.height=canvas.clientHeight; ctx.clearRect(0,0,W,H);
  const max = Math.max(1, ...values); const bw = W/(values.length*1.4);
  values.forEach((v,i)=>{ const x = i*(W/values.length)+bw*0.2; const h=(v/max)*H*0.8; ctx.fillStyle='#0b5ed7'; ctx.fillRect(x, H-h, bw, h); });
}
fetch('/api/stats/dashboard', {headers: token? {'X-Analytics-Token':token} : {}})
 .then(r=>r.json()).then(d=>{
   q('last24').textContent = `Görüntüleme: ${d.last24.views} · Arama: ${d.last24.searches} · Tıklama: ${d.last24.clicks} · Randevu: ${d.last24.appointments} · E‑posta: ${d.last24.emails}`;
   q('last7').textContent = `Görüntüleme: ${d.last7.views} · Arama: ${d.last7.searches} · Tıklama: ${d.last7.clicks} · Randevu: ${d.last7.appointments} · E‑posta: ${d.last7.emails}`;
   q('last30').textContent = `Görüntüleme: ${d.last30.views} · Arama: ${d.last30.searches} · Tıklama: ${d.last30.clicks} · Randevu: ${d.last30.appointments} · E‑posta: ${d.last30.emails}`;
   fillTable(q('topBlogs'), d.tops.blogs);
   fillTable(q('topSearches'), d.tops.searches);
   fillTable(q('subClicks'), d.tops.subs);
   drawLine(q('tsCanvas'), [ {y:d.timeseries.appointments}, {y:d.timeseries.emails} ]);
   drawBars(q('hourCanvas'), d.appointmentHours.labels, d.appointmentHours.values);
 }).catch(()=>{ q('last24').textContent='Veri yok'; q('last7').textContent='Veri yok'; });
</script>
"""


def get_db():
    dbp = os.environ.get("ANALYTICS_DB", DB_PATH)
    os.makedirs(os.path.dirname(os.path.abspath(dbp)), exist_ok=True)
    conn = sqlite3.connect(dbp)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          ts INTEGER NOT NULL,
          client_id TEXT,
          session_id TEXT,
          ip TEXT,
          ua TEXT,
          ref TEXT,
          page TEXT,
          event TEXT,
          element TEXT,
          value TEXT,
          props TEXT
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_event ON events(event);")
    return conn


def ok_token(headers):
    if not TOKEN:
        return True
    return headers.get('X-Analytics-Token', '') == TOKEN


class Handler(BaseHTTPRequestHandler):
    server_version = "VMAnalytics/1.0"

    def _set_cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Analytics-Token')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')

    def do_OPTIONS(self):
        self.send_response(204)
        self._set_cors()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/admin':
            self.send_response(200)
            self._set_cors()
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(ADMIN_HTML.encode('utf-8'))
            return
        if parsed.path == '/api/stats/summary':
            if not ok_token(self.headers):
                self.send_response(401); self._set_cors(); self.end_headers(); return
            conn = get_db()
            now = int(time.time())
            def count(event_like, since):
                cur = conn.execute("SELECT count(*) FROM events WHERE ts>=? AND event LIKE ?", (since, event_like))
                return cur.fetchone()[0]
            last24 = now - 24*3600
            last7 = now - 7*24*3600
            data = {
                'last24': {
                    'views': count('view%', last24),
                    'searches': count('search%', last24),
                    'clicks': count('click%', last24),
                },
                'last7': {
                    'views': count('view%', last7),
                    'searches': count('search%', last7),
                    'clicks': count('click%', last7),
                },
            }
            # top pages & searches (7d)
            cur = conn.execute("SELECT page, COUNT(*) c FROM events WHERE ts>=? AND event LIKE 'view%' AND page IS NOT NULL GROUP BY page ORDER BY c DESC LIMIT 10", (last7,))
            pages = [{'page': r[0], 'c': r[1]} for r in cur.fetchall()]
            cur = conn.execute("SELECT value, COUNT(*) c FROM events WHERE ts>=? AND event='search' AND value IS NOT NULL GROUP BY value ORDER BY c DESC LIMIT 10", (last7,))
            searches = [{'k': r[0], 'c': r[1]} for r in cur.fetchall()]
            data['tops'] = {'pages': pages, 'searches': searches}
            self.send_response(200)
            self._set_cors()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode('utf-8'))
            return
        if parsed.path == '/api/stats/dashboard':
            if not ok_token(self.headers):
                self.send_response(401); self._set_cors(); self.end_headers(); return
            conn = get_db()
            now = int(time.time())
            span24 = now - 24*3600; span7 = now - 7*24*3600; span30 = now - 30*24*3600
            def cnt(since, like):
                return conn.execute("SELECT count(*) FROM events WHERE ts>=? AND event LIKE ?", (since, like)).fetchone()[0]
            def cnt_eq(since, eq):
                return conn.execute("SELECT count(*) FROM events WHERE ts>=? AND event=?", (since, eq)).fetchone()[0]
            out = {
              'last24': {'views':cnt(span24,'view%'),'searches':cnt(span24,'search%'),'clicks':cnt(span24,'click%'),'appointments':cnt_eq(span24,'appointment')+cnt_eq(span24,'appointment_gcal')+cnt_eq(span24,'appointment_api'),'emails':cnt_eq(span24,'email_send')},
              'last7':  {'views':cnt(span7,'view%'),'searches':cnt(span7,'search%'),'clicks':cnt(span7,'click%'),'appointments':cnt_eq(span7,'appointment')+cnt_eq(span7,'appointment_gcal')+cnt_eq(span7,'appointment_api'),'emails':cnt_eq(span7,'email_send')},
              'last30': {'views':cnt(span30,'view%'),'searches':cnt(span30,'search%'),'clicks':cnt(span30,'click%'),'appointments':cnt_eq(span30,'appointment')+cnt_eq(span30,'appointment_gcal')+cnt_eq(span30,'appointment_api'),'emails':cnt_eq(span30,'email_send')},
            }
            # top blogs (7d)
            cur = conn.execute("SELECT page, COUNT(*) c FROM events WHERE ts>=? AND event LIKE 'view%' AND page LIKE '%/blog/%' GROUP BY page ORDER BY c DESC LIMIT 10", (span7,))
            blogs = [{'page': r[0], 'c': r[1]} for r in cur.fetchall()]
            # top searches (7d)
            cur = conn.execute("SELECT value, COUNT(*) c FROM events WHERE ts>=? AND event='search' AND value IS NOT NULL GROUP BY value ORDER BY c DESC LIMIT 10", (span7,))
            searches = [{'q': r[0], 'c': r[1]} for r in cur.fetchall()]
            # subscribe clicks (7d)
            cur = conn.execute("SELECT COALESCE(page,'(yok)') k, COUNT(*) c FROM events WHERE ts>=? AND event='click' AND (element LIKE '%subscribe%' OR props LIKE '%youtube.com/%') GROUP BY page ORDER BY c DESC LIMIT 10", (span7,))
            subs = [{'k': r[0], 'c': r[1]} for r in cur.fetchall()]
            # timeseries (14d) appointments & emails
            days = 14
            from_dt = now - days*24*3600
            cur = conn.execute("SELECT (ts/86400) d, event, COUNT(*) c FROM events WHERE ts>=? AND event IN ('appointment','appointment_gcal','appointment_api','email_send') GROUP BY d, event", (from_dt,))
            agg = {}
            for drow in cur.fetchall():
                dkey = int(drow[0]); evt = drow[1]; c = drow[2]; agg.setdefault(dkey, {'apt':0,'mail':0});
                if evt.startswith('appointment'): agg[dkey]['apt'] += c
                if evt=='email_send': agg[dkey]['mail'] += c
            # collapse to arrays
            if agg:
                min_d = min(agg.keys()); max_d = max(agg.keys())
            else:
                min_d = int(from_dt/86400); max_d = int(now/86400)
            apt = []; mail = []
            for dkey in range(min_d, max_d+1):
                v = agg.get(dkey, {'apt':0,'mail':0}); apt.append(v['apt']); mail.append(v['mail'])
            # appointment hour histogram (from props.start)
            cur = conn.execute("SELECT props FROM events WHERE ts>=? AND event IN ('appointment','appointment_gcal','appointment_api')", (span30,))
            hours = [0]*24
            import json as _j
            for (pstr,) in cur.fetchall():
                try:
                    pobj = _j.loads(pstr or '{}');
                    s = pobj.get('start')
                    if s and len(s)>=13:
                        hh = int(s[11:13]); hours[hh] += 1
                except Exception:
                    pass
            out['tops'] = {'blogs': blogs, 'searches': searches, 'subs': subs}
            out['timeseries'] = {'appointments': apt, 'emails': mail}
            out['appointmentHours'] = {'labels': [f"{i:02d}" for i in range(24)], 'values': hours}
            self.send_response(200)
            self._set_cors()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(out).encode('utf-8'))
            return
        # CSV exports
        if parsed.path.startswith('/api/export/'):
            if not ok_token(self.headers):
                self.send_response(401); self._set_cors(); self.end_headers(); return
            conn = get_db();
            qs = parse_qs(urlparse(self.path).query)
            def get_int(name, default):
                try:
                    return int((qs.get(name) or [default])[0])
                except Exception:
                    return default
            days = get_int('days', 7)
            now = int(time.time()); since = now - days*24*3600
            import csv, io
            def write_csv(filename, header, rows):
                buf = io.StringIO(); w = csv.writer(buf)
                w.writerow(header)
                for r in rows: w.writerow(r)
                data = buf.getvalue().encode('utf-8')
                self.send_response(200)
                self._set_cors()
                self.send_header('Content-Type', 'text/csv; charset=utf-8')
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                self.end_headers(); self.wfile.write(data)
            # routes
            if parsed.path == '/api/export/top_blogs':
                cur = conn.execute("SELECT page, COUNT(*) c FROM events WHERE ts>=? AND event LIKE 'view%' AND page LIKE '%/blog/%' GROUP BY page ORDER BY c DESC LIMIT 100", (since,))
                rows = [(r[0], r[1]) for r in cur.fetchall()]
                write_csv('top_blogs.csv', ['page','views'], rows); return
            if parsed.path == '/api/export/top_searches':
                cur = conn.execute("SELECT value, COUNT(*) c FROM events WHERE ts>=? AND event='search' AND value IS NOT NULL GROUP BY value ORDER BY c DESC LIMIT 100", (since,))
                rows = [(r[0], r[1]) for r in cur.fetchall()]
                write_csv('top_searches.csv', ['query','count'], rows); return
            if parsed.path == '/api/export/sub_clicks':
                cur = conn.execute("SELECT COALESCE(page,'(yok)') p, COUNT(*) c FROM events WHERE ts>=? AND event='click' AND (element LIKE '%subscribe%' OR props LIKE '%youtube.com/%') GROUP BY page ORDER BY c DESC LIMIT 200", (since,))
                rows = [(r[0], r[1]) for r in cur.fetchall()]
                write_csv('subscribe_clicks.csv', ['page','clicks'], rows); return
            if parsed.path == '/api/export/timeseries':
                from_dt = since
                cur = conn.execute("SELECT (ts/86400) d, event, COUNT(*) c FROM events WHERE ts>=? AND event IN ('appointment','appointment_gcal','appointment_api','email_send') GROUP BY d, event", (from_dt,))
                agg = {}
                for drow in cur.fetchall():
                    dkey = int(drow[0]); evt = drow[1]; c = drow[2]; agg.setdefault(dkey, {'apt':0,'mail':0});
                    if evt.startswith('appointment'): agg[dkey]['apt'] += c
                    if evt=='email_send': agg[dkey]['mail'] += c
                rows=[]
                if agg:
                    min_d=min(agg.keys()); max_d=max(agg.keys())
                else:
                    min_d=int(from_dt/86400); max_d=int(now/86400)
                import datetime
                for dkey in range(min_d, max_d+1):
                    date = datetime.datetime.utcfromtimestamp(dkey*86400).strftime('%Y-%m-%d')
                    v = agg.get(dkey, {'apt':0,'mail':0}); rows.append((date, v['apt'], v['mail']))
                write_csv('timeseries.csv', ['date','appointments','emails'], rows); return
            if parsed.path == '/api/export/appointment_hours':
                cur = conn.execute("SELECT props FROM events WHERE ts>=? AND event IN ('appointment','appointment_gcal','appointment_api')", (since,))
                hours=[0]*24; import json as _j
                for (pstr,) in cur.fetchall():
                    try:
                        pobj=_j.loads(pstr or '{}'); s=pobj.get('start');
                        if s and len(s)>=13:
                            hh=int(s[11:13]); hours[hh]+=1
                    except Exception: pass
                rows=[(f"{i:02d}", hours[i]) for i in range(24)]
                write_csv('appointment_hours.csv', ['hour','count'], rows); return
            if parsed.path == '/api/export/events':
                limit = get_int('limit', 10000)
                cur = conn.execute("SELECT ts, client_id, session_id, ip, ua, ref, page, event, element, value, props FROM events ORDER BY ts DESC LIMIT ?", (limit,))
                rows = cur.fetchall()
                write_csv('events.csv', ['ts','client_id','session_id','ip','ua','ref','page','event','element','value','props'], rows); return
        self.send_response(404)
        self._set_cors()
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/collect':
            if not ok_token(self.headers):
                self.send_response(401); self._set_cors(); self.end_headers(); return
            length = int(self.headers.get('Content-Length', '0') or 0)
            raw = self.rfile.read(length) if length else b''
            try:
                ev = json.loads(raw.decode('utf-8')) if raw else {}
            except Exception:
                self.send_response(400); self._set_cors(); self.end_headers(); return
            # Insert (single or batch)
            now = int(time.time())
            conn = get_db()
            def insert_one(eo):
                try:
                    conn.execute(
                        "INSERT INTO events(ts, client_id, session_id, ip, ua, ref, page, event, element, value, props) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (
                            int(eo.get('ts') or now),
                            eo.get('cid'), eo.get('sid'),
                            self.client_address[0], self.headers.get('User-Agent',''),
                            eo.get('ref'), eo.get('page'),
                            eo.get('event'), eo.get('element'), eo.get('value'),
                            json.dumps(eo.get('props') or {}, ensure_ascii=False),
                        )
                    )
                except Exception:
                    pass
            if isinstance(ev, dict) and 'batch' in ev and isinstance(ev['batch'], list):
                for item in ev['batch']:
                    if isinstance(item, dict):
                        insert_one(item)
                try: conn.commit()
                except Exception: pass
            else:
                insert_one(ev)
                try: conn.commit()
                except Exception: pass
            self.send_response(204)
            self._set_cors()
            self.end_headers()
            return
        self.send_response(404)
        self._set_cors()
        self.end_headers()


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--host', default='127.0.0.1')
    p.add_argument('--port', type=int, default=8787)
    p.add_argument('--db', default=DB_PATH)
    args = p.parse_args()
    os.environ['ANALYTICS_DB'] = args.db
    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Analytics server running on http://{args.host}:{args.port}  db={args.db}")
    # Background watcher: convert site/bulten_doc/*.html to bulletins
    def bulten_watcher():
        docs_dir = os.path.join(ROOT, 'site', 'bulten_doc')
        data_dir = os.path.join(ROOT, 'data', 'bultenler')
        site_bulten_assets = os.path.join(ROOT, 'site', 'bultenler', 'assets')
        os.makedirs(docs_dir, exist_ok=True)
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(site_bulten_assets, exist_ok=True)
        snap = {}
        def monday_of(dt):
            from datetime import timedelta
            return dt - timedelta(days=dt.weekday())
        TR_MONTHS = {1:'Ocak',2:'Şubat',3:'Mart',4:'Nisan',5:'Mayıs',6:'Haziran',7:'Temmuz',8:'Ağustos',9:'Eylül',10:'Ekim',11:'Kasım',12:'Aralık'}
        def weekly_title_slug(dt):
            t = f"Verinin Dünyası {dt.day} {TR_MONTHS.get(dt.month, dt.strftime('%b'))}"
            slug = f"verinin-dunyasi-{dt.strftime('%Y-%m-%d')}"
            return t, slug, dt.strftime('%Y-%m-%d')
        def extract_title_body(html):
            import re
            m = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE|re.DOTALL)
            title = (m.group(1).strip() if m else 'Haftalık Bülten')
            m2 = re.search(r"<body[^>]*>([\s\S]*?)</body>", html, re.IGNORECASE)
            body = m2.group(1) if m2 else html
            body = re.sub(r"<!--.*?-->", " ", body, flags=re.DOTALL)
            body = re.sub(r"<style[\s\S]*?</style>", " ", body, flags=re.IGNORECASE)
            body = re.sub(r"\sstyle=\"[^\"]*\"", "", body)
            return title, body.strip()
        def rewrite_assets(body, src_dir, slug):
            import re
            out_assets = os.path.join(site_bulten_assets, slug)
            os.makedirs(out_assets, exist_ok=True)
            def repl(m):
                attr, url = m.group(1), m.group(2)
                if url.startswith(('http:','https:','data:','assets/','../','/')):
                    return m.group(0)
                src_path = os.path.join(src_dir, url)
                base = os.path.basename(url)
                dst_path = os.path.join(out_assets, base)
                try:
                    if os.path.isfile(src_path): shutil.copy2(src_path, dst_path)
                except Exception: pass
                new_url = f"assets/{slug}/{base}"
                return f'{attr}="{new_url}"'
            body = re.sub(r"(src)=\"([^\"]+)\"", repl, body, flags=re.IGNORECASE)
            body = re.sub(r"(href)=\"([^\"]+)\"", repl, body, flags=re.IGNORECASE)
            return body
        def find_folder_cover(src_dir):
            try:
                names = os.listdir(src_dir)
            except Exception:
                names = []
            cand = []
            for name in names:
                p = os.path.join(src_dir, name)
                if os.path.isdir(p) and name.lower() in ('image','images','res','assets'):
                    try:
                        for fn in os.listdir(p):
                            if fn.lower().endswith(('.jpg','.jpeg','.png','.webp','.gif')):
                                cand.append(os.path.join(name, fn))
                    except Exception:
                        pass
            if cand:
                return cand[0], os.path.basename(cand[0])
            return None, None
        import importlib, sys
        while True:
            try:
                # Recursively discover all .html files under site/bulten_doc
                cur = {}
                for root, _dirs, files in os.walk(docs_dir):
                    for fn in files:
                        if not fn.lower().endswith('.html'):
                            continue
                        p = os.path.join(root, fn)
                        try:
                            cur[p] = os.path.getmtime(p)
                        except FileNotFoundError:
                            pass
                changed = (set(cur.keys()) != set(snap.keys())) or any(cur.get(k)!=snap.get(k) for k in cur)
                if changed:
                    for p, mt in cur.items():
                        try:
                            raw = open(p, 'r', encoding='utf-8', errors='ignore').read()
                        except Exception:
                            continue
                        title_src, body = extract_title_body(raw)
                        dt = monday_of(datetime.fromtimestamp(mt))
                        title, slug, date_iso = weekly_title_slug(dt)
                        src_dir = os.path.dirname(p)
                        body2 = rewrite_assets(body, src_dir, slug)
                        # cover from image folder if available
                        cover_rel, cover_base = find_folder_cover(src_dir)
                        hero = '../assets/img/covers/default.jpg'
                        if cover_rel and cover_base:
                            try:
                                dst_dir = os.path.join(site_bulten_assets, slug)
                                os.makedirs(dst_dir, exist_ok=True)
                                shutil.copy2(os.path.join(src_dir, cover_rel), os.path.join(dst_dir, cover_base))
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
                        out_json = os.path.join(data_dir, f'{slug}.json')
                        with open(out_json, 'w', encoding='utf-8') as f:
                            json.dump(rec, f, ensure_ascii=False, indent=2)
                    # rebuild bulten pages
                    try:
                        if ROOT not in sys.path:
                            sys.path.insert(0, ROOT)
                        mod = importlib.import_module('scripts.build_bulten')
                        mod.main()
                    except Exception as e:
                        try:
                            print('[bulten-watcher] build error:', e)
                        except Exception:
                            pass
                    snap = cur
            except Exception as e:
                # do not crash server
                pass
            _time.sleep(10)

    t = threading.Thread(target=bulten_watcher, daemon=True)
    t.start()
    httpd.serve_forever()

if __name__ == '__main__':
    main()
