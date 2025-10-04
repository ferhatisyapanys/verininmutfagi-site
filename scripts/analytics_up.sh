#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$DIR"
echo "Building analytics container..."
docker compose -f docker/docker-compose.analytics.yml build
echo "Starting analytics container on http://localhost:8787 ..."
docker compose -f docker/docker-compose.analytics.yml up -d
docker ps --filter name=vm-analytics
