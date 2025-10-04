# Verinin Mutfağı — Static Site

Bu depo, Verinin Mutfağı web sitesinin statik derlenmiş halini (`site/`) ve yardımcı betiklerini içerir.

Hızlı başlangıç:

- `bash scripts/build_all.sh` — Blog, bülten, YouTube ve sitemap üretir.
- Çıktılar `site/` klasöründe. `index.html` doğrudan `site/index.html`’e yönlendirir.

Yapı:

- `site/` — Yayına hazır statik site (favicon, sayfalar, varlıklar)
- `scripts/` — Derleme ve yardımcı betikler
- `data/` — Bülten JSON kayıtları
- `content/` — Kaynak blog HTML dosyaları (opsiyonel)
- `docker/` — Analytics için docker dosyaları
- `docs/` — Deploy ve dokümantasyon

Yapılandırma (.env):

- `SITE_BASE_URL`: Örn. `https://verininmutfagi.com`
- `YT_API_KEY`: YouTube Data API anahtarı (opsiyonel)
- `ANALYTICS_URL`, `ANALYTICS_TOKEN`: (opsiyonel)
- `CONTACT_API_URL`, `CONTACT_API_TOKEN`: (opsiyonel)

Güvenlik notları:
- Gizli anahtarları repo’ya koymayın. GitHub Actions’ta Secrets kullanın.
- `site/contact/config.js` depo içinde boştur; prod’da doldurulmalıdır.

Bkz: `docs/DEPLOY.md`
