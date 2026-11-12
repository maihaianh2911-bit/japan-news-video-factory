"""Synthesize short Japanese lines and time captions against the generated WAV."""
from dataclasses import dataclass
from io import BytesIO
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import wave

from .render import caption_chunks

VOICEVOX = "http://127.0.0.1:50021"


@dataclass(frozen=True)
class Caption:
    start: float
    end: float
    text: str


def request(path, *, params=None, data=None):
    url = VOICEVOX + path + (f"?{urlencode(params)}" if params else "")
    headers = {"Content-Type": "application/json"} if data else {}
    with urlopen(Request(url, data=data, headers=headers), timeout=90) as response:
        return response.read()


def speaker_id():
    speakers = json.loads(request("/speakers"))
    return next(style["id"] for speaker in speakers if speaker["name"] == "青山龍星"
                for style in speaker["styles"] if style["name"] == "ノーマル")


def narration(beats, destination: Path, speed):
    speaker = speaker_id()
    captions = []
    intervals = []
    position = 0.0
    rate = 24000
    with wave.open(str(destination), "wb") as output:
        output.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        for beat in beats:
            start = position
            for index, line in enumerate(beat.lines):
                spoken = beat.say[index] if beat.say else line
                query = json.loads(request("/audio_query", params={"text": spoken, "speaker": speaker}, data=b""))
                query.update(speedScale=speed, prePhonemeLength=0.07, postPhonemeLength=0.12,
                             pauseLengthScale=0.72, outputSamplingRate=rate, outputStereo=False)
                wav = request("/synthesis", params={"speaker": speaker}, data=json.dumps(query).encode())
                with wave.open(BytesIO(wav)) as segment:
                    if (segment.getnchannels(), segment.getsampwidth(), segment.getframerate()) != (1, 2, rate):
                        raise ValueError("Unexpected VOICEVOX audio format")
                    duration = segment.getnframes() / rate
                    output.writeframesraw(segment.readframes(segment.getnframes()))
                chunks = caption_chunks(line)
                length = sum(len(chunk.replace("\n", "")) for chunk in chunks)
                cue = position
                for chunk in chunks:
                    end = cue + duration * len(chunk.replace("\n", "")) / length
                    captions.append(Caption(cue, end, chunk))
                    cue = end
                position += duration
            intervals.append((start, position))
    return intervals, captions
