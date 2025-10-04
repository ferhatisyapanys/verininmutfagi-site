#!/bin/bash
DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$DIR"
echo "Starting Analytics on http://127.0.0.1:8787 ..."
/usr/bin/env python3 "$DIR/scripts/analytics_server.py" --host 127.0.0.1 --port 8787 --db "$DIR/data/runtime/analytics.db"
