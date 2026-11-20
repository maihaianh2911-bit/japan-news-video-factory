"""Where the faces of a picture are, and whether the frame keeps them.

Owner, 19/11/2026, on the rules of the edit: "ảnh k bị mất mặt": the whole face of the person, forehead to chin,
stays inside the frame for as long as the picture is shown, while it zooms or pans too, and the text printed on
the picture (the headline, the hook line) does not lie over it.

The faces are found with YuNet (the face detector of OpenCV Zoo, an open model of 230 KB kept beside this file as
face_yunet.onnx), through OpenCV. Optional, as the picture effects are: without opencv (`pip install
opencv-python-headless numpy`) find() returns None and nothing is checked.
"""
from pathlib import Path

MODEL = Path(__file__).with_name("face_yunet.onnx")
SURE, SMALL, MAIN = 0.75, 0.035, 0.25   # score kept; a face under 3.5 % of the picture's longer side is a passer-by;
#                                         a face counts beside the largest when it has a quarter of its area
CROWD = 5   # more faces of that size than this is a crowd (an audience, a march): its edges always cut someone
STATE = {}


def find(image):
    """The faces of a PIL picture as boxes (left, top, right, bottom) in 0–1 of the picture, the largest first.
    None when they cannot be looked for (no opencv, no model); [] when the picture has none."""
    if "detector" not in STATE:
        try:
            import cv2
            import numpy
            try:   # OpenCV 5 prints a line about its graph engine at every start: errors only
                cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)
            except Exception:
                pass
            STATE.update(cv2=cv2, numpy=numpy,
                         detector=cv2.FaceDetectorYN.create(str(MODEL), "", (320, 320), 0.6, 0.3, 50))
        except Exception as error:   # no opencv, an opencv without this detector, no model file
            STATE.update(detector=None, why=f"{type(error).__name__}: {str(error)[:100]}")
    if STATE["detector"] is None:
        return None
    cv2, numpy, detector = STATE["cv2"], STATE["numpy"], STATE["detector"]
    width, height = image.size
    scale = min(1.0, 960 / max(width, height))
    small = image.convert("RGB").resize((max(1, round(width * scale)), max(1, round(height * scale))))
    pixels = numpy.asarray(small)[:, :, ::-1].copy()   # OpenCV reads blue, green, red
    detector.setInputSize((small.width, small.height))
    _, found = detector.detect(pixels)
    boxes = []
    for face in [] if found is None else found:
        left, top, wide, tall, score = (float(face[0]), float(face[1]), float(face[2]), float(face[3]),
                                        float(face[14]))
        if score < SURE or max(wide, tall) < SMALL * max(small.width, small.height):
            continue
        boxes.append((max(0.0, left / small.width), max(0.0, top / small.height),
                      min(1.0, (left + wide) / small.width), min(1.0, (top + tall) / small.height)))
    return sorted(boxes, key=area, reverse=True)


def area(box):
    return max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1])


def main_faces(boxes):
    """The faces that matter: the largest and the ones not much smaller (not the passers-by behind). None in a
    crowd: the rule is about the people of the story, and the frame of a crowd always cuts someone at its edge."""
    main = [box for box in boxes if area(box) >= MAIN * area(boxes[0])] if boxes else []
    return main if len(main) <= CROWD else []


def centre(boxes):
    """The middle of the faces, as a "focus" of a picture entry (two decimals)."""
    left, top = min(box[0] for box in boxes), min(box[1] for box in boxes)
    right, bottom = max(box[2] for box in boxes), max(box[3] for box in boxes)
    return [round((left + right) / 2, 2), round((top + bottom) / 2, 2)]


def why_off():
    return STATE.get("why", "")
