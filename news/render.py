"""Render vertical news video with timed Japanese captions and stable motion."""
from dataclasses import dataclass
from functools import lru_cache
import math
from pathlib import Path
import re
import subprocess

import budoux
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .story import VOICE_CREDIT, japanese_date

W, H, FPS = 1080, 1920, 30
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


def crop_photo(image, position, height, focus=(0.5, 0.5)):
    iw, ih = image.size
    scale = max(W / iw, height / ih) * (1.0 + 0.15 * position)
    cw, ch = W / scale, height / scale
    left = (iw - cw) * min(1, max(0, focus[0] - 0.04 + 0.08 * position))
    top = (ih - ch) * min(1, max(0, focus[1] - 0.10 * position))
    return image.resize((W, height), Image.Resampling.BICUBIC, box=(left, top, left + cw, top + ch))


@lru_cache(maxsize=8)
def backdrop(key, height):
    image = BACKDROPS[key]
    soft = crop_photo(image, 0, height).resize((W // 8, height // 8)).filter(ImageFilter.GaussianBlur(6))
    return Image.eval(soft.resize((W, height), Image.Resampling.BICUBIC), lambda level: level * 0.45)


BACKDROPS = {}


def whole_photo(image, position, height):
    """Show the whole picture (portraits, charts, documents) over a blurred copy of itself."""
    BACKDROPS[id(image)] = image
    frame = backdrop(id(image), height).copy()
    scale = min(W / image.width, height / image.height) * (0.94 + 0.06 * position)
    size = (round(image.width * scale), round(image.height * scale))
    frame.paste(image.resize(size, Image.Resampling.BICUBIC), ((W - size[0]) // 2, (height - size[1]) // 2))
    return frame


def layout(beat, release, photo, demo):
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
    label(draw, 70, 261, beat.label, style.tag)

    if photo:
        # Picture scene: picture, then headline, value (big figure) and evidence (small text) under each other.
        draw.rectangle((0, 338, W, 1054), fill=style.photo_bed)
        draw.rectangle((0, 1038, W, 1054), fill=style.accent)
        label(draw, 70, 380, "資料写真", style.photo_tag, style.photo_tag_text)
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

    draw.line((70, 1704, W - 70, 1704), fill=style.rule, width=2)
    if release.publisher:
        text(draw, 70, 1742, f"出典  {release.publisher}", 29, style.muted, bold=False)
    text(draw, W - 70, 1742, VOICE_CREDIT, 24, style.muted, bold=False, anchor="rt")
    if photo:
        credit = f"写真  {photo.creator}" + (f" / {photo.license}" if photo.license else "")
        credit, credit_size = fit(credit, 940, 23, 2, bold=False, smallest=16)
        text(draw, 70, 1806, credit, credit_size, style.muted, bold=False)
    return image


def draw_captions(image, caption):
    draw = ImageDraw.Draw(image)
    face = font(CAPTION_SIZE)
    contents = caption.splitlines()
    height = 83 * len(contents) + 26
    draw.rounded_rectangle((69, 1598 - height // 2, 1011, 1598 + height // 2), radius=19, fill=style.caption_box)
    for line_index, line in enumerate(contents):
        draw.text((W / 2, 1598 - height / 2 + 21 + 83 * line_index), line,
                  font=face, fill=style.caption_text, anchor="mt", stroke_width=1, stroke_fill=style.caption_text)


def frame_for(base, photo, fraction, caption):
    frame = base.copy()
    if photo:
        ease = fraction * fraction * (3 - 2 * fraction)
        picture = (whole_photo(photo.image, ease, 700) if photo.fit == "contain"
                   else crop_photo(photo.image, ease, 700, photo.focus))
        frame.paste(picture, (0, 338))
        draw = ImageDraw.Draw(frame)
        label(draw, 70, 380, "資料写真", style.photo_tag, style.photo_tag_text)
    draw_captions(frame, caption)
    return frame


def encode(beats, release, photos, demo, intervals, captions, wav, out):
    cover_beat = beats[0]
    first_photo = photos.get(0)
    cover = frame_for(layout(cover_beat, release, first_photo, demo), first_photo, 0.22, captions[0].text)
    cover.save(out / "cover.jpg", quality=92)

    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", f"{W}x{H}", "-framerate", str(FPS), "-i", "-",
        "-i", str(wav), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-af", "loudnorm=I=-16:TP=-1.5:LRA=7",
        "-movflags", "+faststart", "-shortest", str(out / "video.mp4"),
    ]
    cue = 0
    frame_index = 0
    with subprocess.Popen(cmd, stdin=subprocess.PIPE) as process:
        try:
            for scene, (beat, (start, end)) in enumerate(zip(beats, intervals, strict=True)):
                scene_photo = photos.get(scene)
                base = layout(beat, release, scene_photo, demo)
                cache = {}
                while frame_index < math.ceil(end * FPS):
                    moment = frame_index / FPS
                    while cue + 1 < len(captions) and moment >= captions[cue].end:
                        cue += 1
                    current = captions[cue].text
                    if scene_photo:
                        fraction = min(1, max(0, (moment - start) / (end - start)))
                        raw = frame_for(base, scene_photo, fraction, current).tobytes()
                    else:
                        if current not in cache:
                            cache[current] = frame_for(base, None, 0, current).tobytes()
                        raw = cache[current]
                    process.stdin.write(raw)
                    frame_index += 1
        finally:
            process.stdin.close()
        if process.wait():
            raise RuntimeError("FFmpeg failed")


def stills(beats, release, photos, out):
    """One frame per scene, without the voice, to check pictures and text before rendering."""
    tiles = []
    for scene, beat in enumerate(beats):
        photo = photos.get(scene)
        frame = frame_for(layout(beat, release, photo, False), photo, 0.5, caption_chunks(beat.lines[0])[0])
        frame.save(out / f"scene-{scene + 1:02}.jpg", quality=88)
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
