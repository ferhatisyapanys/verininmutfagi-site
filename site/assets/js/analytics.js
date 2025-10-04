// Minimal client-side analytics: page views, clicks, searches, actions.
// Configure endpoint/token via analytics.config.js (see example below).
(function(){
  var URL = (window.ANALYTICS_URL||'').replace(/\/$/,'');
  var TOKEN = window.ANALYTICS_TOKEN||'';
  if(!URL){ return; }
  var cid = localStorage.getItem('vm_cid');
  if(!cid){ cid = Math.random().toString(36).slice(2)+Date.now().toString(36); localStorage.setItem('vm_cid', cid); }
  var sid = sessionStorage.getItem('vm_sid');
  if(!sid){ sid = Math.random().toString(36).slice(2); sessionStorage.setItem('vm_sid', sid); }
  // queue for reliability (in case network/server down)
  var QKEY = 'vm_evtq';
  function loadQ(){ try{ return JSON.parse(localStorage.getItem(QKEY)||'[]'); }catch(_){ return []; } }
  function saveQ(q){ try{ localStorage.setItem(QKEY, JSON.stringify(q)); }catch(_){} }
  var q = loadQ();
  function send(ev){
    try{
      ev.ts = Math.floor(Date.now()/1000); ev.cid = cid; ev.sid = sid; ev.ref = document.referrer||''; ev.page = location.pathname;
      // enqueue (best-effort)
      q.push(ev); saveQ(q);
      // soft flush async
      setTimeout(flush, 50);
    }catch(e){}
  }
  function flush(){
    if(!q.length) return;
    var batch = q.slice(0, 20); // small batch
    var ok = false;
    try{
      ok = fetch(URL+'/api/collect', {
        method:'POST',
        headers: Object.assign({'Content-Type':'application/json'}, TOKEN? {'X-Analytics-Token':TOKEN} : {}),
        body: JSON.stringify(batch.length>1? {batch:batch} : batch[0])
      }).then(function(res){ if(res.ok){ q.splice(0, batch.length); saveQ(q); } }).catch(function(){});
    }catch(_){ }
  }
  // also flush on pagehide/visibility
  window.addEventListener('visibilitychange', function(){ if(document.visibilityState==='hidden') flush(); });
  window.addEventListener('pagehide', flush);
  // page view
  send({event:'view'});
  // clicks on trackable elements
  document.addEventListener('click', function(e){
    var sel = 'a,button,[role="button"],.sb-btn,.vm-btn,input[type="button"],input[type="submit"],.sb-menu-btn,.sb-info-btn';
    var el = e.target.closest(sel); if(!el) return;
    var label = el.getAttribute('data-track') || el.id || (el.getAttribute('aria-label')||'').trim();
    if(!label){ label = (el.textContent||'').trim().replace(/\s+/g,' ').slice(0,100); }
    var payload = {event:'click', element: label, props: { tag:(el.tagName||'').toLowerCase() }};
    if (el.href) { payload.props.href = el.href; }
    send(payload);
  });
  // search input tracking
  var input = document.getElementById('vm-search-input');
  if(input){
    var t; input.addEventListener('input', function(){
      clearTimeout(t); var q = (input.value||'').trim(); if(q.length<2) return;
      t = setTimeout(function(){ send({event:'search', value:q}); }, 500);
    });
  }
  // Expose manual tracker
  window.vmTrack = function(ev, data){ send({event: ev, value: (data&&data.value)||'', props: data||{}}); };
})();

// Example config (copy to analytics.config.js and include before this file):
// window.ANALYTICS_URL = 'http://127.0.0.1:8787';
// window.ANALYTICS_TOKEN = '';
