#!/bin/bash
DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$DIR"
read -p "Google Docs URL: " URL
if [ -z "$URL" ]; then echo "URL zorunlu"; exit 1; fi
/usr/bin/env python3 "$DIR/scripts/gdoc_to_bulten.py" --url "$URL" --auto-week-title || exit 1
/usr/bin/env python3 "$DIR/scripts/build_bulten.py" || exit 1
echo "Bitti. Arşiv: $DIR/site/bultenler/index.html"
exit 0

