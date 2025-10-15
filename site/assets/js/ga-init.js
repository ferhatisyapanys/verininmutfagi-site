// Google Analytics 4 loader (optional). Loads only if GA_MEASUREMENT_ID is set.
(function(){
  try{
    var ID = (window && window.GA_MEASUREMENT_ID) || '';
    if(!ID) return;
    // Load gtag.js
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(ID);
    document.head.appendChild(s);
    // Init
    window.dataLayer = window.dataLayer || [];
    function gtag(){ dataLayer.push(arguments); }
    window.gtag = gtag;
    gtag('js', new Date());
    // Anonymize IP by default; do not set user_id or PII
    gtag('config', ID, { anonymize_ip: true });
  }catch(e){ /* no-op */ }
})();

