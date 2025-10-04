/* Simple client-side search (TR-friendly) */
(function(){
  const input = document.getElementById('vm-search-input');
  const resultsEl = document.getElementById('vm-results');
  if(!input || !resultsEl) return;

  const trMap = {
    'ç':'c','Ç':'c','ğ':'g','Ğ':'g','ı':'i','İ':'i','ö':'o','Ö':'o','ş':'s','Ş':'s','ü':'u','Ü':'u'
  };
  const normalize = (s) => (s||'').replace(/[çÇğĞıİöÖşŞüÜ]/g, m=>trMap[m]||m).toLowerCase();
  const tokenize = (s) => normalize(s).split(/[^a-z0-9]+/).filter(Boolean);
  const suffixes = ['lar','ler','lari','leri','dan','den','ten','tan','dir','dır','dur','dür','tir','tır','tur','tür','li','lı','lu','lü','in','ın','un','ün','e','a','i','ı','u','ü'];
  function stemTR(token){
    if(token.length <= 3) return token;
    for(const suf of suffixes){
      if(token.endsWith(suf) && token.length - suf.length >= 3){
        return token.slice(0, -suf.length);
      }
    }
    return token;
  }

  let docs = [];
  let ready = false;
  const postsGrid = document.querySelector('.vm-grid');

  function scoreDoc(doc, terms, normQ){
    // Build (or reuse) stem frequency maps
    if(!doc._built){
      const tTokens = tokenize(doc.title).map(stemTR);
      const cTokens = tokenize(doc.content).map(stemTR);
      const tFreq = Object.create(null);
      const cFreq = Object.create(null);
      for(const w of tTokens){ tFreq[w] = (tFreq[w]||0)+1; }
      for(const w of cTokens){ cFreq[w] = (cFreq[w]||0)+1; }
      doc._tFreq = tFreq; doc._cFreq = cFreq; doc._built = true;
    }
    let score = 0;
    for(const t of terms){
      const s = stemTR(t);
      score += (doc._tFreq[s]||0)*5 + (doc._cFreq[s]||0)*1;
    }
    // Strong boost if query appears in title (prefix > contains)
    if(normQ && normQ.length >= 2){
      const nt = normalize(doc.title);
      if(nt.startsWith(normQ)) score += 1000;
      else if(nt.indexOf(normQ) >= 0) score += 500;
    }
    // recency boost: newer posts slightly higher (scale ~ up to +10)
    if(doc.ts){
      const ageDays = Math.max(0, (Date.now()/1000 - doc.ts)/86400);
      const rec = Math.max(0, 10 - Math.log1p(ageDays));
      score += rec;
    }
    return score;
  }

  function makeSnippet(doc, terms){
    const raw = doc.content;
    const nraw = normalize(raw);
    let pos = -1; let term="";
    for(const t of terms){
      const idx = nraw.indexOf(t);
      if(idx>=0){ pos = idx; term=t; break; }
    }
    if(pos<0){ return raw.slice(0,160) + (raw.length>160?'...':''); }
    const start = Math.max(0, pos-60);
    const end = Math.min(raw.length, pos+120);
    let snip = raw.slice(start, end);
    // highlight terms (basic, case-insensitive and TR-normalized)
    terms.forEach(t=>{
      if(!t) return;
      const re = new RegExp(t.replace(/[-/\\^$*+?.()|[\]{}]/g,'\\$&'), 'gi');
      snip = snip.replace(re, (m)=>`<mark>${m}</mark>`);
    });
    return (start>0?'...':'') + snip + (end<raw.length?'...':'');
  }

  function render(list){
    if(!list.length){ resultsEl.innerHTML = '<p class="vm-muted">Sonuç bulunamadı.</p>'; return; }
    // detect section for relative paths
    var path = (location && location.pathname) || '';
    var isBlog = /\/blog\//.test(path);
    var isBulten = /\/bultenler\//.test(path);
    function resolveCover(cover){
      if(!cover) return '';
      if(cover.startsWith('data:')) return cover;
      if(cover.startsWith('assets/')){
        if(isBulten){
          // Bulletin assets live under site/bultenler/assets/<slug>/...
          // Root site assets are like assets/img/... → need one level up
          if(/^assets\/verinin-dunyasi-/.test(cover)) return cover;
          return '../' + cover;
        }
        if(isBlog){
          // Blog index is under site/blog → go up one level to site/assets
          return '../' + cover;
        }
      }
      return cover;
    }
    const html = list.map(doc=>{
      let cover = resolveCover(doc.cover||'');
      const line = `
        <article class="vm-result">
          <div class="vm-result-grid">
            <div class="vm-thumb">${cover?`<img src="${cover}" alt="">`:''}</div>
            <div>
              <h3><a href="${doc.slug}.html">${doc.title}</a></h3>
              <div class="vm-card-meta">${doc.date}</div>
              <p class="vm-snippet">${makeSnippet(doc, currentTerms)}</p>
            </div>
          </div>
        </article>`;
      return line;
    }).join('\n');
    resultsEl.innerHTML = html;
  }

  let currentTerms = [];
  function doSearch(){
    const q = input.value.trim();
    if(q.length < 2){
      // kısa sorguda listeyi gizle, grid göster
      if(postsGrid) postsGrid.style.display = '';
      resultsEl.innerHTML = '<p class="vm-muted">Aramak için en az 2 karakter yazın.</p>';
      return;
    }
    if(postsGrid) postsGrid.style.display = 'none';
    currentTerms = tokenize(q);
    const normQ = normalize(q);
    const scored = docs.map(d=>({doc:d, s:scoreDoc(d,currentTerms, normQ)})).filter(x=>x.s>0)
      .sort((a,b)=> b.s - a.s).map(x=>x.doc);
    render(scored);
  }

  // Prefer inline JSON (works on file://); fallback to fetch
  try{
    const inline = document.getElementById('vm-search-data');
    if(inline && inline.textContent.trim().length){
      docs = JSON.parse(inline.textContent);
      ready = true;
      // başlangıçta grid açık kalsın, ipucu verelim
      resultsEl.innerHTML = '<p class="vm-muted">Aramak için yazmaya başlayın…</p>';
    } else {
      throw new Error('no-inline');
    }
  }catch(err){
    fetch('../search/index.json')
      .then(r=>r.json())
      .then(json=>{ docs = json; ready = true; resultsEl.innerHTML = '<p class="vm-muted">Aramak için yazmaya başlayın…</p>'; })
      .catch(()=>{ resultsEl.innerHTML = '<p class="vm-muted">Arama dizini yüklenemedi.</p>'; });
  }

  input.addEventListener('input', ()=>{ if(ready) doSearch(); });
})();
