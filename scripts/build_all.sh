#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Optional: load .env for SITE_BASE_URL and YT_API_KEY
if [ -f .env ]; then
  export SITE_BASE_URL="$(sed -n 's/^SITE_BASE_URL=//p' .env | tr -d '\r')"
  export YT_API_KEY="$(sed -n 's/^YT_API_KEY=//p' .env | tr -d '\r')"
fi

echo "[1/4] Build blog"
python3 scripts/build_blog.py

echo "[2/4] Build bulletins"
python3 scripts/build_bulten.py

echo "[3/4] Refresh YouTube videos (optional)"
if [ -n "${YT_API_KEY:-}" ]; then
  python3 scripts/fetch_youtube.py --handle @verininmutfagi --max 30 --api-key "$YT_API_KEY" || true
else
  echo "YT_API_KEY not set, skipping YouTube refresh"
fi

echo "[4/4] Build sitemap"
python3 scripts/build_sitemap.py
touch site/.nojekyll

echo "[check] Scanning internal links for broken references"
# Provide empty env.config.js locally if not created by CI secrets
if [ ! -f site/env.config.js ]; then
  echo "window.ANALYTICS_URL=window.ANALYTICS_URL||''; window.ANALYTICS_TOKEN=window.ANALYTICS_TOKEN||''; window.CONTACT_API_URL=window.CONTACT_API_URL||''; window.CONTACT_API_TOKEN=window.CONTACT_API_TOKEN||'';" > site/env.config.js
fi

# Optionally write CNAME for GitHub Pages if PUBLISH_CNAME is set
if [ -n "${PUBLISH_CNAME:-}" ]; then
  echo "Writing CNAME: $PUBLISH_CNAME"
  echo "$PUBLISH_CNAME" > site/CNAME
fi

python3 scripts/check_links.py --base site || true

echo "Done. Artifacts under ./site ready for deploy."
