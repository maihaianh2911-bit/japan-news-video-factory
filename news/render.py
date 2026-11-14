"""Render vertical news video with timed Japanese captions and stable motion."""
from dataclasses import dataclass
from functools import lru_cache
import math
from pathlib import Path
import re
import subprocess

import budoux
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from .story import VOICE_CREDIT, japanese_date

W, H, FPS = 1080, 1920, 30
# GitHub refuses a file over 100 MB on the renders branch: the video is kept under about 90 MB. Up to about
# 1 min 50 s it gets the full quality (6 Mbit/s at most); a longer one gets a lower bitrate instead of failing.
SIZE_BUDGET, MAX_VIDEO_KBPS, AUDIO_KBPS = 88_000_000, 6000, 128
FONT = "/usr/share/fonts/opentype/noto/Noto{}CJK"
WHITE, PAPER, INK = "#ffffff", "#f6f3ec", "#142232"
NAVY, MUTED, RED, GOLD = "#132133", "#99a9bb", "#b91835", "#ffda76"


@dataclass(frozen=True)
class Style:
    """Colours and typeface of the frame. "news": dark blue TV-news frame; "paper": pale yellow old newspaper."""
    family: str = "Sans"
    background: str = NAVY
    text: str = WHITE          # headline and evidence on a picture scene
    muted: str = MUTED         # date, source, credits
    accent: str = RED          # top bar, line under the picture, kicker
    tag: str = "#33475e"       # scene label
    tag_text: str = WHITE
    photo_bed: str = "#29394a"
    photo_tag: str = NAVY      # 資料写真 over the picture
    photo_tag_text: str = WHITE
    value: str = GOLD          # big figure on a picture scene
    card: str = PAPER
    card_ink: str = INK
    card_muted: str = "#5d6671"
    rule: str = "#506075"
    caption_box: str = "#0b1421"
    caption_text: str = WHITE
    grain: bool = False


STYLES = {
    "news": Style(),
    "paper": Style(family="Serif", background="#eee2bf", text="#2a1d10", muted="#6f5d40", accent="#8e2b1b",
                   tag="#4a3520", tag_text="#f6ecd2", photo_bed="#d8c79e", photo_tag="#eee2bf", photo_tag_text="#2a1d10", value="#8e2b1b", card="#f7eed6",
                   card_ink="#2a1d10", card_muted="#6f5d40", rule="#9c8a68", caption_box="#2e2114",
                   caption_text="#f8f0da", grain=True),
}
style = STYLES["news"]


def use_style(name):
    global style
    style = STYLES[name]
CAPTION_WIDTH, CAPTION_SIZE = 866, 52
PHOTO_TEXT_BOTTOM = 1490   # the caption box (two lines) starts at about 1502
PHRASES = budoux.load_default_japanese_parser()


def font(size, bold=True):
    return face_of(style.family, size, bold)


@lru_cache(maxsize=128)
def face_of(family, size, bold):
    weight = "Bold" if bold else "Regular"
    return ImageFont.truetype(f"{FONT.format(family)}-{weight}.ttc", size, index=0)


# Japanese line breaking rules (kinsoku): a line never ends with an opening bracket and never starts with
# a closing bracket, punctuation, a long-vowel mark or a small kana.
NO_END = "(（「『[〔【〈《"
NO_START = ")）」』]〕】〉》、。，．,.！？!?：；:;・ー…‥ぁぃぅぇぉっゃゅょゎァィゥェォッャュョヮヵヶ％%"
NUMBER_END = re.compile(r"[0-9０-９.,．，]$")
NUMBER_TAIL = re.compile(r"[0-9０-９.,．，％%]|[兆億万]?円")


def phrases(value):
    """Split one line of text into the pieces a line may break between: BudouX phrases, with an opening bracket
    kept with what follows it, a closing bracket or punctuation kept with what precedes it, and numbers whole."""
    parts = []
    for phrase in PHRASES.parse(value):
        # a bracket inside a phrase starts a new piece ("引き上げ(見本)" -> "引き上げ" + "(見本)")
        for piece in re.split(f"(?=[{re.escape(NO_END)}])", phrase):
            if not piece:
                continue
            if parts and (piece[0] in NO_START or parts[-1][-1] in NO_END or piece.isspace()
                          or (NUMBER_END.search(parts[-1]) and NUMBER_TAIL.match(piece))):
                parts[-1] += piece
            else:
                parts.append(piece)
    return parts


def split_wide(piece, width, face):
    """Cut a piece wider than the box, between characters, keeping the kinsoku rules (last resort)."""
    out = []
    while face.getlength(piece) > width and len(piece) > 1:
        fits = max(1, max((i for i in range(1, len(piece)) if face.getlength(piece[:i]) <= width), default=1))
        allowed = [i for i in range(1, fits + 1) if piece[i] not in NO_START and piece[i - 1] not in NO_END]
        natural = [i for i in allowed if piece[i - 1] in " 、。）」』)]〕】"]   # after a space, comma or bracket
        cut = (natural or allowed or [fits])[-1]
        out.append(piece[:cut].rstrip())
        piece = piece[cut:]
    out.append(piece)
    return out


def wrap_lines(value, width, face):
    """Break text into lines no wider than width, at phrase boundaries. Never drops text."""
    lines = []
    for part in value.splitlines() or [""]:
        line = ""
        for phrase in phrases(part):
            if line and face.getlength(line + phrase) > width:
                lines.append(line.rstrip())
                line = ""
            if not line and face.getlength(phrase) > width:
                *full, phrase = split_wide(phrase.lstrip(), width, face)
                lines.extend(full)
            line += phrase.lstrip() if not line else phrase
        lines.append(line.rstrip())
    return lines


def fit(value, width, size, maximum, *, bold=True, smallest=None):
    """Wrap text in at most `maximum` lines, making the font smaller when needed (down to `smallest`).
    Returns (text with newlines, size). Text is never cut: at the smallest size every line is kept."""
    smallest = smallest or max(18, round(size * 0.7))
    for candidate in range(size, smallest - 1, -2):
        lines = wrap_lines(value, width, font(candidate, bold))
        if len(lines) <= maximum:
            return "\n".join(lines), candidate
    print(f"warning: text needs {len(lines)} lines (more than {maximum}) even at size {smallest}: {value!r}")
    return "\n".join(lines), smallest


def block_height(value, size, spacing=18):
    return len(value.splitlines()) * (size + spacing) - spacing


def balanced(parts, fits, size):
    """Join parts into the fewest groups that fit, of sizes as equal as possible."""
    best = [(0, 0.0, 0)]
    for end in range(1, len(parts) + 1):
        options = []
        for start in range(end - 1, -1, -1):
            group = parts[start:end]
            if end - start > 1 and not fits(group):
                break
            options.append((best[start][0] + 1, best[start][1] + size("".join(group)) ** 2, start))
        best.append(min(options))
    groups, end = [], len(parts)
    while end:
        start = best[end][2]
        groups.append(parts[start:end])
        end = start
    return groups[::-1]


def caption_chunks(line):
    """Split a spoken line into captions of one or two lines, broken only between Japanese phrases."""
    face = font(CAPTION_SIZE)
    line = re.sub(r"([0-9０-９])パーセント", r"\g<1>％", line)
    pieces = [piece for part in phrases(line) for piece in split_wide(part, CAPTION_WIDTH, face)]
    if not pieces:
        return []

    def one_line(group):
        return face.getlength("".join(group)) <= CAPTION_WIDTH

    def lines(group):
        return ["".join(line).strip() for line in balanced(group, one_line, face.getlength)]

    captions = balanced(pieces, lambda group: len(lines(group)) <= 2, face.getlength)
    return ["\n".join(lines(group)) for group in captions]


def text(draw, x, y, value, size, fill=None, *, bold=True, anchor="lt", spacing=18):
    """Draw lines of text from y; returns the y just below the last line."""
    fill = fill or style.text
    for line_index, line in enumerate(value.splitlines()):
        draw.text((x, y + line_index * (size + spacing)), line, font=font(size, bold), fill=fill, anchor=anchor)
    return y + block_height(value, size, spacing)


def label(draw, x, y, value, fill=None, color=None):
    width = int(font(28).getlength(value)) + 42
    draw.rounded_rectangle((x, y, x + width, y + 58), radius=9, fill=fill or style.accent)
    text(draw, x + 21, y + 14, value, 28, color or style.tag_text)


@lru_cache(maxsize=2)
def paper_grain(color):
    """A flat paper colour with faint fibres and darker, aged edges."""
    import random
    rng = random.Random(7)
    small = Image.new("L", (W // 4, H // 4))
    small.putdata([rng.randint(0, 255) for _ in range(small.width * small.height)])
    noise = small.filter(ImageFilter.GaussianBlur(1.2)).resize((W, H), Image.Resampling.BICUBIC)
    base = Image.new("RGB", (W, H), color)
    darker = Image.eval(base, lambda level: int(level * 0.86))
    vignette = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vignette).rounded_rectangle((60, 60, W - 60, H - 60), radius=200, fill=255)
    edges = Image.eval(vignette.filter(ImageFilter.GaussianBlur(110)), lambda level: 255 - level)
    aged = Image.composite(darker, base, edges)
    speckle = Image.eval(noise, lambda level: max(0, 150 - level) // 6)   # 0..25, mostly 0
    return Image.composite(Image.eval(aged, lambda level: int(level * 0.93)), aged, speckle)


# --- motion: pictures that move, text that comes in, transitions between scenes, film grain (paper) ---
PHOTO_TOP, PHOTO_HEIGHT = 338, 700
TEXT_IN, CAPTION_IN, PHOTO_FADE, TRANSITION = 0.45, 0.2, 0.5, 0.5   # seconds
MOTIONS = ("in", "right", "out", "left")   # one per picture, in turn


def ease(value):
    value = min(1.0, max(0.0, value))
    return value * value * (3 - 2 * value)


def crop_photo(image, height, focus=(0.5, 0.5), zoom=1.0, shift=0.0):
    """The part of the picture shown: `zoom` 1 fills the frame, `shift` moves the window sideways (-1 to 1)."""
    iw, ih = image.size
    scale = max(W / iw, height / ih) * zoom
    cw, ch = W / scale, height / scale
    left = (iw - cw) * min(1, max(0, focus[0] + shift))
    top = (ih - ch) * min(1, max(0, focus[1]))
    return image.resize((W, height), Image.Resampling.BICUBIC, box=(left, top, left + cw, top + ch))


@lru_cache(maxsize=8)
def backdrop(key, height):
    image = BACKDROPS[key]
    soft = crop_photo(image, height).resize((W // 8, height // 8)).filter(ImageFilter.GaussianBlur(6))
    return Image.eval(soft.resize((W, height), Image.Resampling.BICUBIC), lambda level: level * 0.45)


BACKDROPS = {}


def whole_photo(image, position, height):
    """Show the whole picture (portraits, charts, documents) over a blurred copy of itself; it grows slowly."""
    BACKDROPS[id(image)] = image
    frame = backdrop(id(image), height).copy()
    scale = min(W / image.width, height / image.height) * (0.86 + 0.14 * position)
    size = (round(image.width * scale), round(image.height * scale))
    frame.paste(image.resize(size, Image.Resampling.BICUBIC), ((W - size[0]) // 2, (height - size[1]) // 2))
    return frame


def moving_photo(photo, t, kind, height=PHOTO_HEIGHT):
    """The picture at time t (0 at its start, 1 at its end, a little more while it fades out)."""
    t = min(1.25, max(0.0, t))
    if photo.fit == "contain":
        return whole_photo(photo.image, t if kind in ("in", "right") else 1 - min(1, t), height)
    if kind == "in":
        return crop_photo(photo.image, height, photo.focus, zoom=1.0 + 0.2 * t)
    if kind == "out":
        return crop_photo(photo.image, height, photo.focus, zoom=1.25 - 0.2 * t)
    direction = 1 if kind == "right" else -1
    return crop_photo(photo.image, height, photo.focus, zoom=1.18, shift=direction * (-0.3 + 0.6 * t))


def layout(beat, release, has_photo, demo):
    """The page of a scene: the background (what stays still) and the scene's text on a transparent layer
    (it slides in at the start of the scene)."""
    image = paper_grain(style.background).copy() if style.grain else Image.new("RGB", (W, H), style.background)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, W, 14), fill=style.accent)
    if style.grain:   # newspaper masthead rules
        draw.rectangle((40, 40, W - 40, 44), fill=style.text)
        draw.rectangle((40, 50, W - 40, 51), fill=style.text)
        draw.rectangle((40, 234, W - 40, 235), fill=style.text)
        draw.rectangle((40, 240, W - 40, 244), fill=style.text)
    label(draw, 70, 68, release.kicker or "日本のニュース")
    text(draw, 70, 152, japanese_date(release), 35, style.muted)
    if demo:
        text(draw, W - 70, 95, "過去のニュース・動作確認", 28, GOLD, anchor="rt")
    if has_photo:
        draw.rectangle((0, PHOTO_TOP, W, 1054), fill=style.photo_bed)
        draw.rectangle((0, 1038, W, 1054), fill=style.accent)
    draw.line((70, 1704, W - 70, 1704), fill=style.rule, width=2)
    if release.publisher:
        text(draw, 70, 1742, f"出典  {release.publisher}", 29, style.muted, bold=False)
    text(draw, W - 70, 1742, VOICE_CREDIT, 24, style.muted, bold=False, anchor="rt")

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    label(draw, 70, 261, beat.label, style.tag)
    if has_photo:
        # Picture scene: picture, then headline, value (big figure) and evidence (small text) under each other.
        headline, size = fit(beat.headline, 925, 70 if len(beat.headline) < 25 else 51, 3, smallest=44)
        y = text(draw, 70, 1100, headline, size)
        if beat.value:
            value, value_size = fit(beat.value, 925, 90, 1, smallest=60)
            y = text(draw, 70, y + 34, value, value_size, style.value)
        if beat.evidence:
            evidence, evidence_size = fit(beat.evidence, 925, 34, 2, bold=False, smallest=26)
            if y + 26 + block_height(evidence, evidence_size, 12) <= PHOTO_TEXT_BOTTOM:
                text(draw, 70, y + 26, evidence, evidence_size, style.text, bold=False, spacing=12)
            else:
                print(f"warning: no room for the evidence under the headline of scene {beat.label!r}: "
                      f"{beat.evidence!r} is not shown (shorten the headline or the evidence)")
        elif not beat.value:
            text(draw, 70, y + 40, release.publisher, 42, style.muted)
    else:
        # Text card: headline, then value and evidence. Nothing else from the story is shown on it.
        draw.rounded_rectangle((70, 350, 1010, 1410), radius=32, fill=style.card,
                               outline=style.rule if style.grain else None, width=3)
        draw.rectangle((117, 419, 172, 426), fill=style.accent)
        text(draw, 119, 472, release.publisher, 38, style.card_muted)
        headline, size = fit(beat.headline, 840, 60 if len(beat.headline) < 27 else 48, 3, smallest=40)
        y = text(draw, 119, 570, headline, size, style.card_ink)
        if beat.value:
            value, value_size = fit(beat.value, 840, 144 if len(beat.value) <= 7 else 98, 1, smallest=56)
            y = text(draw, 119, max(813, y + 60), value, value_size, style.accent)
            if beat.evidence:
                evidence, evidence_size = fit(beat.evidence, 830, 33, 5, bold=False, smallest=24)
                text(draw, 119, max(1055, y + 50), evidence, evidence_size, style.card_ink, bold=False)
        elif beat.evidence:
            evidence, evidence_size = fit(beat.evidence, 830, 47, 5, bold=False, smallest=30)
            text(draw, 119, max(839, y + 70), evidence, evidence_size, style.card_ink, bold=False)
        if release.publisher:
            text(draw, 119, 1304, "公表資料", 29, style.card_muted)
    return image, layer


def faded(layer, amount):
    """The layer with its opacity multiplied by amount (0 to 1)."""
    alpha = layer.getchannel("A").point(lambda level: round(level * amount))
    out = layer.copy()
    out.putalpha(alpha)
    return out


class Scene:
    """Draws one scene at any moment: its pictures one after the other, each moving and fading into the next,
    and its text coming in at the start."""

    def __init__(self, index, beat, release, photos, demo, start, end):
        self.index, self.photos, self.start, self.end = index, list(photos or ()), start, max(end, start + 0.1)
        self.background, self.text = layout(beat, release, bool(self.photos), demo)
        self.settled = self.background.copy()
        self.settled.paste(self.text, (0, 0), self.text)

    def picture(self, moment):
        count = len(self.photos)
        length = (self.end - self.start) / count
        number = min(count - 1, max(0, int((moment - self.start) // length)))
        local = (moment - self.start - number * length) / length
        kind = MOTIONS[(self.index + number) % len(MOTIONS)]
        picture = moving_photo(self.photos[number], local, kind)
        if number and local * length < PHOTO_FADE:   # the previous picture fades into this one
            previous = moving_photo(self.photos[number - 1], 1 + local, MOTIONS[(self.index + number - 1) % len(MOTIONS)])
            picture = Image.blend(previous, picture, ease(local * length / PHOTO_FADE))
        return picture, self.photos[number]

    def render(self, moment):
        age = moment - self.start
        if age < TEXT_IN:
            amount = ease(age / TEXT_IN)
            frame = self.background.copy()
            layer = faded(self.text, amount)
            frame.paste(layer, (0, round(36 * (1 - amount))), layer)
        else:
            frame = self.settled.copy()
        if self.photos:
            picture, photo = self.picture(moment)
            frame.paste(picture, (0, PHOTO_TOP))
            draw = ImageDraw.Draw(frame)
            label(draw, 70, 380, "資料写真", style.photo_tag, style.photo_tag_text)
            credit = f"写真  {photo.creator}" + (f" / {photo.license}" if photo.license else "")
            credit, credit_size = fit(credit, 940, 23, 2, bold=False, smallest=16)
            text(draw, 70, 1806, credit, credit_size, style.muted, bold=False)
        return frame


@lru_cache(maxsize=1)
def page_shadow():
    shadow = Image.new("RGBA", (48, 1460), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    for x in range(48):
        draw.line((x, 0, x, 1460), fill=(20, 12, 4, round(110 * (x / 48) ** 2)))
    return shadow


def transition(old, new, amount):
    """From one scene to the next: a page turned from the right (paper) or a cross-fade (news)."""
    if not style.grain:
        return Image.blend(old, new, amount)
    offset = round(W * (1 - amount))
    frame = old.copy()
    if offset < W:
        frame.paste(new.crop((0, 245, W - offset, 1700)), (offset, 245))
    if offset >= 48:
        frame.paste(page_shadow(), (offset - 48, 245 - 5), page_shadow())
    return frame


def draw_captions(image, caption, age=1.0):
    face = font(CAPTION_SIZE)
    contents = caption.splitlines()
    height = 83 * len(contents) + 26
    amount = ease(age / CAPTION_IN) if age < CAPTION_IN else 1.0
    layer = Image.new("RGBA", (W, height + 4), (0, 0, 0, 0)) if amount < 1 else None
    draw = ImageDraw.Draw(layer if layer else image)
    top = 0 if layer else 1598 - height // 2
    draw.rounded_rectangle((69, top, 1011, top + height), radius=19, fill=style.caption_box)
    for line_index, line in enumerate(contents):
        draw.text((W / 2, top + 21 + 83 * line_index), line,
                  font=face, fill=style.caption_text, anchor="mt", stroke_width=1, stroke_fill=style.caption_text)
    if layer:
        layer = faded(layer, amount)
        image.paste(layer, (0, 1598 - height // 2 + round(14 * (1 - amount))), layer)


class Grain:
    """Old film on the paper frame: moving grain and now and then a speck of dust or a thin scratch."""
    FRAMES = 6

    def __init__(self):
        import random
        self.random = random
        self.light, self.dark = [], []
        for seed in range(self.FRAMES):
            rng = random.Random(seed)
            for target in (self.light, self.dark):
                # soft, coarse grain that changes every other frame: it reads as film without making the video
                # too big to store (fine grain on every frame made a 70-second video 180 MB)
                small = Image.new("L", (W // 4, H // 4))
                small.putdata([max(0, rng.randint(-10, 7)) for _ in range(small.width * small.height)])
                target.append(small.resize((W, H), Image.Resampling.BILINEAR).convert("RGB"))

    def apply(self, frame, index):
        step = index // 2
        frame = ImageChops.subtract(ImageChops.add(frame, self.light[step % self.FRAMES]),
                                    self.dark[(step * 7 + 3) % self.FRAMES])
        rng = self.random.Random(index // 2)   # dust stays two frames
        draw = ImageDraw.Draw(frame)
        for _ in range(rng.choice((0, 0, 1, 2, 3))):
            x, y, r = rng.randrange(W), rng.randrange(H), rng.choice((1, 1, 2, 3))
            draw.ellipse((x - r, y - r, x + r, y + r), fill=(58, 44, 30))
        if rng.random() < 0.06:
            x = rng.randrange(80, W - 80)
            draw.line((x, rng.randrange(0, H // 2), x + rng.randint(-6, 6), rng.randrange(H // 2, H)),
                      fill=(214, 200, 168), width=1)
        return frame


def scenes_for(beats, release, photos, demo, intervals):
    scenes, start = [], 0.0
    for index, (beat, (_, end)) in enumerate(zip(beats, intervals, strict=True)):
        scenes.append(Scene(index, beat, release, photos.get(index), demo, start, end))
        start = end
    return scenes


def frame_at(scenes, number, moment):
    frame = scenes[number].render(moment)
    if number and moment - scenes[number].start < TRANSITION:
        old = scenes[number - 1].render(moment)
        frame = transition(old, frame, ease((moment - scenes[number].start) / TRANSITION))
    return frame


def video_kbps(duration, budget=SIZE_BUDGET):
    """The highest video bitrate (kbit/s) that keeps a video of `duration` seconds within `budget` bytes."""
    room = budget * 8 / 1000 / max(duration, 1.0) * 0.98 - AUDIO_KBPS   # 2 % for the container
    return max(300, min(MAX_VIDEO_KBPS, int(room)))


def codec_args(duration):
    """FFmpeg output options: H.264 at constant quality, capped so that the file fits the size budget."""
    kbps = video_kbps(duration)
    return ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-maxrate", f"{kbps}k", "-bufsize", f"{2 * kbps}k",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", f"{AUDIO_KBPS}k", "-af", "loudnorm=I=-16:TP=-1.5:LRA=7",
            "-movflags", "+faststart", "-shortest"]


def encode(beats, release, photos, demo, intervals, captions, wav, out):
    scenes = scenes_for(beats, release, photos, demo, intervals)
    grain = Grain() if style.grain else None
    cover = scenes[0].render(min(1.5, intervals[0][1] * 0.3))
    draw_captions(cover, captions[0].text)
    cover.save(out / "cover.jpg", quality=92)

    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", f"{W}x{H}", "-framerate", str(FPS), "-i", "-",
        "-i", str(wav), *codec_args(intervals[-1][1]), str(out / "video.mp4"),
    ]
    cue = 0
    frame_index = 0
    with subprocess.Popen(cmd, stdin=subprocess.PIPE) as process:
        try:
            for number, scene in enumerate(scenes):
                while frame_index < math.ceil(scene.end * FPS):
                    moment = frame_index / FPS
                    while cue + 1 < len(captions) and moment >= captions[cue].end:
                        cue += 1
                    frame = frame_at(scenes, number, moment)
                    draw_captions(frame, captions[cue].text, moment - captions[cue].start)
                    if grain:
                        frame = grain.apply(frame, frame_index)
                    process.stdin.write(frame.tobytes())
                    frame_index += 1
        finally:
            process.stdin.close()
        if process.wait():
            raise RuntimeError("FFmpeg failed")


def stills(beats, release, photos, out):
    """One frame per picture, without the voice, to check pictures and text before rendering."""
    grain = Grain() if style.grain else None
    tiles = []
    for index, beat in enumerate(beats):
        scene = Scene(index, beat, release, photos.get(index), False, 0.0, 10.0)   # a 10-second scene
        count = max(1, len(scene.photos))
        for number in range(count):
            frame = scene.render(10 * (number + 0.5) / count)
            draw_captions(frame, caption_chunks(beat.lines[0])[0])
            if grain:
                frame = grain.apply(frame, index * 10 + number)
            name = f"scene-{index + 1:02}" + (f"-{number + 1}" if count > 1 else "")
            frame.save(out / f"{name}.jpg", quality=88)
            tiles.append(frame.resize((405, 720), Image.Resampling.BICUBIC))
    columns = min(5, len(tiles))
    rows = math.ceil(len(tiles) / columns)
    sheet = Image.new("RGB", (columns * 415 + 10, rows * 730 + 10), "#000000")
    for index, tile in enumerate(tiles):
        sheet.paste(tile, (10 + index % columns * 415, 10 + index // columns * 730))
    sheet.save(out / "sheet.jpg", quality=85)


def srt_time(seconds):
    milliseconds = round(seconds * 1000)
    total_seconds, fraction = divmod(milliseconds, 1000)
    minutes, sec = divmod(total_seconds, 60)
    hours, minute = divmod(minutes, 60)
    return f"{hours:02}:{minute:02}:{sec:02},{fraction:03}"


def write_subtitles(captions, path: Path):
    entries = []
    for index, caption in enumerate(captions, 1):
        entries.append(f"{index}\n{srt_time(caption.start)} --> {srt_time(caption.end)}\n{caption.text}\n")
    path.write_text("\n".join(entries), encoding="utf-8")
