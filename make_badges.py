#!/usr/bin/env python3
"""
Badge layout: 9 badges (3 designs x3) on A4 LANDSCAPE at 300dpi
Horizontal gap ~22mm between badges; cut grey horizontal lines into strips first.
"""

from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import os

DPI = 300
CM  = DPI / 2.54

BADGE_CUT_CM     = 7.0
VISIBLE_CM       = 5.8
LOGO_OUTER_CM    = 5.6
LOGO_OUTER_RATIO = 0.90

BADGE_PX   = round(BADGE_CUT_CM * CM)           # 827 px
VISIBLE_PX = round(VISIBLE_CM * CM)             # 685 px
LOGO_PX    = round(LOGO_OUTER_CM * CM)          # 661 px
SRC_SCALE  = round(LOGO_PX / LOGO_OUTER_RATIO)  # 734 px

# A4 landscape: 297 x 210 mm → 3508 x 2480 px
A4_W, A4_H = 3508, 2480
COLS, ROWS = 3, 3   # 9 badges total

# Vertical: 3 x 827 = 2481 ≈ 2480 → rows fill height, no vertical gap
# Horizontal: distribute remaining width equally as gaps
MARGIN_Y = max(0, (A4_H - ROWS * BADGE_PX) // 2)
GAP_X    = (A4_W - COLS * BADGE_PX) // (COLS + 1)   # ~257 px ≈ 2.2 cm
MARGIN_X = GAP_X

BASE  = '/root/.claude/uploads/cd45970f-517c-49d9-88c1-163d42b92796'
PATHS = [
    os.path.join(BASE, '0b7e3a42-45493.jpg'),
    os.path.join(BASE, '84403272-45492.jpg'),
    os.path.join(BASE, 'e5ce541e-45491.jpg'),
]
NAMES   = ['badge_green_english', 'badge_beige_chinese', 'badge_gold_chinese']
OUT_DIR = '/home/user/photo-hymn-video/output'


def crop_to_square(img):
    w, h = img.size
    s = min(w, h)
    return img.crop(((w-s)//2, (h-s)//2, (w+s)//2, (h+s)//2))


def outpaint_bleed(img, target):
    src = img.size[0]
    if src >= target:
        off = (src - target) // 2
        return img.crop((off, off, off+target, off+target))
    pad   = (target - src) // 2
    pad_r = target - src - pad
    arr   = np.array(img)
    padded = np.pad(arr, ((pad, pad_r), (pad, pad_r), (0, 0)), mode='reflect')
    result = Image.fromarray(padded[:target, :target].astype(np.uint8))
    if pad > 4:
        blurred = result.filter(ImageFilter.GaussianBlur(radius=2))
        mask = Image.new('L', (target, target), 0)
        ImageDraw.Draw(mask).ellipse([pad+4, pad+4, target-pad-4, target-pad-4], fill=255)
        result = Image.composite(result, blurred, mask)
    return result


def make_badge(path):
    img = Image.open(path).convert('RGB')
    img = crop_to_square(img)
    img = img.resize((SRC_SCALE, SRC_SCALE), Image.LANCZOS)
    img = outpaint_bleed(img, BADGE_PX)
    aa = BADGE_PX * 2
    mask = Image.new('L', (aa, aa), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, aa-1, aa-1], fill=255)
    mask = mask.resize((BADGE_PX, BADGE_PX), Image.LANCZOS)
    result = img.convert('RGBA')
    result.putalpha(mask)
    return result


def build_layout(badges, out_dir, basename):
    a4   = Image.new('RGB', (A4_W, A4_H), (255, 255, 255))
    draw = ImageDraw.Draw(a4)

    for row in range(ROWS):
        for col in range(COLS):
            x = MARGIN_X + col * (BADGE_PX + GAP_X)
            y = MARGIN_Y + row * BADGE_PX
            a4.paste(badges[col], (x, y), badges[col])

            # grey circle = 5.8 cm visible-area guide
            cx, cy = x + BADGE_PX//2, y + BADGE_PX//2
            r = VISIBLE_PX // 2
            draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=(160, 160, 160), width=2)

    # horizontal strip-cut guides between rows
    for row in range(1, ROWS):
        gy = MARGIN_Y + row * BADGE_PX
        draw.line([(0, gy), (A4_W, gy)], fill=(200, 200, 200), width=3)

    png = os.path.join(out_dir, f'{basename}.png')
    pdf = os.path.join(out_dir, f'{basename}.pdf')
    a4.save(png, dpi=(DPI, DPI))
    a4.save(pdf, resolution=DPI)
    print(f'  ✓  {png}')
    print(f'  ✓  {pdf}')


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    print('Processing badges ...')
    badges = []
    for i, (path, name) in enumerate(zip(PATHS, NAMES)):
        print(f'  [{i+1}/3] {name}')
        badge = make_badge(path)
        preview = Image.new('RGB', (BADGE_PX, BADGE_PX), (255, 255, 255))
        preview.paste(badge, (0, 0), badge)
        preview.save(os.path.join(OUT_DIR, f'{name}.png'))
        badges.append(badge)

    print('\nBuilding A4 landscape layout (9 badges) ...')
    build_layout(badges, OUT_DIR, 'badge_layout_A4')

    print(f'\nDone.  A4 landscape @ {DPI} dpi  |  {COLS}x{ROWS} = {COLS*ROWS} badges')
    print(f'Badge cut Ø {BADGE_PX/CM:.1f} cm  |  H-gap ~{GAP_X/CM:.1f} cm  |  V-margin ~{MARGIN_Y/CM:.1f} cm')
    print('Cut: first cut along the grey horizontal lines (rows), then cut each circle.')


if __name__ == '__main__':
    main()
