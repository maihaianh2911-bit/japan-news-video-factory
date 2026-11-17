"""Check of "fx": frame (news/framing.py): the people of a picture stay in the frame.

    python tools/frame_test.py

No network and no real picture: the faces are given by hand, so the rules are checked on their own; the face
detector itself is only started on an empty picture (it must find nothing and not fail). Needs numpy and
opencv-python-headless for the last two checks; without them they are skipped and said so.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image, ImageDraw   # noqa: E402

from news import framing, render   # noqa: E402
from news.visuals import Photo   # noqa: E402

HEIGHT = render.STORY_HEIGHT
problems = []


def check(what, good):
    print(("ok   " if good else "FAIL ") + what)
    if not good:
        problems.append(what)


def photo(size, move, focus=(0.5, 0.5), fit="cover"):
    return Photo(Image.new("RGB", size, "#777"), "", "", "", "", "", focus, fit, move)


def face(cx, cy, tall, sure=0.93):
    return (cx - tall * 0.4, cy - tall / 2, cx + tall * 0.4, cy + tall / 2, sure)


def held(picture, faces, seconds):
    """Every face is whole in the frame from the start of the move to its end."""
    size = picture.image.size
    windows = [render.window(size, HEIGHT, *render.camera(picture, size, t / 10, picture.move, seconds, HEIGHT))
               for t in range(11)]
    return all(framing.inside(box[:4], window) for box in faces for window in windows)


# 1. an old story: a picture without the new fields moves exactly as before
plain = photo((1800, 1200), "pan-right", (0.3, 0.4))
size = plain.image.size
fill = max(render.W / size[0], HEIGHT / size[1])
zoom, first, last, _ = render.pan_plan(size[0], render.W, fill, 0.3, 5.0)
check("a picture without people keeps its old pan",
      render.camera(plain, size, 0.0, "pan-right", 5.0, HEIGHT) == (zoom, first, 0.4)
      and render.camera(plain, size, 1.0, "pan-right", 5.0, HEIGHT) == (zoom, last, 0.4))
check("... and its old push-in", render.camera(plain, size, 1.0, "push-in", 5.0, HEIGHT) == (1.25, 0.3, 0.4))
same, note = framing.frame(plain, HEIGHT, faces=[])
check("no face found: the picture is left as it was chosen", same is plain and note is None)

# 2. one person at the side of a wide picture, the chosen pan would cut the face
side = [face(1560, 420, 300)]
panned = photo((1800, 1200), "pan-left", (0.85, 0.4))
check("(the chosen pan does cut the face)", not held(panned, side, 5.0))
framed, note = framing.frame(panned, HEIGHT, faces=side)
check("the face is held through the pan, short or long", note and all(held(framed, side, s) for s in (2.5, 5.0, 9.0)))
close = framing.frame(photo((1800, 1200), "close-up", (0.85, 0.35)), HEIGHT, faces=side)[0]
check("a close-up closes in on the whole face", held(close, side, 5.0))
for move in ("push-in", "pull-back", "reveal", "punch-in", "rise", "fall", "hold"):
    moved = framing.frame(photo((1800, 1200), move, (0.8, 0.4)), HEIGHT, faces=side)[0]
    if move != "reveal":   # a reveal starts close on purpose
        check(f"the face is held through {move}", all(held(moved, side, s) for s in (2.5, 5.0, 9.0)))

# 3. two people side by side who fit: both stay in
pair = [face(620, 500, 260), face(1150, 480, 250)]
both, note = framing.frame(photo((1800, 1200), "pan-right", (0.3, 0.4)), HEIGHT, faces=pair)
check("two people who fit are both held", both.fit == "cover" and all(held(both, pair, s) for s in (2.5, 5.0, 9.0)))

# 4. people standing wider than the frame: the picture is shown whole, cut to the part with them
wide = [face(400, 500, 250), face(1400, 480, 250)]
whole, note = framing.frame(photo((1800, 1200), "pan-right", (0.5, 0.4)), HEIGHT, faces=wide)
check("two people the pan passes, too far apart for the frame: shown whole",
      whole.fit == "contain" and "hiện cả ảnh" in (note or "") and whole.image.width >= 1200)
alone, note = framing.frame(photo((1800, 1200), "push-in", (0.2, 0.4)), HEIGHT, faces=wide)
check("... but a camera that looks at one of them keeps that one", alone.fit == "cover" and held(alone, wide[:1], 5.0))

# 5. a crowd, a view with small faces, a blurred face in the background: left as chosen
crowd = [face(430 + 115 * n, 400 + 160 * (n % 3), 110) for n in range(9)]
picture = photo((1800, 1200), "push-in")
check("a crowd is left as it was chosen", framing.frame(picture, HEIGHT, faces=crowd)[0] is picture)
check("small faces are left as they were chosen", framing.frame(picture, HEIGHT, faces=[face(200, 300, 40)])[0] is picture)
check("a blurred face does not count", framing.frame(picture, HEIGHT, faces=[face(1650, 400, 300, sure=0.7)])[0] is picture)
check("a picture shown whole is left alone",
      framing.frame(photo((1800, 1200), "push-in", fit="contain"), HEIGHT, faces=side)[1] is None)

# 6. the bars at the sides of a picture, and the detector itself
try:
    import cv2   # noqa: F401
    import numpy   # noqa: F401
except ImportError as error:
    print(f"skipped: the bars and the detector ({error})")
else:
    barred = Image.effect_noise((1200, 800), 40).convert("RGB")
    draw = ImageDraw.Draw(barred)
    draw.rectangle((0, 0, 149, 799), fill="white")
    draw.rectangle((1050, 0, 1199, 799), fill="white")
    cut, offset = framing.trimmed(barred)
    check("white bars at the sides are cut off", abs(cut.width - 900) <= 6 and cut.height == 800 and abs(offset[0] - 150) <= 3)
    dark = Image.effect_noise((1200, 800), 12).point(lambda level: level // 6).convert("RGB")
    check("a dark background is not taken for a bar", framing.trimmed(dark)[0] is dark)
    check("the face detector starts and finds no face on an empty picture",
          framing.find_faces(Image.effect_noise((900, 600), 30).convert("RGB")) == [])
    photos = framing.frame_story({0: [photo((1800, 1200), "push-in")]}, HEIGHT)
    check("a whole story goes through", len(photos[0]) == 1 and photos[0][0].fit == "cover")

if problems:
    sys.exit(f"{len(problems)} problem(s)")
print("frame test: OK")
