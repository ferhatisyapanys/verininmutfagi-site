# Verinin Mutfağı – Açık Kaynak Analitik + Dashboard

Bu repo, sitedeki tıklamalar, aramalar, randevu ve e‑posta aksiyonları gibi olayları toplayıp raporlamak için hafif bir arka uç ve küçük bir dashboard içerir. Tamamen açık kaynak ve tek dosyalık SQLite kullandığı için kurulum çok kolaydır.

## Neler Toplanır?

- Sayfa görüntüleme (`view`)
- Tıklamalar (`click`) — buton/link metni veya `id`
- Arama sorguları (`search`) — blog arama kutusundan
- Randevu/E‑posta aksiyonları (`vmTrack('appointment' ...)`, `vmTrack('email' ...)`) — istenirse çağrılır
- İsteğe bağlı başka olaylar: `window.vmTrack('eventAdı', { value:'...', props:{...} })`

Olaylar aşağıdaki alanlarla saklanır: zaman damgası, `client_id` (localStorage), `session_id`, sayfa yolu, element, değer, IP ve UserAgent.

## Hızlı Kurulum

1) Sunucuyu çalıştırın:

```
python3 scripts/analytics_server.py --host 127.0.0.1 --port 8787 --db data/runtime/analytics.db
```

- İlk açılışta `analytics.db` dosyasını oluşturur.
- Ortam değişkeni `ANALYTICS_TOKEN` belirleyip istemciden doğrulama isteyebilirsiniz.

2) İstemci yapılandırması

- `site/assets/js/analytics.config.example.js` dosyasını `analytics.config.js` olarak kopyalayın ve sunucu adresini girin:

```
window.ANALYTICS_URL = 'http://127.0.0.1:8787';
window.ANALYTICS_TOKEN = '';
```

- Bu dosya, ana sayfa, blog, YouTube ve iletişim sayfalarında yüklendi.

## Dashboard

- Tarayıcıda `http://127.0.0.1:8787/admin` adresine gidin.
- Son 24 saat/7 gün özetleri ve en çok görüntülenen sayfalar ile aramalar listelenir.

## Gelişmiş – Özel Olay Gönderme

Örneğin iletişim sayfasında randevu butonuna basıldığında bir olay göndermek için:

```
window.vmTrack('appointment', { value: 'contact-hero', when: new Date().toISOString() });
```

## Gizlilik / KVKK

- Veri toplanması, yalnızca site sahibi içindir; çerez/saklama politikanızda belirtin.
- E‑posta ve KVKK onayı zorunlu akışlarda zaten sayfada onay kutusu bulunuyor.

## Notlar

- Bu sistem **yalın** ve **yerel** kullanım içindir. Trafiğiniz çok artarsa bir HTTP reverse proxy kurmanızı veya Postgres gibi bir sunucu DB’si kullanmanızı öneririz (şema aynı kalabilir).
- Yalnızca stdlib kullanır: `http.server` + `sqlite3`. Ek bağımlılık yoktur.

## Production (Sunucusuz/Sunucu ile) Yayınlama

Seçenek 1 — Docker container:

```
docker build -f docker/Dockerfile.analytics -t vm-analytics .
docker run -p 8080:8080 -e ANALYTICS_TOKEN=GIZLI --name vm-analytics vm-analytics
```

- Üretimde bir reverse proxy (Caddy/Nginx) ile `https://analytics.senin-domainin.com` altına yönlendirin.
- Site tarafında `site/assets/js/analytics.config.js` içindeki `ANALYTICS_URL`’ü bu adrese çevirin.

Seçenek 2 — Uygulama platformları (Render/Fly/Railway)

- Dockerfile.analytics ile doğrudan deploy edebilirsiniz.
- 8080 portunu expose edin ve platformun verdiği URL’i `ANALYTICS_URL` olarak girin.

Seçenek 3 — Cloudflare Workers/D1 (opsiyon)

- İsterseniz bu minimal API’yi Workers’a taşıyabilir, D1 (SQLite) ile persist edebilirsiniz. Şema aynı kalır; sadece HTTP handler’ı Workers uyumlu hale getirmek gerekir.
