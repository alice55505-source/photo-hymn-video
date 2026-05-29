#!/usr/bin/env python3
"""
Badge layout: 6 badges (3 English + 3 Chinese), A4 portrait 300dpi.
2 cols x 3 rows. Slot = 8 cm. Logo = 5.6 cm. Morandi palette.
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

MARGIN_X = (A4_W - COLS * SLOT_PX) // 2
MARGIN_Y = (A4_H - ROWS * SLOT_PX) // 2

BASE  = '/root/.claude/uploads/cd45970f-517c-49d9-88c1-163d42b92796'
ENG   = os.path.join(BASE, '0b7e3a42-45493.jpg')
ZHO1  = os.path.join(BASE, '84403272-45492.jpg')
ZHO2  = os.path.join(BASE, 'e5ce541e-45491.jpg')
OUT_DIR = '/home/user/photo-hymn-video/output'

# 6 Morandi colours picked from the palette
# (3 for English column, 3 for Chinese column)
MORANDI = [
    (143, 155, 130),  # sage green       – English row 0
    (110, 128, 150),  # steel blue       – Chinese row 0
    (178, 150, 148),  # dusty rose       – English row 1
    (183, 166, 143),  # warm sand        – Chinese row 1
    (153, 140, 160),  # soft lavender    – English row 2
    (158, 135, 135),  # dusty mauve      – Chinese row 2
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


def otsu_thresh(gray_arr):
    hist = np.bincount(gray_arr.flatten(), minlength=256)
    total = gray_arr.size
    s1 = np.dot(np.arange(256, dtype=np.float64), hist)
    sb = 0.0; wb = 0; best = 0.0; t = 0
    for i in range(256):
        wb += hist[i]
        if wb == 0: continue
        wf = total - wb
        if wf == 0: break
        sb += i * hist[i]
        mb = sb / wb
        mf = (s1 - sb) / wf
        var = wb * wf * (mb - mf) ** 2
        if var >= best:
            best = var; t = i
    return t


def recolor(img_pil, bg_color):
    """Keep white logo; replace everything else with bg_color."""
    gray = np.array(img_pil.convert('L'))
    t = otsu_thresh(gray)

    # Soft logo mask: 1 = logo (bright), 0 = background
    mask = np.clip((gray.astype(np.float32) - t) / max(255 - t, 1), 0, 1)
    mask_smooth = np.array(
        Image.fromarray((mask * 255).astype(np.uint8))
            .filter(ImageFilter.GaussianBlur(radius=3))
    ) / 255.0

    bg = np.array(bg_color, dtype=np.float32)
    out = np.empty((gray.shape[0], gray.shape[1], 3), dtype=np.float32)
    for c in range(3):
        out[:, :, c] = 255.0 * mask_smooth + bg[c] * (1 - mask_smooth)
    return Image.fromarray(out.astype(np.uint8))


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
    colour_names = ['sage', 'steel-blue', 'rose', 'sand', 'lavender', 'mauve']

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
