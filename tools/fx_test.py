"""Checks of the picture effects ("fx" in a story), without the voice engine:
1. the caption that darkens with the voice: the moment of every character from a made-up VOICEVOX answer
   (audio_query), the captions made of it, and a whole narration against a stand-in engine;
2. stills of a story with the effects on: the display typeface and the depth effect must really work here (their
   stills differ from the plain ones), and all four together must render, as stills and as three seconds of video.
   The stills with every effect on are left in <out>/fx/ (sheet.jpg) to look at.
Needs numpy, opencv-python-headless, onnxruntime, the depth model ($DEPTH_MODEL or ~/.cache/news-depth/), the
display typeface ($NEWS_DISPLAY_FONT or fonts/ShipporiMinchoB1-ExtraBold.ttf) and ffmpeg.
Usage: python tools/fx_test.py stories/mau-boj.json <find folder> <out folder>"""
from dataclasses import replace
from io import BytesIO
import json
from pathlib import Path
import sys
import tempfile
import wave

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from news import render, voice   # noqa: E402
from news.custom import load_story   # noqa: E402

ALL = {"motion": True, "depth": True, "text": True, "face": True}


def mora(seconds=0.1):
    return {"text": "ア", "consonant": "k", "consonant_length": round(seconds * 0.4, 3), "vowel": "a",
            "vowel_length": round(seconds * 0.6, 3), "pitch": 5.0}


def phrase(count, pause=None):
    rest = {"text": "、", "consonant": None, "consonant_length": None, "vowel": "pau", "vowel_length": pause, "pitch": 0}
    return {"moras": [mora() for _ in range(count)], "accent": 1, "pause_mora": rest if pause else None,
            "is_interrogative": False}


def query(phrases):
    return {"accent_phrases": phrases, "speedScale": 1.0, "pitchScale": 0.0, "intonationScale": 1.0,
            "volumeScale": 1.0, "prePhonemeLength": 0.1, "postPhonemeLength": 0.1, "pauseLength": None,
            "pauseLengthScale": 0.5, "outputSamplingRate": 24000, "outputStereo": False, "kana": ""}


def near(a, b):
    return abs(a - b) < 1e-6


def timing():
    """日本銀行は、金利を上げた。 read as ニッポンギンコオワ (pause) キンリオ アゲタ: every sound 0.1 s, a pause of 0.2 s,
    0.1 s of silence before and after = 2 s, stretched to a sound of 4 s."""
    text = "日本銀行は、金利を上げた。"
    answer = query([phrase(9, pause=0.4), phrase(4), phrase(3)])
    times = voice.spoken_times(text, answer, 4.0)
    assert len(times) == len(text)
    assert near(times[0][0], 0.2) and near(times[0][1], 0.6), times[0]           # 日: two of the eight kanji sounds
    assert near(times[4][0], 1.8) and near(times[4][1], 2.0), times[4]           # は: the ninth sound, exactly
    assert times[5] == (times[4][1], times[4][1])                                # 、 takes no time of its own
    assert near(times[6][0], 2.4), times[6]                                      # 金 starts after the real pause
    assert near(times[8][0], 2.4 + 0.2 * 4 / 3 * 2) and near(times[8][1] - times[8][0], 0.2), times[8]   # を: one sound
    assert near(times[11][1], 3.8) and times[12] == (times[11][1], times[11][1]), times[11:]
    assert all(end >= begin for begin, end in times) and all(b[0] >= a[1] - 1e-9 for a, b in zip(times, times[1:]))
    # kana only: every kana its own sound, a small kana with the one before
    kana = voice.spoken_times("きょうは", query([phrase(3)]), 0.5)
    assert [round(end - begin, 3) for begin, end in kana] == [0.1, 0.0, 0.1, 0.1], kana
    # the text and the reading do not match up: no times (the renderer estimates, as before)
    assert voice.spoken_times("日本、銀行は、上げた", answer, 4.0) is None
    assert voice.spoken_times(text, query([]), 4.0) is None and voice.spoken_times(text, {}, 4.0) is None

    chunks = ["日本銀行は、", "金利を\n上げた。"]
    plain = voice.line_captions(chunks, 10.0, 4.0, None, False)
    cut = 10.0 + 4.0 * 6 / 13
    assert [(c.start, c.end, c.text, c.marks) for c in plain] == [
        (10.0, cut, chunks[0], ()), (cut, cut + 4.0 * 7 / 13, chunks[1], ())], plain   # as always, to the last digit
    kept = voice.line_captions(chunks, 10.0, 4.0, times, False)
    assert [(c.start, c.end) for c in kept] == [(c.start, c.end) for c in plain] and all(c.marks for c in kept)
    exact = voice.line_captions(chunks, 10.0, 4.0, times, True)
    assert near(exact[0].start, 10.0) and near(exact[0].end, 12.3) and near(exact[1].end, 14.0), exact   # 0.1 s before 金
    assert exact[1].marks[0] == (0.0, round(0.1 / 1.7, 4)) and exact[1].marks[-1][0] == 1.0, exact[1].marks
    for caption in exact:
        assert all(b[0] >= a[0] and b[1] >= a[1] for a, b in zip(caption.marks, caption.marks[1:])), caption.marks
    marks = exact[0].marks   # 日本銀行は、 spoken from 10.2 to 12.0 of a caption shown from 10.0 to 12.3
    assert render.read_share(marks, 0.0) == 0.0 and render.read_share(marks, 1.0) == 1.0
    assert abs(render.read_share(marks, (11.1 - 10.0) / 2.3) - 2.25 / 6) < 1e-3, render.read_share(marks, 1.1 / 2.3)
    assert render.read_share(marks, 2.1 / 2.3) == 1.0   # in the pause everything is read, the mark too


def narrated(beats):
    """A whole narration against a stand-in engine (two sounds a kanji, one a kana, a pause at every mark): the
    captions follow each other, keep the text and carry marks; without `exact` their times are the old ones."""
    def answer(text):
        phrases, count = [], 0
        for char in text:
            if char in voice.PAUSES:
                if count:
                    phrases.append(phrase(count, pause=0.3))
                count = 0
            elif voice.sounds_of(char) is not None or render.reading_weight(char) > 0:
                count += 1 if voice.sounds_of(char) is not None else 2
        if count:
            phrases.append(phrase(count))
        if phrases and not count:
            phrases[-1]["pause_mora"] = None
        return query(phrases)

    def engine(path, *, params=None, data=None):
        if path == "/speakers":
            return json.dumps([{"name": voice.SPEAKER, "styles": [{"name": voice.STYLE, "id": 13}]}]).encode()
        if path == "/audio_query":
            return json.dumps(answer(params["text"])).encode()
        asked = json.loads(data)
        seconds = (asked["prePhonemeLength"] + asked["postPhonemeLength"] + sum(
            sum(m["consonant_length"] + m["vowel_length"] for m in p["moras"])
            + (p["pause_mora"]["vowel_length"] * asked["pauseLengthScale"] if p["pause_mora"] else 0)
            for p in asked["accent_phrases"])) / asked["speedScale"]
        sound = BytesIO()
        with wave.open(sound, "wb") as output:
            output.setparams((1, 2, 24000, 0, "NONE", "not compressed"))
            output.writeframes(b"\x00\x00" * round(24000 * seconds))
        return sound.getvalue()
    real = voice.request
    try:
        voice.request = engine
        with tempfile.TemporaryDirectory(prefix="fx-voice-") as scratch:
            _, old = voice.narration(beats, Path(scratch) / "old.wav", 1.1, 0.1, 0.2)
            spans, new = voice.narration(beats, Path(scratch) / "new.wav", 1.1, 0.1, 0.2, exact=True)
    finally:
        voice.request = real
    assert [c.text for c in old] == [c.text for c in new] and len(new) >= sum(len(beat.lines) for beat in beats)
    at = 0   # the old times: every caption its share of the line by its characters
    for beat in beats:
        for line in beat.lines:
            sizes = [len(chunk.replace("\n", "")) for chunk in render.caption_chunks(line)]
            mine = old[at:at + len(sizes)]
            at += len(sizes)
            whole = mine[-1].end - mine[0].start
            assert all(abs((c.end - c.start) / whole - size / sum(sizes)) < 1e-6 for c, size in zip(mine, sizes)), line
    with_marks = sum(bool(c.marks) for c in new)
    assert with_marks == len(new), f"{len(new) - with_marks} of {len(new)} captions without marks"
    assert all(b.start >= a.end - 1e-6 and a.end > a.start for a, b in zip(new, new[1:])) and new[-1].end <= spans[-1][1]
    moved = sum(abs(a.start - b.start) > 0.02 for a, b in zip(old, new))
    return len(new), moved


def frames(folder):
    return {path.name: path.read_bytes() for path in sorted(folder.glob("scene-*.jpg"))}


def effects(story, pictures, out):
    release, beats, photos = load_story(story, pictures)
    # the camera rhythm and the depth act on pictures with a named move (every edited story); the sample has none
    photos = {index: [replace(photo, move="push-in") for photo in scene] for index, scene in photos.items()}
    render.use_style(release.style)
    stills = {}
    for name, fx in (("plain", None), ("face", {"face": True}), ("depth", {"depth": True}), ("fx", ALL)):
        render.use_fx(fx)
        (out / name).mkdir(parents=True, exist_ok=True)
        render.stills(beats, release, photos, out / name)
        stills[name] = frames(out / name)
        assert stills[name] and stills[name].keys() == stills["plain"].keys(), name
        if name == "face":
            assert render.DISPLAY_FONT, ("the display typeface was not found: set NEWS_DISPLAY_FONT or put it in "
                                         "fonts/ShipporiMinchoB1-ExtraBold.ttf")
        if name == "depth":
            made = [scene for key, scene in render.PARALLAX.items() if key != "warned" and scene is not None]
            assert made and not render.PARALLAX.get("warned"), (
                "the depth effect did not run: it needs numpy, opencv-python-headless, onnxruntime and the model")
    changed = {name: sum(stills[name][key] != stills["plain"][key] for key in stills["plain"])
               for name in ("face", "depth", "fx")}
    assert all(changed.values()), f"stills equal to the plain ones: {changed}"
    # the caption while it is spoken: paler at first, darker as the voice goes on, in full ink at the end
    render.use_fx(ALL)
    text = render.caption_chunks(beats[0].lines[0])[0]
    size = len(text.replace("\n", ""))
    marks = tuple((count / size, 0.1 + 0.8 * count / size) for count in range(size + 1))
    shots = []
    for age in (0.3, 1.5, 2.95):
        frame = render.Scene(0, beats[0], release, photos.get(0), False, 0.0, 10.0).render(5.0)
        render.draw_captions(frame, text, age, 3.0, marks)
        shots.append(frame)
    centre = render.caption_centre()
    ink = [sum(frame.crop((0, centre - 110, render.W, centre + 110)).convert("L").resize((108, 22)).tobytes())
           for frame in shots]
    assert ink[0] < ink[1] < ink[2] or ink[0] > ink[1] > ink[2], f"the caption does not go on darkening: {ink}"
    # three seconds of real video (as tools/encode_test.py) with every effect on and a caption with its marks
    wav = out / "silence.wav"
    with wave.open(str(wav), "wb") as silence:
        silence.setparams((1, 2, 24000, 0, "NONE", "not compressed"))
        silence.writeframes(bytes(2 * 3 * 24000))
    (out / "video").mkdir(exist_ok=True)
    render.encode(beats[:1], release, photos, False, [(0.0, 3.0)], [voice.Caption(0.0, 3.0, text, marks)], wav,
                  out / "video")
    wav.unlink()
    assert (out / "video" / "video.mp4").stat().st_size > 50_000, "no video with the effects on"
    render.use_fx(None)
    again = out / "plain-again"
    again.mkdir(exist_ok=True)
    render.stills(beats, release, photos, again)
    assert frames(again) == stills["plain"], "the plain stills changed after the effects were used"
    return beats, changed


def main():
    story, pictures, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    timing()
    beats, changed = effects(story, pictures, out)
    count, moved = narrated(beats)
    print(f"picture effects OK: stills that differ from the plain ones: typeface {changed['face']}, depth "
          f"{changed['depth']}, all four {changed['fx']} of {len(frames(out / 'plain'))}; caption timing on a made-up "
          f"voice: {count} captions with marks, {moved} start at another moment with \"fx\": text. Look at {out / 'fx' / 'sheet.jpg'}")


if __name__ == "__main__":
    main()
