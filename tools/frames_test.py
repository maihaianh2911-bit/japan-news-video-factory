"""Check of tools/video_frames.py (pictures out of the video the owner sent) on a made-up video: four shots of two
seconds, the fourth showing the first again. Needs ffmpeg, no network. Usage: python tools/frames_test.py"""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from PIL import Image   # noqa: E402

import video_frames as V   # noqa: E402
from find_test import blocks   # noqa: E402

STORY = "zz-frames-test"


def main():
    media = V.REPO / "stories" / "media" / STORY
    with tempfile.TemporaryDirectory(prefix="frames-test-") as scratch:
        scratch = Path(scratch)
        for number, seed in enumerate((1, 2, 3, 1)):
            blocks(seed, (540, 960)).save(scratch / f"p{number}.jpg", quality=92)
        listing = "".join(f"file '{scratch}/p{n}.jpg'\nduration 2\n" for n in range(4)) + f"file '{scratch}/p3.jpg'\n"
        (scratch / "list.txt").write_text(listing, encoding="utf-8")
        video = scratch / "source.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(scratch / "list.txt"),
                        "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", str(video)], check=True)
        try:
            V.main([str(video), STORY])
            out = scratch / "source.mp4.frames"
            frames = json.loads((out / "frames.json").read_text(encoding="utf-8"))["frames"]
            assert frames == [1.0, 3.0, 5.0], frames   # the middle of each shot; the repeated shot once
            assert (out / "sheet.jpg").exists() and Image.open(out / "frame-2.jpg").size == (540, 960)
            V.main([str(video), STORY, "--keep", "1,3", "--crop", "0,0.2,1,0.5"])
            V.main([str(video), STORY, "--at", "3"])
            kept = sorted(path.name for path in media.glob("*.jpg"))
            assert kept == ["v-0m01s.jpg", "v-0m03s.jpg", "v-0m05s.jpg"], kept
            assert Image.open(media / "v-0m01s.jpg").size == (540, 480) and Image.open(media / "v-0m03s.jpg").size == (540, 960)
            V.main([str(video), STORY, "--keep", "1"])   # the same moment again: another file, nothing overwritten
            assert (media / "v-0m01s-2.jpg").exists()
            for wrong in (["--keep", "9"], ["--keep", "1", "--crop", "0.5,0,0.8,1"]):
                try:
                    V.main([str(video), STORY, *wrong])
                    raise AssertionError(f"{wrong} must be refused")
                except SystemExit as stop:
                    assert str(stop.code).startswith("error:"), stop.code
        finally:
            shutil.rmtree(media, ignore_errors=True)
    print("video frames check OK (3 shots found in a made-up video of 4, frames kept and cropped)")


if __name__ == "__main__":
    main()
