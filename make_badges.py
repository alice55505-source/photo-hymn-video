#!/usr/bin/env python3
"""
Badge layout generator — 5.8cm circular badges on A4 at 300dpi
3 designs × 4 each = 12 badges, arranged in 3 cols × 4 rows
"""

from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import os

# ── Print constants ───────────────────────────────────────────────────────────
DPI = 300
CM = DPI / 2.54  # px per cm

# The outer circular logo in each source image fills ~90% of the image width.
# We scale the source so that outer circle = 5.6 cm (safely inside the 5.8 cut line).
LOGO_OUTER_RATIO = 0.90   # outer ring ≈ 90 % of image side
LOGO_OUTER_CM    = 5.6    # keep outer ring at this diameter
CUT_CM           = 5.8    # final badge cut line
BLEED_CM         = 6.4    # cut + 3 mm bleed each side

LOGO_OUTER_PX = round(LOGO_OUTER_CM * CM)   # 661 px
CUT_PX        = round(CUT_CM        * CM)   # 685 px
BLEED_PX      = round(BLEED_CM      * CM)   # 756 px
SRC_SCALE     = round(LOGO_OUTER_PX / LOGO_OUTER_RATIO)  # ≈ 735 px

# ── A4 layout ─────────────────────────────────────────────────────────────────
A4_W, A4_H = 2480, 3508   # A4 @ 300 dpi
COLS, ROWS  = 3, 4
GAP_PX      = 24           # 2 mm gap between badges

# centred margins
TOTAL_W = COLS * BLEED_PX + (COLS - 1) * GAP_PX
TOTAL_H = ROWS * BLEED_PX + (ROWS - 1) * GAP_PX
MARGIN_X = (A4_W - TOTAL_W) // 2
MARGIN_Y = (A4_H - TOTAL_H) // 2

# ── Source images ─────────────────────────────────────────────────────────────
BASE  = '/root/.claude/uploads/cd45970f-517c-49d9-88c1-163d42b92796'
PATHS = [
    os.path.join(BASE, '0b7e3a42-45493.jpg'),   # green  – English
    os.path.join(BASE, '84403272-45492.jpg'),   # beige  – Chinese
    os.path.join(BASE, 'e5ce541e-45491.jpg'),   # gold   – Chinese
]
NAMES = ['badge_green_english', 'badge_beige_chinese', 'badge_gold_chinese']

OUT_DIR = '/home/user/photo-hymn-video/output'


# ── Helpers ───────────────────────────────────────────────────────────────────

def crop_to_square(img: Image.Image) -> Image.Image:
    w, h = img.size
    s = min(w, h)
    return img.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2))


def outpaint_bleed(img: Image.Image, target: int) -> Image.Image:
    """
    Extend a square image to `target` px using reflection padding so
    the background texture flows naturally into the bleed area.
    """
    src = img.size[0]
    if src >= target:
        off = (src - target) // 2
        return img.crop((off, off, off + target, off + target))

    pad   = (target - src) // 2
    pad_r = target - src - pad
    arr   = np.array(img)

    # reflect-mode padding replicates the edge texture
    padded = np.pad(arr, ((pad, pad_r), (pad, pad_r), (0, 0)), mode='reflect')
    result = Image.fromarray(padded[:target, :target].astype(np.uint8))

    # soften only the narrow extension strip (not the original logo)
    if pad > 4:
        blurred = result.filter(ImageFilter.GaussianBlur(radius=2))
        mask    = Image.new('L', (target, target), 0)
        dr      = ImageDraw.Draw(mask)
        inset   = pad + 4
        dr.ellipse([inset, inset, target - inset, target - inset], fill=255)
        result  = Image.composite(result, blurred, mask)

    return result


def make_badge(path: str) -> Image.Image:
    img = Image.open(path).convert('RGB')
    img = crop_to_square(img)
    img = img.resize((SRC_SCALE, SRC_SCALE), Image.LANCZOS)
    img = outpaint_bleed(img, BLEED_PX)
    return img


def build_a4(badges: list, out_dir: str, basename: str):
    a4   = Image.new('RGB', (A4_W, A4_H), (255, 255, 255))
    draw = ImageDraw.Draw(a4)

    for row in range(ROWS):
        for col in range(COLS):
            design = col   # 3 designs, one per column, repeated 4 rows
            x = MARGIN_X + col * (BLEED_PX + GAP_PX)
            y = MARGIN_Y + row * (BLEED_PX + GAP_PX)
            a4.paste(badges[design], (x, y))

            # thin grey cut-guide circle at the 5.8 cm cut line
            cx, cy = x + BLEED_PX // 2, y + BLEED_PX // 2
            r = CUT_PX // 2
            draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                         outline=(160, 160, 160), width=2)

    png = os.path.join(out_dir, f'{basename}.png')
    pdf = os.path.join(out_dir, f'{basename}.pdf')
    a4.save(png, dpi=(DPI, DPI))
    a4.save(pdf, resolution=DPI)
    print(f'  ✓  {png}')
    print(f'  ✓  {pdf}')


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    print('Processing badges …')
    badges = []
    for i, (path, name) in enumerate(zip(PATHS, NAMES)):
        print(f'  [{i+1}/3] {name}')
        badge = make_badge(path)
        preview_path = os.path.join(OUT_DIR, f'{name}.png')
        badge.save(preview_path)
        badges.append(badge)

    print('\nBuilding A4 layout …')
    build_a4(badges, OUT_DIR, 'badge_layout_A4')

    print('\nDone.')
    print(f'Files saved to: {OUT_DIR}')
    print(f'\nLayout summary:')
    print(f'  • A4 @ {DPI} dpi  ({A4_W} × {A4_H} px)')
    print(f'  • {COLS} cols × {ROWS} rows = {COLS*ROWS} badges')
    print(f'  • Badge bleed Ø {BLEED_CM} cm  |  cut line Ø {CUT_CM} cm')
    print(f'  • Logo outer circle Ø ~{LOGO_OUTER_CM} cm')
    print(f'  • Margin L/R ≈ {MARGIN_X/CM:.1f} cm  |  T/B ≈ {MARGIN_Y/CM:.1f} cm')
    print(f'  • Gap between badges ≈ {GAP_PX/CM:.1f} cm')


if __name__ == '__main__':
    main()
