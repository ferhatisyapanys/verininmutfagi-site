// Simple toggle menu for the top-right info/hamburger button
(function(){
  function ready(fn){ if(document.readyState!=='loading') fn(); else document.addEventListener('DOMContentLoaded', fn); }
  ready(function(){
    var infoBtn = document.querySelector('.sb-info-btn');
    var menuBtn = document.querySelector('.sb-menu-btn');
    // Build relative prefixes based on current path
    var p = (location && location.pathname) || '';
    var isBlog = /\/blog\//.test(p);
    var isBulten = /\/bultenler\//.test(p);
    var isYouTube = /\/youtube\//.test(p);
    var isContact = /\/contact\//.test(p);
    var prefix = (isBlog || isBulten || isYouTube || isContact) ? '../' : '';

    // Create panel and overlay once
    var overlay = document.createElement('div');
    overlay.className = 'vm-menu-overlay';
    var panel = document.createElement('div');
    panel.className = 'vm-menu-panel';
    panel.innerHTML = (
      '<nav class="vm-menu-list">' +
        '<a href="'+prefix+'index.html">Ana Sayfa</a>' +
        '<a href="'+prefix+'blog/index.html">Blog</a>' +
        '<a href="'+prefix+'bultenler/index.html">Haftalık Bültenler</a>' +
        '<a href="'+prefix+'youtube/index.html">YouTube</a>' +
        '<a href="'+prefix+'contact/index.html">İletişim</a>' +
      '</nav>'
    );
    document.body.appendChild(overlay);
    document.body.appendChild(panel);

    function open(){ overlay.classList.add('open'); panel.classList.add('open'); }
    function close(){ overlay.classList.remove('open'); panel.classList.remove('open'); }
    function toggle(){ if(panel.classList.contains('open')) close(); else open(); }

    overlay.addEventListener('click', close);
    document.addEventListener('keydown', function(e){ if(e.key==='Escape') close(); });
    panel.addEventListener('click', function(e){
      var a = e.target.closest('a'); if(a){ close(); }
    });

    if(infoBtn){ infoBtn.addEventListener('click', function(e){ e.preventDefault(); toggle(); }); }
    if(menuBtn){ menuBtn.addEventListener('click', function(e){ e.preventDefault(); toggle(); }); }
  });
})();

