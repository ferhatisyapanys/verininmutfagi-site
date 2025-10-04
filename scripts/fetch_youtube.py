#!/usr/bin/env python3
"""
Fetch latest YouTube videos for a channel and write site/youtube/videos.json.

Usage examples:
  python3 scripts/fetch_youtube.py --api-key YOUR_KEY --handle @verininmutfagi --max 30
  python3 scripts/fetch_youtube.py --api-key YOUR_KEY --channel-id UCxxxxxxxx --max 30

This only writes a static JSON; the API key is NOT exposed to the frontend.
"""
import argparse
import os
import json
import sys
import urllib.parse
import urllib.request
import ssl
from pathlib import Path
import re

API_BASE = "https://www.googleapis.com/youtube/v3"


def http_get(url, params):
    q = urllib.parse.urlencode(params)
    full = f"{url}?{q}"
    # Some local environments lack root CAs; allow unverified SSL as a fallback.
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(full, context=ctx) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        unverified = ssl._create_unverified_context()
        with urllib.request.urlopen(full, context=unverified) as r:
            return json.loads(r.read().decode("utf-8"))

def http_get_text(url):
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, context=ctx) as r:
            return r.read().decode('utf-8', errors='ignore')
    except Exception:
        unverified = ssl._create_unverified_context()
        with urllib.request.urlopen(req, context=unverified) as r:
            return r.read().decode('utf-8', errors='ignore')


def resolve_channel_id_by_handle(api_key: str, handle: str) -> str:
    # YouTube Data API supports forHandle to resolve handle to channel resource
    # https://developers.google.com/youtube/v3/docs/channels/list
    data = http_get(
        f"{API_BASE}/channels",
        {"part": "id", "forHandle": handle.lstrip("@"), "key": api_key},
    )
    items = data.get("items", [])
    if not items:
        raise SystemExit(f"No channel found for handle: {handle}")
    return items[0]["id"]


def get_uploads_playlist_id(api_key: str, channel_id: str) -> str:
    data = http_get(
        f"{API_BASE}/channels",
        {"part": "contentDetails", "id": channel_id, "key": api_key},
    )
    items = data.get("items", [])
    if not items:
        raise SystemExit(f"No channel contentDetails for: {channel_id}")
    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]


def fetch_latest_videos(api_key: str, uploads_playlist_id: str, max_items: int):
    out = []
    page_token = None
    remaining = max_items
    while remaining > 0:
        params = {
            "part": "snippet",
            "playlistId": uploads_playlist_id,
            "maxResults": min(50, remaining),
            "key": api_key,
        }
        if page_token:
            params["pageToken"] = page_token
        data = http_get(f"{API_BASE}/playlistItems", params)
        for it in data.get("items", []):
            sn = it.get("snippet", {})
            rid = sn.get("resourceId", {}).get("videoId")
            if not rid:
                continue
            out.append({
                "id": rid,
                "title": sn.get("title", ""),
                "published": sn.get("publishedAt", ""),
            })
            remaining -= 1
            if remaining <= 0:
                break
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    # Include all videos (do not filter out Shorts) to reflect channel grid order
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--api-key", required=False, help="YouTube Data API key (or set YT_API_KEY env)")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--handle")
    g.add_argument("--channel-id")
    p.add_argument("--max", type=int, default=30)
    args = p.parse_args()

    api_key = args.api_key or os.environ.get("YT_API_KEY")
    videos = []
    if api_key:
        # Preferred: official API
        if args.handle:
            channel_id = resolve_channel_id_by_handle(api_key, args.handle)
        else:
            channel_id = args.channel_id
        uploads = get_uploads_playlist_id(api_key, channel_id)
        videos = fetch_latest_videos(api_key, uploads, args.max)
    else:
        # Fallback: public RSS feed (no API key)
        chan_id = args.channel_id
        if chan_id:
            # RSS by channel id
            feed = http_get_text(f"https://www.youtube.com/feeds/videos.xml?channel_id={chan_id}")
            items = re.findall(r"<entry>([\s\S]*?)</entry>", feed)
            out = []
            for it in items:
                idm = re.search(r"<yt:videoId>([^<]+)</yt:videoId>", it)
                tm = re.search(r"<published>([^<]+)</published>", it)
                tt = re.search(r"<title>([^<]+)</title>", it)
                if not idm:
                    continue
                out.append({
                    "id": idm.group(1),
                    "title": (tt.group(1) if tt else "YouTube Video"),
                    "published": (tm.group(1) if tm else "")
                })
            out.sort(key=lambda x: x.get('published',''), reverse=True)
            videos = out[:args.max]
        elif args.handle:
            # Scrape /videos page and extract videoIds in order (newest first visually)
            html = http_get_text(f"https://www.youtube.com/@{args.handle.lstrip('@')}/videos")
            ids = re.findall(r'"videoId":"([A-Za-z0-9_-]{11})"', html)
            # De-duplicate preserving order
            seen = set(); ordered = []
            for vid in ids:
                if vid in seen: continue
                seen.add(vid); ordered.append(vid)
                if len(ordered) >= args.max: break
            # Extract simple titles if possible
            titles = {}
            for m in re.finditer(r'"title":\{"runs":\[\{\"text\":\"([^\"]+)\"\}\]', html):
                t = m.group(1)
                titles.setdefault(t, t)
            # Build with synthetic published to preserve order
            import datetime
            now = datetime.datetime.utcnow()
            out = []
            for i, vid in enumerate(ordered):
                # Spread by seconds to keep order new->old
                pub = (now - datetime.timedelta(seconds=i)).isoformat() + 'Z'
                out.append({
                    'id': vid,
                    'title': titles.get(i, 'YouTube Video') if False else 'YouTube Video',
                    'published': pub,
                })
            videos = out
        else:
            raise SystemExit("Provide --channel-id or --handle")

    # Write to site/youtube/videos.json
    root = Path(__file__).resolve().parents[1]
    out_path = root / "site" / "youtube" / "videos.json"
    out_path.write_text(json.dumps(videos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(videos)} videos to {out_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
