#!/usr/bin/env python3
"""
Badge layout: 6 badges (3 designs x2), A4 portrait 300dpi.
2 cols x 3 rows. Slot = 8 cm. Logo = 5.6 cm centred, edge-extended to fill slot.
"""

from PIL import Image, ImageDraw, ImageFilter
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

MARGIN_X = (A4_W - COLS * SLOT_PX) // 2   # 295 px ≈ 2.5 cm
MARGIN_Y = (A4_H - ROWS * SLOT_PX) // 2   # 336 px ≈ 2.8 cm

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


def make_badge(path):
    """Logo at LOGO_PX (5.6 cm) centred on SLOT_PX (8 cm) canvas.
    Outer band filled by repeating edge pixels outward."""
    img = Image.open(path).convert('RGB')
    img = crop_to_square(img)
    img = img.resize((LOGO_PX, LOGO_PX), Image.LANCZOS)

    pad   = (SLOT_PX - LOGO_PX) // 2
    pad_r = SLOT_PX - LOGO_PX - pad
    arr    = np.array(img)
    padded = np.pad(arr, ((pad, pad_r), (pad, pad_r), (0, 0)), mode='edge')
    return Image.fromarray(padded.astype(np.uint8))


def build_layout(badges, out_dir, basename):
    a4 = Image.new('RGB', (A4_W, A4_H), (255, 255, 255))

    for row in range(ROWS):
        for col in range(COLS):
            x = MARGIN_X + col * SLOT_PX
            y = MARGIN_Y + row * SLOT_PX
            idx = (row * COLS + col) % len(badges)
            a4.paste(badges[idx], (x, y))

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

    print('\nBuilding A4 layout (6 badges) ...')
    build_layout(badges, OUT_DIR, 'badge_layout_A4')

    print(f'\nDone.  A4 portrait @ {DPI} dpi  |  {COLS}x{ROWS} = {COLS*ROWS} badges')
    print(f'Slot {SLOT_CM} cm  |  Logo {LOGO_CM} cm  |  Margin X {MARGIN_X/CM:.1f} cm  Y {MARGIN_Y/CM:.1f} cm')


if __name__ == '__main__':
    main()
