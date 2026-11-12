"""Render vertical news video with timed Japanese captions and stable motion."""
from functools import lru_cache
import math
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw, ImageFont

from .story import VOICE_CREDIT, japanese_date

W, H, FPS = 1080, 1920, 30
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK"
WHITE, PAPER, INK = "#ffffff", "#f6f3ec", "#142232"
NAVY, MUTED, RED, GOLD = "#132133", "#99a9bb", "#b91835", "#ffda76"


@lru_cache(maxsize=64)
def font(size, bold=True):
    weight = "Bold" if bold else "Regular"
    return ImageFont.truetype(f"{FONT}-{weight}.ttc", size, index=0)


def wrap(value, width, face, maximum):
    lines = []
    for part in value.splitlines():
        line = ""
        for character in part:
            if line and face.getlength(line + character) > width and character not in "、。！？）」":
                lines.append(line)
                line = ""
            line += character
        if line:
            lines.append(line)
    if len(lines) > maximum:
        lines = lines[:maximum]
        lines[-1] = lines[-1][:-1] + "…"
    return "\n".join(lines)


def text(draw, x, y, value, size, fill=WHITE, *, bold=True, anchor="lt", spacing=18):
    for line_index, line in enumerate(value.splitlines()):
        draw.text((x, y + line_index * (size + spacing)), line, font=font(size, bold), fill=fill, anchor=anchor)


def label(draw, x, y, value, fill=RED):
    width = int(font(28).getlength(value)) + 42
    draw.rounded_rectangle((x, y, x + width, y + 58), radius=9, fill=fill)
    text(draw, x + 21, y + 14, value, 28)


def crop_photo(image, position, height):
    iw, ih = image.size
    scale = max(W / iw, height / ih) * (1.0 + 0.15 * position)
    cw, ch = W / scale, height / scale
    left = (iw - cw) * (0.46 + 0.08 * position)
    top = (ih - ch) * (0.50 - 0.10 * position)
    return image.resize((W, height), Image.Resampling.BICUBIC, box=(left, top, left + cw, top + ch))


def layout(beat, release, photo, demo):
    image = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, W, 14), fill=RED)
    label(draw, 70, 68, "日本のニュース")
    text(draw, 70, 152, japanese_date(release), 35, MUTED)
    if demo:
        text(draw, W - 70, 95, "過去のニュース・動作確認", 28, GOLD, anchor="rt")
    label(draw, 70, 261, beat.label, "#33475e")

    if photo:
        draw.rectangle((0, 338, W, 1054), fill="#29394a")
        draw.rectangle((0, 1038, W, 1054), fill=RED)
        label(draw, 70, 380, "資料写真", NAVY)
        headline_size = 70 if len(beat.headline) < 25 else 51
        text(draw, 70, 1100, wrap(beat.headline, 925, font(headline_size), 3), headline_size)
        if beat.value:
            text(draw, 70, 1320, beat.value, 90, GOLD)
        else:
            text(draw, 70, 1355, release.publisher, 42, MUTED)
    else:
        draw.rounded_rectangle((70, 350, 1010, 1410), radius=32, fill=PAPER)
        draw.rectangle((117, 419, 172, 426), fill=RED)
        text(draw, 119, 472, release.publisher, 38, "#5d6671")
        size = 60 if len(beat.headline) < 27 else 48
        text(draw, 119, 570, wrap(beat.headline, 840, font(size), 3), size, INK)
        if beat.value:
            value_size = 144 if len(beat.value) <= 7 else 98
            text(draw, 119, 813, beat.value, value_size, RED)
            if beat.evidence:
                text(draw, 119, 1055, wrap(beat.evidence, 830, font(33, False), 5), 33,
                     INK, bold=False)
        else:
            evidence = beat.evidence or release.title
            text(draw, 119, 839, wrap(evidence, 830, font(47, False), 5), 47, INK, bold=False)
        text(draw, 119, 1304, "公表資料", 29, "#5d6671")

    draw.line((70, 1704, W - 70, 1704), fill="#506075", width=2)
    text(draw, 70, 1742, f"出典  {release.publisher}", 29, MUTED, bold=False)
    text(draw, W - 70, 1742, VOICE_CREDIT, 24, MUTED, bold=False, anchor="rt")
    if photo:
        text(draw, 70, 1806, wrap(f"写真  {photo.creator} / {photo.license}", 940, font(23, False), 2),
             23, MUTED, bold=False)
    return image


def draw_captions(image, caption):
    draw = ImageDraw.Draw(image)
    face = font(52)
    contents = wrap(caption, 866, face, 2).splitlines()
    height = 83 * len(contents) + 26
    draw.rounded_rectangle((69, 1598 - height // 2, 1011, 1598 + height // 2), radius=19, fill="#0b1421")
    for line_index, line in enumerate(contents):
        draw.text((W / 2, 1598 - height / 2 + 21 + 83 * line_index), line,
                  font=face, fill=WHITE, anchor="mt", stroke_width=1, stroke_fill=WHITE)


def frame_for(base, photo, fraction, caption):
    frame = base.copy()
    if photo:
        ease = fraction * fraction * (3 - 2 * fraction)
        frame.paste(crop_photo(photo.image, ease, 700), (0, 338))
        draw = ImageDraw.Draw(frame)
        label(draw, 70, 380, "資料写真", NAVY)
    draw_captions(frame, caption)
    return frame


def encode(beats, release, photo, demo, intervals, captions, wav, out):
    cover_beat = beats[0]
    first_photo = photo if cover_beat.visual == "photo" else None
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
            for beat, (start, end) in zip(beats, intervals, strict=True):
                scene_photo = photo if beat.visual == "photo" else None
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


def srt_time(seconds):
    milliseconds = round(seconds * 1000)
    total_seconds, fraction = divmod(milliseconds, 1000)
    minutes, sec = divmod(total_seconds, 60)
    hours, minute = divmod(minutes, 60)
    return f"{hours:02}:{minute:02}:{sec:02},{fraction:03}"


def write_subtitles(captions, path: Path):
    entries = []
    for index, caption in enumerate(captions, 1):
        line = wrap(caption.text, 866, font(52), 2)
        entries.append(f"{index}\n{srt_time(caption.start)} --> {srt_time(caption.end)}\n{line}\n")
    path.write_text("\n".join(entries), encoding="utf-8")
