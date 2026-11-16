"""Trial (owner, 16/11/2026): the first seconds of a finished video again, with four new effects.

1. 3D camera: the picture moves in depth (near things move more than far ones), from a depth map (tools/fx/prep.py;
   the idea of github.com/sniklaus/3d-ken-burns, done on the CPU with a displacement warp).
2. Sharper pictures: Real-ESRGAN copies made by tools/fx/prep.py (no face redrawing).
3. Captions that follow the voice phrase by phrase (the idea of pycaps / captacity, drawn by us for Japanese).
4. Transitions ported from github.com/gl-transitions/gl-transitions (MIT): DirectionalWarp, CrossZoom, FilmBurn,
   InkBleed.

The voice, the music and the caption times come from the finished video, so the sample compares directly with it.

    python tools/fx/sample.py <story.json> <find folder> <prep folder> <old video.mp4> <old subtitles.srt> <out> [seconds]
"""
from dataclasses import replace
import math
from pathlib import Path
import re
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from news import render as R                     # noqa: E402
from news.custom import load_story, read         # noqa: E402
from news.voice import Caption                   # noqa: E402

W, H, FPS = R.W, R.H, R.FPS


# ---------------------------------------------------------------- 1. the picture in depth

class Deep:
    """A picture with its depth map, shown through a camera that moves in space."""

    def __init__(self, photo, depth, height, closest=1.5):
        image = photo.image
        self.size = image.size
        self.fill = max(W / image.width, height / image.height)
        self.k = min(1.0, self.fill * closest)       # never keep more pixels than the closest view needs
        small = (round(image.width * self.k), round(image.height * self.k))
        self.rgb = np.asarray(image.resize(small, Image.Resampling.LANCZOS))
        grid = (max(8, small[0] // 4), max(8, small[1] // 4))
        depth = cv2.resize(depth, grid, interpolation=cv2.INTER_AREA)
        # the near things grow a little, so that the stretching falls on the background, not on a face
        depth = cv2.dilate(depth, np.ones((5, 5), np.uint8))
        self.depth = cv2.GaussianBlur(depth, (0, 0), 2.0)
        fx, fy = photo.focus
        gx, gy = int(fx * (grid[0] - 1)), int(fy * (grid[1] - 1))
        self.subject = float(np.median(self.depth[max(0, gy - 6):gy + 7, max(0, gx - 6):gx + 7]))
        self.height = height

    def view(self, zoom, x, y, shift=(0.0, 0.0), dolly=0.0, anchor=None):
        """The window at `zoom`, placed at x, y (0 to 1 of the room left). `shift`: how many pixels the nearest
        thing moves against the farthest; `dolly`: how much more the near things grow than the far ones.
        `anchor`: the depth that stays where it is (default: the subject)."""
        iw, ih = self.size
        scale = self.fill * zoom
        cw, ch = min(iw, W / scale), min(ih, self.height / scale)
        left, top = (iw - cw) * R.clamp(x, 0, 1), (ih - ch) * R.clamp(y, 0, 1)
        anchor = self.subject if anchor is None else anchor
        gw, gh = W // 4, self.height // 4
        X, Y = np.meshgrid((np.arange(gw, dtype=np.float32) + 0.5) * 4, (np.arange(gh, dtype=np.float32) + 0.5) * 4)
        xs, ys = X, Y
        to_depth = self.k / 4
        for _ in range(3):   # where does the point that lands here come from
            d = cv2.remap(self.depth, (left + xs / scale) * to_depth, (top + ys / scale) * to_depth,
                          cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE) - anchor
            xs = X - d * (shift[0] + dolly * (xs - W / 2))
            ys = Y - d * (shift[1] + dolly * (ys - self.height / 2))
        xs = cv2.resize(xs, (W, self.height), interpolation=cv2.INTER_LINEAR)
        ys = cv2.resize(ys, (W, self.height), interpolation=cv2.INTER_LINEAR)
        out = cv2.remap(self.rgb, (left + xs / scale) * self.k, (top + ys / scale) * self.k, cv2.INTER_CUBIC,
                        borderMode=cv2.BORDER_REFLECT_101)
        return Image.fromarray(out)

    def shot(self, photo, t, seconds):
        """The moves of news/edits.py, in depth."""
        t = R.clamp(t, 0.0, 1.25)
        fx, fy = photo.focus
        gain = R.clamp(0.05 * seconds, 0.16, 0.30)
        iw, ih = self.size
        name = photo.move or "push-in"
        if name in ("pan-right", "pan-left"):
            zoom, first, last, _ = R.pan_plan(iw, W, self.fill, fx, seconds)
            direction = 1 if name == "pan-right" else -1
            if direction < 0:
                first, last = last, first
            return self.view(zoom + 0.04, first + (last - first) * t, fy, shift=(-direction * 60 * (2 * t - 1), 0),
                             anchor=float(np.median(self.depth)))
        if name in ("rise", "fall"):
            zoom, first, last, _ = R.pan_plan(ih, self.height, self.fill, fy, seconds)
            direction = -1 if name == "rise" else 1
            if direction < 0:
                first, last = last, first
            return self.view(zoom + 0.04, fx, first + (last - first) * t, shift=(0, -direction * 50 * (2 * t - 1)),
                             dolly=0.05 * t, anchor=float(np.median(self.depth)))
        if name == "pull-back":
            return self.view(1.05 + gain * 0.6 * (1 - t), fx, fy, shift=(30 * (2 * t - 1), 0), dolly=0.2 * (1 - t))
        # push-in: the camera goes forward and a little to the side
        return self.view(1.05 + gain * 0.6 * t, fx, fy, shift=(-30 * (2 * t - 1), 0), dolly=0.2 * t)


# ---------------------------------------------------------------- 4. transitions (ports of gl-transitions, MIT)

def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def grid(w, h, step=1):
    u, v = np.meshgrid((np.arange(0, w, step, dtype=np.float32) + 0.5) / w,
                       (np.arange(0, h, step, dtype=np.float32) + 0.5) / h)
    return u, v


def sample(image, u, v):
    h, w = image.shape[:2]
    return cv2.remap(image, np.float32(u * w - 0.5), np.float32(v * h - 0.5), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)


def directional_warp(a, b, p, direction=(1.0, -1.0), smoothness=0.35):
    """DirectionalWarp (pschroen): a diagonal wipe with a warped, smeared edge."""
    h, w = a.shape[:2]
    u, v = grid(w, h)
    vx, vy = np.array(direction) / np.hypot(*direction)
    vx, vy = vx / (abs(vx) + abs(vy)), vy / (abs(vx) + abs(vy))
    d = vx * 0.5 + vy * 0.5
    m = 1 - smoothstep(-smoothness, 0.0, vx * u + vy * v - (d - 0.5 + p * (1 + smoothness)))
    old = sample(a, (u - 0.5) * (1 - m) + 0.5, (v - 0.5) * (1 - m) + 0.5)
    new = sample(b, (u - 0.5) * m + 0.5, (v - 0.5) * m + 0.5)
    m = m[..., None]
    return old * (1 - m) + new * m


def cross_zoom(a, b, p, strength=0.4, samples=24):
    """CrossZoom (rectalogic): a cross-fade through a strong zoom blur."""
    h, w = a.shape[:2]
    u, v = grid(w, h)
    cx = 0.25 + 0.5 * p
    if p <= 0:
        dissolve = 0.0
    elif p >= 1:
        dissolve = 1.0
    elif p < 0.5:
        dissolve = 0.5 * 2 ** (10 * (2 * p - 1))
    else:
        dissolve = 0.5 * (2 - 2 ** (-10 * (2 * p - 1)))
    strength = -strength / 2 * (math.cos(math.pi * p / 0.5) - 1)
    mixed = a * (1 - dissolve) + b * dissolve
    total, weights = np.zeros_like(a), 0.0
    for index in range(samples + 1):
        percent = (index + 0.5) / samples
        weight = 4 * (percent - percent * percent)
        if weight <= 0:
            continue
        total += sample(mixed, u + (cx - u) * percent * strength, v + (0.5 - v) * percent * strength) * weight
        weights += weight
    return total / weights


def fract(x):
    return x - np.floor(x)


def film_burn(a, b, p, seed=2.31, light=0.75):
    """FilmBurn (Anastasia Dunbar): glowing light leaks wash over the picture and reveal the next one. The 50-tap
    blur of the original is a Gaussian blur here."""
    h, w = a.shape[:2]

    def sigmoid(x, k):
        return (2 * x) ** k / 2 if x <= 0.5 else 1 - (2 - 2 * x) ** k / 2

    def rand(co):
        return float(fract(math.sin(co * 24.9898 + seed) * 43758.5453))

    def random(co, shift):
        co += 10.0

        def one(s):
            return float(fract(math.sin(co * (12.9898 + math.floor(s) * 0.5) + co * (78.233 + seed)) * 43758.5453))
        return one(shift) + (one(shift + 1) - one(shift)) * sigmoid(shift - math.floor(shift), 2.0)

    def smooth_random(co, shift):
        f = co - math.floor(co)
        k = sigmoid(f, 2.0)
        top = random(math.floor(co), shift) + (random(math.floor(co) + 1, shift) - random(math.floor(co), shift)) * k
        return top   # both rows are the same when x == y

    u, v = grid(w, h, 8)
    v = 1 - v
    leak = np.zeros_like(u)
    for i in range(13):
        leak += (np.sin(u * rand(i) * 6 + p * 8 + rand(i + 1.43)) * np.sin(v * rand(i + 4.4) * 6 + p * 6 + rand(i + 2.4)))
        cx, cy = smooth_random(p * 1.3, i + 1.0), smooth_random(p * 0.5, i + 6.25)
        leak += 1 - np.clip(np.hypot(u - cx, v - cy) * (20 + 50 * rand(i)), 0, 1)
    leak = (leak + 4) / 11
    glow = math.sin(p * math.pi)
    colour = np.stack([np.abs(leak * 1.0) ** 1.0, np.abs(leak * 0.7) ** (2 - glow), np.abs(leak * 0.6) ** 1.3], -1)
    colour = cv2.resize((colour * glow).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    mix = sigmoid(p, 10.0)
    mixed = a * (1 - mix) + b * mix
    blur = glow * 0.03 * w * 0.5
    if blur > 0.6:
        mixed = cv2.GaussianBlur(mixed, (0, 0), blur)
    return mixed + colour * light


def ink_bleed(a, b, p, drops=4, tendrils=0.7, rim=0.5, seed=3.0):
    """InkBleed (gre): the next picture spreads over this one like drops of ink in water."""
    h, w = a.shape[:2]
    ratio = w / h
    u, v = grid(w, h, 3)

    def hash2(x, y):
        p3x, p3y, p3z = fract(x * 0.1031), fract(y * 0.1031), fract(x * 0.1031)
        dot = p3x * (p3y + 33.33) + p3y * (p3z + 33.33) + p3z * (p3x + 33.33)
        p3x, p3y, p3z = p3x + dot, p3y + dot, p3z + dot
        return fract((p3x + p3y) * p3z)

    def vnoise(x, y):
        ix, iy = np.floor(x), np.floor(y)
        fx, fy = x - ix, y - iy
        fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
        top = hash2(ix, iy) * (1 - fx) + hash2(ix + 1, iy) * fx
        bottom = hash2(ix, iy + 1) * (1 - fx) + hash2(ix + 1, iy + 1) * fx
        return top * (1 - fy) + bottom * fy

    def fbm(x, y):
        value, amplitude = 0.0, 0.5
        for _ in range(4):
            value = value + amplitude * vnoise(x, y)
            x, y = 1.6 * x - 1.2 * y + 7.3, 1.2 * x + 1.6 * y + 7.3
            amplitude *= 0.5
        return value / 0.9375

    def scalar_hash(x, y):
        return float(hash2(np.float64(x), np.float64(y)))

    qx, qy = u * ratio, v
    sx, sy = qx * 2.2 + seed * 3.1, qy * 2.2 + seed * 1.7
    w1x, w1y = fbm(sx, sy + 0.6 * p), fbm(sx + 5.2 - 0.5 * p, sy + 1.3)
    w2x, w2y = fbm(sx + 3 * w1x + 1.7, sy + 3 * w1y + 9.2), fbm(sx + 3 * w1x + 8.3, sy + 3 * w1y + 2.8)
    swirl = fbm(sx * 0.8 + 2.5 * w2x, sy * 0.8 + 2.5 * w2y) - 0.5
    flow_x, flow_y = w2x - 0.5, w2y - 0.5
    amp = 0.05 + 0.35 * tendrils
    rim_w, feather = 0.1, 0.05
    margin = 1.2 * amp + rim_w + 0.08
    f = np.full_like(u, -1e3)
    fs = np.full_like(u, -1e3)
    for i in range(drops):
        hx, hy = i * 7.13 + seed, i * 3.71 - seed
        cx, cy = (0.15 + 0.7 * scalar_hash(hx, hy)) * ratio, 0.15 + 0.7 * scalar_hash(hx + 19.7, hy + 19.7)
        start = 0.2 * i / drops
        s = R.clamp((p - start) / (1 - start), 0.0, 1.0)
        far = math.hypot(max(cx, ratio - cx), max(cy, 1 - cy)) + margin
        s3 = s * s * s
        r = (far + 0.02) * s * (0.35 + 0.65 * s3 * s3) - 0.02
        reach = amp * min(1.0, max(r, 0.0) * 5.0)
        g = r - np.hypot(qx - cx + 1.3 * reach * flow_x, qy - cy + 1.3 * reach * flow_y) + reach * 0.9 * swirl
        f = np.maximum(f, g)
        fs = np.maximum(fs, g - 0.15 * (1 - min(1.0, s * 12)))
    inside = smoothstep(-0.003, 0.003, f)
    wisp = 1 - smoothstep(0.0, 0.08, np.abs(fbm(sx * 2 + 5 * w2x, sy * 2 + 5 * w2y) - 0.5))
    soft = smoothstep(-feather, 0.0, fs) * (0.35 + 0.4 * wisp)
    haze = 0.35 * wisp * (1 - smoothstep(0.0, 0.1, -fs))
    cover = np.maximum(inside, np.maximum(soft, haze))
    edge = 1 - smoothstep(0.0, rim_w, f)

    def full(layer):
        return cv2.resize(layer.astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)

    cover, edge = np.clip(full(cover), 0, 1)[..., None], np.clip(full(edge), 0, 1)
    fu, fv = grid(w, h)
    new = sample(b, fu - 0.015 * edge * full(flow_x) / ratio, fv - 0.015 * edge * full(flow_y))
    edge = (rim * edge)[..., None]
    new = new * (1 - edge) + new * new * 0.7 * edge
    return a * (1 - cover) + new * cover


def blend(effect, old, new, amount, **options):
    a, b = np.asarray(old, np.float32) / 255, np.asarray(new, np.float32) / 255
    out = effect(a, b, float(R.clamp(amount, 0, 1)), **options)
    return Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8))


# which transition between the pictures of a scene (scene, picture) and into a scene, and how long (seconds)
PICTURE_CUTS = {(0, 1): (directional_warp, 0.9, {}), (0, 2): (cross_zoom, 0.8, {}), (1, 1): (ink_bleed, 1.5, {})}
SCENE_CUTS = {1: (film_burn, 1.0, {})}


class DeepScene(R.Scene):
    """A scene whose pictures move in depth and change by a gl-transition."""
    deep = {}   # (scene, picture) -> Deep

    def shot(self, number, local, length):
        deep = self.deep.get((self.index, number))
        if deep is None:
            return super().shot(number, local, length)
        return deep.shot(self.photos[number], local, length)

    def picture(self, moment):
        count = len(self.photos)
        length = (self.end - self.start) / count
        number = min(count - 1, max(0, int((moment - self.start) // length)))
        local = (moment - self.start - number * length) / length
        picture = self.shot(number, local, length)
        effect, seconds, options = PICTURE_CUTS.get((self.index, number), (None, R.PHOTO_FADE, {}))
        if number and local * length < seconds:
            previous = self.shot(number - 1, 1 + local, length)
            amount = local * length / seconds
            picture = (blend(effect, previous, picture, amount, **options) if effect
                       else Image.blend(previous, picture, R.ease(amount)))
        return picture, self.photos[number]


def frame_at(scenes, number, moment):
    frame = scenes[number].render(moment)
    effect, seconds, options = SCENE_CUTS.get(number, (None, R.TRANSITION, {}))
    if number and moment - scenes[number].start < seconds:
        old = scenes[number - 1].render(moment)
        amount = (moment - scenes[number].start) / seconds
        if not effect:
            return R.transition(old, frame, R.ease(amount), scenes[number].cut)
        top, height = R.photo_box()   # only the picture burns; the page around it changes quietly
        area = (0, top, W, top + height)
        page = blend(effect, old.crop(area), frame.crop(area), amount, **options)
        frame = Image.blend(old, frame, R.ease(amount))
        frame.paste(page, area[:2])
    return frame


# ---------------------------------------------------------------- 3. captions that follow the voice

KANJI = re.compile(r"[一-鿿々]")


def reading_weight(piece):
    """About how long the voice takes for a piece: a kanji or a digit is read as two sounds, a comma is a rest."""
    total = 0.0
    for char in piece:
        if char in "「」『』（）()“”\"":
            continue
        total += 1.5 if char in "、。，．" else 2.0 if KANJI.match(char) or char.isdigit() else 1.0
    return max(total, 0.01)


def spoken_state(rows, progress):
    """rows: lists of phrases. For every phrase: 1 = said, 0 = not yet, between = being said now."""
    weights = [[reading_weight(piece) for piece in row] for row in rows]
    position = progress * sum(map(sum, weights))
    states = []
    for row in weights:
        states.append([])
        for weight in row:
            states[-1].append(R.clamp(position / weight, 0.0, 1.0))
            position -= weight
    return states


def rgba(colour, alpha=255):
    colour = colour.lstrip("#")
    return tuple(int(colour[i:i + 2], 16) for i in (0, 2, 4)) + (alpha,)


def draw_following(layer, rows, states, face, top, pitch, said, now, later, marker=None):
    """Draw rows of phrases centred on the layer: said, being said (with a marker-pen band growing behind it) and
    not yet said."""
    draw = ImageDraw.Draw(layer)
    size = face.size
    for row_index, (row, row_states) in enumerate(zip(rows, states)):
        x = (W - face.getlength("".join(row))) / 2
        y = top + row_index * pitch
        for piece, state in zip(row, row_states):
            width = face.getlength(piece)
            if 0 < state < 1 and marker:
                draw.rounded_rectangle((x - 6, y + size * 0.52, x + 6 + width * R.ease(min(1, state * 1.6)),
                                        y + size * 1.16), radius=8, fill=marker)
            colour = said if state >= 1 else now if state > 0 else later
            lift = round(-4 * math.sin(math.pi * state)) if 0 < state < 1 else 0
            draw.text((x, y + lift), piece, font=face, fill=colour, anchor="lt", stroke_width=1, stroke_fill=colour)
            x += width


def draw_captions(image, caption, age, progress):
    face = R.font(R.CAPTION_SIZE)
    rows = [R.phrases(line) for line in caption.splitlines()]
    height = 83 * len(rows) + 26
    amount = R.ease(age / R.CAPTION_IN) if age < R.CAPTION_IN else 1.0
    layer = Image.new("RGBA", (W, height + 16), (0, 0, 0, 0))
    ink = R.style.caption_text
    draw_following(layer, rows, spoken_state(rows, progress), face, 21, 83, rgba(ink), rgba(R.style.accent),
                   rgba(ink, 95), marker=rgba("#f1c96b", 150))
    if amount < 1:
        layer = R.faded(layer, amount)
    image.paste(layer, (0, R.caption_centre() - height // 2 + round(14 * (1 - amount))), layer)


def draw_quote(image, line, age, progress):
    """The big quote over the picture: its words light up as they are spoken."""
    top, height = R.photo_box()
    amount = R.ease(age / R.QUOTE_IN) if age < R.QUOTE_IN else 1.0
    if amount <= 0:
        return
    dark = Image.new("RGBA", (W, height), (12, 8, 4, round(178 * amount)))
    image.paste(dark, (0, top), dark)
    pieces = [row for chunk in R.caption_chunks(line) for row in chunk.splitlines()]
    words, size = R.fit("\n".join(pieces), 900, 104, max(len(pieces), 2), smallest=56)
    rows = [R.phrases(row) for row in words.splitlines()]
    block = R.block_height(words, size, 26)
    layer = Image.new("RGBA", (W, block + 140), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.rectangle((W // 2 - 60, 0, W // 2 + 60, 5), fill=R.style.accent)
    draw_following(layer, rows, spoken_state(rows, progress), R.font(size), 60, size + 26, rgba(R.STORY_TEXT),
                   rgba("#f1c96b"), rgba(R.STORY_TEXT, 70))
    draw.rectangle((W // 2 - 60, block + 120, W // 2 + 60, block + 125), fill=R.style.accent)
    layer = R.faded(layer, amount)
    image.paste(layer, (0, top + (height - layer.height) // 2 + round(24 * (1 - amount))), layer)


# ---------------------------------------------------------------- the sample

def read_srt(path, until):
    captions = []
    for block in Path(path).read_text(encoding="utf-8").strip().split("\n\n"):
        _, times, *lines = block.splitlines()
        start, end = (sum(float(part.replace(",", ".")) * unit for part, unit in zip(stamp.split(":"), (3600, 60, 1)))
                      for stamp in times.split(" --> "))
        if start < until:
            captions.append(Caption(start, end, "\n".join(lines)))
    return captions


def main():
    story, find, prep, old_video, old_srt, out, *rest = sys.argv[1:]
    seconds = float(rest[0]) if rest else 18.7
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    release, beats, photos = load_story(Path(story), Path(find))
    R.use_style(release.style)
    captions = read_srt(old_srt, seconds)
    # the scenes whose captions start before the end of the sample; a scene ends where its last caption ends
    counts = [sum(len(R.caption_chunks(line)) for line in beat.lines) for beat in beats]
    intervals, used = [], 0
    for count in counts:
        if used >= len(captions):
            break
        last = used + count - 1
        end = (captions[last].end + captions[last + 1].start) / 2 if last + 1 < len(captions) else seconds
        intervals.append((0.0, min(end, seconds)))
        used += count
    beats = beats[:len(intervals)]
    picks = [R_pick for scene in read(Path(story))["scenes"][:len(beats)] for R_pick in [scene.get("photo")]]
    top, height = R.photo_box()
    for index in range(len(beats)):
        entries = picks[index] if isinstance(picks[index], list) else [picks[index]]
        for number, (photo, entry) in enumerate(zip(photos.get(index, []), entries)):
            name = entry["pick"] if isinstance(entry, dict) else entry
            sharp, depth = Path(prep) / f"{name}.png", Path(prep) / f"{name}_depth.png"
            if not depth.exists() or not sharp.exists() or photo.fit == "contain":
                continue
            with Image.open(sharp) as better:   # the sharper copy (2), same picture
                better = better.convert("RGB")
            if better.size != photo.image.size:
                # 60 % of the Real-ESRGAN copy over the plain enlargement: sharper, without the painted look
                better = Image.blend(photo.image.resize(better.size, Image.Resampling.LANCZOS), better, 0.6)
            photo = replace(photo, image=better)
            photos[index][number] = photo
            DeepScene.deep[(index, number)] = Deep(
                photo, cv2.imread(str(depth), cv2.IMREAD_UNCHANGED).astype(np.float32) / 65535, height)
    scenes, start = [], 0.0
    for index, (beat, (_, end)) in enumerate(zip(beats, intervals)):
        scenes.append(DeepScene(index, beat, release, photos.get(index), False, start, end))
        start = end
    quotes = R.quote_lines(beats, captions)
    grain = R.Grain() if R.style.grain else None
    fade = max(0.0, seconds - 0.5)
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", f"{W}x{H}", "-framerate", str(FPS), "-i", "-",
           "-t", f"{seconds}", "-i", str(old_video), "-map", "0:v", "-map", "1:a",
           "-af", f"afade=t=out:st={fade}:d=0.5", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", "-shortest",
           str(out / "video.mp4")]
    stills = {round(float(value) * FPS) for value in rest[1:]}
    cue = frame_index = 0
    with subprocess.Popen(cmd, stdin=subprocess.PIPE) as process:
        try:
            for number, scene in enumerate(scenes):
                while frame_index < math.ceil(scene.end * FPS):
                    moment = frame_index / FPS
                    while cue + 1 < len(captions) and moment >= captions[cue].end:
                        cue += 1
                    shown = cue - 1 if cue and moment < captions[cue].start else cue
                    if not stills or frame_index in stills:
                        frame = frame_at(scenes, number, moment)
                        caption = captions[shown]
                        progress = R.clamp((moment - caption.start) / (caption.end - caption.start), 0.0, 1.0)
                        if quotes[shown]:
                            draw_quote(frame, quotes[shown][0], moment - quotes[shown][1], progress)
                        else:
                            draw_captions(frame, caption.text, moment - caption.start, progress)
                        if grain:
                            frame = grain.apply(frame, frame_index)
                        if stills:
                            frame.save(out / f"t{moment:05.2f}.jpg", quality=88)
                        else:
                            process.stdin.write(frame.tobytes())
                    frame_index += 1
        finally:
            process.stdin.close()
        process.wait()


if __name__ == "__main__":
    main()
