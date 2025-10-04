# Deploying the Site

This repo builds a static site under `site/`. Use the scripts below to generate artifacts. Root only contains `index.html` (redirect) and `README.md`; everything else lives in subfolders.

## 1) Configure

Copy `config/env.sample` to `.env` (repo root) and fill values as needed:

- `SITE_BASE_URL` for canonical links and sitemap URLs
- `YT_API_KEY` for YouTube refresh (optional)
- `ANALYTICS_URL` and `ANALYTICS_TOKEN` for analytics collector (optional)
- `CONTACT_API_URL` and `CONTACT_API_TOKEN` for the contact page API (optional)

Do not commit `.env` — it is ignored by git.

GitHub Actions uses `secrets.YT_API_KEY` for YouTube refresh. Add it under Settings → Secrets → Actions.

## 2) Build Everything

```
bash scripts/build_all.sh
```

Artifacts will be in `site/`.

## 3) Refresh YouTube Videos (optional)

If `YT_API_KEY` is provided in `.env`, `build_all.sh` will refresh `site/youtube/videos.json` automatically. Otherwise, you can run:

```
python3 scripts/fetch_youtube.py --handle @verininmutfagi --max 30 --api-key "$YT_API_KEY"
bash scripts/refresh_youtube.sh
```

## 4) Deploy

Upload the `site/` directory to your static hosting (GitHub Pages / Cloudflare Pages / Netlify).

Ensure:

- Analytics (if used): set `ANALYTICS_URL` and `ANALYTICS_TOKEN` via a small script before `assets/js/analytics.js` or by editing `site/assets/js/analytics.config.js`.
- Contact API (if used): set `site/contact/config.js` with your URL/TOKEN (keep secrets out of repo).
