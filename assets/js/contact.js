// Rewritten, robust contact logic
(function(){
  const nameEl = document.getElementById('c-name');
  const emailEl = document.getElementById('c-email');
  const subjectEl = document.getElementById('c-subject');
  const msgEl = document.getElementById('c-message');
  const btnMail = document.getElementById('btn-mail');

  const dateEl = document.getElementById('r-date');
  const timeEl = document.getElementById('r-time');
  const noteEl = document.getElementById('r-note');
  const rNameEl = document.getElementById('r-name');
  const rEmailEl = document.getElementById('r-email');
  const btnGcal = document.getElementById('btn-gcal');
  const btnApi = document.getElementById('btn-api');
  const kvkkOk = document.getElementById('kvkk-ok');

  const OWNER_EMAIL = 'ferhatisyapan@gmail.com';
  let CONTACT_API_URL = window.CONTACT_API_URL || '';
  let CONTACT_API_TOKEN = window.CONTACT_API_TOKEN || '';

  function pad(n){ return n<10?('0'+n):(''+n); }
  function normalizeEmail(s){ return (s||'').trim(); }
  function isValidEmail(s){
    s = normalizeEmail(s);
    const re = /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i;
    if(!re.test(s)) return false;
    if(s.indexOf('..') !== -1) return false;
    const at = s.lastIndexOf('@');
    const domain = s.slice(at+1);
    if(domain.indexOf('.') === -1) return false;
    return true;
  }

  // Build 15-min time slots (10:00–17:45) for <select>
  const allowedTimes = [];
  (function buildSlots(){
    for(let h=10; h<=17; h++){
      for(let m=0; m<60; m+=15){
        if(h===17 && m>45) break;
        const hh = (h<10? '0'+h : ''+h);
        const mm = (m<10? '0'+m : ''+m);
        allowedTimes.push(`${hh}:${mm}`);
      }
    }
    if(timeEl && timeEl.tagName && timeEl.tagName.toLowerCase()==='select'){
      if(timeEl.options.length <= 1){
        allowedTimes.forEach(t=>{
          const opt = document.createElement('option');
          opt.value = t; opt.textContent = t; timeEl.appendChild(opt);
        });
      }
    }
  })();

  function toLocalDateTime(){
    const d = dateEl && dateEl.value;
    const t = timeEl && timeEl.value;
    if(!d || !t) return null;
    const [yy,mm,dd] = d.split('-');
    const [HH,MM] = t.split(':');
    const start = new Date(Number(yy), Number(mm)-1, Number(dd), Number(HH), Number(MM), 0);
    const end = new Date(start.getTime() + 15*60*1000);
    return {start, end};
  }

  function validateTimeSlots(){
    const t = (timeEl && timeEl.value||'').trim();
    if(!t){ alert('Lütfen saat seçin.'); return false; }
    if(allowedTimes.length && allowedTimes.indexOf(t) === -1){ alert('Lütfen 15 dk aralıklarında geçerli bir saat seçin.'); return false; }
    const parts = t.split(':'); if(parts.length!==2) return false;
    const HH = parseInt(parts[0],10), MM = parseInt(parts[1],10);
    if(isNaN(HH) || isNaN(MM)) return false;
    if(MM % 15 !== 0) return false;
    if(HH < 10 || HH > 17 || (HH === 17 && MM > 45)) return false;
    return true;
  }

  function fmtGoogle(dt){
    return dt.getFullYear()+pad(dt.getMonth()+1)+pad(dt.getDate())+'T'+pad(dt.getHours())+pad(dt.getMinutes())+pad(dt.getSeconds());
  }
  function mailto(subject, body){
    const url = 'mailto:'+OWNER_EMAIL+'?subject='+encodeURIComponent(subject)+'&body='+encodeURIComponent(body);
    location.href = url;
  }

  function validateBasic(){
    const email = normalizeEmail(((rEmailEl && rEmailEl.value) || (emailEl && emailEl.value) || ''));
    const emailOk = isValidEmail(email);
    if(kvkkOk && !kvkkOk.checked){ alert('Lütfen KVKK Aydınlatma Metni’ni onaylayın.'); return false; }
    if(!emailOk){ alert('Lütfen geçerli bir e‑posta girin.'); return false; }
    return true;
  }

  // Mail
  if(btnMail){
    btnMail.addEventListener('click', function(){
      if(!validateBasic()) return;
      const subj = (subjectEl && subjectEl.value) || 'İletişim';
      const body = `Ad: ${nameEl && nameEl.value || ''}\nE-posta: ${emailEl && emailEl.value || ''}\n\nMesaj:\n${msgEl && msgEl.value || ''}`;
      try { window.vmTrack && window.vmTrack('email_send', { source:'contact-form', email: normalizeEmail(emailEl && emailEl.value), subject: subj, length: (msgEl && msgEl.value || '').length }); } catch(e){}
      mailto(subj, body);
    });
  }

  // Google Calendar taslağı
  function openGCalTemplateFromSelection(){
    const sel = toLocalDateTime();
    const title = 'Görüşme - Verinin Mutfağı';
    const email = normalizeEmail(((rEmailEl && rEmailEl.value) || (emailEl && emailEl.value) || ''));
    const details = (noteEl && noteEl.value ? (noteEl.value+'\n\n') : '') + 'Rezervasyon talebi' + (email? ('\nE-posta: '+email) : '');
    let url = 'https://calendar.google.com/calendar/render?action=TEMPLATE' + '&text=' + encodeURIComponent(title) + '&details=' + encodeURIComponent(details);
    if (sel) url += '&dates=' + encodeURIComponent(fmtGoogle(sel.start) + '/' + fmtGoogle(sel.end));
    window.open(url, '_blank');
  }

  // Hero randevu ve form randevu linkleri
  try{
    var a1 = document.getElementById('btn-appointment-link');
    if(a1){ a1.addEventListener('click', function(e){ e.preventDefault(); if(!validateBasic()) return; try{ const t=toLocalDateTime(); window.vmTrack && window.vmTrack('appointment', { source:'contact-hero', email: (rEmailEl && rEmailEl.value)||(emailEl&&emailEl.value||''), start: t&&t.start&&t.start.toISOString(), end: t&&t.end&&t.end.toISOString() }); }catch(_){}; openGCalTemplateFromSelection(); }); a1.style.display='inline-block'; }
    var a2 = document.getElementById('btn-appointment-link-2');
    if(a2){ a2.addEventListener('click', function(e){ e.preventDefault(); if(!validateBasic()) return; try{ const t=toLocalDateTime(); window.vmTrack && window.vmTrack('appointment', { source:'contact-form', email: (rEmailEl && rEmailEl.value)||(emailEl&&emailEl.value||''), start: t&&t.start&&t.start.toISOString(), end: t&&t.end&&t.end.toISOString() }); }catch(_){}; openGCalTemplateFromSelection(); }); a2.style.display='inline-block'; }
  }catch(e){}

  if(btnGcal){
    btnGcal.addEventListener('click', function(){
      if(!validateBasic() || !validateTimeSlots()) return;
      const sel = toLocalDateTime(); if(!sel){ alert('Lütfen tarih ve saat seçin.'); return; }
      const title = 'Görüşme - Verinin Mutfağı';
      const email = normalizeEmail(((rEmailEl && rEmailEl.value) || (emailEl && emailEl.value) || ''));
      const details = (noteEl.value? (noteEl.value+'\n\n') : '') + 'Rezervasyon talebi' + (email? ('\nE-posta: '+email) : '');
      const dates = fmtGoogle(sel.start)+'/'+fmtGoogle(sel.end);
      try { window.vmTrack && window.vmTrack('appointment_gcal', { source:'contact-form', email: (rEmailEl && rEmailEl.value)||(emailEl.value||''), start: sel.start.toISOString(), end: sel.end.toISOString() }); } catch(_){}
      const url = 'https://calendar.google.com/calendar/render?action=TEMPLATE'
        +'&text='+encodeURIComponent(title)
        +'&dates='+encodeURIComponent(dates)
        +'&details='+encodeURIComponent(details);
      window.open(url, '_blank');
    });
  }

  if(btnApi){
    if(CONTACT_API_URL){ btnApi.style.display=''; }
    btnApi.addEventListener('click', async function(){
      if(!validateBasic() || !validateTimeSlots()) return;
      if(!CONTACT_API_URL){ alert('API yapılandırılmadı.'); return; }
      const sel = toLocalDateTime(); if(!sel){ alert('Lütfen tarih ve saat seçin.'); return; }
      const payload = {
        name: ((rNameEl && rNameEl.value) || nameEl.value || ''),
        email: ((rEmailEl && rEmailEl.value) || emailEl.value || ''),
        note: noteEl.value || '',
        start: sel.start.toISOString(),
        end: sel.end.toISOString(),
        token: CONTACT_API_TOKEN
      };
      try {
        const res = await fetch(CONTACT_API_URL, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
        const data = await res.json().catch(()=>({}));
        if(res.ok){
          try { window.vmTrack && window.vmTrack('appointment_api', { ok:true, id:data.id||'', email: payload.email, start: payload.start, end: payload.end }); } catch(_){}
          alert('Rezervasyon talebi alındı' + (data.id? (' (ID: '+data.id+')') : ''));
        } else {
          try { window.vmTrack && window.vmTrack('appointment_api', { ok:false, status:res.status, email: payload.email, start: payload.start, end: payload.end }); } catch(_){}
          alert('Rezervasyon başarısız: '+(data.error||res.status));
        }
      } catch(err){
        try { window.vmTrack && window.vmTrack('appointment_api', { ok:false, error: String(err), email: payload.email, start: payload.start, end: payload.end }); } catch(_){}
        alert('Ağ hatası: '+err);
      }
    });
  }
})();
