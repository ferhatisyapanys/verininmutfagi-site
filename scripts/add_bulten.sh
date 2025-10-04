#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

URL="${1:-}"
if [ -z "$URL" ]; then
  echo "Lütfen Google Docs linkini girin:" >&2
  read -r URL
fi
if [ -z "$URL" ]; then
  echo "Hata: URL girilmedi" >&2
  exit 1
fi

echo "[1/2] Google Docs içeriği alınıyor…"
python3 "$ROOT/scripts/gdoc_to_bulten.py" --url "$URL" --auto-week-title || {
  echo "Google Docs içeriği alınamadı." >&2; exit 1; }

echo "[2/2] Bülten sayfaları oluşturuluyor…"
python3 "$ROOT/scripts/build_bulten.py"

echo "Bitti. Arşiv: $ROOT/site/bultenler/index.html"
echo "İsterseniz: open \"$ROOT/site/bultenler/index.html\""

