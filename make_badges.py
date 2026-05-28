#!/usr/bin/env python3
"""
Badge layout: 9 badges, A4 portrait, HEX stagger (offset every other column).
Col 0 & 2: y = 3.5, 10.5, 17.5 cm
Col 1 (middle): y = 7, 14, 21 cm  (offset down by 3.5 cm)
Adjacent badges between columns: ~8 mm diagonal gap.
Cutting: slice along vertical lines x=7 cm and x=14 cm first (3 strips),
then cut each circle from its strip.
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
VISIBLE_PX = round(VISIBLE_CM   * CM)           # 685 px
LOGO_PX    = round(LOGO_OUTER_CM * CM)          # 661 px
SRC_SCALE  = round(LOGO_PX / LOGO_OUTER_RATIO)  # 734 px
HALF       = BADGE_PX // 2                       # 413 px

# A4 portrait
A4_W, A4_H = 2480, 3508

# Hex stagger positions (in px)
# 3 columns: x = 413, 1240, 2067 (centers)
COL_X = [HALF, A4_W // 2, A4_W - HALF]

# Col 0 & 2: y = 413, 1240, 2067
# Col 1:     y = 826, 1653, 2480  (shifted down by HALF)
COL_Y = [
    [HALF,        HALF + BADGE_PX,        HALF + 2 * BADGE_PX],
    [HALF + HALF, HALF + HALF + BADGE_PX, HALF + HALF + 2 * BADGE_PX],
    [HALF,        HALF + BADGE_PX,        HALF + 2 * BADGE_PX],
]

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

    # Place 9 badges in hex pattern: col 0→design 0, col 1→design 1, col 2→design 2
    for col in range(3):
        for row in range(3):
            cx = COL_X[col]
            cy = COL_Y[col][row]
            x  = cx - HALF
            y  = cy - HALF

            a4.paste(badges[col], (x, y), badges[col])

            # visible-area guide (5.8 cm)
            r = VISIBLE_PX // 2
            draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=(160, 160, 160), width=2)

    # Vertical cut guides at x = BADGE_PX and x = 2*BADGE_PX (7 cm and 14 cm)
    for vx in [BADGE_PX, 2 * BADGE_PX]:
        draw.line([(vx, 0), (vx, A4_H)], fill=(200, 200, 200), width=3)

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

    print('\nBuilding hex-stagger A4 layout (9 badges) ...')
    build_layout(badges, OUT_DIR, 'badge_layout_A4')

    import math
    gap_mm = (math.sqrt((COL_X[1]-COL_X[0])**2 + (COL_Y[1][0]-COL_Y[0][0])**2) - BADGE_PX) / CM * 10
    print(f'\nDone. A4 portrait @ {DPI} dpi | hex stagger 3×3 = 9 badges')
    print(f'Diagonal gap between adjacent badges: ~{gap_mm:.1f} mm')
    print('Cut: slice along the 2 grey vertical lines first (at 7 cm & 14 cm),')
    print('     then cut each circle from its strip.')


if __name__ == '__main__':
    main()
