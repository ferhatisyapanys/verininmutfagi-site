#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Load API key from .env if present
if [ -f .env ]; then
  export YT_API_KEY="$(sed -n 's/^YT_API_KEY=//p' .env)"
fi

echo "Refreshing YouTube videos (handle=@verininmutfagi, max=30)..."
python3 scripts/fetch_youtube.py --handle @verininmutfagi --max 30 ${YT_API_KEY:+--api-key "$YT_API_KEY"}

# Sync inline JSON for file:// usage
python3 - "$@" << 'PY'
import json, pathlib, re
p = pathlib.Path('site/youtube/index.html')
vids = json.loads(pathlib.Path('site/youtube/videos.json').read_text(encoding='utf-8'))
s = p.read_text(encoding='utf-8')
new_json = json.dumps(vids, ensure_ascii=False)
s = re.sub(r'<script id="vm-yt-videos"[^>]*>[\s\S]*?</script>',
           f'<script id="vm-yt-videos" type="application/json">{new_json}</script>', s)
p.write_text(s, encoding='utf-8')
print(f"YouTube inline JSON updated ({len(vids)} items)")
PY

echo "Done."

