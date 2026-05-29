#!/usr/bin/env python3
"""
Badge layout: 6 badges, A4 portrait 300dpi.
2 cols x 3 rows. Slot = 8 cm. Logo = 5.6 cm.
Left col = English (3), Right col = Chinese (3).
5 original images + 1 purple recolour.
"""

from PIL import Image, ImageOps
import numpy as np
import os

DPI = 300
CM  = DPI / 2.54

LOGO_CM = 5.6
SLOT_CM = 8.0

A4_W, A4_H = 2480, 3508
COLS, ROWS  = 2, 3

LOGO_PX = round(LOGO_CM * CM)   # 661 px
SLOT_PX = round(SLOT_CM * CM)   # 945 px

MARGIN_X = (A4_W - COLS * SLOT_PX) // 2
MARGIN_Y = (A4_H - ROWS * SLOT_PX) // 2

BASE1 = '/root/.claude/uploads/cd45970f-517c-49d9-88c1-163d42b92796'
BASE2 = '/root/.claude/uploads/22097788-396a-4cb3-801d-b4c10d483403'

ENG_GREEN  = os.path.join(BASE1, '0b7e3a42-45493.jpg')   # English green original
ZHO_BEIGE  = os.path.join(BASE1, '84403272-45492.jpg')   # Chinese beige original
ZHO_GOLD   = os.path.join(BASE1, 'e5ce541e-45491.jpg')   # Chinese gold original
ZHO_BLUE   = os.path.join(BASE2, 'c8bfde1b-45527.jpg')   # Chinese blue (new)
ENG_PINK   = os.path.join(BASE2, '7c45659f-45528.jpg')   # English pink (new)

OUT_DIR = '/home/user/photo-hymn-video/output'

PURPLE = (185, 165, 205)   # Morandi muted purple

# 6 badge configs: (source_path, tint or None)
# None = use original image as-is
# Layout: row-major, left col = English, right col = Chinese
BADGE_CONFIGS = [
    (ENG_GREEN, None),    # row0 left  – English green (original)
    (ZHO_BEIGE, None),    # row0 right – Chinese beige (original)
    (ENG_PINK,  None),    # row1 left  – English pink (original)
    (ZHO_GOLD,  None),    # row1 right – Chinese gold (original)
    (ENG_GREEN, PURPLE),  # row2 left  – English purple (recoloured)
    (ZHO_BLUE,  None),    # row2 right – Chinese blue (original)
]
LABELS = [
    'EN-green', 'ZH-beige', 'EN-pink', 'ZH-gold', 'EN-purple', 'ZH-blue'
]


def crop_to_square(img):
    w, h = img.size
    s = min(w, h)
    return img.crop(((w-s)//2, (h-s)//2, (w+s)//2, (h+s)//2))


def recolor(img_pil, tint):
    """Grayscale + colorize: preserves fabric texture, applies new colour tint."""
    gray = ImageOps.autocontrast(img_pil.convert('L'))
    return ImageOps.colorize(gray, black=tint, white=(255, 255, 255))


def make_badge(path, tint=None):
    img = Image.open(path).convert('RGB')
    img = crop_to_square(img)
    img = img.resize((LOGO_PX, LOGO_PX), Image.LANCZOS)
    if tint is not None:
        img = recolor(img, tint)

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

    print('Processing badges ...')
    badges = []
    for i, (path, tint) in enumerate(BADGE_CONFIGS):
        note = f'tint={tint}' if tint else 'original'
        print(f'  [{i+1}/6] {LABELS[i]}  ({note})')
        badge = make_badge(path, tint)
        badge.save(os.path.join(OUT_DIR, f'badge_{i+1}_{LABELS[i]}.png'))
        badges.append(badge)

    print('\nBuilding A4 layout ...')
    build_layout(badges, OUT_DIR, 'badge_layout_A4')
    print(f'\nDone.  {COLS}×{ROWS} = {COLS*ROWS} badges @ {DPI} dpi  |  slot {SLOT_CM} cm  logo {LOGO_CM} cm')


if __name__ == '__main__':
    main()
