"""Depth of a picture, and the picture seen from a camera that moved a little (a light 2.5D parallax).

Only used when a story asks for it ("fx": {"depth": true}). The depth comes from Depth Anything V2 Small
(Apache-2.0; ONNX export of github.com/fabio-sim/Depth-Anything-ONNX), run on the CPU, about a second per picture.
The model file is taken from $DEPTH_MODEL or downloaded once to ~/.cache/news-depth/. Needs numpy, onnxruntime and
opencv-python-headless (imported here only, so a story without "fx" needs none of them).
"""
from functools import lru_cache
import os
from pathlib import Path
from urllib.request import urlretrieve

from PIL import Image

MODEL_URL = "https://github.com/fabio-sim/Depth-Anything-ONNX/releases/download/v2.0.0/depth_anything_v2_vits.onnx"
SIDE = 518          # the model's size (a multiple of its 14-pixel patches)
LONGEST = 2000      # pictures are warped at this size at most
FOCUS = 0.45        # the depth that stays where it is (0 far, 1 near): things nearer and farther part around it


@lru_cache(maxsize=1)
def session():
    import onnxruntime
    path = Path(os.environ.get("DEPTH_MODEL") or Path.home() / ".cache/news-depth/depth_anything_v2_vits.onnx")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        urlretrieve(MODEL_URL, f"{path}.part")
        os.replace(f"{path}.part", path)
    return onnxruntime.InferenceSession(str(path), providers=["CPUExecutionProvider"])


def depth_map(image):
    """Relative depth of a picture as a float array of its size: 0 far, 1 near, with soft edges (a hard edge
    between near and far would tear when the camera moves)."""
    import cv2
    import numpy as np
    pixels = np.asarray(image.convert("RGB").resize((SIDE, SIDE), Image.Resampling.BICUBIC), dtype=np.float32) / 255
    pixels = (pixels - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    model = session()
    depth = model.run(None, {model.get_inputs()[0].name: pixels.transpose(2, 0, 1)[None].astype(np.float32)})[0]
    depth = depth.squeeze()
    low, high = np.percentile(depth, 1), np.percentile(depth, 99)
    depth = np.clip((depth - low) / max(1e-6, high - low), 0, 1).astype(np.float32)
    depth = cv2.resize(depth, image.size, interpolation=cv2.INTER_CUBIC)
    blur = max(image.size) / 110
    return cv2.GaussianBlur(depth, (0, 0), blur)


class Parallax:
    """A picture with its depth: `at()` gives the picture as seen after the camera moved sideways (pan) or
    closer (push), things near the camera moving more than things far away."""

    def __init__(self, image, centre=(0.5, 0.5)):
        import numpy as np
        if max(image.size) > LONGEST:
            scale = LONGEST / max(image.size)
            image = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
        self.image = image
        self.pixels = np.asarray(image.convert("RGB"))
        self.depth = depth_map(image)
        height, width = self.depth.shape
        self.ys, self.xs = np.mgrid[0:height, 0:width].astype(np.float32)
        self.centre = (centre[0] * width, centre[1] * height)

    def at(self, pan_x=0.0, pan_y=0.0, push=0.0):
        """pan_x, pan_y: how far (in pixels of the picture) the nearest things are shifted; push: how much more
        (as a share of their distance from the centre) the nearest things grow than the resting plane."""
        import cv2
        if not (pan_x or pan_y or push):
            return self.image
        cx, cy = self.centre
        shift_x = (pan_x + (self.xs - cx) * push) / (1 - FOCUS)
        shift_y = (pan_y + (self.ys - cy) * push) / (1 - FOCUS)
        from_x, from_y = self.xs, self.ys
        for _ in range(2):   # where each point of the new view comes from: two rounds are enough for small moves
            rel = cv2.remap(self.depth, from_x, from_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE) - FOCUS
            from_x, from_y = self.xs - shift_x * rel, self.ys - shift_y * rel
        out = cv2.remap(self.pixels, from_x, from_y, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return Image.fromarray(out)
