"""Try every edit of the catalogue (news/edits.py) on the pictures of the sample story, without the voice engine.

python tools/edits_test.py stories/mau-boj.json <its find folder> <out folder> [<seconds per move, default 2>]

Writes <out>/edits-sample.json (a story that uses every move and every cut: it is read through the same checks as
a real story), <out>/moves.jpg (each move at its start, middle and end, for a picture shown 5 seconds),
<out>/cuts.jpg (each cut a quarter, half and three quarters through, in both frames) and <out>/news/video.mp4,
<out>/paper/video.mp4 (every move for a few seconds, the cuts in turn, silence as the voice). Also checks that
wrong names are refused. There is no sample video for this channel: these files are what the owner and Claude
look at to judge the edits.
"""
import json
from pathlib import Path
import sys
import wave

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from news.custom import load_story, validate   # noqa: E402
from news.edits import CONTAIN_MOVES, CUTS, MOVES   # noqa: E402
from news import render   # noqa: E402
from news.voice import Caption   # noqa: E402

RATE = 24000
# a picture of the sample that suits each move: wide ones to pan across, tall ones to rise and fall along
PICTURES = {
    "push-in": {"pick": "4-5", "focus": [0.5, 0.4]}, "pull-back": {"pick": "5-1"},
    "pan-right": {"pick": "4-8"}, "pan-left": {"pick": "5-2"},
    "rise": {"pick": "5-3", "focus": [0.5, 0.4]}, "fall": {"pick": "6-6"},
    "close-up": {"pick": "5-7", "focus": [0.5, 0.45]}, "reveal": {"pick": "4-2"},
    "punch-in": {"pick": "4-3"}, "hold": {"pick": "2-1", "fit": "contain"},
}


def sample(story):
    """A story with one scene per move, the cuts in turn."""
    data = json.loads(Path(story).read_text(encoding="utf-8"))
    cuts = list(CUTS)
    scenes = []
    for number, name in enumerate(MOVES):
        scene = {"label": name, "headline": name, "lines": [name], "photo": dict(PICTURES[name], move=name),
                 "why": "thử từng kiểu"}
        if number:
            scene["cut"] = cuts[(number - 1) % len(cuts)]
            scene["lines"] = [f"{name} / {scene['cut']}"]
        scenes.append(scene)
    return {"title": "edits", "date": data["date"], "source": data.get("source", ""), "stage": "render",
            "searches": data["searches"], "scenes": scenes}


def refused(data):
    """Wrong names must be refused, with the valid names in the message."""
    def problems(change):
        broken = json.loads(json.dumps(data))
        change(broken["scenes"])
        return "\n".join(validate(broken))
    checks = (
        (lambda scenes: scenes[0]["photo"].update(move="zoom"), "push-in, pull-back"),
        (lambda scenes: scenes[1].update(cut="wipe"), "fade, page, hard, dip"),
        (lambda scenes: scenes[-1]["photo"].update(move="pan-left"), ", ".join(CONTAIN_MOVES)),
        (lambda scenes: scenes[1].update(why=""), '"why"'),
    )
    for change, expected in checks:
        found = problems(change)
        if expected not in found:
            sys.exit(f"error: a wrong edit was not refused as expected ({expected!r} not in {found!r})")
    print(f"wrong names: refused ({len(checks)} cases)")


def tag(image, words, size=30):
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, int(render.font(size).getlength(words)) + 24, size + 20), fill="#000000")
    draw.text((12, 8), words, font=render.font(size), fill="#ffd25a")
    return image


def moves_sheet(photos, out):
    names = list(MOVES)
    sheet = Image.new("RGB", (3 * 370 + 10, len(names) * 243 + 10), "#000000")
    for row, name in enumerate(names):
        for column, at in enumerate((0.0, 0.5, 1.0)):
            picture = render.named_photo(photos[row][0], at, name, 5.0).resize((360, 233), Image.Resampling.BICUBIC)
            if not column:
                tag(picture, name, 22)
            sheet.paste(picture, (10 + column * 370, 10 + row * 243))
    sheet.save(out / "moves.jpg", quality=88)


def cuts_sheet(release, beats, photos, out):
    cuts = list(CUTS)
    sheet = Image.new("RGB", (6 * 280 + 10, len(cuts) * 490 + 10), "#000000")
    for half, name in enumerate(("news", "paper")):
        render.use_style(name)
        for row, cut in enumerate(cuts):
            length = render.CUT_SECONDS[cut] or 0.5
            pair = [beats[0], beats[1].__class__(**{**beats[1].__dict__, "cut": cut})]
            scenes = render.scenes_for(pair, release, {0: photos[0], 1: photos[2]}, False, [(0.0, 3.0), (3.0, 6.0)])
            for column, at in enumerate((0.25, 0.5, 0.75)):
                frame = render.frame_at(scenes, 1, 3.0 + at * length).resize((270, 480), Image.Resampling.BICUBIC)
                if not column:
                    tag(frame, f"{cut} ({name})", 20)
                sheet.paste(frame, (10 + (half * 3 + column) * 280, 10 + row * 490))
    sheet.save(out / "cuts.jpg", quality=88)


def video(release, beats, photos, seconds, name, out):
    folder = out / name
    folder.mkdir(parents=True, exist_ok=True)
    intervals = [(index * seconds, (index + 1) * seconds) for index in range(len(beats))]
    captions = [Caption(start, end, beat.lines[0]) for beat, (start, end) in zip(beats, intervals)]
    wav = folder / "silence.wav"
    with wave.open(str(wav), "wb") as silence:
        silence.setparams((1, 2, RATE, 0, "NONE", "not compressed"))
        silence.writeframes(bytes(2 * int(seconds * len(beats) * RATE)))
    render.use_style(name)
    render.encode(beats, release, photos, False, intervals, captions, wav, folder)
    wav.unlink()
    size = (folder / "video.mp4").stat().st_size
    if size < 100_000:
        sys.exit(f"error: edits test ({name}): the video is only {size} bytes")
    print(f"edits test ({name}): OK, {seconds * len(beats):.0f} s, {size // 1000} kB")


def main():
    story, pictures, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    seconds = float(sys.argv[4]) if len(sys.argv) > 4 else 2.0
    out.mkdir(parents=True, exist_ok=True)
    data = sample(story)
    refused(data)
    (out / "edits-sample.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    release, beats, photos = load_story(out / "edits-sample.json", pictures)
    for index in sorted(photos):
        if warning := render.move_warning(photos[index][0]):
            sys.exit(f"error: the sample picture of {beats[index].label} does not suit its move ({warning})")
    moves_sheet(photos, out)
    cuts_sheet(release, beats, photos, out)
    render.use_style("news")
    render.stills(beats, release, photos, out)   # sheet.jpg and edits.md, as for a real story
    for name in ("news", "paper"):
        video(release, beats, photos, seconds, name, out)


if __name__ == "__main__":
    main()
