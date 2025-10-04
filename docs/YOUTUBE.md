# YouTube thumbnails with a hidden API key

This site does NOT expose your YouTube Data API key to the browser. Thumbnails are driven by a static JSON file committed to the repo (`site/youtube/videos.json`).

## One‑time setup

1) Create a YouTube Data API v3 key (read‑only) and restrict it:
   - API restrictions: only "YouTube Data API v3"
   - Application restrictions: ideally IP or none (since you run locally)
2) Copy `.env.sample` to `.env` and put your key under `YT_API_KEY=` (do NOT commit `.env`).

## Refresh the thumbnails list

Run from the project root (choose one):

- With handle (recommended):

```
export YT_API_KEY="$(cat .env | sed -n 's/^YT_API_KEY=//p')"
python3 scripts/fetch_youtube.py --handle @verininmutfagi --max 30
```

- With channel id:

```
export YT_API_KEY="$(cat .env | sed -n 's/^YT_API_KEY=//p')"
python3 scripts/fetch_youtube.py --channel-id UCxxxxxxxx --max 30
```

The script writes `site/youtube/videos.json` with `[ { id, title, published }, ... ]`.
The frontend (`site/assets/js/youtube.js`) reads this file and renders the grid with real YouTube thumbnails from `i.ytimg.com`.

## Privacy & security
- The API key never goes to the browser. It is only used locally by the script.
- `.env` is ignored by git. Keep your key out of commits.
- If your key was ever exposed, rotate it in Google Cloud Console.

## Customization
- To include the very latest video as well, change `START_INDEX` from `1` to `0` in `site/assets/js/youtube.js`.
- Adjust `LIMIT` (default 24) to control how many videos are shown.

## Notlar
- videos.json güncellemesi: Yeni video yükledikçe `scripts/fetch_youtube.py` komutunu tekrar çalıştırın; grid anında güncellenir.
- İnternet erişimi: Grid kapakları doğrudan `i.ytimg.com` üzerinden gelir; kapak görünmüyorsa internet/proxy kısıtına bakın.
- Sıralama: Varsayılan olarak en yeni videodan bir önceki videodan başlar (START_INDEX=1). En yeni videoyu da listeye dahil etmek için `START_INDEX=0` yapın.
- Sayı: Çok fazla video göstermek istiyorsanız `LIMIT` değerini yükseltin; performans için 24–48 önerilir.
- Güvenlik: API anahtarı sadece scriptte (local) kullanılıp `site/youtube/videos.json` dosyasına yazılır. Frontend’e asla anahtar gönderilmez.
- Yedek: API’ye erişemeyeceğiniz ortamlarda videos.json’u manuel düzenleyebilirsiniz: `[ { "id":"VIDEO_ID", "title":"Başlık", "published":"ISO_TARIH" }, ... ]`.
