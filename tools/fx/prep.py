"""Trial (owner, 16/11/2026): prepare pictures for the effects sample.

For each picture: a depth map (MiDaS, for the 3D camera move) and, when asked, a sharper and larger copy
(Real-ESRGAN, no face redrawing). Runs on the CPU.

    python tools/fx/prep.py <find folder> <out folder> <models folder> 1-1 7-1:sharp ...
"""
from pathlib import Path
import sys

import cv2
import numpy as np
import torch


def sharpen(image, weights, tile=256, pad=16):
    """Real-ESRGAN x4 in tiles, brought back to twice the size of the picture."""
    from spandrel import ModelLoader
    model = ModelLoader().load_from_file(weights).model.eval()
    h, w = image.shape[:2]
    out = np.zeros((h * 4, w * 4, 3), np.float32)
    for top in range(0, h, tile):
        for left in range(0, w, tile):
            y0, x0 = max(0, top - pad), max(0, left - pad)
            y1, x1 = min(h, top + tile + pad), min(w, left + tile + pad)
            piece = torch.from_numpy(image[y0:y1, x0:x1, ::-1].copy()).permute(2, 0, 1)[None].float() / 255
            with torch.no_grad():
                big = model(piece)[0].permute(1, 2, 0).clamp(0, 1).numpy()
            ty, tx = (top - y0) * 4, (left - x0) * 4
            hh, ww = (min(h, top + tile) - top) * 4, (min(w, left + tile) - left) * 4
            out[top * 4:top * 4 + hh, left * 4:left * 4 + ww] = big[ty:ty + hh, tx:tx + ww]
        print(f"  sharpen: row {top // tile + 1}/{-(-h // tile)}", flush=True)
    out = (out[:, :, ::-1] * 255).round().astype(np.uint8)
    return cv2.resize(out, (w * 2, h * 2), interpolation=cv2.INTER_AREA)


def depth_of(image, midas, transform):
    """Depth of every pixel, 0 (far) to 1 (near)."""
    with torch.no_grad():
        prediction = midas(transform(cv2.cvtColor(image, cv2.COLOR_BGR2RGB)))
        prediction = torch.nn.functional.interpolate(prediction[:, None], size=image.shape[:2], mode="bicubic")[0, 0]
    depth = prediction.numpy()
    low, high = np.percentile(depth, 1), np.percentile(depth, 99)
    return np.clip((depth - low) / (high - low), 0, 1)


def main():
    find, out, models, *names = sys.argv[1:]
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    torch.hub.set_dir(models)
    midas = torch.hub.load(f"{models}/MiDaS", "DPT_Hybrid", source="local").eval()
    transform = torch.hub.load(f"{models}/MiDaS", "transforms", source="local").dpt_transform
    for name in names:
        name, _, option = name.partition(":")
        image = cv2.imread(f"{find}/{name}.jpg")
        print(name, image.shape, flush=True)
        cv2.imwrite(str(out / f"{name}_depth.png"), (depth_of(image, midas, transform) * 65535).astype(np.uint16))
        if option == "sharp":
            image = sharpen(image, f"{models}/RealESRGAN_x4plus.pth")
        cv2.imwrite(str(out / f"{name}.png"), image)


if __name__ == "__main__":
    main()
