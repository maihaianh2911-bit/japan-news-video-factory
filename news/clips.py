"""Moving pictures: a short video clip in the place of a picture (owner, 18/11/2026: "dùng nhiều đoạn video có công
chúa trông rất đẹp" — the best moments of the source video, cut out by the owner).

A clip is kept in the repository as stories/media/<story>/<name>.mp4 and asked for like a picture of the repository,
with the search "file:stories/media/<story>/<name>.mp4". The find stage copies it as <k>-1.mp4 beside a still of its
middle (<k>-1.jpg, for the contact sheet and the review); the render plays it, frame by frame, in the picture box,
and the chosen move (push-in, pan, …) runs over the moving picture. Its sound is not used. The depth effect is never
used on a clip (it would wobble from frame to frame).

If the clip is shorter than the time its picture stays on screen, its last frame is held (a warning says so).
"""
import json
from pathlib import Path
import subprocess

from PIL import Image

FPS = 30
OPEN = []   # every clip being read, closed at the end of a render
WARN = [True]   # off for the stills (their scenes last a made-up 10 seconds)


def probe(path):
    """(width, height, seconds) of a video file."""
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height:format=duration", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True).stdout
    info = json.loads(out)
    stream = info["streams"][0]
    return int(stream["width"]), int(stream["height"]), float(info["format"]["duration"])


def still(path, seconds, out):
    """Save the frame of the clip at `seconds` as a picture."""
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0.0, seconds):.3f}", "-i", str(path),
                    "-frames:v", "1", "-q:v", "2", str(out)], check=True)


class Clip:
    """Reads the frames of a clip in order (a render goes forward in time); going back starts it again."""

    def __init__(self, path, start=0.0):
        self.path, self.start = str(path), float(start)
        _, _, self.seconds = probe(path)
        # the size of a decoded frame (a phone video may be stored turned and shown upright)
        first = subprocess.run(["ffmpeg", "-v", "error", "-i", self.path, "-frames:v", "1", "-pix_fmt", "rgb24",
                                "-f", "image2pipe", "-vcodec", "ppm", "-"],
                               capture_output=True, check=True).stdout
        header = first.split(maxsplit=3)
        self.width, self.height = int(header[1]), int(header[2])
        self.process, self.number, self.frame = None, -1, None
        self.warned = False

    def length(self):
        """The seconds of the clip that are played (from `start` to its end)."""
        return max(0.0, self.seconds - self.start)

    def close(self):
        if self.process:
            self.process.kill()
            self.process.wait()
            self.process = None

    def open(self, number):
        self.close()
        self.process = subprocess.Popen(
            ["ffmpeg", "-v", "error", "-ss", f"{number / FPS:.4f}", "-i", self.path, "-an",
             "-vf", f"fps={FPS}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
            stdout=subprocess.PIPE)
        self.number = number - 1
        if self not in OPEN:
            OPEN.append(self)

    def at(self, seconds):
        """The frame `seconds` after the clip's `start` (the last frame once the clip has ended)."""
        number = max(0, int(round((self.start + max(0.0, seconds)) * FPS)))
        last = max(0, int(self.seconds * FPS) - 1)
        if seconds - self.length() > 0.2 and WARN[0] and not self.warned:
            self.warned = True
            print(f"warning: clip {Path(self.path).stem} ends {seconds - self.length():.1f} s before its time on screen is up: "
                  "its last frame is held (cut a longer clip, or give it less time)")
        number = min(number, last)
        if self.frame is not None and number == self.number:
            return self.frame
        if self.process is None or number < self.number or number > self.number + 5 * FPS:
            self.open(number)
        size = self.width * self.height * 3
        while self.number < number:
            data = self.process.stdout.read(size)
            if len(data) < size:   # the clip ended a little before its announced length: keep the last frame
                break
            self.frame = Image.frombytes("RGB", (self.width, self.height), data)
            self.number += 1
        if self.frame is None:   # nothing could be read at that point: the first frame
            self.open(0)
            data = self.process.stdout.read(size)
            self.frame = Image.frombytes("RGB", (self.width, self.height), data)
            self.number = 0
        return self.frame


def close_all():
    while OPEN:
        OPEN.pop().close()
