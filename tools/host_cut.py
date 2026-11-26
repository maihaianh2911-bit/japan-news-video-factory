"""Cut the narrator's poses out of character sheets drawn on a green background, make the green transparent and
size them alike, for the narrator of the "band" frame (news/render.py, "host").

Usage: python tools/host_cut.py <name> <sheet.png>:<pose>,<pose>,... [<sheet.png>:<pose>,...]
  The poses of a sheet are its figures from left to right; the names are those of render.HOST_POSES
  (neutral, talk, point, cross, present, surprised). Writes stories/media/host/<name>/<pose>.png and sheet.jpg.
  e.g. python tools/host_cut.py samurai a.png:neutral,talk,point,cross b.png:present,surprised
All the figures are scaled so that their heads (the top fifth of each figure) are the same width, and placed on
one canvas size with the head at the same place, so that switching poses (and the mouth) does not make them jump.
"""
from pathlib import Path
import sys

from PIL import Image, ImageFilter

CANVAS = (900, 1120)   # width, height of every pose
HEAD_TOP, HEAD_WIDTH = 40, 420   # where the top of the head (helmet) stands, and how wide the head is


def key_green(image):
    """Green (the chroma background) becomes transparent; the green tint on the edges is taken off."""
    rgb = image.convert("RGB")
    pixels = rgb.load()
    alpha = Image.new("L", rgb.size, 255)
    mask = alpha.load()
    for y in range(rgb.height):
        for x in range(rgb.width):
            r, g, b = pixels[x, y]
            other = max(r, b)
            if g > 90 and g > other * 1.35:
                excess = (g - other) / max(1, g)
                mask[x, y] = 0 if excess > 0.45 else round(255 * (1 - excess / 0.45))
                pixels[x, y] = (r, min(g, other + 10), b)
    alpha = alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.7))
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    return out


def figures(image, count):
    """The `count` figures of a sheet, left to right: split where the columns are empty."""
    alpha = image.getchannel("A")
    width, height = image.size
    filled = [sum(1 for y in range(0, height, 4) if alpha.getpixel((x, y)) > 128) for x in range(width)]
    runs, start = [], None
    for x, value in enumerate(filled + [0]):
        if value > 2 and start is None:
            start = x
        elif value <= 2 and start is not None:
            if x - start > 40:
                runs.append((start, x))
            start = None
    while len(runs) > count:   # join the two closest runs (an arm apart from its body)
        gaps = [runs[i + 1][0] - runs[i][1] for i in range(len(runs) - 1)]
        i = gaps.index(min(gaps))
        runs[i:i + 2] = [(runs[i][0], runs[i + 1][1])]
    if len(runs) != count:   # figures that touch: cut at the emptiest column near each equal share
        cuts = [0]
        for i in range(1, count):
            guess = round(width * i / count)
            near = range(max(1, guess - 90), min(width - 1, guess + 90))
            cuts.append(min(near, key=lambda x: filled[x]))
        cuts.append(width)
        runs = list(zip(cuts[:-1], cuts[1:]))
    return [image.crop((left, 0, right, height)).crop(image.crop((left, 0, right, height)).getbbox()) for left, right in runs]


def head_box(figure):
    """Left and right of the head: the widest part of the top fifth of the figure."""
    alpha = figure.getchannel("A")
    band = alpha.crop((0, 0, figure.width, max(1, figure.height // 5)))
    box = band.getbbox() or (0, 0, figure.width, 1)
    return box[0], box[2]


def main():
    name, specs = sys.argv[1], sys.argv[2:]
    out = Path("stories/media/host") / name
    out.mkdir(parents=True, exist_ok=True)
    made = []
    for spec in specs:
        path, poses = spec.split(":")
        poses = poses.split(",")
        sheet = key_green(Image.open(path))
        for pose, figure in zip(poses, figures(sheet, len(poses))):
            left, right = head_box(figure)
            scale = HEAD_WIDTH / max(1, right - left)
            figure = figure.resize((round(figure.width * scale), round(figure.height * scale)), Image.Resampling.LANCZOS)
            centre = (left + right) / 2 * scale
            canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
            canvas.paste(figure, (round(CANVAS[0] / 2 - centre), HEAD_TOP), figure)
            canvas.save(out / f"{pose}.png")
            made.append((pose, canvas))
            print(f"{pose}: {out / (pose + '.png')}")
    preview = Image.new("RGB", (CANVAS[0] * len(made) // 3, CANVAS[1] // 3), "#204060")
    for index, (pose, canvas) in enumerate(made):
        small = canvas.resize((CANVAS[0] // 3, CANVAS[1] // 3))
        preview.paste(small, (index * CANVAS[0] // 3, 0), small)
    preview.save(out / "sheet.jpg", quality=85)


if __name__ == "__main__":
    main()
