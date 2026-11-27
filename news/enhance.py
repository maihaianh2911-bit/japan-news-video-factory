"""Finer pictures (owner, 26/11/2026: "đẩy công cụ lên luôn, cho vào bước phù hợp"), each tool in its step:

- the picture search: `sharp()` says how crisp a picture is at the size the frame shows it. news/find.py writes
  it into index.json ("sharp") and on the contact sheet ("s27"); the preview warns of a soft first picture.
- the preview and the render, for a story with "fx": {"enhance": true}: `enhanced()` gives a dull picture its
  light back (`lit`) and enlarges a small one with Real-ESRGAN (`finer`), so that it is not blown up soft by the
  frame. A picture entry with "enhance": false is left as it is.

`sharp` and `lit` need Pillow only. `finer` needs numpy and onnxruntime (the libraries of the depth effect) and
the model beside this file, news/upscale_x4.onnx: realesr-general-x4v3 of github.com/xinntao/Real-ESRGAN
(BSD 3-Clause, its notice is news/upscale_x4.LICENSE), the small general model, rewritten to ONNX; 5–7 seconds a
picture on four cores. Without the libraries the picture is enlarged the plain way and a warning says so once.
"""
from functools import lru_cache
import math
from pathlib import Path

from PIL import Image, ImageFilter, ImageStat

MODEL = Path(__file__).with_name("upscale_x4.onnx")
SIDE = 540          # sharp(): the picture is measured with its shorter side at half the width of the frame
SOFT = 12           # sharp() under this: a soft picture (the softest twentieth of 388 found pictures)
SMALL = 1100        # finer(): a picture whose shorter side is under this is enlarged …
TARGET = 1600       # … to about this shorter side (four times at most),
LONGEST = 2600      # and to this longer side at most
STRETCH = 1.33      # lit(): a picture is stretched by a third at most
MIX = 0.6           # the share of the model in the result; the rest is the plain enlargement, which keeps the
                    # grain of skin (the model alone looked painted on faces: tried on press photos, 26/11/2026)
TILE, PAD = 192, 12
LAPLACE = ImageFilter.Kernel((3, 3), (0, 1, 0, 1, -4, 1, 0, 1, 0), scale=1, offset=128)
WARNED = []


def sharp(image):
    """How crisp a picture is at the size the frame shows it: about 5 (soft, blurred, a small picture blown up)
    to 60 and more (crisp and full of detail); under SOFT it is soft. It counts edges, so a plain studio portrait
    scores lower than a crowd: a hint to look closer, not a verdict."""
    grey = image.convert("L")
    scale = SIDE / min(grey.size)
    grey = grey.resize((max(SIDE, round(grey.width * scale)), max(SIDE, round(grey.height * scale))),
                       Image.Resampling.BICUBIC)
    left, top = (grey.width - SIDE) // 2, (grey.height - SIDE) // 2
    return min(99, round(ImageStat.Stat(grey.crop((left, top, left + SIDE, top + SIDE)).filter(LAPLACE)).stddev[0]))


def lit(image):
    """A dull picture gets its light back: its darkest and brightest half percent are moved most of the way to
    black and white (the picture is stretched by a third at most), and a dark picture is lifted a little. The
    three colours get the same curve, so the colours stay what they were. A picture that needs nothing comes back
    untouched."""
    histogram = image.convert("L").histogram()
    total = sum(histogram)

    def level(share):
        running = 0
        for value, count in enumerate(histogram):
            running += count
            if running >= total * share:
                return value
        return 255

    low, middle, high = level(0.005), level(0.5), level(0.995)
    if high - low < 48:   # one flat tone (a card, an empty page): stretching it would only show its noise
        return image
    black, white = low * 0.7, 255 - (255 - high) * 0.7
    if white - black < 255 / STRETCH:   # never stretched by more than a third: the window is widened around its middle
        centre = min(255 - 127.5 / STRETCH, max(127.5 / STRETCH, (black + white) / 2))
        black, white = centre - 127.5 / STRETCH, centre + 127.5 / STRETCH
    after = (middle - black) / max(1.0, white - black)
    gamma = 1.0
    if 0.02 < after < 0.36:   # a dark picture: its middle is lifted towards 0.40, gently
        gamma = max(0.82, math.log(0.40) / math.log(after))
    if black < 2 and white > 253 and gamma == 1.0:
        return image
    table = [round(255 * min(1.0, max(0.0, (value - black) / (white - black))) ** gamma) for value in range(256)]
    return image.point(table * len(image.getbands()))


@lru_cache(maxsize=1)
def session():
    import onnxruntime
    return onnxruntime.InferenceSession(str(MODEL), providers=["CPUExecutionProvider"])


def four_times(image):
    """The picture four times as large, by the model, tile by tile (each tile with a margin, so no seam shows)."""
    import numpy as np
    model = session()
    pixels = np.asarray(image.convert("RGB"), dtype=np.float32) / 255
    height, width, _ = pixels.shape
    large = np.zeros((height * 4, width * 4, 3), dtype=np.float32)
    for top in range(0, height, TILE):
        for left in range(0, width, TILE):
            y0, x0 = max(0, top - PAD), max(0, left - PAD)
            y1, x1 = min(height, top + TILE + PAD), min(width, left + TILE + PAD)
            tile = np.ascontiguousarray(pixels[y0:y1, x0:x1].transpose(2, 0, 1)[None])
            made = model.run(None, {"input": tile})[0][0].transpose(1, 2, 0)
            rows, columns = (min(height, top + TILE) - top) * 4, (min(width, left + TILE) - left) * 4
            large[top * 4:top * 4 + rows, left * 4:left * 4 + columns] = \
                made[(top - y0) * 4:(top - y0) * 4 + rows, (left - x0) * 4:(left - x0) * 4 + columns]
    return Image.fromarray((np.clip(large, 0, 1) * 255 + 0.5).astype(np.uint8))


def finer(image):
    """A small picture enlarged so that the frame does not blow it up soft: the model's picture mixed with the
    plain enlargement. A picture that is large enough comes back untouched."""
    factor = min(4.0, TARGET / min(image.size), LONGEST / max(image.size))
    if min(image.size) >= SMALL or factor < 1.15:
        return image
    size = (round(image.width * factor), round(image.height * factor))
    plain = image.resize(size, Image.Resampling.LANCZOS)
    try:
        return Image.blend(plain, four_times(image).resize(size, Image.Resampling.LANCZOS), MIX)
    except Exception as error:   # no numpy, no onnxruntime, no model: the plain enlargement, said once
        if not WARNED:
            print(f"warning: enhance effect off, small pictures are enlarged the plain way "
                  f"({type(error).__name__}: {str(error)[:120]})")
            WARNED.append(True)
        return plain


def enhanced(image):
    """The picture as a story with "fx": {"enhance": true} shows it: lit, and enlarged when it is small."""
    return finer(lit(image.convert("RGB")))
