"""Keeps the people of a picture in the frame ("fx": {"frame": true}).

The frame of a story is tall and most press pictures are wide: filling the frame shows about half of a wide
picture, and the people at its sides are cut. Here the machine finds the faces of each chosen picture (YuNet, a
small face detector of OpenCV: news/models/face_detection_yunet_2023mar.onnx, MIT licence) and frames it by them:
  - the people fit in the frame: the camera is aimed at the point between them and never comes closer than the
    zoom that still holds every face; a pan only travels as far as they stay in the frame (news/render.py camera);
  - they stand wider than the frame can show: the picture is shown whole instead of filling the frame, cut down to
    the part that holds the people, so that it is as large as it can be.
A picture without people (a view, a building, a document) or of a crowd of small faces stays as it was chosen.
Needs numpy and opencv-python-headless (imported here only); without them every picture stays as it was chosen.
"""
import os
from dataclasses import replace
from pathlib import Path

MODEL = Path(os.environ.get("FACE_MODEL") or Path(__file__).with_name("models") / "face_detection_yunet_2023mar.onnx")
SIDES = (1280, 480)   # searched at two sizes: small faces show in the large one, a face that fills the picture in the small one
SURE = 0.6            # how sure the detector must be of a face
CLEAR = 0.85          # ... and of a face that counts as one of the people (a blurred face in the background stays under it)
MAIN = 0.6            # a face at least this share as tall as the largest one belongs to the people of the picture
SMALL = 80            # pixels on screen: no face taller than this means a view, left as it was chosen
CROWD = 5             # more people than this are a crowd: left as it was chosen
WHOLE = 0.55          # a picture shown whole must fill at least this share of the frame
TYPICAL = 5.0         # seconds a picture usually stays: what its camera looks at is judged over this move
SIDE, ABOVE, BELOW = 0.25, 0.45, 0.45   # the room kept around a face (hair, a hat, the chin), in face widths and heights


def overlap(a, b):
    left, top, right, bottom = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    return max(0.0, right - left) * max(0.0, bottom - top)


DETECTOR = []


def detector(size):
    import cv2
    if not DETECTOR:
        try:   # OpenCV 5 prints a line for every picture otherwise
            cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)
        except AttributeError:
            pass
        DETECTOR.append(cv2.FaceDetectorYN.create(str(MODEL), "", size, SURE, 0.3, 500))
    DETECTOR[0].setInputSize(size)
    return DETECTOR[0]


def find_faces(image):
    """The faces of a picture: (left, top, right, bottom, how sure) in its pixels, the largest first."""
    import numpy as np
    found = []
    for side in SIDES:
        scale = min(1.0, side / max(image.size))
        size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
        pixels = np.asarray(image.convert("RGB").resize(size))[:, :, ::-1].copy()
        rows = detector(size).detect(pixels)[1]
        for row in rows if rows is not None else []:
            x, y, w, h = (float(value) / scale for value in row[:4])
            box = (max(0.0, x), max(0.0, y), min(image.width, x + w), min(image.height, y + h), float(row[14]))
            if box[2] - box[0] < 4 or box[3] - box[1] < 4:
                continue
            same = [other for other in found
                    if overlap(box, other) > 0.4 * min((box[2] - box[0]) * (box[3] - box[1]),
                                                       (other[2] - other[0]) * (other[3] - other[1]))]
            if not same:
                found.append(box)
            elif box[4] > max(other[4] for other in same):   # the same face seen at both sizes: the surer one
                found[:] = [other for other in found if other not in same] + [box]
        if scale == 1.0:
            break
    return sorted(found, key=lambda box: box[1] - box[3])


def around(faces, size, room=1.0):
    """The part of the picture that holds these faces with some room around each."""
    boxes = [(l - SIDE * room * (r - l), t - ABOVE * room * (b - t), r + SIDE * room * (r - l), b + BELOW * room * (b - t))
             for l, t, r, b in (face[:4] for face in faces)]
    return (max(0.0, min(box[0] for box in boxes)), max(0.0, min(box[1] for box in boxes)),
            min(size[0], max(box[2] for box in boxes)), min(size[1], max(box[3] for box in boxes)))


def inside(box, frame, slack=2.0):
    return (box[0] >= frame[0] - slack and box[1] >= frame[1] - slack
            and box[2] <= frame[2] + slack and box[3] <= frame[3] + slack)


def held(photo, keep, height):
    """Whether the camera of this picture shows all of `keep` from the start of its move to the end."""
    from . import render
    name = photo.move or "push-in"
    return all(inside(keep, render.window(photo.image.size, height,
                                          *render.camera(photo, photo.image.size, t, name, TYPICAL, height)))
               for t in (0.0, 0.5, 1.0))


def trimmed(image):
    """The picture without the plain white or black bars some copies carry at their sides (a scan's margin, the
    bars of a television picture). Only bars: a dark background has grain and no straight edge."""
    import numpy as np
    grey = np.asarray(image.convert("L"), dtype=np.float32)

    def bar(lines):   # how many lines from this side are one flat white or black
        count, limit = 0, int(len(lines) * 0.3)
        for line in lines[:limit]:
            if line.std() > 4 or 16 < line.mean() < 240:
                break
            count += 1
        return count if count >= max(3, len(lines) * 0.008) and count < limit else 0
    left, right = bar(grey.T), bar(grey.T[::-1])
    top, bottom = bar(grey), bar(grey[::-1])
    if not (left or right or top or bottom):
        return image, (0, 0)
    edge = 2   # the soft edge of a bar
    box = (left + edge * bool(left), top + edge * bool(top),
           image.width - right - edge * bool(right), image.height - bottom - edge * bool(bottom))
    return image.crop(box), (box[0], box[1])


def frame(photo, height, faces=None):
    """The picture framed by its people: (picture, note). The note says in Vietnamese what was changed, None
    when the picture stays as it was chosen."""
    from . import render
    if photo.fit == "contain":
        return photo, None
    notes = []
    image, (dx, dy) = trimmed(photo.image)
    if image is not photo.image:   # the chosen point stays on the same thing of the picture
        focus = (render.clamp((photo.focus[0] * photo.image.width - dx) / image.width, 0, 1),
                 render.clamp((photo.focus[1] * photo.image.height - dy) / image.height, 0, 1))
        photo, faces = replace(photo, image=image, focus=focus), None
        notes.append("cắt bỏ viền trắng/đen của ảnh")
    iw, ih = image.size
    fill = max(render.W / iw, height / ih)
    cw, ch = min(iw, render.W / fill), min(ih, height / fill)   # what the frame shows at its widest
    faces = [box for box in (find_faces(image) if faces is None else faces)
             if box[4] >= CLEAR and (box[3] - box[1]) * fill >= SMALL / 2]
    name = photo.move or "push-in"
    point = (photo.focus[0] * iw, photo.focus[1] * ih)

    def near(box):
        return ((box[0] + box[2]) / 2 - point[0]) ** 2 + ((box[1] + box[3]) / 2 - point[1]) ** 2

    def done(picture=photo, note=None):
        return picture, ", ".join(notes + ([note] if note else [])) or None
    if name == "close-up":   # one person is meant: the face nearest to the chosen point
        main = sorted(faces, key=near)[:1]
        room = around(main, (iw, ih), room=3.0) if main else None
        if not main or not (room[0] <= point[0] <= room[2] and room[1] <= point[1] <= room[3]):
            return done()   # the close-up is on something else than a face
    else:
        # the people meant are those the chosen camera looks at: the faces it shows, of about the size of the largest
        views = [render.window((iw, ih), height, *render.camera(photo, (iw, ih), t, name, TYPICAL, height))
                 for t in (0.0, 0.5, 1.0)]
        shown = [box for box in faces
                 if any(v[0] <= (box[0] + box[2]) / 2 <= v[2] and v[1] <= (box[1] + box[3]) / 2 <= v[3] for v in views)]
        if not shown:
            return done()
        tallest = max(box[3] - box[1] for box in shown)
        main = [box for box in shown if box[3] - box[1] >= MAIN * tallest]
        if tallest * fill < SMALL or len(main) > CROWD:
            return done()   # a view or a crowd: left as it was chosen
    subject, tight = around(main, (iw, ih)), around(main, (iw, ih), room=0.3)
    if tight[2] - tight[0] > cw or tight[3] - tight[1] > ch:
        # the people stand wider (or higher) than the frame can show: the whole picture, cut to the part with them
        w, h = min(iw, (subject[2] - subject[0]) * 1.04), min(ih, (subject[3] - subject[1]) * 1.04)
        if w / h > render.W / height:
            h = min(ih, w * height / render.W)
        else:
            w = min(iw, h * render.W / height)
        left = render.clamp((subject[0] + subject[2]) / 2 - w / 2, 0, iw - w)
        top = render.clamp((subject[1] + subject[3]) / 2 - h / 2, 0, ih - h)
        part = image if w * h > 0.97 * iw * ih else image.crop((round(left), round(top), round(left + w), round(top + h)))
        scale = min(render.W / part.width, height / part.height)
        share = part.width * part.height * scale * scale / (render.W * height)
        if share >= WHOLE:
            return done(replace(photo, image=part, fit="contain", focus=(0.5, 0.5)),
                        f"{len(main)} người đứng rộng hơn khung: hiện cả ảnh (chiếm {share:.0%} khung)")
        # shown whole the picture would be small: the frame keeps the people nearest to the chosen point
        kept = []
        for box in sorted(main, key=near):
            group = around(kept + [box], (iw, ih), room=0.3)
            if group[2] - group[0] <= cw and group[3] - group[1] <= ch:
                kept.append(box)
        notes.append(f"ảnh quá rộng so với khung: chỉ giữ được {len(kept)}/{len(main)} người, nên đổi ảnh khác")
        main = kept or sorted(main, key=near)[:1]
        subject, tight = around(main, (iw, ih)), around(main, (iw, ih), room=0.3)
    keep = (tight[0] / iw, tight[1] / ih, tight[2] / iw, tight[3] / ih)
    if held(photo, tight, height):
        return done(replace(photo, keep=keep))
    width, tall = subject[2] - subject[0], subject[3] - subject[1]
    aim = ((subject[0] + subject[2]) / 2 / iw, (subject[1] + subject[3]) / 2 / ih)
    cap = max(min(cw / width, ch / tall), min(1.10, cw / (tight[2] - tight[0]), ch / (tight[3] - tight[1])))
    return done(replace(photo, aim=aim, cap=round(max(1.0, cap), 3), keep=keep, move=name), "căn khung theo mặt người")


NOTES = []   # what was changed in the story being made, for edits.md


def frame_story(photos, height):
    """Every chosen picture of a story framed by its people ({scene: [pictures]}); says what was changed."""
    NOTES.clear()
    try:
        import cv2   # noqa: F401
        import numpy   # noqa: F401
    except ImportError as error:
        print(f"warning: framing by faces off ({error})")
        return photos
    framed = {}
    for index, scene in photos.items():
        framed[index] = []
        for number, photo in enumerate(scene, 1):
            try:
                picture, note = frame(photo, height)
            except Exception as error:   # one picture the detector cannot read must not stop the video
                print(f"warning: scene {index + 1}, picture {number}: not framed ({type(error).__name__}: {str(error)[:100]})")
                picture, note = photo, None
            if note:
                NOTES.append(f"cảnh {index + 1}, ảnh {number}: {note}")
                print(f"{'warning' if 'nên đổi' in note else 'framing'}: scene {index + 1}, picture {number}: {note}")
            framed[index].append(picture)
    return framed
