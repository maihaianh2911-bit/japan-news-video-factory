"""Render vertical news video with timed Japanese captions and stable motion."""
from dataclasses import dataclass, replace
from functools import lru_cache
import math
import os
from pathlib import Path
import re
import subprocess

import budoux
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from . import faces
from .edits import AUTO_CUT, CUTS, MOVES, edit_list
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
    caption_box: str = "#0b1421"   # "" = no box: the caption is printed on the page
    caption_text: str = WHITE
    grain: bool = False
    layout: str = "news"           # "news": picture in the upper part; "story": a large picture with the text on it


STYLES = {
    "news": Style(),
    "paper": Style(family="Serif", background="#eee2bf", text="#2a1d10", muted="#6f5d40", accent="#8e2b1b",
                   tag="#4a3520", tag_text="#f6ecd2", photo_bed="#d8c79e", photo_tag="#eee2bf", photo_tag_text="#2a1d10", value="#8e2b1b", card="#f7eed6",
                   card_ink="#2a1d10", card_muted="#6f5d40", rule="#9c8a68", caption_box="#2e2114",
                   caption_text="#f8f0da", grain=True),
    # "story": the old-newspaper page for a story told in pictures (history, a life, a love story): the picture
    # fills most of the page, the year of the scene stands at the top, the headline lies on the foot of the picture
    # and a quote is printed big over the picture while it is spoken.
    "story": Style(family="Serif", background="#eee2bf", text="#f8efd9", muted="#6f5d40", accent="#8e2b1b",
                   tag="#8e2b1b", tag_text="#f8efd9", photo_bed="#1a120a", photo_tag="#eee2bf",
                   photo_tag_text="#2a1d10", value="#f1c96b", card="#f7eed6", card_ink="#2a1d10",
                   card_muted="#6f5d40", rule="#9c8a68", caption_box="", caption_text="#2a1d10", grain=True,
                   layout="story"),
    # "history": the frame of the history channel (trial of 20/11/2026): a dark ink page, the picture or the clip
    # fills the upper three quarters and melts into the page at its foot, the kicker stands in a vermilion seal,
    # the headline lies on the melting foot and the captions are printed in ivory on the dark page.
    "history": Style(family="Serif", background="#100d0a", text="#f4ead2", muted="#857b68", accent="#b3261e",
                     tag="#b3261e", tag_text="#f4ead2", photo_bed="#100d0a", photo_tag="#100d0a",
                     photo_tag_text="#f4ead2", value="#d9b96a", card="#1b1612", card_ink="#f4ead2",
                     card_muted="#857b68", rule="#5a4d33", caption_box="", caption_text="#f4ead2", grain=False,
                     layout="ink"),
    # "full": the picture fills the whole frame, nothing dark laid over it; the headline, the quote and the captions
    # stand in the middle of the frame, a little under its centre (under the face), in white and pale gold with a
    # dark outline (owner, 21/11/2026: "để ảnh full màn hình… không cần khoảng tối… để chữ ở giữa màn hình").
    "full": Style(family="Serif", background="#0d0a08", text="#ffffff", muted="#f4ead2", accent="#b3261e",
                  tag="#b3261e", tag_text="#f4ead2", photo_bed="#0d0a08", photo_tag="#0d0a08",
                  photo_tag_text="#f4ead2", value="#ffe9a8", card="#1b1612", card_ink="#f4ead2",
                  card_muted="#857b68", rule="#5a4d33", caption_box="", caption_text="#ffe9a8", grain=False,
                  layout="full"),
    # "band" (owner, 24/11/2026, from a short he liked: "lịch sử dựng dạng này đẹp hơn, vì mình toàn tìm đc ảnh
    # ngang"): the scene's own picture, blurred and dark, fills the frame; the kicker and the big title (masthead)
    # stand at the top between gold rules, the era of the scene in gold on the right, the picture itself in a wide
    # band across the middle between two thin gold lines, the headline and the pale gold captions under it.
    "band": Style(family="Serif", background="#0e0b09", text="#ffffff", muted="#d9cdb4", accent="#b3261e",
                  tag="#b3261e", tag_text="#f4ead2", photo_bed="#0e0b09", photo_tag="#0e0b09",
                  photo_tag_text="#f4ead2", value="#ffe9a8", card="#1b1612", card_ink="#f4ead2",
                  card_muted="#857b68", rule="#7a6744", caption_box="", caption_text="#f3dfae", grain=False,
                  layout="band"),
    # "album" (owner, 25/11/2026: "M có thể tự làm vài khung nữa, khoảng 5 khung đổi liên thiên là ổn"): a family photo
    # album for love, couple and mother-and-child stories: warm cream paper, the picture as a print in a white mat
    # with a strip of tape, the era written on the mat under the picture, the headline and the captions in dark ink.
    "album": Style(family="Serif", background="#efe4cf", text="#2f2116", muted="#7a6a55", accent="#b3452f",
                   tag="#b3452f", tag_text="#fff8ee", photo_bed="#efe4cf", photo_tag="#efe4cf",
                   photo_tag_text="#2f2116", value="#b3452f", card="#fbf6ec", card_ink="#2f2116",
                   card_muted="#7a6a55", rule="#b9a789", caption_box="", caption_text="#2f2116", grain=False,
                   layout="album"),
    # "magazine" (same day): a clean white weekly-magazine page for today's stories: the picture across the top,
    # a red rule, the era in red, a bold black headline set left, dark captions; the kicker as a red tag on the picture.
    "magazine": Style(family="Sans", background="#fbfaf7", text="#111111", muted="#6b6b6b", accent="#c8102e",
                      tag="#c8102e", tag_text="#ffffff", photo_bed="#fbfaf7", photo_tag="#fbfaf7",
                      photo_tag_text="#111111", value="#c8102e", card="#f2f0eb", card_ink="#111111",
                      card_muted="#6b6b6b", rule="#d8d4cc", caption_box="", caption_text="#1b1b1b", grain=False,
                      layout="magazine"),
}
style = STYLES["news"]


def use_style(name):
    global style
    style = STYLES[name]


# --- "host": a narrator character in the lower part of the "band" frame (owner, 26/11/2026, from a short he liked:
# "kiểu có 1 con nhân vật ở dưới, còn hình chạy ở trên"). The story names it: "host": {"name": "samurai",
# "poses": [one per scene]}; its pictures are stories/media/host/<name>/<pose>.png (transparent, waist up, made by
# tools/host_cut.py from the sheets the owner had drawn). The picture band moves up and gets shorter (16:9), the
# headline and the captions sit under it, the character stands at the foot, sways a little, moves its mouth while
# the voice speaks, and opens each scene with the scene's gesture.
HOST = None
HOST_POSES = ("neutral", "talk", "point", "cross", "present", "surprised")
HOST_TOP, HOST_PICTURE = 410, 608        # the picture band in the host frame: from y 410, 1080x608 (16:9)
HOST_CAPTION_CENTRE, HOST_QUOTE_CENTRE = 1196, 1160
HOST_FIGURE_HEIGHT, HOST_GESTURE = 640, 2.2   # the character's height on screen; how long a gesture is held
HOST_IMAGES = {}


def use_host(host):
    """Switch the "band" frame to its narrator form (or back to the plain band when `host` is None)."""
    global HOST, BAND_TOP, BAND_HEIGHT, BAND_QUOTE_CENTRE
    HOST = dict(host) if host else None
    if HOST:
        BAND_TOP, BAND_HEIGHT, BAND_QUOTE_CENTRE = HOST_TOP, HOST_PICTURE, HOST_QUOTE_CENTRE
    else:
        BAND_TOP, BAND_HEIGHT, BAND_QUOTE_CENTRE = 470, 780, 1490
    BOXES["band"] = (BAND_TOP, BAND_HEIGHT)
    band_shade.cache_clear()


def host_image(pose):
    name = HOST["name"]
    if (name, pose) not in HOST_IMAGES:
        image = Image.open(Path("stories/media/host") / name / f"{pose}.png").convert("RGBA")
        scale = HOST_FIGURE_HEIGHT / image.height
        HOST_IMAGES[name, pose] = image.resize((round(image.width * scale), HOST_FIGURE_HEIGHT),
                                               Image.Resampling.LANCZOS)
    return HOST_IMAGES[name, pose]


def draw_host(frame, scene_number, age, speaking, frame_index):
    """The narrator at the foot of the frame: the scene's gesture for its first seconds, then the calm pose with the
    mouth opening and closing while the voice speaks (`speaking`), a light sway all the time."""
    poses = HOST.get("poses") or []
    gesture = poses[scene_number] if scene_number < len(poses) else "neutral"
    if gesture != "neutral" and age < HOST_GESTURE:
        pose = gesture
    else:
        pose = "talk" if speaking and (frame_index // 4) % 2 == 0 else "neutral"
    figure = host_image(pose)
    sway = math.sin(frame_index / FPS * math.pi) * 6
    x = (W - figure.width) // 2
    frame.paste(figure, (x, H - figure.height + round(abs(sway))), figure)


def voice_levels(wav, frames):
    """For each video frame, whether the voice is speaking (loud enough), from the voice wav."""
    import wave
    import array
    with wave.open(str(wav), "rb") as sound:
        rate, width, channels = sound.getframerate(), sound.getsampwidth(), sound.getnchannels()
        data = sound.readframes(sound.getnframes())
    if width != 2:
        return [False] * frames
    samples = array.array("h", data)[::channels]
    step = rate / FPS
    levels = []
    for index in range(frames):
        chunk = samples[int(index * step):int((index + 1) * step)]
        levels.append((sum(value * value for value in chunk[::8]) / max(1, len(chunk[::8]))) ** 0.5 if chunk else 0.0)
    loud = sorted(levels)[int(len(levels) * 0.9)] if levels else 0.0
    return [level > loud * 0.18 for level in levels]


# Picture effects of a story ("fx" in stories/<name>.json), all off by default:
#   "motion": the camera has a rhythm (quick at first, then settling) instead of one even speed
#   "depth":  pictures that fill the frame get a light parallax from a depth map (news/depth.py)
#   "text":   the tag, the headline and a quote come in piece by piece; the caption darkens as it is spoken
#   "face":   a display typeface for the large text (headline, quote, year, captions): a font file, or true for
#             $NEWS_DISPLAY_FONT / fonts/ShipporiMinchoB1-ExtraBold.ttf (SIL Open Font License)
FX = {}
DISPLAY_FONT = ""


def use_fx(fx):
    global FX, DISPLAY_FONT
    FX = dict(fx or {})
    face = FX.get("face")
    path = (os.environ.get("NEWS_DISPLAY_FONT") or "fonts/ShipporiMinchoB1-ExtraBold.ttf") if face is True else face or ""
    DISPLAY_FONT = path if path and Path(path).exists() else ""
    if face and not DISPLAY_FONT:
        print(f"warning: display font {path!r} not found, the usual typeface is used")
CAPTION_WIDTH, CAPTION_SIZE = 866, 52
PHOTO_TEXT_BOTTOM = 1490   # the caption box (two lines) starts at about 1502
PHRASES = budoux.load_default_japanese_parser()


def font(size, bold=True):
    """The typeface of the frame; large bold text is set in the display face when the story has one."""
    if DISPLAY_FONT and bold and size >= 40:
        return display_face(DISPLAY_FONT, size)
    return face_of(style.family, size, bold)


@lru_cache(maxsize=128)
def display_face(path, size):
    return ImageFont.truetype(path, size)


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
    face = face_of(style.family, CAPTION_SIZE, True)   # not the display face: the split stays the same with it
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
STORY_TOP, STORY_HEIGHT = 172, 1258     # "story": the picture from under the masthead to above the captions
INK_TOP, INK_HEIGHT = 0, 1480           # "history": the picture from the top of the frame, melting into the page
INK_GOLD = "#d9b96a"
FULL_TEXT_CENTRE, FULL_TEXT_FOOT, OUTLINE = 1300, 1420, "#140e08"   # "full": the middle of the headline and of a
# quote, the lowest their foot may come (the captions run under it), the colour of the text's outline
BAND_TOP, BAND_HEIGHT = 470, 780       # "band": the picture in a wide band across the middle (about 7:5)
# "album": the picture is made full width (W x ALBUM_HEIGHT) and set into the print at ALBUM_W x ALBUM_SHOWN
ALBUM_X, ALBUM_TOP, ALBUM_W, ALBUM_SHOWN = 80, 196, 920, 1000
ALBUM_HEIGHT = round(ALBUM_SHOWN * W / ALBUM_W)
MAG_HEIGHT = 1130                      # "magazine": the picture across the top of the page
BOXES = {"story": (STORY_TOP, STORY_HEIGHT), "ink": (INK_TOP, INK_HEIGHT), "full": (0, H),
         "band": (BAND_TOP, BAND_HEIGHT), "album": (ALBUM_TOP, ALBUM_HEIGHT), "magazine": (0, MAG_HEIGHT)}
ON_PICTURE = ("story", "ink", "full")   # frames whose headline and quote are printed on the picture


def box_height(name):
    """Height of the picture in the frame of the style `name` (for what is cut to fit it: a clip)."""
    return BOXES.get(STYLES[name].layout, (PHOTO_TOP, PHOTO_HEIGHT))[1]


def photo_box():
    """Top and height of the picture in the current frame."""
    return BOXES.get(style.layout, (PHOTO_TOP, PHOTO_HEIGHT))


def page_area():
    """The part of the frame that turns like a page, goes dark in a dip (the rest stays)."""
    if style.layout == "band":   # the title at the top stays while the scene changes under it
        return (0, BAND_TOP - 90, W, H)
    if style.layout == "full" or style.layout == "magazine":
        return (0, 0, W, H)
    if style.layout == "album":   # the kicker at the top stays
        return (0, 150, W, H)
    return (0, 0, W, 1752) if style.layout in ON_PICTURE else (0, 245, W, 1700)


def caption_centre():
    if HOST and style.layout == "band":
        return HOST_CAPTION_CENTRE
    return {"story": 1590, "ink": 1614, "full": 1560, "band": 1590, "album": 1652, "magazine": 1622}.get(style.layout, 1598)
TEXT_IN, CAPTION_IN, PHOTO_FADE, TRANSITION = 0.45, 0.2, 0.5, 0.5   # seconds
HOOK_SECONDS = 5.0   # the first picture of a video with "fx" stays at most this long (owner, 21/11/2026)
MOTIONS = ("in", "right", "out", "left")   # one per picture, in turn


def ease(value):
    value = min(1.0, max(0.0, value))
    return value * value * (3 - 2 * value)


def crop_photo(image, height, focus=(0.5, 0.5), zoom=1.0, shift=0.0):
    """The part of the picture shown: `zoom` 1 fills the frame, `shift` moves the window sideways (-1 to 1)."""
    iw, ih = image.size
    scale = max(W / iw, height / ih) * zoom
    cw, ch = min(iw, W / scale), min(ih, height / scale)
    left = max(0.0, (iw - cw) * min(1, max(0, focus[0] + shift)))
    top = max(0.0, (ih - ch) * min(1, max(0, focus[1])))
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


# --- Moves chosen by name (news/edits.py MOVES). Their speed follows the time the picture is on screen: a short
# picture moves a shorter way, a long one a longer way, so neither rushes nor crawls.

CLOSE_UP = 1.8   # how close a close-up starts (1 = the picture fills the frame)


def clamp(value, low, high):
    return min(high, max(low, value))


def view(image, height, zoom, x, y):
    """The window of the picture at `zoom` (1 fills the frame); x and y (0 to 1) place it within the room left."""
    iw, ih = image.size
    scale = max(W / iw, height / ih) * zoom
    # rounding can make the window a hair larger than the picture (a negative offset, refused by Pillow)
    cw, ch = min(iw, W / scale), min(ih, height / scale)
    left, top = max(0.0, (iw - cw) * clamp(x, 0, 1)), max(0.0, (ih - ch) * clamp(y, 0, 1))
    return image.resize((W, height), Image.Resampling.BICUBIC, box=(left, top, left + cw, top + ch))


def pan_plan(size, across, along, centre, seconds):
    """Zoom, start and end (0 to 1 of the room) and length in pixels of a pan along one side of the picture.
    `size` is that side of the picture and `across` the same side of the frame; `along` is the scale that fills
    the frame. About 70 pixels a second around the focus point, kept inside the picture."""
    travel = clamp(120 * seconds, 200, 760)   # owner, 19/11/2026: a picture must be seen to move all the time
    zoom = clamp((across + travel) / (size * along), 1.10, 1.50)
    room = size * along * zoom - across
    half = min(travel, room) / room / 2
    middle = clamp(centre, half, 1 - half)
    return zoom, middle - half, middle + half, min(travel, room)


def paced(t):
    """The rhythm of the camera ("fx": motion): it starts quicker and settles, but never stops. 0 to 1, as t."""
    if not FX.get("motion"):
        return t
    # a light rhythm only: the camera keeps moving to the end (the end speed is three quarters of the start);
    # the stronger settling of 17/11 looked like a still picture in its second half (owner, 19/11/2026)
    return 0.85 * t + 0.15 * (1 - (1 - min(t, 1.0)) ** 2)


PARALLAX = {}
PUSH, PAN = 0.07, 0.012   # how much more the nearest things grow in a push-in; their shift in a pan (share of the side)


def with_depth(photo, name, p):
    """The picture as the moving camera sees it at progress p of its move ("fx": depth): near things move more
    than far ones. A light move around the focus point, so that a face there keeps its shape."""
    if not FX.get("depth") or photo.fit == "contain" or not getattr(photo, "depth", True):
        return photo.image
    key = id(photo.image)
    if key not in PARALLAX:
        try:   # needs numpy, onnxruntime, opencv and the model: without them the picture simply stays flat
            from .depth import Parallax
            PARALLAX[key] = Parallax(photo.image, photo.focus)
        except Exception as error:
            if not PARALLAX.get("warned"):
                print(f"warning: depth effect off ({type(error).__name__}: {str(error)[:120]})")
            PARALLAX["warned"] = True
            PARALLAX[key] = None
    scene = PARALLAX[key]
    if scene is None:
        return photo.image
    width, height = scene.image.size
    swing = 2 * min(p, 1.25) - 1
    if name in ("pan-right", "pan-left"):
        return scene.at(pan_x=(-1 if name == "pan-right" else 1) * PAN * width * swing, push=0.3 * PUSH * p)
    if name in ("rise", "fall"):
        return scene.at(pan_y=(1 if name == "rise" else -1) * PAN * height * swing, push=0.3 * PUSH * p)
    if name in ("pull-back", "reveal"):
        return scene.at(push=PUSH * (1 - min(p, 1.0)))
    return scene.at(push=PUSH * p * (0.5 if name in ("hold", "close-up") else 1))


def named_photo(photo, t, name, seconds, height=PHOTO_HEIGHT, delay=0.0):
    """The picture at time t (0 at its start, 1 at its end, a little more while it fades out) for a move of the
    catalogue; `seconds` is how long the picture stays. `delay`: seconds a punch-in waits (until the scene has
    arrived), so that its hit is seen."""
    t = clamp(t, 0.0, 1.25)
    p = paced(t)   # the steady moves follow the rhythm of the camera; reveal and punch-in have their own
    (fx, fy) = photo.focus
    if photo.fit == "contain":   # the whole picture: it grows, shrinks or stays
        # a quarter or more in size (owner, 25/11/2026: a whole picture growing by a tenth looked still, mostly in
        # the "album" print, which is smaller than the frame)
        small = 1 - clamp(0.05 * seconds, 0.22, 0.32)
        size = {"push-in": small + (1 - small) * min(1, p), "pull-back": 1 - (1 - small) * min(1, p)}.get(name, 1.0)
        return whole_photo(photo.image, (size - 0.86) / 0.14, height)
    image = with_depth(photo, name, t if name in ("reveal", "punch-in") else p)
    # at least 25 % closer or wider, so that even a 2-second picture is seen to move; 45 % at most
    # (owner, 19/11/2026: "nhiều ảnh trông như không chuyển động gì")
    gain = clamp(0.08 * seconds, 0.25, 0.45)
    if name == "push-in":
        return view(image, height, 1.0 + gain * p, fx, fy)
    if name == "pull-back":
        return view(image, height, max(1.0, 1.02 + gain * (1 - p)), fx, fy)
    if name == "close-up":   # tight around the focus point, still moving closer
        return view(image, height, CLOSE_UP + clamp(0.05 * seconds, 0.15, 0.35) * p, fx, fy)
    if name == "reveal":
        start, done = 1.0 + clamp(0.16 * seconds, 0.45, 0.8), 1 - (1 - min(1, t)) ** 2
        return view(image, height, start - (start - 1.0) * done, fx, fy)
    if name == "punch-in":
        quick, now = min(0.35, seconds * 0.25), max(0.0, t * seconds - delay)
        if now < quick:
            return view(image, height, 1.0 + 0.26 * (1 - (1 - now / quick) ** 2), fx, fy)
        return view(image, height, 1.26 + 0.012 * (now - quick), fx, fy)
    fill = max(W / image.width, height / image.height)
    if name in ("pan-right", "pan-left"):
        zoom, first, last, _ = pan_plan(image.width, W, fill, fx, seconds)
        if name == "pan-left":
            first, last = last, first
        return view(image, height, zoom, first + (last - first) * p, fy)
    if name in ("rise", "fall"):
        zoom, first, last, _ = pan_plan(image.height, height, fill, fy, seconds)
        if name == "rise":
            first, last = last, first
        return view(image, height, zoom, fx, first + (last - first) * p)
    return view(image, height, 1.0 + clamp(0.03 * seconds, 0.08, 0.15) * p, fx, fy)   # hold: a slow drift, never frozen


def move_warning(photo, seconds=5.0, height=PHOTO_HEIGHT):
    """Why the chosen move will not look good on this picture, or None."""
    image, name = photo.image, photo.move
    if not name or photo.fit == "contain":
        return None
    fill = max(W / image.width, height / image.height)
    if name in ("pan-right", "pan-left") and pan_plan(image.width, W, fill, photo.focus[0], seconds)[3] < 100:
        return f"{name}: the picture is not wide enough to pan across (try rise, fall or push-in)"
    if name in ("rise", "fall") and pan_plan(image.height, height, fill, photo.focus[1], seconds)[3] < 100:
        return f"{name}: the picture is not tall enough to move along (try pan-left, pan-right or push-in)"
    if name == "close-up" and tuple(photo.focus) == (0.5, 0.5):
        return "close-up: no \"focus\" given, it closes in on the middle of the picture (put focus on the detail)"
    closest = {"close-up": CLOSE_UP + 0.25, "reveal": 1.8, "punch-in": 1.3}.get(name)
    if closest and W / (fill * closest) < 500:
        return f"{name}: the picture is small ({image.width}x{image.height}), it will look soft that close"
    return None


# The rules of the edit about pictures (owner, 19/11/2026: "hook 5s đầu phải là ảnh đẹp, rồi ảnh k bị mất mặt").
# In the "story" frame the headline is printed on the foot of the picture and the hook line higher still: a face
# whose middle lies in that part is under the text. The first picture is the best one of the video.
HEADLINE_ZONE, HOOK_ZONE, HOOK_SIDE = 0.22, 0.34, 900
FULL_LINE = 0.6   # "full": the text stands from about three fifths of the frame down: a face ends above it


def frame_windows(photo, seconds=5.0, height=PHOTO_HEIGHT):
    """The part of the picture the frame shows at the start and at the end of its move: two windows (left, top,
    right, bottom) in 0–1 of the picture. Asked of the code that makes the video itself: a picture whose grey rises
    from one side to the other is sent through the same move, and its edges in the frame say where they came from."""
    size = photo.image.size
    down = Image.linear_gradient("L").resize(size, Image.Resampling.BILINEAR)
    across = Image.linear_gradient("L").transpose(Image.Transpose.TRANSPOSE).resize(size, Image.Resampling.BILINEAR)
    windows = []
    for moment in (0.0, 1.0):
        def shown(probe):
            if photo.move:
                return named_photo(replace(photo, image=probe, depth=False), moment, photo.move, seconds, height)
            return view(probe, height, 1.0 + 0.2 * moment, *photo.focus)   # the automatic moves: up to a fifth closer
        sideways, upright = shown(across), shown(down)
        windows.append((sideways.getpixel((0, height // 2)) / 255, upright.getpixel((W // 2, 0)) / 255,
                        sideways.getpixel((W - 1, height // 2)) / 255, upright.getpixel((W // 2, height - 1)) / 255))
    return windows


def inside(box, window, slack=0.006):
    return (box[0] >= window[0] - slack and box[1] >= window[1] - slack
            and box[2] <= window[2] + slack and box[3] <= window[3] + slack)


def face_warnings(photo, hook=False, seconds=5.0, height=PHOTO_HEIGHT):
    """Which of the owner's picture rules this picture breaks as it is framed (CLAUDE.md, "The picture rules of the
    edit"): the whole face stays inside the frame from the start of its move to the end, the text printed on the
    picture does not lie over it, and on the first picture (`hook`) the face is in the upper half. The faces are
    found by news/faces.py. Nothing is said when the faces cannot be looked for or the picture has none."""
    if photo.fit == "contain":
        return []
    found = faces.find(photo.image)
    if not found:
        return []
    main = faces.main_faces(found)
    if not main:   # a crowd
        return []
    windows = frame_windows(photo, seconds, height)
    zone = (HOOK_ZONE if hook else HEADLINE_ZONE) if style.layout in ON_PICTURE else 0.0

    def place(box, window, part=0.5):   # how far down the frame the middle (or `part`) of the face is (0 top, 1 bottom)
        return (box[1] + (box[3] - box[1]) * part - window[1]) / max(0.001, window[3] - window[1])
    cut = any(not inside(box, window) for box in main for window in windows)
    kept = [box for box in main if all(inside(box, window) for window in windows)]
    under = bool(zone) and any(place(box, window) > 1 - zone for box in kept for window in windows)
    if style.layout == "full":   # the text stands in the middle of the picture: the whole face stays above it
        under = any(place(box, window, 1.0) > FULL_LINE for box in kept for window in windows)
    low = hook and any(place(box, windows[0]) > 0.5 for box in kept)
    advice = 'another move, the whole picture ("fit": "contain") or another picture'
    if cut and photo.move not in ("pan-right", "pan-left", "rise", "fall"):
        # the focus that puts the faces in the middle of the frame at its closest, if the frame can hold them then
        tight = min(windows, key=lambda window: window[2] - window[0])
        wide, tall = tight[2] - tight[0], tight[3] - tight[1]
        left, top = min(box[0] for box in main), min(box[1] for box in main)
        right, bottom = max(box[2] for box in main), max(box[3] for box in main)
        if right - left < wide - 0.02 and bottom - top < tall - 0.02:
            centred = (round(clamp(((left + right) / 2 - wide / 2) / max(0.001, 1 - wide), 0, 1), 2),
                       round(clamp(((top + bottom) / 2 - tall / 2) / max(0.001, 1 - tall), 0, 1), 2))
            again = frame_windows(replace(photo, focus=centred), seconds, height)
            if all(inside(box, window) for box in main for window in again):
                advice = f'try "focus": {list(centred)}; or {advice}'
    said = []
    if cut:
        said.append("a face is cut by the frame or leaves it during the move (the whole face stays in the frame): "
                    + advice)
    if under:
        said.append("a face lies under the " + ("hook line" if hook else "headline") + " printed on the "
                    + ("middle" if style.layout == "full" else "foot") + " of the picture: a picture or a framing "
                    "with the face higher")
    elif low:
        said.append("the hook: the face is in the lower half of the first picture (it belongs in the upper half, "
                    "clear of the hook line): a picture or a framing with the face higher")
    return said


def hook_warnings(photo):
    """The first picture of a video (the hook, about its first 5 seconds) is its best one: large and sharp, a
    photograph and not a page, a document or a collage (owner, 19/11/2026)."""
    said = []
    if min(photo.image.size) < HOOK_SIDE:
        said.append(f"the hook: the first picture is small ({photo.image.width}x{photo.image.height}, under "
                    f"{HOOK_SIDE} px on one side), it will look soft: open on the best picture of the video")
    if photo.fit == "contain" or not photo.depth:
        said.append("the hook: the first picture is shown whole or marked flat (a document, a page, a collage): "
                    "open on a photograph of the person, the place or the thing")
    return said


STORY_TEXT = "#f8efd9"


def piece(kind, paint, order=0):
    """One element of a scene's text on its own layer, cut to what it holds: (kind, picture, (x, y), order). A row
    of text gets a soft shadow, so that it stands clear of the picture."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    paint(ImageDraw.Draw(layer))
    box = layer.getbbox()
    if not box:
        return None
    if kind == "row":
        box = (max(0, box[0] - 24), max(0, box[1] - 24), min(W, box[2] + 24), min(H, box[3] + 28))
        ink = layer.crop(box)
        soft = ImageChops.offset(ink.getchannel("A"), 0, 4).filter(ImageFilter.GaussianBlur(7))
        shadow = Image.new("RGBA", ink.size, (10, 6, 2, 0))
        shadow.putalpha(soft.point(lambda level: round(level * 0.6)))
        return kind, Image.alpha_composite(shadow, ink), box[:2], order
    return kind, layer.crop(box), box[:2], order


def story_layout(beat, release, has_photo, demo):
    """The "story" page: masthead with the kicker and the year of the scene, a large picture with the headline on its
    foot, the captions printed on the page under it, the credits at the bottom. Returns the page, the layer of the
    scene's text and, with "fx": text, that text as separate pieces that come in one after the other."""
    animated, parts = bool(FX.get("text")) and has_photo, []
    image = paper_grain(style.background).copy()
    draw = ImageDraw.Draw(image)
    ink = "#2a1d10"
    draw.rectangle((0, 0, W, 10), fill=style.accent)
    draw.rectangle((36, 26, W - 36, 31), fill=ink)
    draw.rectangle((36, 36, W - 36, 37), fill=ink)
    draw.rectangle((36, 146, W - 36, 147), fill=ink)
    draw.rectangle((36, 152, W - 36, 157), fill=ink)
    label(draw, 60, 62, release.kicker or "日本のニュース", style.accent, STORY_TEXT)
    if demo:
        text(draw, W // 2, 76, "動作確認", 28, GOLD, anchor="mt")
    if has_photo:
        draw.rectangle((0, STORY_TOP - 4, W, STORY_TOP + STORY_HEIGHT + 4), fill=style.photo_bed)
    draw.line((60, 1752, W - 60, 1752), fill=style.rule, width=2)
    if release.publisher:
        text(draw, 60, 1812, f"出典  {release.publisher}", 24, style.muted, bold=False)
    text(draw, W - 60, 1774, VOICE_CREDIT, 24, style.muted, bold=False, anchor="rt")
    if release.music:
        music = f"音楽  {release.music.title.rsplit('.', 1)[0]}"
        music, music_size = fit(music, 600, 22, 1, bold=False, smallest=16)
        text(draw, W - 60, 1812, music, music_size, style.muted, bold=False, anchor="rt")

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if not animated:   # animated: the year belongs to the page and stays still, only the scene's own text moves
        draw = ImageDraw.Draw(layer)
    if beat.era:
        era, era_size = fit(beat.era, 520, 68, 1, smallest=40)
        text(draw, W - 60, 46, era, era_size, style.accent, anchor="rt")
    else:
        text(draw, W - 60, 74, japanese_date(release), 35, style.muted, anchor="rt")
    draw = ImageDraw.Draw(layer)
    if not has_photo:   # a text card in the place of the picture
        draw.rounded_rectangle((70, 260, 1010, 1340), radius=32, fill=style.card, outline=style.rule, width=3)
        headline, size = fit(beat.headline, 840, 64, 3, smallest=40)
        y = text(draw, 119, 360, headline, size, style.card_ink)
        if beat.value:
            value, value_size = fit(beat.value, 840, 120, 1, smallest=56)
            y = text(draw, 119, y + 70, value, value_size, style.accent)
        if beat.evidence:
            evidence, evidence_size = fit(beat.evidence, 830, 40, 5, bold=False, smallest=26)
            text(draw, 119, y + 60, evidence, evidence_size, style.card_ink, bold=False)
        return image, layer, parts
    if animated:
        parts.append(piece("tag", lambda d: label(d, 60, STORY_TOP + 34, beat.label, style.tag, STORY_TEXT)))
    else:
        label(draw, 60, STORY_TOP + 34, beat.label, style.tag, STORY_TEXT)
    # the headline lies on the foot of the picture, over a dark gradient; built from the bottom up
    bottom = STORY_TOP + STORY_HEIGHT - 44
    blocks = []
    if beat.value:
        value, value_size = fit(beat.value, 960, 80, 1, smallest=56)
        blocks.append((value, value_size, style.value, True, 18))
    headline, size = fit(beat.headline, 960, 68 if len(beat.headline) < 25 else 56, 3, smallest=46)
    blocks.append((headline, size, STORY_TEXT, True, 18))
    if beat.evidence:
        evidence, evidence_size = fit(beat.evidence, 960, 34, 2, bold=False, smallest=26)
        blocks.append((evidence, evidence_size, STORY_TEXT, False, 12))
    heights = [block_height(value, size, spacing) for value, size, _, _, spacing in blocks]
    y = bottom - sum(heights) - 22 * (len(blocks) - 1)
    if animated:   # a short red rule is drawn first, then the rows rise into place one after the other
        parts.append(piece("rule", lambda d, y=y: d.rectangle((60, y - 34, 156, y - 28), fill="#c23a26")))
    order = 0
    for (value, size, colour, bold, spacing), height in zip(blocks, heights):
        if animated:
            for row, line in enumerate(value.splitlines()):
                parts.append(piece("row", lambda d, line=line, at=y + row * (size + spacing), size=size, colour=colour,
                                   bold=bold: d.text((60, at), line, font=font(size, bold), fill=colour), order))
                order += 1
        else:
            text(draw, 60, y, value, size, colour, bold=bold, spacing=spacing)
        y += height + 22
    return image, layer, [part for part in parts if part]


@lru_cache(maxsize=2)
def story_shade(height):
    """Dark gradients over the picture of the "story" page: a strong one at the foot (the headline lies on it) and a
    light one at the top (the tag)."""
    shade = Image.new("RGBA", (W, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shade)
    start = int(height * 0.52)
    for y in range(start, height):
        draw.line((0, y, W, y), fill=(14, 9, 4, round(225 * ((y - start) / (height - start)) ** 1.6)))
    for y in range(0, 150):
        draw.line((0, y, W, y), fill=(14, 9, 4, round(90 * (1 - y / 150) ** 2)))
    return shade


def upright_text(draw, x, y, value, size, fill, step=None):
    """Japanese written downwards: one character under the other, centred on x, from y. Returns the y below."""
    step = step or round(size * 1.22)
    for index, char in enumerate(value):
        draw.text((x, y + index * step + size // 2), char, font=font(size), fill=fill, anchor="mm")
    return y + len(value) * step


@lru_cache(maxsize=2)
def ink_shade(height):
    """Over the picture of the "history" page: its foot melts into the dark page (the headline lies there) and its
    top is a little darker (the seal and the year)."""
    shade = Image.new("RGBA", (W, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shade)
    for y in range(0, 280):
        draw.line((0, y, W, y), fill=(8, 6, 4, round(150 * (1 - y / 280) ** 2)))
    return shade


@lru_cache(maxsize=2)
def ink_mask(height):
    """How much of the picture is seen, line by line: all of it down to three fifths, then it melts into the page."""
    mask = Image.new("L", (W, height), 255)
    draw = ImageDraw.Draw(mask)
    start, gone = int(height * 0.60), height - 30
    for y in range(start, height):
        draw.line((0, y, W, y), fill=round(255 * (1 - ease((y - start) / (gone - start)) ** 0.9)))
    return mask


def ink_layout(beat, release, has_photo, demo):
    """The "history" page. Returns the page, the layer of the scene's text and its pieces: the seal and the year are
    "fixed" (drawn over the picture, never moving), the rest comes in piece by piece with "fx": text."""
    animated, parts = bool(FX.get("text")) and has_photo, []
    image = paper_grain(style.background).copy()
    draw = ImageDraw.Draw(image)
    draw.line((60, 1752, W - 60, 1752), fill=style.rule, width=2)
    if release.publisher:
        text(draw, 60, 1812, f"出典  {release.publisher}", 24, style.muted, bold=False)
    text(draw, W - 60, 1774, VOICE_CREDIT, 24, style.muted, bold=False, anchor="rt")
    if release.music:
        music, music_size = fit(f"音楽  {release.music.title.rsplit('.', 1)[0]}", 600, 22, 1, bold=False, smallest=16)
        text(draw, W - 60, 1812, music, music_size, style.muted, bold=False, anchor="rt")

    def seal(d):   # the kicker in a vermilion seal, written downwards
        kicker = release.kicker or "歴史の物語"
        d.rounded_rectangle((52, 62, 118, 62 + len(kicker) * 40 + 30), radius=7, fill=style.accent)
        d.rounded_rectangle((57, 67, 113, 62 + len(kicker) * 40 + 25), radius=4, outline="#e8b9a6", width=1)
        upright_text(d, 85, 80, kicker, 32, style.text, 40)

    def year(d):
        era, size = fit(beat.era, 620, 60, 1, smallest=40)
        d.text((W - 54, 74 + 3), era, font=font(size), fill=(6, 4, 2, 200), anchor="rt", stroke_width=1, stroke_fill=(6, 4, 2, 200))
        d.text((W - 56, 74), era, font=font(size), fill=INK_GOLD, anchor="rt")
        width = round(font(size).getlength(era))
        d.rectangle((W - 56 - width, 74 + size + 22, W - 56, 74 + size + 24), fill=INK_GOLD)

    parts.append(piece("fixed", seal))
    if beat.era:
        parts.append(piece("fixed", year))
    if demo:
        parts.append(piece("fixed", lambda d: text(d, W // 2, 76, "動作確認", 28, GOLD, anchor="mt")))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    if not has_photo:   # a text card in the place of the picture
        draw.rounded_rectangle((70, 300, 1010, 1340), radius=18, fill=style.card, outline=style.rule, width=2)
        draw.rectangle((119, 372, 215, 378), fill=style.accent)
        headline, size = fit(beat.headline, 840, 68, 3, smallest=40)
        y = text(draw, 119, 430, headline, size, style.card_ink)
        if beat.value:
            value, value_size = fit(beat.value, 840, 120, 1, smallest=56)
            y = text(draw, 119, y + 70, value, value_size, style.value)
        if beat.evidence:
            evidence, evidence_size = fit(beat.evidence, 830, 40, 5, bold=False, smallest=26)
            text(draw, 119, y + 60, evidence, evidence_size, style.card_ink, bold=False)
        return image, layer, [part for part in parts if part]
    bottom = INK_TOP + INK_HEIGHT - 44
    blocks = []
    if beat.value:
        value, value_size = fit(beat.value, 960, 84, 1, smallest=56)
        blocks.append((value, value_size, style.value, True, 18))
    headline, size = fit(beat.headline, 960, 80 if len(beat.headline) < 20 else 60, 3, smallest=46)
    blocks.append((headline, size, style.text, True, 18))
    if beat.evidence:
        evidence, evidence_size = fit(beat.evidence, 960, 34, 2, bold=False, smallest=26)
        blocks.append((evidence, evidence_size, style.text, False, 12))
    heights = [block_height(value, size, spacing) for value, size, _, _, spacing in blocks]
    y = bottom - sum(heights) - 22 * (len(blocks) - 1)

    def rule(d, y=y):
        d.rectangle((60, y - 36, 150, y - 31), fill="#c23a26")

    def tag(d, y=y):   # the scene's label beside the rule, in gold
        d.text((168, y - 34), beat.label, font=font(30), fill=INK_GOLD, anchor="lm")

    if animated:
        parts += [piece("rule", rule), piece("tag", tag)]
    else:
        rule(draw), tag(draw)
    order = 0
    for (value, size, colour, bold, spacing), height in zip(blocks, heights):
        if animated:
            for row, line in enumerate(value.splitlines()):
                parts.append(piece("row", lambda d, line=line, at=y + row * (size + spacing), size=size, colour=colour,
                                   bold=bold: d.text((60, at), line, font=font(size, bold), fill=colour), order))
                order += 1
        else:
            text(draw, 60, y, value, size, colour, bold=bold, spacing=spacing)
        y += height + 22
    return image, layer, [part for part in parts if part]


def outlined(d, x, y, value, size, fill, *, bold=True, anchor="mt", stroke=7):
    """A line of text with a dark outline, so that it reads on any picture with nothing dark laid under it."""
    d.text((x, y), value, font=font(size, bold), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=OUTLINE)


def full_layout(beat, release, has_photo, demo):
    """The "full" frame (owner, 21/11/2026): the picture fills the whole frame and nothing dark is laid over it.
    The tag stands at the top left; the headline stands in the middle of the frame, a little under its centre
    (under the face), white with a dark outline, and comes in row by row after the picture; the captions run
    under it as they are spoken. Everything is drawn as pieces over the picture ("fixed": the credits)."""
    animated, parts = bool(FX.get("text")) and has_photo, []
    image = Image.new("RGB", (W, H), style.background)

    # no credits on the picture (owner, 24/11/2026: the small lines at the foot cluttered the full picture): the
    # source, the voice, the music and every picture are named in credits.txt, which goes in the video's description
    if demo:
        parts.append(piece("fixed", lambda d: outlined(d, W // 2, 90, "動作確認", 28, GOLD, stroke=3)))
    tag = beat.era or release.kicker or "日本のニュース"
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    if not has_photo:   # a text card in the place of the picture
        draw.rounded_rectangle((70, 300, 1010, 1340), radius=18, fill=style.card, outline=style.rule, width=2)
        draw.rectangle((119, 372, 215, 378), fill=style.accent)
        headline, size = fit(beat.headline, 840, 68, 3, smallest=40)
        y = text(draw, 119, 430, headline, size, style.card_ink)
        if beat.value:
            value, value_size = fit(beat.value, 840, 120, 1, smallest=56)
            y = text(draw, 119, y + 70, value, value_size, style.value)
        if beat.evidence:
            evidence, evidence_size = fit(beat.evidence, 830, 40, 5, bold=False, smallest=26)
            text(draw, 119, y + 60, evidence, evidence_size, style.card_ink, bold=False)
        label(draw, 60, 80, tag, style.tag, style.tag_text)
        return image, layer, [part for part in parts if part]
    blocks = []
    headline, size = fit(beat.headline, 960, 92 if len(beat.headline) < 20 else 72, 3, smallest=48)
    blocks.append((headline, size, style.text, True, 22))
    if beat.value:
        value, value_size = fit(beat.value, 960, 96, 1, smallest=56)
        blocks.append((value, value_size, style.value, True, 18))
    if beat.evidence:
        evidence, evidence_size = fit(beat.evidence, 960, 36, 2, bold=False, smallest=26)
        blocks.append((evidence, evidence_size, style.muted, False, 12))
    heights = [block_height(value, size, spacing) for value, size, _, _, spacing in blocks]
    total = sum(heights) + 22 * (len(blocks) - 1)
    y = min(FULL_TEXT_CENTRE - total // 2, FULL_TEXT_FOOT - total)
    if animated:
        parts.append(piece("tag", lambda d: label(d, 60, 80, tag, style.tag, style.tag_text)))
    else:
        label(draw, 60, 80, tag, style.tag, style.tag_text)
    order = 0
    for (value, size, colour, bold, spacing), height in zip(blocks, heights):
        for row, line in enumerate(value.splitlines()):
            at = y + row * (size + spacing)
            if animated:
                parts.append(piece("row", lambda d, line=line, at=at, size=size, colour=colour, bold=bold:
                                   outlined(d, W // 2, at, line, size, colour, bold=bold,
                                            stroke=7 if bold else 4), order))
                order += 1
            else:
                outlined(draw, W // 2, at, line, size, colour, bold=bold, stroke=7 if bold else 4)
        y += height + 22
    return image, layer, [part for part in parts if part]


BAND_GOLD, BAND_IVORY = "#d9b96a", "#e9dcbd"


def band_layout(beat, release, has_photo, demo):
    """The "band" frame (owner, 24/11/2026): the kicker between two gold rules and the big title (masthead) at the
    top, a small ornament under it, the era of the scene in gold on the right above the picture, the picture in a
    band across the middle (drawn by Scene.render over its own blurred copy), the headline under the band. The
    masthead and the ornament are "fixed"; the era and the headline come in with "fx": text."""
    animated, parts = bool(FX.get("text")) and has_photo, []
    image = Image.new("RGB", (W, H), style.background)
    kicker = release.kicker or "日本の物語"
    title = release.masthead or ""

    def masthead(d):
        size = 38
        width = font(size).getlength(kicker)
        y = 132 if title else 210
        d.text((W // 2, y), kicker, font=font(size), fill=BAND_IVORY, anchor="mm")
        for x0, x1 in ((70, W // 2 - width / 2 - 26), (W // 2 + width / 2 + 26, W - 70)):
            d.line((x0, y, x1, y), fill=BAND_GOLD, width=2)
        if title:
            words, title_size = fit(title, 940, 112, 1, smallest=72)
            d.text((W // 2 + 3, 262 + 5), words, font=font(title_size), fill=(0, 0, 0, 150), anchor="mm")
            d.text((W // 2, 262), words, font=font(title_size), fill="#ffffff", anchor="mm")
        y = 352 if title else 262
        d.line((W // 2 - 150, y, W // 2 - 22, y), fill=BAND_GOLD, width=2)
        d.line((W // 2 + 22, y, W // 2 + 150, y), fill=BAND_GOLD, width=2)
        d.polygon(((W // 2, y - 10), (W // 2 + 10, y), (W // 2, y + 10), (W // 2 - 10, y)), fill="#c23a26")

    parts.append(piece("fixed", masthead))
    if demo:
        parts.append(piece("fixed", lambda d: text(d, W // 2, 40, "動作確認", 26, GOLD, anchor="mt")))

    def era(d):   # the era of the scene, in gold on the right above the picture, underlined
        value, size = fit(beat.era, 600, 46, 1, smallest=32)
        d.text((W - 62, BAND_TOP - 30), value, font=font(size), fill=BAND_GOLD, anchor="rs")
        width = font(size).getlength(value)
        d.line((W - 62 - width - 6, BAND_TOP - 16, W - 56, BAND_TOP - 16), fill=BAND_GOLD, width=2)

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    if beat.era:
        if animated:
            parts.append(piece("tag", era))
        else:
            era(draw)
    if not has_photo:   # a text card in the place of the picture
        draw.rectangle((0, BAND_TOP, W, BAND_TOP + BAND_HEIGHT), fill=style.card)
        headline, size = fit(beat.headline, 900, 68, 3, smallest=40)
        y = text(draw, 90, BAND_TOP + 90, headline, size, style.card_ink)
        if beat.value:
            value, value_size = fit(beat.value, 900, 120, 1, smallest=56)
            y = text(draw, 90, y + 60, value, value_size, style.value)
        if beat.evidence:
            evidence, evidence_size = fit(beat.evidence, 900, 40, 5, bold=False, smallest=26)
            text(draw, 90, y + 50, evidence, evidence_size, style.card_ink, bold=False)
        return image, layer, [part for part in parts if part]
    blocks = []
    headline, size = fit(beat.headline, 960, 56 if HOST else 70, 1 if HOST else 2, smallest=40)
    blocks.append((headline, size, style.text, True, 16))
    if beat.value:
        value, value_size = fit(beat.value, 960, 84, 1, smallest=52)
        blocks.append((value, value_size, style.value, True, 16))
    if beat.evidence:
        evidence, evidence_size = fit(beat.evidence, 960, 34, 2, bold=False, smallest=26)
        blocks.append((evidence, evidence_size, style.muted, False, 10))
    y = BAND_TOP + BAND_HEIGHT + (30 if HOST else 44)
    order = 0
    for value, size, colour, bold, spacing in blocks:
        for row, line in enumerate(value.splitlines()):
            at = y + row * (size + spacing)
            paint = (lambda d, line=line, at=at, size=size, colour=colour, bold=bold:
                     d.text((W // 2, at), line, font=font(size, bold), fill=colour, anchor="mt"))
            if animated:
                parts.append(piece("row", paint, order))
                order += 1
            else:
                part = piece("row", paint)
                if part:
                    layer.paste(part[1], part[2], part[1])
        y += block_height(value, size, spacing) + 18
    return image, layer, [part for part in parts if part]


@lru_cache(maxsize=1)
def band_shade():
    """Over the blurred backdrop of the "band" frame: darker at the top (the title) and at the foot (the captions)."""
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shade)
    for y in range(H):
        top = max(0.0, 1 - y / BAND_TOP) ** 1.2 * 110
        foot = max(0.0, (y - BAND_TOP - BAND_HEIGHT) / (H - BAND_TOP - BAND_HEIGHT)) ** 1.1 * 120
        draw.line((0, y, W, y), fill=(6, 4, 2, round(min(200, 40 + top + foot))))
    return shade


def band_backdrop(picture):
    """The picture of the band, blurred and dark, filling the whole frame behind it."""
    pw, ph = picture.size
    cw = ph * W / H
    small = picture.resize((27, 48), Image.Resampling.BILINEAR, box=((pw - cw) / 2, 0, (pw + cw) / 2, ph))
    soft = small.filter(ImageFilter.GaussianBlur(2.2)).resize((W, H), Image.Resampling.BICUBIC)
    frame = soft.point(lambda level: round(level * 0.42))
    frame.paste(band_shade(), (0, 0), band_shade())
    return frame


ALBUM_INK = "#2f2116"


@lru_cache(maxsize=1)
def album_page():
    """The cream page of the "album" frame with the print (a white mat with its soft shadow) and a strip of tape."""
    page = paper_grain(STYLES["album"].background).copy()
    mat = (ALBUM_X - 26, ALBUM_TOP - 26, ALBUM_X + ALBUM_W + 26, ALBUM_TOP + ALBUM_SHOWN + 96)
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rectangle((mat[0] + 8, mat[1] + 14, mat[2] + 8, mat[3] + 16), fill=(60, 40, 20, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(16))
    page.paste(shadow, (0, 0), shadow)
    ImageDraw.Draw(page).rectangle(mat, fill="#fffdf8")
    tape = Image.new("RGBA", (250, 62), (226, 190, 160, 165))
    ImageDraw.Draw(tape).line((0, 4, 250, 4), fill=(255, 255, 255, 60), width=3)
    tape = tape.rotate(-4, expand=True, resample=Image.Resampling.BICUBIC)
    page.paste(tape, (W // 2 - tape.width // 2, mat[1] - 30), tape)
    return page


def album_layout(beat, release, has_photo, demo):
    """The "album" frame: the kicker between two thin rules at the top, the picture as a print on the cream page
    (drawn by Scene.render), the era written on the mat under it, the headline in dark ink under the print."""
    animated, parts = bool(FX.get("text")) and has_photo, []
    image = album_page().copy()
    kicker = release.kicker or "日本の物語"

    def head(d):
        size = 34
        width = font(size).getlength(kicker)
        d.text((W // 2, 92), kicker, font=font(size), fill=ALBUM_INK, anchor="mm")
        for x0, x1 in ((90, W // 2 - width / 2 - 24), (W // 2 + width / 2 + 24, W - 90)):
            d.line((x0, 92, x1, 92), fill=style.rule, width=2)

    parts.append(piece("fixed", head))
    if demo:
        parts.append(piece("fixed", lambda d: text(d, W // 2, 30, "動作確認", 24, style.accent, anchor="mt")))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    if not has_photo:   # a text card in the place of the picture
        draw.rectangle((ALBUM_X, ALBUM_TOP, ALBUM_X + ALBUM_W, ALBUM_TOP + ALBUM_SHOWN), fill=style.card)
        headline, size = fit(beat.headline, 820, 66, 3, smallest=40)
        y = text(draw, ALBUM_X + 50, ALBUM_TOP + 90, headline, size, style.card_ink)
        if beat.value:
            value, value_size = fit(beat.value, 820, 120, 1, smallest=56)
            y = text(draw, ALBUM_X + 50, y + 60, value, value_size, style.value)
        if beat.evidence:
            evidence, evidence_size = fit(beat.evidence, 820, 40, 5, bold=False, smallest=26)
            text(draw, ALBUM_X + 50, y + 50, evidence, evidence_size, style.card_ink, bold=False)
        return image, layer, [part for part in parts if part]

    def era(d):   # written on the mat under the picture, like a note on a print
        value, size = fit(beat.era, 760, 46, 1, smallest=30)
        d.text((W // 2, ALBUM_TOP + ALBUM_SHOWN + 48), value, font=font(size), fill="#6b5236", anchor="mm")

    if beat.era:
        if animated:
            parts.append(piece("tag", era))
        else:
            era(draw)
    blocks = []
    headline, size = fit(beat.headline, 940, 62, 2, smallest=44)
    blocks.append((headline, size, ALBUM_INK, True, 16))
    if beat.value:   # small enough to stay clear of the captions under it
        value, value_size = fit(beat.value, 940, 62, 1, smallest=44)
        blocks.append((value, value_size, style.value, True, 16))
    y = ALBUM_TOP + ALBUM_SHOWN + 128
    order = 0
    for value, size, colour, bold, spacing in blocks:
        for row, line in enumerate(value.splitlines()):
            at = y + row * (size + spacing)
            paint = (lambda d, line=line, at=at, size=size, colour=colour, bold=bold:
                     d.text((W // 2, at), line, font=font(size, bold), fill=colour, anchor="mt"))
            if animated:
                parts.append(piece("text", paint, order))
                order += 1
            else:
                paint(draw)
        y += block_height(value, size, spacing) + 16
    return image, layer, [part for part in parts if part]


def magazine_layout(beat, release, has_photo, demo):
    """The "magazine" frame: the picture across the top (drawn by Scene.render), the kicker as a red tag on it, a red
    rule under it, the era in red, the headline in bold black set left, the captions under it on the white page."""
    animated, parts = bool(FX.get("text")) and has_photo, []
    image = Image.new("RGB", (W, H), style.background)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, MAG_HEIGHT, W, MAG_HEIGHT + 9), fill=style.accent)
    draw.line((60, 1826, W - 60, 1826), fill=style.rule, width=2)
    kicker = release.kicker or "日本のニュース"
    parts.append(piece("fixed", lambda d: label(d, 48, 56, kicker, style.tag, style.tag_text)))
    if demo:
        parts.append(piece("fixed", lambda d: text(d, W - 60, 70, "動作確認", 24, style.accent, anchor="rt")))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    if not has_photo:   # a text card in the place of the picture
        draw.rectangle((0, 0, W, MAG_HEIGHT), fill=style.card)
        headline, size = fit(beat.headline, 900, 70, 3, smallest=40)
        y = text(draw, 90, 300, headline, size, style.card_ink)
        if beat.value:
            value, value_size = fit(beat.value, 900, 130, 1, smallest=56)
            y = text(draw, 90, y + 60, value, value_size, style.value)
        if beat.evidence:
            evidence, evidence_size = fit(beat.evidence, 900, 40, 5, bold=False, smallest=26)
            text(draw, 90, y + 50, evidence, evidence_size, style.card_ink, bold=False)
        return image, layer, [part for part in parts if part]

    def era(d):   # a red square, then the era in red
        value, size = fit(beat.era, 800, 38, 1, smallest=28)
        d.rectangle((60, MAG_HEIGHT + 52, 80, MAG_HEIGHT + 72), fill=style.accent)
        d.text((96, MAG_HEIGHT + 62), value, font=face_of("Sans", size, True), fill=style.accent, anchor="lm")

    if beat.era:
        if animated:
            parts.append(piece("tag", era))
        else:
            era(draw)
    blocks = []
    headline, size = fit(beat.headline, 960, 56 if HOST else 70, 1 if HOST else 2, smallest=40)
    blocks.append((headline, size, style.text, True, 14))
    if beat.value:
        value, value_size = fit(beat.value, 960, 84, 1, smallest=52)
        blocks.append((value, value_size, style.value, True, 14))
    y = MAG_HEIGHT + 112
    order = 0
    for value, size, colour, bold, spacing in blocks:
        for row, line in enumerate(value.splitlines()):
            at = y + row * (size + spacing)
            paint = (lambda d, line=line, at=at, size=size, colour=colour, bold=bold:
                     d.text((60, at), line, font=font(size, bold), fill=colour))
            if animated:
                parts.append(piece("text", paint, order))
                order += 1
            else:
                paint(draw)
        y += block_height(value, size, spacing) + 14
    return image, layer, [part for part in parts if part]


def layout(beat, release, has_photo, demo):
    """The page of a scene: the background (what stays still) and the scene's text on a transparent layer
    (it slides in at the start of the scene)."""
    if style.layout == "album":
        return album_layout(beat, release, has_photo, demo)
    if style.layout == "magazine":
        return magazine_layout(beat, release, has_photo, demo)
    if style.layout == "band":
        return band_layout(beat, release, has_photo, demo)
    if style.layout == "story":
        return story_layout(beat, release, has_photo, demo)
    if style.layout == "ink":
        return ink_layout(beat, release, has_photo, demo)
    if style.layout == "full":
        return full_layout(beat, release, has_photo, demo)
    return (*plain_layout(beat, release, has_photo, demo), [])


def plain_layout(beat, release, has_photo, demo):
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
        self.cut = beat.cut
        # how long the scene takes to arrive: a punch-in on its first picture waits for it
        self.arrival = 0.0 if not index else CUT_SECONDS[beat.cut] if beat.cut else TRANSITION
        self.background, text_layer, self.parts = layout(beat, release, bool(self.photos), demo)
        self.top, self.height = photo_box()
        # the text layer is pasted over the picture each frame: keep only the part that holds text
        box = text_layer.getbbox() or (0, 0, 1, 1)
        self.text, self.text_at = text_layer.crop(box), box[:2]

    def lengths(self):
        """How long each picture of the scene stays: an equal share, except the hook. With "fx", the first picture
        of the video stays at most HOOK_SECONDS and the others share the rest (owner, 21/11/2026: "ảnh hook đầu
        không quá 5s")."""
        count, total = len(self.photos), self.end - self.start
        if self.index == 0 and FX and count > 1 and total / count > HOOK_SECONDS:
            return [HOOK_SECONDS] + [(total - HOOK_SECONDS) / (count - 1)] * (count - 1)
        return [total / count] * count

    def picture(self, moment):
        lengths = self.lengths()
        starts = [self.start + sum(lengths[:number]) for number in range(len(lengths))]
        number = max([0] + [n for n, start in enumerate(starts) if moment >= start])
        length = lengths[number]
        local = (moment - starts[number]) / length
        picture = self.shot(number, local, length)
        # the previous picture fades into this one; a punch-in arrives by a hard cut, or its hit would be hidden
        if number and local * length < PHOTO_FADE and self.photos[number].move != "punch-in":
            previous = self.shot(number - 1, (moment - starts[number - 1]) / lengths[number - 1], lengths[number - 1])
            picture = Image.blend(previous, picture, ease(local * length / PHOTO_FADE))
        return picture, self.photos[number]

    def shot(self, number, local, length):
        """Picture `number` at its time `local`: the move chosen for it, else the four old moves in turn."""
        photo = self.photos[number]
        if photo.footage:   # a clip plays at its own speed (slowed when it is shorter than its place), closing in a little
            frame = photo.footage.at(local * length, length + PHOTO_FADE)
            return view(frame, self.height, 1.0 + 0.05 * clamp(local, 0.0, 1.25), 0.5, 0.5)
        if photo.move:
            return named_photo(photo, local, photo.move, length, self.height, delay=0.0 if number else self.arrival)
        return moving_photo(photo, local, MOTIONS[(self.index + number) % len(MOTIONS)], self.height)

    def render(self, moment):
        age = moment - self.start
        frame = self.background.copy()
        photo = None
        if self.photos:
            picture, photo = self.picture(moment)
            if style.layout == "ink":
                frame.paste(picture, (0, self.top), ink_mask(self.height))
            elif style.layout == "album":   # the picture set into the print, a little smaller than it was made
                frame.paste(picture.resize((ALBUM_W, ALBUM_SHOWN), Image.Resampling.BICUBIC), (ALBUM_X, ALBUM_TOP))
            elif style.layout == "band":   # the picture over its own blurred copy, between two thin gold lines
                frame = band_backdrop(picture)
                frame.paste(picture, (0, self.top))
                draw = ImageDraw.Draw(frame)
                for y in (self.top - 2, self.top + self.height):
                    draw.rectangle((0, y, W, y + 1), fill=BAND_GOLD)
            else:
                frame.paste(picture, (0, self.top))
            if style.layout in ("story", "ink"):   # "full": nothing dark over the picture (owner, 21/11/2026)
                shade = ink_shade(self.height) if style.layout == "ink" else story_shade(self.height)
                frame.paste(shade, (0, self.top), shade)
        for kind, part, at, _ in self.parts:   # what never moves: the seal and the year of the "history" page
            if kind == "fixed":
                frame.paste(part, at, part)
        if QUOTE_ON:   # a quote stands on the picture: the headline comes in after it
            self.quiet_until = moment
            if style.layout in ("full", "band", "album", "magazine"):   # the tag (the era) comes in all the same
                self.draw_parts(frame, age, only="tag")
        else:
            age = moment - max(self.start, getattr(self, "quiet_until", self.start))
            amount = ease(age / TEXT_IN) if age < TEXT_IN else 1.0
            layer = faded(self.text, amount) if amount < 1 else self.text
            frame.paste(layer, (self.text_at[0], self.text_at[1] + round(36 * (1 - amount))), layer)
            self.draw_parts(frame, age)
        if photo and style.layout not in ("full", "band", "album", "magazine"):   # these: credits.txt only
            draw = ImageDraw.Draw(frame)
            creator = photo.creator if len(photo.creator) <= 36 else photo.creator[:34] + "…"   # the full credit is in credits.txt
            credit = ("映像  " if photo.footage else "写真  ") + creator + (f" / {photo.license}" if photo.license else "")
            if style.layout in ON_PICTURE:
                credit, credit_size = fit(credit, 560, 24, 1, bold=False, smallest=16)
                text(draw, 60, 1774, credit, credit_size, style.muted, bold=False)
            else:
                label(draw, 70, 380, "資料写真", style.photo_tag, style.photo_tag_text)
                credit, credit_size = fit(credit, 940, 23, 2, bold=False, smallest=16)
                text(draw, 70, 1806, credit, credit_size, style.muted, bold=False)
        return frame


    def draw_parts(self, frame, age, only=None):
        """The scene's text coming in piece by piece ("fx": text): the tag is wiped in from the left, a red rule is
        drawn, then each row of the headline rises into its place from behind its own lower edge. `only`: draw the
        pieces of that kind only."""
        start = 0.1 + 0.6 * self.arrival   # most of it is seen after the scene has arrived
        if style.layout == "full":   # the picture is seen alone a moment first, then the text comes (owner, 21/11/2026)
            start += 0.15
        for kind, picture, (x, y), order in self.parts:
            if kind == "fixed" or only and kind != only:
                continue
            if kind in ("tag", "rule"):
                amount = ease((age - start - (0.0 if kind == "tag" else 0.12)) / (0.3 if kind == "tag" else 0.4))
                width = round(picture.width * amount)
                if width > 0:
                    part = picture.crop((0, 0, width, picture.height))
                    frame.paste(part, (x, y), part)
                continue
            amount = (age - start - 0.22 - 0.13 * order) / 0.45
            if amount <= 0:
                continue
            amount = 1 - (1 - min(1.0, amount)) ** 3
            drop = round((1 - amount) * 34)
            part = picture.crop((0, 0, picture.width, picture.height - drop)) if drop else picture
            if amount < 0.6:
                part = faded(part, amount / 0.6)
            frame.paste(part, (x, y + drop), part)


@lru_cache(maxsize=2)
def page_shadow(height=1460):
    shadow = Image.new("RGBA", (48, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    for x in range(48):
        draw.line((x, 0, x, height), fill=(20, 12, 4, round(110 * (x / 48) ** 2)))
    return shadow


CUT_SECONDS = {"fade": TRANSITION, "page": TRANSITION, "dip": 0.9, "hard": 0.0, "flash": 0.45, "slide": 0.5,
               "zoom": 0.6}


def cut_area():
    """The part of the frame a "slide" or a "zoom" moves: in the "band" frame the picture, the era above it and the
    text under it (the title at the top stays put), elsewhere the page."""
    return page_area()


@lru_cache(maxsize=1)
def slide_shadow():
    shadow = Image.new("RGBA", (140, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    for x in range(140):
        draw.line((x, 0, x, H), fill=(0, 0, 0, round(170 * (x / 140) ** 2)))
    return shadow


def transition(old, new, amount, cut=""):
    """From one scene to the next. Without a chosen cut: a page turned from the right (paper) or a cross-fade
    (news). "dip": the old scene goes dark, then the new one comes up."""
    cut = cut or ("page" if style.grain else "fade")
    if cut == "fade":
        return Image.blend(old, new, amount)
    if cut == "flash":   # a burst of pale light on the cut, then the new scene comes out of it (a blow, a betrayal)
        light = Image.new("RGB", (W, H), "#f6efe0")
        if amount < 0.25:
            return Image.blend(old, light, 0.85 * amount / 0.25)
        return Image.blend(light, new, 0.15 + 0.85 * ease((amount - 0.25) / 0.75))
    if cut in ("slide", "zoom"):
        step = ease(amount)
        frame = Image.blend(old, new, step)   # what does not move (the same in both scenes) stays as it is
        area = cut_area()
        left, top, right, bottom = area
        width, height = right - left, bottom - top
        before, after = old.crop(area), new.crop(area)
        if cut == "slide":   # the new scene pushes the old one out to the left
            shift = round(width * step)
            moving = Image.new("RGB", (width, height))
            moving.paste(before, (-shift, 0))
            moving.paste(after, (width - shift, 0))
            frame.paste(moving, (left, top))
            if 0 < shift < width:
                ImageDraw.Draw(frame).rectangle((left + width - shift, top, left + width - shift + 3, bottom),
                                                fill=BAND_GOLD if style.layout == "band" else style.accent)
            return frame
        # "zoom": the old scene rushes towards the viewer and melts into the new one, which settles from a little close
        grow = 1 + 0.35 * step
        zoomed = before.resize((round(width * grow), round(height * grow)), Image.Resampling.BILINEAR)
        x, y = (zoomed.width - width) // 2, (zoomed.height - height) // 2
        zoomed = zoomed.crop((x, y, x + width, y + height))
        settle = 1.12 - 0.12 * step
        arriving = after.resize((round(width * settle), round(height * settle)), Image.Resampling.BILINEAR)
        x, y = (arriving.width - width) // 2, (arriving.height - height) // 2
        arriving = arriving.crop((x, y, x + width, y + height))
        frame.paste(Image.blend(zoomed, arriving, ease(min(1.0, amount * 1.6))), (left, top))
        return frame
    if cut == "dip":
        # Only the scene (picture and its text) goes dark; the header and the foot change quietly and the caption,
        # drawn afterwards, stays readable.
        frame = Image.blend(old, new, ease(amount))
        area = page_area()
        dark = Image.new("RGB", (W, area[3] - area[1]), "#07090c" if not style.grain else "#1c140b")
        depth = 0.55   # how dark the middle of the dip gets
        scene = (Image.blend(old.crop(area), dark, depth * ease(amount * 2)) if amount < 0.5
                 else Image.blend(new.crop(area), dark, depth * (1 - ease(amount * 2 - 1))))
        frame.paste(scene, area[:2])
        return frame
    if not style.grain:
        # "page" in the news frame: the new scene slides in from the right over the whole height, behind a red
        # edge and a soft shadow (the paper page turn below is too faint on the dark frame).
        offset = round(W * (1 - amount))
        frame = old.copy()
        if offset < W:
            frame.paste(new.crop((0, 0, W - offset, H)), (offset, 0))
        if offset > 0:
            shadow = slide_shadow()
            left = max(0, offset - shadow.width)
            frame.paste(shadow.crop((shadow.width - (offset - left), 0, shadow.width, H)), (left, 0),
                        shadow.crop((shadow.width - (offset - left), 0, shadow.width, H)))
            ImageDraw.Draw(frame).rectangle((offset, 0, min(W, offset + 9), H), fill=style.accent)
        return frame
    offset = round(W * (1 - amount))
    frame = old.copy()
    _, top, _, bottom = page_area()
    if offset < W:
        frame.paste(new.crop((0, top, W - offset, bottom)), (offset, top))
    if offset >= 48:
        shadow = page_shadow(bottom - top + 10)
        frame.paste(shadow, (offset - 48, max(0, top - 5)), shadow)
    return frame


def mix(first, second, share):
    """A colour between two "#rrggbb" colours: share 0 gives the first, 1 the second."""
    a, b = (tuple(int(colour[i:i + 2], 16) for i in (1, 3, 5)) for colour in (first, second))
    return "#" + "".join(f"{round(x + (y - x) * share):02x}" for x, y in zip(a, b))


def reading_weight(char):
    """About how long a character takes to say, in morae: a kanji about two, a digit more, a comma a short pause."""
    if char in "「」『』（）()・ 　":
        return 0.0
    if char in "、，":
        return 1.6
    if char in "。．！？!?…":
        return 0.8
    if char.isdigit():
        return 2.6
    if "\u4e00" <= char <= "\u9fff" or char == "々":
        return 2.0
    if char in "ゃゅょっぁぃぅぇぉャュョッァィゥェォ":
        return 0.4
    return 1.0


SWEEP = 44   # width of the soft edge between the spoken and the unspoken part of a caption


@lru_cache(maxsize=1)
def sweep_edge(height):
    return Image.linear_gradient("L").rotate(-90).resize((SWEEP, height), Image.Resampling.BILINEAR)


@lru_cache(maxsize=8)
def caption_art(caption, key):
    """A caption drawn twice, paler (not yet spoken) and in full ink (spoken), with the x of every character edge
    and the reading weight of every character, line by line. `key`: what the drawing depends on besides the text."""
    face = font(CAPTION_SIZE)
    contents = caption.splitlines()
    height = 83 * len(contents) + 26
    layers = []
    for colour in (mix(style.caption_text, style.caption_box or style.background, 0.55), style.caption_text):
        layer = Image.new("RGBA", (W, height + 4), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        for line_index, line in enumerate(contents):
            if style.layout == "full":   # printed on the picture itself: a dark outline
                draw.text((W / 2, 21 + 83 * line_index), line, font=face, fill=colour, anchor="mt",
                          stroke_width=6, stroke_fill=OUTLINE)
            else:
                draw.text((W / 2, 21 + 83 * line_index), line, font=face, fill=colour, anchor="mt",
                          stroke_width=1, stroke_fill=colour)
        layers.append(layer)
    edges = [[W / 2 - face.getlength(line) / 2 + face.getlength(line[:count]) for count in range(len(line) + 1)]
             for line in contents]
    weights = [[reading_weight(char) for char in line] for line in contents]
    return layers, edges, weights, height


def read_share(marks, moment):
    """How much of a caption's text the voice has read at `moment` (a share of the caption's time), from its
    marks (voice.Caption.marks: (share of the text, share of the time), in the order of the text)."""
    before = marks[0]
    if moment <= before[1]:
        return before[0]
    for mark in marks[1:]:
        if moment < mark[1]:
            return before[0] + (mark[0] - before[0]) * (moment - before[1]) / (mark[1] - before[1])
        before = mark
    return before[0]


def draw_spoken_caption(image, caption, age, span, marks=()):
    """The caption of "fx": text: all of it is there from the start (paler), and it darkens to full ink from left
    to right as the voice reads it: with `marks` at the real moment of every character (a touch ahead of the
    voice), else at about the pace of the reading (an estimate by character)."""
    (pale, full), edges, weights, height = caption_art(caption, (style.caption_text, DISPLAY_FONT, style.layout))
    centre = caption_centre()
    amount = ease(age / CAPTION_IN) if age < CAPTION_IN else 1.0
    top = centre - height // 2 + round(14 * (1 - amount))
    if style.caption_box:
        box = Image.new("RGBA", (W, height + 4), (0, 0, 0, 0))
        ImageDraw.Draw(box).rounded_rectangle((69, 0, 1011, height), radius=19, fill=style.caption_box)
        box = faded(box, amount) if amount < 1 else box
        image.paste(box, (0, top), box)
    if marks:   # one unit a character: the marks count characters
        weights = [[1.0] * len(row) for row in weights]
        done = sum(map(len, weights)) * read_share(marks, (age + 0.06) / span)
    else:
        done = sum(map(sum, weights)) * clamp((age + 0.1) / max(0.3, span - 0.12), 0.0, 1.0)
    spoken = Image.new("L", pale.size, 0)
    for line_index, (row_edges, row_weights) in enumerate(zip(edges, weights)):
        band = (83 * line_index, 83 * (line_index + 1) + (30 if line_index == len(edges) - 1 else 0))
        row_total = sum(row_weights)
        if done >= row_total:
            spoken.paste(255, (0, band[0], W, band[1]))
        elif done > 0:
            passed, x = 0.0, row_edges[0]
            for index, weight in enumerate(row_weights):
                if passed + weight >= done:
                    share = (done - passed) / weight if weight else 1.0
                    x = row_edges[index] + (row_edges[index + 1] - row_edges[index]) * share
                    break
                passed += weight
            x = round(x)
            spoken.paste(255, (0, band[0], max(0, x - SWEEP // 2), band[1]))
            spoken.paste(sweep_edge(band[1] - band[0]), (x - SWEEP // 2, band[0]))
        done -= row_total
    if style.layout != "full":   # "full": nothing before the voice reaches it, the words come as they are spoken
        pale_layer = faded(pale, amount) if amount < 1 else pale
        image.paste(pale_layer, (0, top), pale_layer)
    ink = ImageChops.multiply(full.getchannel("A"), spoken)
    image.paste(full, (0, top), ink.point(lambda level: round(level * amount)) if amount < 1 else ink)


def draw_captions(image, caption, age=1.0, span=None, marks=()):
    """`span`: how long the caption is spoken; with "fx": text it then darkens as it is read (`marks`: when the
    voice reaches which part of it, see voice.Caption)."""
    if span and FX.get("text"):
        return draw_spoken_caption(image, caption, age, span, marks)
    face = font(CAPTION_SIZE)
    contents = caption.splitlines()
    height = 83 * len(contents) + 26
    centre = caption_centre()
    amount = ease(age / CAPTION_IN) if age < CAPTION_IN else 1.0
    layer = Image.new("RGBA", (W, height + 4), (0, 0, 0, 0)) if amount < 1 else None
    draw = ImageDraw.Draw(layer if layer else image)
    top = 0 if layer else centre - height // 2
    if style.caption_box:
        draw.rounded_rectangle((69, top, 1011, top + height), radius=19, fill=style.caption_box)
    outline = (6, OUTLINE) if style.layout == "full" else (1, style.caption_text)
    for line_index, line in enumerate(contents):
        draw.text((W / 2, top + 21 + 83 * line_index), line,
                  font=face, fill=style.caption_text, anchor="mt", stroke_width=outline[0], stroke_fill=outline[1])
    if layer:
        layer = faded(layer, amount)
        image.paste(layer, (0, centre - height // 2 + round(14 * (1 - amount))), layer)


QUOTE_IN = 0.35


QUOTE_ROWS = 4     # the rows a quote may take (owner, 25/11/2026)
QUOTE_ON = False   # set by encode()/stills() while a quote is shown: the scene's own text waits meanwhile


@lru_cache(maxsize=8)
def quote_band(height):
    """A dark band, clear at its top and dense from about two fifths down, laid on the foot of the picture."""
    band = Image.new("RGBA", (W, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(band)
    solid = int(height * 0.42)
    for y in range(height):
        alpha = 215 * min(1.0, y / solid) ** 1.4
        draw.line((0, y, W, y), fill=(10, 7, 4, round(alpha)))
    return band


@lru_cache(maxsize=8)
def ink_quote_band(height):
    """The band of a quote on the "history" page: it darkens the picture behind the words and is gone at the foot,
    where the picture has already melted into the page."""
    band = quote_band(height).copy()
    fall = Image.new("L", (W, height), 255)
    draw = ImageDraw.Draw(fall)
    start = int(height * 0.45)
    for y in range(start, height):
        draw.line((0, y, W, y), fill=round(255 * (1 - ease((y - start) / (height - start - 30)))))
    band.putalpha(ImageChops.multiply(band.getchannel("A"), fall))
    return band


HOOK_SIZE = {"full": 124, "band": 124, "album": 108, "magazine": 108}   # a short opening line, printed larger


def draw_quote(image, line, age, hook=False):
    """A quote printed big while it is spoken. The picture stays bright: the main picture is what keeps the
    viewer (owner, 17/11/2026), so only the foot of the picture gets a soft dark band, the words stand on it
    between two short red rules, and the scene's headline waits (QUOTE_ON) so that nothing is drawn twice.
    `hook`: the opening line of the video. With "fx": text it is all there from the first frame, larger when it is
    short (owner, 25/11/2026, on the growth plan: the first two seconds decide whether a Short is watched)."""
    top, height = photo_box()
    if hook and FX.get("text"):
        age = max(age, 3.0)
    amount = ease(age / QUOTE_IN) if age < QUOTE_IN else 1.0
    if amount <= 0:
        return
    # break where the captions break (after a comma, between phrases), each piece on its own line if it fits
    pieces = [row for chunk in caption_chunks(line) for row in chunk.splitlines()]
    # 4 rows at most (owner, 21/11/2026: 3 rows; 25/11/2026, after the three videos with the most views had hooks of
    # 44-48 characters on 4 rows: "Cho phép kể hết ý chứ k ép xuống 3 dòng"): more pieces are run together and wrapped
    joined = "\n".join(pieces) if len(pieces) <= QUOTE_ROWS else "".join(pieces)
    if style.layout in ("full", "band", "album", "magazine"):   # as large as the rows allow
        largest = 96 if style.layout in ("full", "band") else 84
        if hook and FX.get("text"):   # the opening line: larger when it is short enough
            largest = HOOK_SIZE[style.layout]
        if HOST and style.layout == "band":   # the narrator frame: the words sit between the picture and the character
            largest = 80
        words, size = fit("".join(pieces), 960, largest, QUOTE_ROWS, smallest=52)
    else:
        words, size = fit(joined, 920, 104 if hook and FX.get("text") else 92, min(QUOTE_ROWS, max(len(pieces), 2)),
                          smallest=52)
    rows = words.splitlines()
    block = block_height(words, size, 22)
    if style.layout == "full":
        return draw_full_quote(image, rows, size, block, age)
    if style.layout == "band":
        return draw_band_quote(image, rows, size, block, age)
    if style.layout in ("album", "magazine"):
        return draw_page_quote(image, rows, size, block, age)
    band_height = min(height, block + 330)
    band = quote_band(band_height)
    if style.layout == "ink":
        band = ink_quote_band(band_height)
    band = faded(band, amount) if amount < 1 else band
    image.paste(band, (0, top + height - band_height), band)
    y = top + height - 80 - block - 40          # the text block ends 80 px above the foot of the picture
    draw = ImageDraw.Draw(image)
    half = round(60 * (ease(age / 0.5) if FX.get("text") else amount))
    rule = "#c23a26" if FX.get("text") else style.accent
    draw.rectangle((W // 2 - half, y, W // 2 + half, y + 5), fill=rule)
    draw.rectangle((W // 2 - half, y + block + 75, W // 2 + half, y + block + 80), fill=rule)
    for index, row in enumerate(rows):
        shown = ease((age - 0.08 - 0.22 * index) / 0.42) if FX.get("text") else amount
        if shown <= 0:
            continue
        strip = Image.new("RGBA", (W, size + 44), (0, 0, 0, 0))
        ImageDraw.Draw(strip).text((W // 2, 10), row, font=font(size), fill=STORY_TEXT, anchor="mt",
                                   stroke_width=3, stroke_fill=(12, 8, 4))
        strip = faded(strip, shown) if shown < 1 else strip
        image.paste(strip, (0, y + 30 + index * (size + 22) + round(22 * (1 - shown))), strip)


def draw_full_quote(image, rows, size, block, age):
    """A quote in the "full" frame: no band, the words stand in the middle of the picture, white with a dark outline,
    row after row rising into place (owner, 21/11/2026: "không cần khoảng tối… để chữ ở giữa màn hình")."""
    y = min(FULL_TEXT_CENTRE - block // 2, FULL_TEXT_FOOT - block)
    for index, row in enumerate(rows):   # the picture is seen alone a moment first, then the words come
        shown = ease((age - 0.25 - 0.22 * index) / 0.42) if FX.get("text") else ease(age / QUOTE_IN)
        if shown <= 0:
            continue
        ink = Image.new("RGBA", (W, size + 60), (0, 0, 0, 0))
        outlined(ImageDraw.Draw(ink), W // 2, 24, row, size, style.text)
        soft = ImageChops.offset(ink.getchannel("A"), 0, 4).filter(ImageFilter.GaussianBlur(7))
        strip = Image.new("RGBA", ink.size, (10, 6, 2, 0))
        strip.putalpha(soft.point(lambda level: round(level * 0.6)))
        strip = Image.alpha_composite(strip, ink)
        strip = faded(strip, shown) if shown < 1 else strip
        image.paste(strip, (0, y - 24 + index * (size + 22) + round(30 * (1 - shown))), strip)


BAND_QUOTE_CENTRE = 1490


def draw_band_quote(image, rows, size, block, age):
    """A quote in the "band" frame: big and white under the picture, in the place of the headline and the
    captions, row after row rising into place."""
    y = BAND_QUOTE_CENTRE - block // 2
    for index, row in enumerate(rows):
        shown = ease((age - 0.1 - 0.22 * index) / 0.42) if FX.get("text") else ease(age / QUOTE_IN)
        if shown <= 0:
            continue
        ink = Image.new("RGBA", (W, size + 60), (0, 0, 0, 0))
        ImageDraw.Draw(ink).text((W // 2, 24), row, font=font(size), fill="#ffffff", anchor="mt",
                                 stroke_width=2, stroke_fill=(20, 14, 8))
        soft = ImageChops.offset(ink.getchannel("A"), 0, 5).filter(ImageFilter.GaussianBlur(8))
        strip = Image.new("RGBA", ink.size, (6, 4, 2, 0))
        strip.putalpha(soft.point(lambda level: round(level * 0.75)))
        strip = Image.alpha_composite(strip, ink)
        strip = faded(strip, shown) if shown < 1 else strip
        image.paste(strip, (0, y - 24 + index * (size + 22) + round(30 * (1 - shown))), strip)


PAGE_QUOTE_CENTRE = {"album": 1560, "magazine": 1500}


def draw_page_quote(image, rows, size, block, age):
    """A quote in the "album" and "magazine" frames: big, in the page's dark ink, under the picture in the place of
    the headline and the captions, row after row rising into place."""
    y = PAGE_QUOTE_CENTRE[style.layout] - block // 2
    for index, row in enumerate(rows):
        shown = ease((age - 0.1 - 0.22 * index) / 0.42) if FX.get("text") else ease(age / QUOTE_IN)
        if shown <= 0:
            continue
        strip = Image.new("RGBA", (W, size + 60), (0, 0, 0, 0))
        ImageDraw.Draw(strip).text((W // 2, 24), row, font=font(size), fill=style.text, anchor="mt")
        strip = faded(strip, shown) if shown < 1 else strip
        image.paste(strip, (0, y - 24 + index * (size + 22) + round(30 * (1 - shown))), strip)


def quote_lines(beats, captions):
    """For each caption: (the whole quote line, when its first caption starts) when it belongs to a line marked
    "quote", else None. Captions are made line by line in order (voice.narration), so they follow the lines."""
    marks, number = [], 0
    for beat in beats:
        for index, line in enumerate(beat.lines):
            chunks = caption_chunks(line)
            first = captions[number].start if number < len(captions) else 0.0
            for _ in chunks:
                marks.append((line, first) if index in beat.quotes else None)
            number += len(chunks)
    return marks if len(marks) == len(captions) else [None] * len(captions)


def held_quotes(beats, captions, quotes):
    """The "full" frame: for each caption, the quote of its scene said before it (it stays in the middle of the
    picture, as the scene's headline, while the scene's next lines run under it), else None; and the scene of
    each caption."""
    owners = [index for index, beat in enumerate(beats) for line in beat.lines for _ in caption_chunks(line)]
    if len(owners) != len(captions):
        return [None] * len(captions), [-1] * len(captions)
    held, last = [], None
    for number, quote in enumerate(quotes):
        if number and owners[number] != owners[number - 1]:
            last = None
        last = quote or last
        held.append(None if quote or style.layout != "full" else last)
    return held, owners


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
    cut = scenes[number].cut
    length = CUT_SECONDS[cut] if cut else TRANSITION
    if number and moment - scenes[number].start < length:
        old = scenes[number - 1].render(moment)
        amount = (moment - scenes[number].start) / length
        frame = transition(old, frame, amount if cut in ("dip", "flash") else ease(amount), cut)
    return frame


def video_kbps(duration, budget=SIZE_BUDGET):
    """The highest video bitrate (kbit/s) that keeps a video of `duration` seconds within `budget` bytes."""
    room = budget * 8 / 1000 / max(duration, 1.0) * 0.98 - AUDIO_KBPS   # 2 % for the container
    return max(300, min(MAX_VIDEO_KBPS, int(room)))


VOICE = 1.0   # "voice" of a story: how loud the finished sound is (1 = the usual -16 LUFS; 1.7 = 70 % louder)


def use_voice(volume):
    global VOICE
    VOICE = float(volume or 1.0)


def use_speaker(choice):
    """The voice credit printed on the frames follows the story's VOICEVOX voice ("speaker"; "" = 青山龍星)."""
    global VOICE_CREDIT
    from .voice import voice_credit
    VOICE_CREDIT = voice_credit(choice)


def loudness():
    """The filters that bring the finished sound to its loudness: -16 LUFS, then, for a story that asks for a louder
    voice, that much gain (at most 8 dB) and a limiter that keeps the peaks from clipping. (Asking loudnorm itself
    for a higher target gave only 1.6 dB of the 4.6 asked: it will not push the peaks.)"""
    chain = "loudnorm=I=-16:TP=-1.5:LRA=7"
    # the limiter takes back part of the gain: measured, 8 dB of gain gives the 4.6 dB (70 %) asked for
    gain = min(14.0, 1.75 * 20 * math.log10(max(0.3, VOICE)))
    if abs(gain) > 0.05:
        chain += f",volume={gain:.1f}dB"
    if VOICE > 2.0:
        # louder still (owner, 24/11/2026: "tăng voice to hơn 40%", 1.7 → 2.4): the slow limiter above stops at about
        # -11 LUFS whatever the gain; a quicker one with a higher ceiling reaches -9 (measured: 13 dB → -9.3 LUFS)
        chain += ",alimiter=limit=0.89:attack=1:release=20:level=disabled"
    elif gain > 0.05:
        chain += ",alimiter=limit=0.89:attack=3:release=60:level=disabled"
    return chain


MUSIC_LUFS = -35   # the music sits about 17 dB under the voice (VOICEVOX speaks at about -18 LUFS)


def codec_args(duration, mixed=False):
    """FFmpeg output options: H.264 at constant quality, capped so that the file fits the size budget. `mixed`:
    the audio comes from a -filter_complex (voice and music), already brought to the loudness."""
    kbps = video_kbps(duration)
    return ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-maxrate", f"{kbps}k", "-bufsize", f"{2 * kbps}k",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", f"{AUDIO_KBPS}k", *([] if mixed else ["-af", loudness()]),
            "-movflags", "+faststart", "-shortest"]


def music_args(music, duration):
    """Inputs and audio graph that lay the music (looped if short, faded in and out) under the voice (input 1)."""
    level = MUSIC_LUFS + 20 * math.log10(max(0.2, music.volume)) - 20 * math.log10(max(1.0, VOICE))
    fade_out = max(0.0, duration - 3.0)
    graph = (f"[1:a]aformat=sample_rates=44100:channel_layouts=mono[voice];"
             f"[2:a]aformat=channel_layouts=mono,loudnorm=I={level:.1f}:TP=-9:LRA=11,aresample=44100,"
             f"afade=t=in:st=0:d=2,afade=t=out:st={fade_out:.2f}:d=3,atrim=0:{duration:.2f}[music];"
             f"[voice][music]amix=inputs=2:duration=first:normalize=0,{loudness()},aresample=44100[mix]")
    skip = ["-ss", f"{music.start:.2f}"] if getattr(music, "start", 0) else []
    return [*skip, "-stream_loop", "-1", "-i", music.path], ["-filter_complex", graph, "-map", "0:v", "-map", "[mix]"]


def encode(beats, release, photos, demo, intervals, captions, wav, out):
    global QUOTE_ON
    scenes = scenes_for(beats, release, photos, demo, intervals)
    grain = Grain() if style.grain else None
    quotes = quote_lines(beats, captions)
    QUOTE_ON = bool(quotes[0])
    cover = scenes[0].render(min(1.5, intervals[0][1] * 0.3))
    QUOTE_ON = False
    scenes[0].__dict__.pop("quiet_until", None)   # the cover must not hold back the first scene's text
    if quotes[0]:
        draw_quote(cover, quotes[0][0], 1.0, hook=True)
    else:
        draw_captions(cover, captions[0].text)
    cover.save(out / "cover.jpg", quality=92)

    duration = intervals[-1][1]
    music = getattr(release, "music", None)
    inputs, mapping = music_args(music, duration) if music else ([], [])
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", f"{W}x{H}", "-framerate", str(FPS), "-i", "-",
        "-i", str(wav), *inputs, *mapping, *codec_args(duration, mixed=bool(music)), str(out / "video.mp4"),
    ]
    cue = 0
    frame_index = 0
    held, owners = held_quotes(beats, captions, quotes)
    speaking = voice_levels(wav, math.ceil(duration * FPS) + 2) if HOST else []
    with subprocess.Popen(cmd, stdin=subprocess.PIPE) as process:
        try:
            for number, scene in enumerate(scenes):
                while frame_index < math.ceil(scene.end * FPS):
                    moment = frame_index / FPS
                    while cue + 1 < len(captions) and moment >= captions[cue].end:
                        cue += 1
                    # in the silence between two lines the last caption (or quote) stays until the next one starts
                    shown = cue - 1 if cue and moment < captions[cue].start else cue
                    kept = held[shown] if owners[shown] == number else None   # "full": the scene's quote stays
                    QUOTE_ON = bool(quotes[shown] or kept)
                    frame = frame_at(scenes, number, moment)
                    QUOTE_ON = False
                    if HOST and style.layout == "band":   # the narrator stands in front of the scene, under the words
                        draw_host(frame, number, moment - scene.start,
                                  speaking[frame_index] if frame_index < len(speaking) else False, frame_index)
                    # the opening line of the video (scene 1's quote) is there from the first frame
                    opening = quotes[0][0] if quotes[0] and number == 0 else None
                    if kept:
                        draw_quote(frame, kept[0], moment - kept[1], hook=kept[0] is opening)
                    if quotes[shown]:
                        draw_quote(frame, quotes[shown][0], moment - quotes[shown][1],
                                   hook=quotes[shown][0] is opening)
                    else:
                        draw_captions(frame, captions[shown].text, moment - captions[shown].start,
                                      captions[shown].end - captions[shown].start,
                                      getattr(captions[shown], "marks", ()))
                    if grain:
                        frame = grain.apply(frame, frame_index)
                    if style.layout in ("ink", "band"):   # the video comes out of the dark and goes back into it
                        # ("band": the hook is seen at once, the video only goes back into the dark at its end)
                        edge = (duration - moment) / 0.8 if style.layout == "band" else min(moment / 0.5, (duration - moment) / 0.8)
                        if edge < 1:
                            frame = Image.blend(Image.new("RGB", (W, H), "#000000"), frame, ease(max(0.0, edge)))
                    process.stdin.write(frame.tobytes())
                    frame_index += 1
        finally:
            process.stdin.close()
        if process.wait():
            raise RuntimeError("FFmpeg failed")


def stills(beats, release, photos, out):
    """One frame per picture, without the voice, to check pictures and text before rendering."""
    global QUOTE_ON
    grain = Grain() if style.grain else None
    tiles = []
    for index, beat in enumerate(beats):
        scene = Scene(index, beat, release, photos.get(index), False, 0.0, 10.0)   # a 10-second scene
        count = max(1, len(scene.photos))
        held = style.layout == "full" and 0 in beat.quotes   # "full": the scene's quote stays over its pictures
        for number in range(count):
            QUOTE_ON = 0 in beat.quotes and (number == 0 or held)
            frame = scene.render(10 * (number + 0.5) / count)
            QUOTE_ON = False
            if HOST and style.layout == "band":
                draw_host(frame, index, 0.5 if number == 0 else 9.0, number % 2 == 1, 0)
            if 0 in beat.quotes and (number == 0 or held):
                draw_quote(frame, beat.lines[0], 3.0, hook=index == 0)
            if held and number and len(beat.lines) > 1:   # under the quote, a line spoken while this picture is on
                draw_captions(frame, caption_chunks(beat.lines[min(number, len(beat.lines) - 1)])[0])
            elif not (0 in beat.quotes and (number == 0 or held)):
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
    # The list of edits, scene by scene: the owner answers with "cảnh 5 đổi sang kiểu …" (names: news/edits.py).
    lines = edit_list(beats, photos, "paper" if style.grain else "news")
    (out / "edits.md").write_text(
        "# Cách edit từng cảnh\n\n" + "\n".join(f"- {line}" for line in lines)
        + f"\n\nCác kiểu chuyển động của ảnh: {', '.join(MOVES)}.\nCác kiểu vào cảnh: {', '.join(CUTS)}.\n"
        "Muốn đổi: bình luận, ví dụ \"cảnh 5 đổi sang kiểu pull-back\".\n", encoding="utf-8")
    print("Edits (also in edits.md):")
    for line in lines:
        print(f"  {line}")
    first = min(photos) if photos else None
    for index in sorted(photos):
        for number, photo in enumerate(photos[index], 1):
            hook = index == first and number == 1
            for warning in [move_warning(photo, height=photo_box()[1]), *(hook_warnings(photo) if hook else []),
                            *face_warnings(photo, hook, height=photo_box()[1])]:
                if warning:
                    print(f"warning: scene {index + 1}, picture {number}: {warning}")
    if photos and faces.find(Image.new("RGB", (64, 64))) is None:
        print(f"note: faces not checked ({faces.why_off()}): pip install opencv-python-headless numpy, then look "
              "at every face yourself all the same")


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
