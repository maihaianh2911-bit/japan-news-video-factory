"""How the voice will read every line of a story, and how long the voice will be — before any render.

python tools/readings.py stories/<name>.json

Common rules 22 and 23 (`CLAUDE.md`, owner 26/11/2026: check before the render, render once). Needs
`pip install pyopenjtalk` in the session (the render does not use it, so it is not in requirements.txt).

1. The reading: each spoken line (its `say` when it has one) in kana, as Open JTalk reads it — the dictionary the
   VOICEVOX engine reads with. Look at names, numbers, counters and kanji with several readings (名, 方, 一言, 間,
   月日 …); a wrong one is written `{"text": "<caption>", "say": "<reading in kana>"}` in the story, and this is
   run again. The engine has a few words of its own on top of the dictionary, so a rare line can still differ.
2. The length: measured on the finished videos of 20–26/11/2026 (34 videos in 青山龍星, speeds 1.08–1.3: 0.5 s off
   on average, 1.8 s at most; a guess from the written characters was 5 s off on average):
       seconds = (0.0975 × kana + 0.425 × commas + 0.59 × lines) ÷ speed × voice
                 + line_pause × lines + scene_pause × scenes
   `commas`: every 、 and every 。？！ inside a line (each is a pause of the voice; a `say` written with a comma
   after every word reads much slower). `voice`: 1 for 青山龍星; もち子さん 1.08 (4 videos); 剣崎雌雄 0.99 and
   玄野武宏 0.94 (one video each); a voice not measured yet counts 1: after its first video, add its factor here.
"""
import json
import re
import sys
from pathlib import Path

PER_KANA, PER_COMMA, PER_LINE = 0.0975, 0.425, 0.59
VOICES = {"青山龍星": 1.0, "もち子さん": 1.08, "剣崎雌雄": 0.99, "玄野武宏": 0.94}
DEFAULT_VOICE = "青山龍星"
DEFAULT_SPEED = 0.96          # news/custom.py: the speed of a story without "pace"
MINIMUM, MARGIN = 61.0, 2.0   # common rule 2, and the margin of common rule 23
LOUD = 2.4                    # "voice" of every new story (CLAUDE.md, "The rules of each kind of video")
MAXIMUM = 65.0                # common rule 3 (owner, 26/11/2026: every video 61–65 s, the film channel excepted)
KANA = re.compile(r"[ァ-ヺー]")
PAUSES = re.compile(r"[、，,。！？!?]")
LINE_END = "。．.！？!?」』）) 　"


def spoken(line):
    return line if isinstance(line, str) else line.get("say") or line["text"]


def main(path):
    try:
        import pyopenjtalk
    except ImportError:
        sys.exit("pip install pyopenjtalk   (the dictionary of the voice engine; then run this again)")
    story = json.loads(Path(path).read_text(encoding="utf-8"))
    pace = story.get("pace") or {}
    speed = float(pace.get("speed", DEFAULT_SPEED))
    line_pause, scene_pause = float(pace.get("line_pause", 0.0)), float(pace.get("scene_pause", 0.0))
    scenes = story.get("scenes") or []
    seconds = kana = commas = lines = 0
    unmeasured = set()
    for number, scene in enumerate(scenes, 1):
        name = (scene.get("speaker") or story.get("speaker") or DEFAULT_VOICE).split("/")[0]
        if name not in VOICES:
            unmeasured.add(name)
        print(f"\n{number}. {scene.get('label', '')}" + (f"  [{name}]" if scene.get("speaker") else ""))
        for line in scene.get("lines") or []:
            text = spoken(line)
            reading = pyopenjtalk.g2p(text, kana=True)
            k, c = len(KANA.findall(reading)), len(PAUSES.findall(text.rstrip(LINE_END)))
            kana, commas, lines = kana + k, commas + c, lines + 1
            seconds += (PER_KANA * k + PER_COMMA * c + PER_LINE) / speed * VOICES.get(name, 1.0) + line_pause
            shown = line if isinstance(line, str) else line["text"]
            print(f"   {shown}")
            print(f"   → {reading}" + ("   (say)" if not isinstance(line, str) and line.get("say") else ""))
        seconds += scene_pause
    voice = (story.get("speaker") or DEFAULT_VOICE).split("/")[0]
    print(f"\n{kana} kana, {commas} pauses, {lines} lines, {len(scenes)} scenes; {voice} at speed {speed:g}"
          f" (pauses {line_pause:g} / {scene_pause:g})")
    print(f"estimated voice: {seconds:.1f} s")
    for name in sorted(unmeasured):
        print(f"note: the voice {name} was never measured (counted like {DEFAULT_VOICE}): the estimate is rough")
    if seconds < MINIMUM + MARGIN:
        print(f"warning: under {MINIMUM + MARGIN:g} s: the video must pass {MINIMUM:g} s (common rule 2) with a "
              f"margin of {MARGIN:g} s (common rule 23): add true details of the same story before the render "
              f"(a trial or sample video is the exception)")
    if seconds > MAXIMUM:
        print(f"warning: over {MAXIMUM:g} s: every video is {MINIMUM:g}–{MAXIMUM:g} s (common rule 3): cut it to the main "
              f"thread before the render (only the film channel, 2–3 minutes, is longer)")
    if float(story.get("voice", 1.0)) < LOUD:
        print(f'warning: the sound is at {float(story.get("voice", 1.0)):g}: every new story carries "voice": {LOUD:g} '
              f'(owner, 26/11/2026: every video is loud)')
    others = sorted({(scene.get("speaker") or story.get("speaker") or DEFAULT_VOICE).split("/")[0]
                     for scene in scenes} - {DEFAULT_VOICE})
    if others:
        print(f"warning: the voice is {', '.join(others)}: every channel reads in {DEFAULT_VOICE} (common rule 21); "
              f"another voice only in a trial the owner asks for")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
