"""Synthesize short Japanese lines and time captions against the generated WAV."""
from dataclasses import dataclass
from io import BytesIO
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import wave

from .render import caption_chunks, reading_weight

VOICEVOX = "http://127.0.0.1:50021"


@dataclass(frozen=True)
class Caption:
    start: float
    end: float
    text: str
    # (share of the text, share of the time) points: how far the voice has read at which moment of the caption,
    # from the real lengths of the sounds (spoken_times); empty when unknown (the renderer then estimates)
    marks: tuple = ()


PAUSES = "、，。．！？!?…"            # where the voice pauses
SMALL_KANA = "ゃゅょぁぃぅぇぉゎャュョァィゥェォヮ"   # said together with the kana before: no sound of their own
LEAD = 0.1                           # a caption comes this much before its first sound, when the voice pauses there


def sounds_of(char):
    """How many sounds (morae) a character is: exactly known for kana, None for kanji, digits and letters."""
    if char in SMALL_KANA:
        return 0.0
    if "\u3041" <= char <= "\u3096" or "\u30a1" <= char <= "\u30fa" or char == "ー":
        return 1.0
    return None


def spoken_times(text, query, duration):
    """When the voice says every character of `text`: a list of (begin, end) in seconds from the start of the
    line's sound, from the real lengths VOICEVOX gave for every sound (audio_query: accent_phrases[].moras[]
    .consonant_length / vowel_length, pause_mora), stretched to the real `duration`. The pauses and the sounds are
    exact; which sounds belong to which character is exact for kana, and kanji share the remaining sounds of their
    stretch between two pauses by their usual weight. A mark or a bracket takes no time (it comes with the
    character before it). None when the text and the reading cannot be laid side by side (another number of
    pauses, no sounds): the caller then estimates."""
    phrases = query.get("accent_phrases") or []
    groups, pauses = [[]], []
    for number, phrase in enumerate(phrases):
        groups[-1] += [(mora.get("consonant_length") or 0.0) + (mora.get("vowel_length") or 0.0)
                       for mora in phrase.get("moras") or []]
        pause = phrase.get("pause_mora")
        if pause and number < len(phrases) - 1:
            pauses.append((pause.get("vowel_length") or 0.0) * (query.get("pauseLengthScale") or 1.0))
            groups.append([])
    # the text in stretches of spoken characters, cut where a pause mark stands between two of them
    stretches, waiting = [[]], False
    for index, char in enumerate(text):
        if char in PAUSES:
            waiting = bool(stretches[-1])
        elif reading_weight(char) > 0 or sounds_of(char) is not None:
            if waiting:
                stretches.append([])
            waiting = False
            stretches[-1].append(index)
    if len(stretches) != len(groups) or not all(stretches) or not all(groups) or duration <= 0:
        return None
    said = {}   # character index -> (begin, end), before stretching
    clock = query.get("prePhonemeLength") or 0.0
    for stretch, lengths, pause in zip(stretches, groups, [*pauses, 0.0]):
        known = [sounds_of(text[index]) for index in stretch]
        guessed = [reading_weight(text[index]) if sounds is None else 0.0 for index, sounds in zip(stretch, known)]
        rest = len(lengths) - sum(sounds or 0.0 for sounds in known)
        if sum(guessed) > 0 and rest > 0:      # kana take their own sounds, the kanji share the others
            counts = [weight * rest / sum(guessed) if sounds is None else sounds
                      for sounds, weight in zip(known, guessed)]
        elif not sum(guessed) and abs(rest) < 0.5:   # kana only, and as many sounds as kana
            counts = known
        else:                                  # the counts do not fit: every character by its usual weight
            weights = [reading_weight(text[index]) for index in stretch]
            counts = [weight * len(lengths) / (sum(weights) or 1.0) for weight in weights]
        edges = [0.0]
        for length in lengths:
            edges.append(edges[-1] + length)

        def moment(sounds):   # seconds into this stretch after that many sounds
            whole = min(int(sounds), len(lengths) - 1)
            return edges[whole] + (edges[whole + 1] - edges[whole]) * min(1.0, sounds - whole)

        done = 0.0
        for index, count in zip(stretch, counts):
            said[index] = (clock + moment(done), clock + moment(done + count))
            done += count
        clock += edges[-1] + pause
    total = clock + (query.get("postPhonemeLength") or 0.0)
    scale = duration / total if total > 0 else 1.0
    times, last = [], said[stretches[0][0]][0] * scale
    for index in range(len(text)):
        if index in said:
            times.append((said[index][0] * scale, said[index][1] * scale))
            last = times[-1][1]
        else:
            times.append((last, last))
    return times


def line_captions(chunks, position, duration, times, exact):
    """The captions of one spoken line. Without `times`, or when not `exact`, each caption gets its share of the
    line by its number of characters (as always); `exact`: it starts when the voice reaches it (a little before,
    when the voice pauses there). With `times` every caption also carries its marks."""
    texts = [chunk.replace("\n", "") for chunk in chunks]
    length = sum(map(len, texts))
    offsets = [sum(map(len, texts[:number])) for number in range(len(texts) + 1)]
    if times and exact:
        cuts = [position]
        for offset in offsets[1:-1]:
            begins = next((begin for begin, end in times[offset:] if end > begin), times[offset][0])
            cuts.append(position + max(times[offset - 1][1], begins - LEAD))
        cuts.append(position + duration)
    else:
        cuts = [position]
        for text in texts:
            cuts.append(cuts[-1] + duration * len(text) / length)
    captions = []
    for number, chunk in enumerate(chunks):
        start, end = cuts[number], cuts[number + 1]
        marks = []
        if times and end > start:
            first, size = offsets[number], len(texts[number])
            for count in range(size):
                for share, moment in zip((count, count + 1), times[first + count]):
                    mark = (round(share / size, 4), round((position + moment - start) / (end - start), 4))
                    if not marks or mark != marks[-1]:
                        marks.append(mark)
        captions.append(Caption(start, end, chunk, tuple(marks)))
    return captions


def request(path, *, params=None, data=None):
    url = VOICEVOX + path + (f"?{urlencode(params)}" if params else "")
    headers = {"Content-Type": "application/json"} if data else {}
    with urlopen(Request(url, data=data, headers=headers), timeout=90) as response:
        return response.read()


SPEAKER, STYLE = "青山龍星", "ノーマル"   # the one voice of every channel; a story's "speaker" is ignored


def voice_name(choice=""):
    """(name, style) of the voice: always 青山龍星/ノーマル, whatever the story or a scene names. The owner, 27/11/2026:
    "Ép tất cả các kênh quay về giọng nhật cũ, k đổi lung tung nữa, giọng nam cũ của kênh hoàng gia nhật ấy" (the
    voices tried on 25–26/11/2026 were turned down one after the other): a `"speaker"` key left in a story is not
    read, so no video can come out in another voice (`python -m news.custom` warns of the key)."""
    return SPEAKER, STYLE


def voice_credit(choice="", others=()):
    """The credit VOICEVOX asks for, on screen and in credits.txt: "VOICEVOX:<name>" (each voice once)."""
    names = []
    for one in (choice, *others):
        name = voice_name(one)[0]
        if name not in names:
            names.append(name)
    return "、".join(f"VOICEVOX:{name}" for name in names)


def speaker_id(choice=""):
    """The engine's id of the one voice (`voice_name`: `choice` is not read)."""
    name, wanted = voice_name(choice)
    speakers = json.loads(request("/speakers"))
    found = next((style["id"] for speaker in speakers if speaker["name"] == name
                  for style in speaker["styles"] if style["name"] == wanted), None)
    if found is None:
        available = ", ".join(f"{speaker['name']}/{style['name']}" for speaker in speakers for style in speaker["styles"])
        raise RuntimeError(f"VOICEVOX voice {name}/{wanted} not found in this engine. Available: {available}")
    return found


def narration(beats, destination: Path, speed, line_pause=0.0, scene_pause=0.0, exact=False, speaker_choice=""):
    """The voice of every line, one after the other, with `line_pause` seconds of silence after each line (a quote
    also gets one before it and a longer one after it) and `scene_pause` more at the end of each scene.
    `exact` ("fx": text): a caption starts when the voice reaches it, not at its share of the characters.
    `speaker_choice` and a scene's "speaker" are not read: every line is read by 青山龍星 (`voice_name`)."""
    ids = {}

    def voice_of(beat):   # the one voice for every scene, asked of the engine once
        if "id" not in ids:
            ids["id"] = speaker_id()
        return ids["id"]

    captions = []
    intervals = []
    position = 0.0
    rate = 24000
    with wave.open(str(destination), "wb") as output:
        output.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        def silence(seconds):
            nonlocal position
            frames = round(rate * seconds)
            if frames > 0:
                output.writeframesraw(b"\x00\x00" * frames)
                position += frames / rate

        for beat in beats:
            start = position
            speaker = voice_of(beat)
            for index, line in enumerate(beat.lines):
                if index in beat.quotes and index:
                    silence(line_pause)
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
                try:   # the real moment of every character; any surprise in the answer: the estimate, as before
                    times = spoken_times("".join(chunk.replace("\n", "") for chunk in chunks), query, duration)
                except (AttributeError, KeyError, TypeError, ValueError):
                    times = None
                captions += line_captions(chunks, position, duration, times, exact)
                position += duration
                silence(line_pause * (1.6 if index in beat.quotes else 1.0))
            silence(scene_pause)
            intervals.append((start, position))
    return intervals, captions
