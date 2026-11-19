"""Pictures out of the video the owner sent (owner, 19/11/2026: "nếu repo nào đc dựng bằng cách remix video hoặc tao
có gửi video, có thể sử dụng hình ảnh/video trong video tao gửi").

The video the owner sends for a story is a source of pictures like the searches are: this tool lays out its shots to
choose from, then keeps the chosen ones in the repository, where a `file:` search finds them (credited 元動画).

1. Look:  python tools/video_frames.py <video> <story name>
   One frame from the middle of every shot of the video (a shot = the picture staying the same for a second or
   more; a shot seen before is not shown twice), full size, in <video>.frames/: frame-<n>.jpg, frames.json (the time
   of each) and sheet.jpg, a numbered contact sheet with the times. Look at the sheet yourself.
2. Keep:  python tools/video_frames.py <video> <story name> --keep 3,7,12 [--crop x,y,w,h]
   Saves those frames as stories/media/<story name>/v-<m>m<ss>s.jpg and prints the lines to append to "searches"
   ("file:stories/media/<story name>/v-0m12s.jpg"). --crop cuts the same part out of each kept frame, as fractions
   of the frame (x, y of the top-left corner, then width and height: "0,0.18,1,0.45" keeps a band of the middle):
   use it to take the picture without the burnt-in caption or the blurred background around an inset picture. Run
   it again with other numbers for frames that need another crop.

A picture with the source's caption, logo or watermark burnt over it is still not used as it is: crop it clean, or
leave it. Needs ffmpeg. Options: --out <folder> (instead of <video>.frames), --every <seconds> between the frames
looked at (0.5), --at <seconds>[,<seconds>…] with --keep, to take exact moments instead of numbered frames.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageDraw, ImageFont   # noqa: E402

REPO = Path(__file__).resolve().parent.parent
NAME = re.compile(r"[A-Za-z0-9._-]+")
SAME = 10       # fingerprints this close (bits of 64) are the same picture, as in news/find.py
SMALL = 400     # a kept picture should have this many pixels on its smaller side, as the searches ask


def fingerprint(image):
    grey = image.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
    pixels = list(grey.tobytes())
    return sum(1 << i for i in range(64) if pixels[i // 8 * 9 + i % 8] > pixels[i // 8 * 9 + i % 8 + 1])


def close(one, other):
    return bin(one ^ other).count("1") <= SAME


def run(*command):
    done = subprocess.run(command, capture_output=True, text=True)
    if done.returncode:
        sys.exit(f"error: {command[0]} failed: {done.stderr.strip()[-400:]}")
    return done.stdout


def length(video):
    return float(run("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)))


def grab(video, seconds, path):
    """One full-size frame of the video at a moment."""
    run("ffmpeg", "-v", "error", "-y", "-ss", f"{seconds:.3f}", "-i", str(video), "-frames:v", "1", "-q:v", "2",
        str(path))


def shots(video, every):
    """The moments (seconds) of the middle of each shot, a shot seen before left out."""
    with tempfile.TemporaryDirectory(prefix="frames-") as scratch:
        run("ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf", f"fps={1 / every:.4f},scale=160:-2",
            "-q:v", "5", f"{scratch}/%06d.jpg")
        marks = []
        for path in sorted(Path(scratch).glob("*.jpg")):
            with Image.open(path) as small:
                marks.append(fingerprint(small))
    groups, start = [], 0
    for index in range(1, len(marks) + 1):
        if index == len(marks) or not close(marks[index], marks[start]):
            groups.append((start, index))   # frames start … index - 1 show one picture
            start = index
    kept, moments = [], []
    for first, after in groups:
        if (after - first) * every < 1 and len(groups) > 1:   # a flash or a cut in progress
            continue
        if any(close(marks[first], mark) for mark in kept):
            continue
        kept.append(marks[first])
        moments.append((first + (after - first) / 2) * every)
    return moments


def stamp(seconds):
    return f"{int(seconds // 60)}m{int(seconds % 60):02d}s"


def sheet(paths, moments, path):
    face = ImageFont.load_default(size=17)
    board = Image.new("RGB", (4 * 380, -(-len(paths) // 4) * 400), "#0a0a0c")
    for index, (name, seconds) in enumerate(zip(paths, moments)):
        with Image.open(name) as picture:
            size = picture.size
            picture.thumbnail((360, 360))
            board.paste(picture, (index % 4 * 380 + (380 - picture.width) // 2, index // 4 * 400 + 10))
        label = f"#{index + 1}  {stamp(seconds)}  {size[0]}x{size[1]}"
        ImageDraw.Draw(board).text((index % 4 * 380 + 10, index // 4 * 400 + 374), label, fill="#ffd25a", font=face)
    board.save(path, quality=85)


def look(video, out, every):
    moments = shots(video, every)
    if not moments:
        sys.exit("error: no frame could be read from the video")
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("frame-*.jpg"):
        old.unlink()
    paths = []
    for number, seconds in enumerate(moments, 1):
        paths.append(out / f"frame-{number}.jpg")
        grab(video, seconds, paths[-1])
    (out / "frames.json").write_text(json.dumps({"video": video.name, "frames": [round(m, 2) for m in moments]}),
                                     encoding="utf-8")
    sheet(paths, moments, out / "sheet.jpg")
    print(f"{len(paths)} shots of {video.name} ({stamp(length(video))}): look at {out / 'sheet.jpg'}")
    print("then: python tools/video_frames.py <video> <story name> --keep <numbers> [--crop x,y,w,h]")


def keep(video, out, story, numbers, moments, crop):
    if moments is None:
        listed = out / "frames.json"
        if not listed.exists():
            sys.exit(f"error: no {listed}: run without --keep first (and look at the sheet), or give --at <seconds>")
        known = json.loads(listed.read_text(encoding="utf-8"))["frames"]
        wrong = [number for number in numbers if not 1 <= number <= len(known)]
        if wrong:
            sys.exit(f"error: no frame {wrong[0]}: the sheet has frames 1 to {len(known)}")
        moments = [known[number - 1] for number in numbers]
    media = REPO / "stories" / "media" / story
    media.mkdir(parents=True, exist_ok=True)
    lines = []
    for seconds in moments:
        target = media / f"v-{stamp(seconds)}.jpg"
        count = 1
        while target.exists():   # another crop of the same moment, or the same second of another run
            count += 1
            target = media / f"v-{stamp(seconds)}-{count}.jpg"
        with tempfile.TemporaryDirectory(prefix="frames-") as scratch:
            grab(video, seconds, Path(scratch) / "frame.jpg")
            with Image.open(Path(scratch) / "frame.jpg") as frame:
                picture = frame.convert("RGB")
        if crop:
            x, y, w, h = crop
            box = (round(x * picture.width), round(y * picture.height),
                   round((x + w) * picture.width), round((y + h) * picture.height))
            picture = picture.crop(box)
        picture.save(target, quality=93)
        small = "   (small: under %d px on one side)" % SMALL if min(picture.size) < SMALL else ""
        print(f"kept {target.relative_to(REPO)}  {picture.width}x{picture.height}{small}")
        lines.append(f'"file:{target.relative_to(REPO).as_posix()}"')
    print('append to "searches" of the story (credited 元動画):')
    print("  " + ",\n  ".join(lines))


def numbers_of(text, kind=int):
    try:
        return [kind(part) for part in text.split(",") if part.strip()]
    except ValueError:
        sys.exit(f"error: expected numbers separated by commas, got {text!r}")


def main(arguments=None):
    parser = argparse.ArgumentParser(description="Pictures out of the video the owner sent (see the top of the file).")
    parser.add_argument("video")
    parser.add_argument("story", help="the story name (stories/<name>.json without .json)")
    parser.add_argument("--out")
    parser.add_argument("--every", type=float, default=0.5)
    parser.add_argument("--keep")
    parser.add_argument("--at")
    parser.add_argument("--crop")
    options = parser.parse_args(arguments)
    video = Path(options.video)
    if not video.is_file():
        sys.exit(f"error: no video at {video}")
    if not NAME.fullmatch(options.story):
        sys.exit(f"error: the story name must be ASCII letters, digits, '.', '_', '-', got {options.story!r}")
    out = Path(options.out) if options.out else video.with_name(video.name + ".frames")
    crop = None
    if options.crop:
        crop = numbers_of(options.crop, float)
        if len(crop) != 4 or not (0 <= crop[0] < 1 and 0 <= crop[1] < 1 and 0 < crop[2] and 0 < crop[3]
                                  and crop[0] + crop[2] <= 1.0001 and crop[1] + crop[3] <= 1.0001):
            sys.exit('error: --crop is "x,y,w,h" as fractions of the frame, e.g. "0,0.18,1,0.45"')
    if options.keep or options.at:
        keep(video, out, options.story, numbers_of(options.keep or ""),
             numbers_of(options.at, float) if options.at else None, crop)
    else:
        look(video, out, options.every)


if __name__ == "__main__":
    main()
