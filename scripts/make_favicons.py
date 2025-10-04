#!/usr/bin/env python3
"""
Generate favicon set (ico + png sizes + apple-touch-icon) from a source logo image.

Usage:
  python3 scripts/make_favicons.py --src path/to/logo.png [--tight 0.8]

This will:
  - crop a vertical slice from the left (width = tight * height), centered on a square canvas
  - write outputs under site/:
      favicon.ico, favicon-16x16.png, favicon-32x32.png, apple-touch-icon.png
      plus helper images: favicon-48x48.png, favicon-64x64.png, favicon-256.png, android-chrome-512x512.png
"""
import argparse
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'site'

def make_set(src: Path, tight: float):
    im = Image.open(src).convert('RGBA')
    w, h = im.size
    size = h
    crop_w = int(size * tight)
    if crop_w < 1:
        crop_w = 1
    # Crop from very left edge, full height
    box = (0, 0, min(crop_w, w), size)
    crop = im.crop(box)
    # Place into a square RGBA canvas centered horizontally
    sq = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    x = max(0, int((size - crop.width) / 2))
    sq.paste(crop, (x, 0))
    # Write variants
    (ROOT / 'site' / 'assets' / 'img' / 'favicon.png').write_bytes(b'')  # ensure folder exists
    sq.save(OUT / 'assets' / 'img' / 'favicon.png')
    for s in (16, 32, 48, 64, 180, 256, 512):
        imr = sq.resize((s, s), Image.LANCZOS)
        if s in (16, 32, 48, 64):
            imr.save(OUT / f'favicon-{s}x{s}.png')
        if s == 180:
            imr.save(OUT / 'apple-touch-icon.png')
        if s == 256:
            imr.save(OUT / 'favicon-256.png')
        if s == 512:
            imr.save(OUT / 'android-chrome-512x512.png')
    sq.resize((64, 64), Image.LANCZOS).save(OUT / 'favicon.ico')
    print('Favicons written to', OUT)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True, help='Path to source logo image')
    ap.add_argument('--tight', type=float, default=0.8, help='Crop width as fraction of height (default 0.8)')
    args = ap.parse_args()
    make_set(Path(args.src), args.tight)

if __name__ == '__main__':
    main()

