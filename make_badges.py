#!/usr/bin/env python3
"""
Badge layout generator — 5.8cm circular badges on A4 at 300dpi
3 designs × 4 each = 12 badges, arranged in 3 cols × 4 rows
Badges are circular-masked (no square corners visible on page).
"""

from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import os

# ── Print constants ───────────────────────────────────────────────────────────
DPI = 300
CM = DPI / 2.54  # px per cm

# Badge press mechanics:
#   BADGE_CUT_CM  = full paper circle fed into the press (7 cm)
#   VISIBLE_CM    = embossed face visible on finished badge (5.8 cm)
#   LOGO_OUTER_CM = target outer logo ring diameter (≤ visible area)
BADGE_CUT_CM     = 7.0
VISIBLE_CM       = 5.8
LOGO_OUTER_CM    = 5.6
LOGO_OUTER_RATIO = 0.90   # outer ring ≈ 90 % of source image width

# 3 × 7 cm = 21 cm = exact A4 width → use A4_W//3 to avoid rounding overflow
A4_W, A4_H = 2480, 3508
COLS, ROWS  = 3, 4
BADGE_PX    = A4_W // COLS                               # 826 px ≈ 6.99 cm
VISIBLE_PX  = round(VISIBLE_CM  * CM)                   # 685 px
LOGO_PX     = round(LOGO_OUTER_CM * CM)                 # 661 px
SRC_SCALE   = round(LOGO_PX / LOGO_OUTER_RATIO)         # 734 px

MARGIN_X = (A4_W - COLS * BADGE_PX) // 2               # ≈ 1 px
MARGIN_Y = (A4_H - ROWS * BADGE_PX) // 2               # ≈ 100 px

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
    """Extend to target px with reflection padding for natural texture bleed."""
    src = img.size[0]
    if src >= target:
        off = (src - target) // 2
        return img.crop((off, off, off + target, off + target))

    pad   = (target - src) // 2
    pad_r = target - src - pad
    arr   = np.array(img)
    padded = np.pad(arr, ((pad, pad_r), (pad, pad_r), (0, 0)), mode='reflect')
    result = Image.fromarray(padded[:target, :target].astype(np.uint8))

    if pad > 4:
        blurred = result.filter(ImageFilter.GaussianBlur(radius=2))
        mask    = Image.new('L', (target, target), 0)
        dr      = ImageDraw.Draw(mask)
        inset   = pad + 4
        dr.ellipse([inset, inset, target - inset, target - inset], fill=255)
        result  = Image.composite(result, blurred, mask)

    return result


def make_circular_badge(path: str) -> Image.Image:
    """Return RGBA badge: circular at BADGE_PX, logo centered in VISIBLE_PX area."""
    img = Image.open(path).convert('RGB')
    img = crop_to_square(img)
    img = img.resize((SRC_SCALE, SRC_SCALE), Image.LANCZOS)
    img = outpaint_bleed(img, BADGE_PX)   # extend background to full 7 cm circle

    # Anti-aliased circular mask at BADGE_PX
    aa = BADGE_PX * 2
    circle_mask = Image.new('L', (aa, aa), 0)
    ImageDraw.Draw(circle_mask).ellipse([0, 0, aa - 1, aa - 1], fill=255)
    circle_mask = circle_mask.resize((BADGE_PX, BADGE_PX), Image.LANCZOS)

    result = img.convert('RGBA')
    result.putalpha(circle_mask)
    return result


def build_a4(badges: list, out_dir: str, basename: str):
    a4   = Image.new('RGB', (A4_W, A4_H), (255, 255, 255))
    draw = ImageDraw.Draw(a4)

    for row in range(ROWS):
        for col in range(COLS):
            design = col
            x = MARGIN_X + col * BADGE_PX
            y = MARGIN_Y + row * BADGE_PX

            badge = badges[design]
            a4.paste(badge, (x, y), badge)

            # dashed inner circle = 5.8 cm visible area boundary
            cx, cy = x + BADGE_PX // 2, y + BADGE_PX // 2
            r = VISIBLE_PX // 2
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
        badge = make_circular_badge(path)
        # Save preview with white background
        preview = Image.new('RGB', (BADGE_PX, BADGE_PX), (255, 255, 255))
        preview.paste(badge, (0, 0), badge)
        preview.save(os.path.join(OUT_DIR, f'{name}.png'))
        badges.append(badge)

    print('\nBuilding A4 layout …')
    build_a4(badges, OUT_DIR, 'badge_layout_A4')

    print('\nDone.')
    print(f'\nLayout:  A4 @ {DPI} dpi  |  {COLS}×{ROWS} = {COLS*ROWS} badges')
    print(f'Badge circle (paper cut) Ø {BADGE_PX/CM:.2f} cm  |  visible face Ø {VISIBLE_CM} cm  |  logo Ø ~{LOGO_OUTER_CM} cm')
    print(f'Margin L/R ≈ {MARGIN_X/CM:.2f} cm  |  T/B ≈ {MARGIN_Y/CM:.1f} cm')


if __name__ == '__main__':
    main()
