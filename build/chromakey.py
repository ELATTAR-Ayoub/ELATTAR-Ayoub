"""Chroma-key a Gemini green-screen render to a transparent PNG.

Gemini cannot emit alpha, so the documented workaround is to render on flat
green and key it out here. Also despills the green fringe that survives on
soft edges (petals, ribbon tips), which is what makes a naive threshold key
look like a sticker.
"""
import sys
import numpy as np
from PIL import Image, ImageFilter


def key(src, dst, width=None, lo=0.06, hi=0.30, pad=6):
    im = Image.open(src).convert("RGB")
    a = np.asarray(im).astype(np.float32) / 255.0
    R, G, B = a[..., 0], a[..., 1], a[..., 2]

    # greenness: how far G sits above the strongest of the other two channels
    other = np.maximum(R, B)
    greenness = G - other

    # soft matte -- linear ramp between lo and hi keeps petal edges feathered
    alpha = np.clip((hi - greenness) / (hi - lo), 0.0, 1.0)

    # despill: pull G down to the neutral of R/B wherever it still dominates
    spill = G > other
    G = np.where(spill, np.minimum(G, (R + B) * 0.5 + 0.02), G)

    rgb = np.stack([R, G, B], axis=-1)
    out = np.concatenate([rgb, alpha[..., None]], axis=-1)
    out = (np.clip(out, 0, 1) * 255).astype(np.uint8)
    img = Image.fromarray(out, "RGBA")

    # slight alpha blur softens the key edge without eating the artwork
    r, g, b, al = img.split()
    al = al.filter(ImageFilter.GaussianBlur(0.6))
    img = Image.merge("RGBA", (r, g, b, al))

    bbox = img.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    if bbox:
        x0, y0, x1, y1 = bbox
        x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
        x1, y1 = min(img.width, x1 + pad), min(img.height, y1 + pad)
        img = img.crop((x0, y0, x1, y1))

    if width:
        h = max(1, round(width * img.height / img.width))
        img = img.resize((width, h), Image.LANCZOS)

    img.save(dst, optimize=True)
    op = np.asarray(img)[..., 3]
    print(f"{dst}  {img.size}  opaque={round(100 * float((op > 250).mean()), 1)}%  "
          f"clear={round(100 * float((op < 5).mean()), 1)}%")


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    w = int(sys.argv[3]) if len(sys.argv) > 3 else None
    key(src, dst, w)
