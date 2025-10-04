(function(){
  const grid = document.getElementById('vm-yt-grid');
  if(!grid) return;

  const START_INDEX = 0; // en son videodan başla
  const LIMIT = 24;

  function videoCard(v){
    const thumb = `https://i.ytimg.com/vi/${v.id}/hqdefault.jpg`;
    const href = `https://www.youtube.com/watch?v=${v.id}`;
    const title = v.title || 'YouTube Video';
    const date = v.published ? new Date(v.published).toLocaleDateString('tr-TR') : '';
    if (grid.classList.contains('vm-grid')) {
      const item = document.createElement('article');
      item.className = 'vm-card';
      item.innerHTML = `
        <a href="${href}" target="_blank"><img class="vm-card-cover" src="${thumb}" alt="${title}"></a>
        <div class="vm-card-body">
          <div class="vm-card-meta">${date}</div>
          <h3><a href="${href}" target="_blank">${title}</a></h3>
          <p><a href="${href}" target="_blank">YouTube'da izle →</a></p>
        </div>`;
      return item;
    } else {
      const item = document.createElement('div');
      item.className = 'sb-grid-item sb-item-50';
      item.innerHTML = `
        <a href="${href}" target="_blank" class="sb-blog-card sb-mb-30">
          <div class="sb-cover-frame sb-mb-30">
            <img src="${thumb}" alt="${title}">
          </div>
          <div class="sb-blog-card-descr">
            <h3 class="sb-mb-10">${title}</h3>
            <div class="sb-suptitle sb-mb-15"><span>${date}</span></div>
            <p class="sb-text">YouTube</p>
          </div>
        </a>`;
      return item;
    }
  }

  function sortByDateDesc(arr){
    try{
      return arr.slice().sort((a,b)=>{
        const da = Date.parse(a.published||'')||0;
        const db = Date.parse(b.published||'')||0;
        return db - da;
      });
    }catch(_){ return arr; }
  }

  function render(videos){
    const sorted = sortByDateDesc(Array.isArray(videos)? videos : []);
    const slice = sorted.slice(START_INDEX, START_INDEX + LIMIT);
    if (!grid.classList.contains('vm-grid')) {
      grid.innerHTML = '<div class="sb-grid-sizer"></div>';
    } else {
      grid.innerHTML = '';
    }
    slice.forEach(v => grid.appendChild(videoCard(v)));
    // trigger isotope if available (only for starbelly grids)
    if(!grid.classList.contains('vm-grid') && window.jQuery && jQuery('.sb-masonry-grid').isotope){
      const $g = jQuery(grid);
      if (typeof $g.imagesLoaded === 'function') {
        $g.imagesLoaded(function(){ $g.isotope({ itemSelector: '.sb-grid-item', percentPosition: true, masonry: { columnWidth: '.sb-grid-sizer' } }); });
      } else {
        // imagesLoaded yoksa yine de isotope'u çağır
        setTimeout(function(){ $g.isotope({ itemSelector: '.sb-grid-item', percentPosition: true, masonry: { columnWidth: '.sb-grid-sizer' } }); }, 0);
      }
    }
  }

  function parseFeed(xml){
    const doc = (new DOMParser()).parseFromString(xml, 'application/xml');
    const entries = Array.from(doc.getElementsByTagName('entry'));
    const out = entries.map(en => ({
      id: (en.getElementsByTagName('yt:videoId')[0]||{}).textContent || (en.getElementsByTagName('id')[0]||{}).textContent.split(':').pop(),
      title: (en.getElementsByTagName('title')[0]||{}).textContent || '',
      published: (en.getElementsByTagName('published')[0]||{}).textContent || ''
    })).filter(x=>x.id);
    return out;
  }

  function load(){
    // Tercih: yerel videos.json (script ile güncellenir)
    fetch('videos.json')
      .then(r=>r.json())
      .then(list => { if(Array.isArray(list) && list.length) { render(list); return; } else tryInline(); })
      .catch(()=> tryInline());

    function tryInline(){
      try{
        const inline = document.getElementById('vm-yt-videos');
        if(inline && inline.textContent.trim().length){
          const list = JSON.parse(inline.textContent);
          if(Array.isArray(list) && list.length){ render(list); return; }
        }
      }catch(e){ /* ignore */ }
      // file:// altında fetch CORS ile engellenir; inline yoksa boş bırak
      if (location.protocol === 'file:') { showEmpty(); return; }
      tryFallback();
    }
  }

  function tryFallback(){
    // blog sayfasından youtube klasöründeki json'a bak
    fetch('../youtube/videos.json')
      .then(r=>r.json())
      .then(list => { if(Array.isArray(list) && list.length) render(list); else showEmpty(); })
      .catch(()=> showEmpty());
  }

  function showEmpty(){
    grid.innerHTML = '<div class="sb-grid-sizer"></div><p class="sb-text">Videolar yüklenemedi. Lütfen videos.json dosyasını doldurun.</p>';
  }

  load();
})();
