# İletişim ve Rezervasyon Entegrasyonu

Bu sayfadaki rezervasyon akışı üç düzey sunar:

1) E‑posta: Kullanıcının posta istemcisinde yeni e‑posta açar (mailto). Sunucu gerekmez.
2) Google Calendar taslağı: Kullanıcının takviminde (kendi hesabında) seçilen tarih/saat için taslak oluşturur.
3) Doğrudan takvime ekleme (önerilen): Sizin takviminize (ferhatisyapan@gmail.com) 15 dk etkinlik açar. Bunun için bir arka uç API gerekir.

## 3. Yöntem: Doğrudan Takvime Ekle (Önerilen)

İki hızlı yol:

### A) Google Apps Script (GAS) Web App (en kolay)

- Google hesabınızda yeni bir Apps Script projesi oluşturun
- Aşağıdaki kodu yapıştırın ve `Deploy > New deployment > type: Web app` ile yayınlayın
  - Execute as: Me (you)
  - Who has access: Anyone with the link

```
function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    var token = data.token || '';
    // Basit gizli: eşleştirme (opsiyonel)
    if (token && token !== 'YOUR_SHARED_SECRET') {
      return ContentService.createTextOutput(JSON.stringify({error:'unauthorized'})).setMimeType(ContentService.MimeType.JSON);
    }
    var name = data.name || '';
    var email = data.email || '';
    var note = data.note || '';
    var start = new Date(data.start);
    var end = new Date(data.end);
    // Birincil takvime ekle + çakışma kontrolü
    var cal = CalendarApp.getDefaultCalendar();
    var conflicts = cal.getEvents(start, end);
    if (conflicts && conflicts.length) {
      return ContentService.createTextOutput(JSON.stringify({error:'busy'})).setMimeType(ContentService.MimeType.JSON);
    }
    var ev = cal.createEvent('Görüşme - Verinin Mutfağı', start, end, {
      description: (note ? note + '\n\n' : '') + 'Talep eden: ' + name + ' <' + email + '>',
      guests: email,
      sendInvites: true
    });
    return ContentService.createTextOutput(JSON.stringify({ok:true,id:ev.getId()})).setMimeType(ContentService.MimeType.JSON);
  } catch(err) {
    return ContentService.createTextOutput(JSON.stringify({error:String(err)})).setMimeType(ContentService.MimeType.JSON);
  }
}
```

- Yayın sonrası verilen Web App URL’sini alın (ör. https://script.google.com/macros/s/XXXX/exec)
- Ön yüzde `site/assets/js/contact.js` dosyasında:
  - `CONTACT_API_URL` = bu URL
  - `CONTACT_API_TOKEN` = `YOUR_SHARED_SECRET` (opsiyonel)
- İletişim sayfasındaki “Doğrudan Takvime Ekle (API)” butonu görünür ve direkt takviminize kayıt açar.

### B) Kendi API’niz (Node/Express örneği)

- Google Cloud Console’da OAuth client/service account ile Calendar API yetkilendirin.
- Örnek uç nokta:

```
const express = require('express');
const {google} = require('googleapis');
const app = express();
app.use(express.json());

app.post('/api/reserve', async (req,res)=>{
  try{
    const {name,email,start,end,note,token} = req.body;
    if(process.env.SHARED_SECRET && token!==process.env.SHARED_SECRET){
      return res.status(401).json({error:'unauthorized'});
    }
    // TODO: auth init (JWT/Service Account veya OAuth)
    const auth = /* ... */;
    const calendar = google.calendar({version:'v3', auth});
    // FreeBusy kontrol (opsiyonel)
    // const fb = await calendar.freebusy.query({ requestBody:{ timeMin:start, timeMax:end, items:[{id:'primary'}] } });
    // Etkinlik oluştur
    const event = await calendar.events.insert({
      calendarId: 'primary',
      requestBody: {
        summary: 'Görüşme - Verinin Mutfağı',
        description: (note? note+'\n\n':'' ) + `Talep eden: ${name} <${email}>`,
        start: {dateTime: start},
        end: {dateTime: end},
        attendees: email? [{email}]: [],
        reminders: { useDefault: true }
      }, sendUpdates: 'all'
    });
    res.json({ok:true, id: event.data.id});
  }catch(err){ res.status(500).json({error:String(err)}); }
});

app.listen(3000,()=>console.log('running on :3000'));
```

- URL’yi `CONTACT_API_URL` olarak girin; “Doğrudan Takvime Ekle (API)” butonu aktif olur.

## E‑posta ve ICS
- E‑posta: mailto ile e‑posta penceresi açılır ve içerik hazır gelir.
- ICS: 15 dk’lık bir .ics dosyası indirir, çift tıklayın ve takviminize ekleyin.

## Özelleştirme
- Varsayılan zaman aralığı: 15 dk (contact.js içinde hesaplanır)
- Çalışma saatleri: HTML’de time input min/max (10:00–18:00) olarak ayarlı
- Sahip e‑posta: contact.js içindeki `OWNER_EMAIL`
