"""Write down the words spoken in a video or sound file (speech to text), for a source video that has no
burnt-in captions. Works in Claude's cloud session: the recogniser is on PyPI and its model on GitHub releases.

Usage: python tools/listen.py <video or audio> [language] [window] [step]
       language: ja (default), vi, en, ...; window and step in seconds (20 and 15 by default)
Needs: pip install sherpa-onnx numpy, and ffmpeg. The model (Whisper large-v3-turbo, 560 MB) is fetched on first
use into ~/.cache/sherpa-onnx-whisper-turbo (or LISTEN_MODEL=<folder>).

The sound is read in windows of 20 seconds that start every 15 seconds, so the end of a window says the start of
the next one again: join them by reading. A window with only music may come back as a made-up sentence (a
"subscribe to the channel" line), mostly over loud music: run it again with other windows (13 and 9) and join the
two readings; never quote a line you could not hear twice.
"""
import os
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import wave
from pathlib import Path

MODEL_URL = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-turbo.tar.bz2"
WINDOW, STEP, RATE = 20, 15, 16000


def model_folder():
    folder = Path(os.environ.get("LISTEN_MODEL", Path.home() / ".cache" / "sherpa-onnx-whisper-turbo"))
    if not (folder / "turbo-tokens.txt").exists():
        folder.parent.mkdir(parents=True, exist_ok=True)
        print("fetching the model (560 MB)…", file=sys.stderr)
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "model.tar.bz2"
            urllib.request.urlretrieve(MODEL_URL, archive)
            with tarfile.open(archive) as tar:
                tar.extractall(tmp, filter="data")
            (Path(tmp) / "sherpa-onnx-whisper-turbo").rename(folder)
    return folder


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    source, language = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "ja")
    window = int(sys.argv[3]) if len(sys.argv) > 3 else WINDOW
    step = int(sys.argv[4]) if len(sys.argv) > 4 else STEP
    import numpy
    import sherpa_onnx
    folder = model_folder()
    recogniser = sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=str(folder / "turbo-encoder.int8.onnx"), decoder=str(folder / "turbo-decoder.int8.onnx"),
        tokens=str(folder / "turbo-tokens.txt"), language=language, task="transcribe", num_threads=os.cpu_count() or 2)
    with tempfile.TemporaryDirectory() as tmp:
        sound = str(Path(tmp) / "sound.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", source, "-vn", "-ac", "1", "-ar", str(RATE), sound],
                       check=True)
        with wave.open(sound) as file:
            samples = numpy.frombuffer(file.readframes(file.getnframes()), dtype=numpy.int16).astype(numpy.float32)
    samples /= 32768
    for start in range(0, max(1, len(samples) // RATE), step):
        piece = samples[start * RATE:(start + window) * RATE]
        if len(piece) < RATE:
            break
        stream = recogniser.create_stream()
        stream.set_option("max_tokens_per_second", "14")   # fast speech: the default of 6 cuts a window short
        stream.accept_waveform(RATE, piece)
        recogniser.decode_stream(stream)
        print("[%d:%02d] %s" % (start // 60, start % 60, stream.result.text.strip()), flush=True)


if __name__ == "__main__":
    main()
