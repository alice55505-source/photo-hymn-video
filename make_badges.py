#!/usr/bin/env python3
"""
Badge layout: 6 badges (3 English + 3 Chinese), A4 portrait 300dpi.
2 cols x 3 rows. Slot = 8 cm. Logo = 5.6 cm. Morandi palette.
"""

from PIL import Image, ImageDraw, ImageFilter, ImageOps
import numpy as np
import os

DPI = 300
CM  = DPI / 2.54

LOGO_CM  = 5.6
SLOT_CM  = 8.0

A4_W, A4_H = 2480, 3508
COLS, ROWS  = 2, 3

LOGO_PX = round(LOGO_CM * CM)   # 661 px
SLOT_PX = round(SLOT_CM * CM)   # 945 px

MARGIN_X = (A4_W - COLS * SLOT_PX) // 2
MARGIN_Y = (A4_H - ROWS * SLOT_PX) // 2

BASE  = '/root/.claude/uploads/cd45970f-517c-49d9-88c1-163d42b92796'
ENG   = os.path.join(BASE, '0b7e3a42-45493.jpg')
ZHO1  = os.path.join(BASE, '84403272-45492.jpg')
ZHO2  = os.path.join(BASE, 'e5ce541e-45491.jpg')
OUT_DIR = '/home/user/photo-hymn-video/output'

# 6 light Morandi colours — all pale/muted, fabric texture preserved via grayscale+colorize
MORANDI = [
    (225, 175, 165),  # coral pink       – English row 0
    (155, 175, 200),  # soft steel blue  – Chinese row 0
    (175, 198, 162),  # pale sage        – English row 1
    (225, 208, 185),  # warm sand        – Chinese row 1
    (193, 180, 213),  # pale lavender    – English row 2
    (220, 200, 178),  # warm beige       – Chinese row 2
]

# Each entry: (source_path, morandi_index)
# Layout order is row-major: [row0col0, row0col1, row1col0, ...]
BADGE_CONFIGS = [
    (ENG,  0),   # row0 left  – English, sage
    (ZHO1, 1),   # row0 right – Chinese, blue
    (ENG,  2),   # row1 left  – English, rose
    (ZHO2, 3),   # row1 right – Chinese, sand
    (ENG,  4),   # row2 left  – English, lavender
    (ZHO1, 5),   # row2 right – Chinese, mauve
]


def crop_to_square(img):
    w, h = img.size
    s = min(w, h)
    return img.crop(((w-s)//2, (h-s)//2, (w+s)//2, (h+s)//2))


def recolor(img_pil, tint_color):
    """Preserve fabric texture; remap dark tones → tint_color, bright → white."""
    gray = ImageOps.autocontrast(img_pil.convert('L'))
    return ImageOps.colorize(gray, black=tint_color, white=(255, 255, 255))


def make_badge(path, bg_color):
    img = Image.open(path).convert('RGB')
    img = crop_to_square(img)
    img = img.resize((LOGO_PX, LOGO_PX), Image.LANCZOS)
    img = recolor(img, bg_color)

    # Edge-extend to fill 8 cm slot (background is now flat Morandi colour → clean result)
    pad   = (SLOT_PX - LOGO_PX) // 2
    pad_r = SLOT_PX - LOGO_PX - pad
    arr   = np.array(img)
    padded = np.pad(arr, ((pad, pad_r), (pad, pad_r), (0, 0)), mode='edge')
    return Image.fromarray(padded.astype(np.uint8))


def build_layout(badges, out_dir, basename):
    a4 = Image.new('RGB', (A4_W, A4_H), (255, 255, 255))
    for i, badge in enumerate(badges):
        row = i // COLS
        col = i % COLS
        a4.paste(badge, (MARGIN_X + col * SLOT_PX, MARGIN_Y + row * SLOT_PX))

    png = os.path.join(out_dir, f'{basename}.png')
    pdf = os.path.join(out_dir, f'{basename}.pdf')
    a4.save(png, dpi=(DPI, DPI))
    a4.save(pdf, resolution=DPI)
    print(f'  ✓  {png}')
    print(f'  ✓  {pdf}')


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    colour_names = ['coral-pink', 'steel-blue', 'sage', 'sand', 'lavender', 'warm-beige']

    print('Processing badges ...')
    badges = []
    for i, (path, ci) in enumerate(BADGE_CONFIGS):
        lang = 'EN' if path == ENG else 'ZH'
        print(f'  [{i+1}/6] {lang}  {colour_names[ci]}  {MORANDI[ci]}')
        badge = make_badge(path, MORANDI[ci])
        badge.save(os.path.join(OUT_DIR, f'badge_{i+1}_{lang}_{colour_names[ci]}.png'))
        badges.append(badge)

    print('\nBuilding A4 layout ...')
    build_layout(badges, OUT_DIR, 'badge_layout_A4')
    print(f'\nDone.  {COLS}×{ROWS} = {COLS*ROWS} badges @ {DPI} dpi  |  slot {SLOT_CM} cm  logo {LOGO_CM} cm')


if __name__ == '__main__':
    main()
