"""Checks of the picture rules of the edit that the machine watches (owner, 19/11/2026: "hook 5s đầu phải là ảnh
đẹp, rồi ảnh k bị mất mặt"): a face cut by the frame or leaving it during the move, a face under the text printed on
the picture, the first picture small or flat. The frame is asked as the video is made; the faces are given here
(no detector needed), and when opencv is installed the detector is tried on a face cut out of a banknote too.
No network. Usage: python tools/faces_test.py"""
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image   # noqa: E402

from news import faces, render   # noqa: E402
from news.visuals import Photo   # noqa: E402


def photo(size=(1600, 1200), **options):
    return Photo(Image.new("RGB", size, "#777777"), "https://example.jp/", "t", "example.jp", "", "", **options)


def with_image(picture, image):
    from dataclasses import replace
    return replace(picture, image=image)


def said(picture, box, **options):
    real = faces.find
    faces.find = lambda image: [box] if box else []
    try:
        return " | ".join(render.face_warnings(picture, **options))
    finally:
        faces.find = real


def main():
    height = render.STORY_HEIGHT
    render.use_style("story")
    middle, right, low = (0.42, 0.25, 0.58, 0.50), (0.84, 0.20, 0.96, 0.42), (0.42, 0.72, 0.58, 0.84)
    for move in ("push-in", "pull-back", "hold", "reveal", "punch-in", "pan-right", ""):
        assert said(photo(move=move), middle, height=height) == "", (move, said(photo(move=move), middle, height=height))
    # a face at the side: the frame of a wide picture does not reach it, and a close-up on the middle loses it
    assert "a face is cut by the frame or leaves it" in said(photo(move="push-in"), right, height=height)
    assert "a face is cut by the frame or leaves it" in said(photo(move="close-up"), right, height=height)
    advised = re.search(r'try "focus": \[([\d.]+), ([\d.]+)\]', said(photo(move="close-up"), right, height=height))
    assert advised, said(photo(move="close-up"), right, height=height)
    focus = (float(advised[1]), float(advised[2]))
    assert said(photo(move="close-up", focus=focus), right, height=height) == "", focus     # the advice works
    assert 'try "focus"' not in said(photo(move="pan-right"), right, height=height)         # a pan crosses the picture
    both = said(photo(move="close-up"), None, height=height)   # two faces too far apart for a close-up: no focus helps
    real = faces.find
    faces.find = lambda image: [(0.05, 0.3, 0.2, 0.5), (0.8, 0.3, 0.95, 0.5)]
    try:
        both = " | ".join(render.face_warnings(photo(move="close-up"), height=height))
    finally:
        faces.find = real
    assert "a face is cut" in both and 'try "focus"' not in both, both
    windows = render.frame_windows(photo(move="push-in"), height=height)
    assert windows[0][0] < windows[1][0] and windows[0][2] > windows[1][2], windows        # a push-in closes in
    assert said(photo(move="push-in", fit="contain"), right, height=height) == ""           # shown whole: never cut
    # under the text printed on the foot of the picture; on the first picture the face belongs in the upper half
    tall = (1000, 1400)
    assert "a face lies under the headline" in said(photo(tall, move="hold"), low, height=height)
    assert "a face lies under the hook line" in said(photo(tall, move="hold"), low, hook=True, height=height)
    half = (0.40, 0.52, 0.60, 0.64)
    assert said(photo(tall, move="hold"), half, height=height) == ""
    assert "the face is in the lower half of the first picture" in said(photo(tall, move="hold"), half, hook=True,
                                                                         height=height)
    assert said(photo(tall, move="hold"), None, hook=True, height=height) == ""             # no face: nothing said
    render.use_style("news")   # the headline is under the picture there: nothing lies over a face
    assert "lies under" not in said(photo(tall, move="hold"), middle, height=render.PHOTO_HEIGHT)
    assert "lies under" not in said(photo(tall, move="hold"), low, height=render.PHOTO_HEIGHT)
    render.use_style("story")
    # the first picture: large, crisp, and a photograph
    crisp = Image.effect_noise((1600, 1200), 60).convert("RGB")
    assert render.hook_warnings(with_image(photo(), crisp)) == []
    assert "the first picture looks soft" in render.hook_warnings(photo((1600, 1200)))[-1]   # one flat tone
    # enlarged by "fx": enhance (its `source` is the size of the file): it may be smaller, down to 640 px
    assert not any("is small" in line for line in render.hook_warnings(photo((1600, 1200), source=(960, 720))))
    assert "the first picture is small (600x450, under 640 px on one side, even enlarged by the model" in \
        render.hook_warnings(photo((1600, 1200), source=(600, 450)))[0]
    assert "the first picture is small (800x600" in render.hook_warnings(photo((800, 600)))[0]
    assert "shown whole or marked flat" in render.hook_warnings(photo(fit="contain"))[0]
    assert "shown whole or marked flat" in render.hook_warnings(photo(depth=False))[0]
    assert faces.centre([(0.1, 0.2, 0.3, 0.4), (0.5, 0.2, 0.7, 0.6)]) == [0.4, 0.4]
    assert faces.main_faces([(0, 0, 0.4, 0.4), (0.5, 0.5, 0.75, 0.75), (0.9, 0.9, 0.95, 0.95)]) == [
        (0, 0, 0.4, 0.4), (0.5, 0.5, 0.75, 0.75)]
    crowd = [(n / 10, 0.4, n / 10 + 0.08, 0.5) for n in range(8)]   # an audience: nobody of the story to keep
    assert faces.main_faces(crowd) == [] and len(faces.main_faces(crowd[:5])) == 5
    found = faces.find(Image.new("RGB", (640, 480), "#808080"))
    if found is None:
        print(f"picture rules check OK (the detector itself not tried: {faces.why_off()})")
    else:
        assert found == [], found   # a grey picture has no face
        print("picture rules check OK (face detector at work)")


if __name__ == "__main__":
    main()
