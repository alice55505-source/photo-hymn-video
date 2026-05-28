#!/usr/bin/env python3
"""
Badge layout: 12 badges (3 designs x4), A4 portrait 300dpi.
3 cols x 4 rows. Circles are tangent (touching) but NOT overlapping.
Each circle exactly fills its SLOT_PX slot — no inset, no overlap.
"""

from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import os

DPI = 300
CM  = DPI / 2.54

VISIBLE_CM       = 5.8
LOGO_OUTER_CM    = 5.6
LOGO_OUTER_RATIO = 0.90

A4_W, A4_H = 2480, 3508
COLS, ROWS  = 3, 4

# Slot = A4_W // COLS so 3 slots fit exactly in A4 width with no overflow
SLOT_PX    = A4_W // COLS                           # 826 px ≈ 6.99 cm
VISIBLE_PX = round(VISIBLE_CM * CM)                 # 685 px
LOGO_PX    = round(LOGO_OUTER_CM * CM)              # 661 px
SRC_SCALE  = round(LOGO_PX / LOGO_OUTER_RATIO)      # 734 px

MARGIN_X = (A4_W - COLS * SLOT_PX) // 2            # 1 px
MARGIN_Y = (A4_H - ROWS * SLOT_PX) // 2            # 102 px

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
    """RGB image exactly SLOT_PX × SLOT_PX — no circular mask.
    Background fills the full square (corners included).
    The circular die cutter handles the actual cut."""
    img = Image.open(path).convert('RGB')
    img = crop_to_square(img)
    img = img.resize((SRC_SCALE, SRC_SCALE), Image.LANCZOS)
    img = outpaint_bleed(img, SLOT_PX)
    return img


def build_layout(badges, out_dir, basename):
    a4   = Image.new('RGB', (A4_W, A4_H), (255, 255, 255))
    draw = ImageDraw.Draw(a4)

    for row in range(ROWS):
        for col in range(COLS):
            x = MARGIN_X + col * SLOT_PX
            y = MARGIN_Y + row * SLOT_PX
            a4.paste(badges[col], (x, y))

            # Grey inner circle = 5.8 cm visible-area guide
            cx = x + SLOT_PX // 2
            cy = y + SLOT_PX // 2
            r  = VISIBLE_PX // 2
            draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=(170, 170, 170), width=2)

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
        badge.save(os.path.join(OUT_DIR, f'{name}.png'))
        badges.append(badge)

    print('\nBuilding A4 layout (12 badges) ...')
    build_layout(badges, OUT_DIR, 'badge_layout_A4')

    print(f'\nDone.  A4 portrait @ {DPI} dpi  |  {COLS}x{ROWS} = {COLS*ROWS} badges')
    print(f'Circle Ø {(SLOT_PX-2)/CM:.2f} cm  |  tangent (no overlap, no gap)')
    print(f'Visible area guide: {VISIBLE_CM} cm (grey circle)')


if __name__ == '__main__':
    main()
