"""Encode 3 seconds of a story without the voice engine: two scenes with a scene change, in the three frames (news,
paper with its film grain, story with a quote over the picture and a test tone as music under the voice), with silence
as the voice. Checks that the frames, FFmpeg, the music mix and the output format work.
Usage: python tools/encode_test.py stories/mau-boj.json <find folder> <out folder>"""
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys
import wave

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from news.custom import Music, load_story   # noqa: E402
from news.render import caption_chunks, encode, use_style   # noqa: E402
from news.voice import Caption   # noqa: E402

SECONDS, RATE = 3.0, 24000


def main():
    story, pictures, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    release, beats, photos = load_story(story, pictures)
    beats = beats[:2]
    half = SECONDS / len(beats)
    intervals = [(index * half, (index + 1) * half) for index in range(len(beats))]
    captions = [Caption(start, end, caption_chunks(beat.lines[0])[0]) for beat, (start, end) in zip(beats, intervals)]
    for name in ("news", "paper", "story"):
        folder = out / name
        folder.mkdir(parents=True, exist_ok=True)
        scene_beats, scene_release = beats, release
        if name == "story":   # the first line printed big as a quote, a test tone as the music
            tone = folder / "tone.ogg"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=330:duration=2",
                            "-c:a", "libvorbis", str(tone)], check=True)
            scene_beats = [replace(beats[0], quotes=(0,), era="1921年"), *beats[1:]]
            scene_release = replace(release, music=Music(str(tone), "Test tone.ogg", "", "", ""))
        wav = folder / "silence.wav"
        with wave.open(str(wav), "wb") as silence:
            silence.setparams((1, 2, RATE, 0, "NONE", "not compressed"))
            silence.writeframes(bytes(2 * int(SECONDS * RATE)))
        use_style(name)
        encode(scene_beats, scene_release, photos, False, intervals, captions, wav, folder)
        wav.unlink()
        probe = json.loads(subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,codec_type,width,height,r_frame_rate:"
             "format=duration", "-of", "json", str(folder / "video.mp4")], check=True, capture_output=True).stdout)
        video = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
        audio = next(stream for stream in probe["streams"] if stream["codec_type"] == "audio")
        found = (video["width"], video["height"], video["r_frame_rate"], video["codec_name"], audio["codec_name"])
        duration = float(probe["format"]["duration"])
        if found != (1080, 1920, "30/1", "h264", "aac") or not SECONDS - 0.3 <= duration <= SECONDS + 0.3:
            sys.exit(f"error: encode test ({name}): unexpected video {found}, {duration:.2f} s")
        print(f"encode test ({name}): OK, {duration:.2f} s, {(folder / 'video.mp4').stat().st_size // 1000} kB")


if __name__ == "__main__":
    main()
