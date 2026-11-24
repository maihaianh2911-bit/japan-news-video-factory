"""Run the Japanese news video factory."""
import argparse
from dataclasses import asdict
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import re
import tempfile
import wave

from .custom import StoryError, load_story
from .render import encode, stills, use_fx, use_style, use_voice, write_subtitles
from .sources import JST, discover, get_release
from .story import VOICE_CREDIT, build_story
from .visuals import find_photos
from .voice import narration

DEMO_URL = "https://www.boj.or.jp/mopo/mpmdeci/state_2025/k250124a.htm"
MIN_SECONDS, MAX_SECONDS = 61, 160   # the length of every video but a trial (CLAUDE.md, iron rules 2 and 3)


def trial(title):
    """A trial or sample video (the owner's words thử, mẫu, test, demo in its title) may be of any length."""
    return bool(re.search(r"thử|mẫu|\btest\b|\bdemo\b", title or "", re.IGNORECASE))


def prepare(args, today):
    if args.demo or args.url:
        release = get_release(DEMO_URL if args.demo else args.url)
        beats = build_story(release)
        if not beats:
            raise ValueError("This release has too little readable material for a grounded video")
        return release, beats
    for entry in discover(today)[:8]:
        try:
            release = get_release(entry.url, entry)
        except (OSError, ValueError) as error:
            print(f"Skipping unreadable release: {error}")
            continue
        if not today - timedelta(days=1) <= release.published <= today:
            continue
        beats = build_story(release)
        if beats:
            return release, beats
    return None, []


def summary(message, ready):
    print(message)
    if summary_path := os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(summary_path).open("a", encoding="utf-8") as output:
            output.write(message + "\n")
    if output_path := os.environ.get("GITHUB_OUTPUT"):
        with Path(output_path).open("a", encoding="utf-8") as output:
            output.write(f"ready={'true' if ready else 'false'}\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--demo", action="store_true")
    mode.add_argument("--url", help="Official METI, Bank of Japan or national CPI release URL")
    mode.add_argument("--story", type=Path, help="A hand-written story, stories/<name>.json")
    parser.add_argument("--pictures", type=Path, help="Folder of the pictures found for the story")
    parser.add_argument("--stills", type=Path, help="Only save one frame per scene of the story here")
    parser.add_argument("--out", type=Path, default=Path("dist"))
    parser.add_argument("--plan-only", action="store_true", help="Print the selected source and Japanese script")
    args = parser.parse_args()
    today = datetime.now(JST).date()
    scene_photos = None
    if args.story:
        try:
            release, beats, scene_photos = load_story(args.story, args.pictures)
        except StoryError as error:
            raise SystemExit(f"error: {error}") from None
        use_style(release.style)
        use_fx(release.fx)
        use_voice(release.voice)
        if args.stills:
            args.stills.mkdir(parents=True, exist_ok=True)
            stills(beats, release, scene_photos, args.stills)
            return
    else:
        release, beats = prepare(args, today)
    if not beats:
        summary(f"Không có thông cáo đủ mới và đủ dữ kiện ngày {today} (JST).", False)
        return
    script = "\n\n".join("\n".join(beat.lines) for beat in beats) + "\n"
    print(f"{release.published} | {release.publisher} | {release.url}")
    if args.plan_only:
        print(script)
        return

    if scene_photos is None:
        photo_scenes = [index for index, beat in enumerate(beats) if beat.visual == "photo"]
        scene_photos = {index: [photo] for index, photo
                        in zip(photo_scenes, find_photos(release.publisher, len(photo_scenes)))}
    photos = [photo for scene in scene_photos.values() for photo in scene]
    if args.demo and not photos:
        raise RuntimeError("Demo could not retrieve a verified Bank of Japan archival photograph")
    for photo in photos:
        print(f"Archival photo: {photo.page} ({photo.license})")

    args.out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="news-") as scratch:
        wav = Path(scratch) / "voice.wav"
        intervals, captions = narration(beats, wav, speed=release.speed, line_pause=release.line_pause,
                                        exact=bool((getattr(release, "fx", None) or {}).get("text")),
                                        scene_pause=release.scene_pause)
        duration = intervals[-1][1]
        if duration > 90 and not args.story:
            intervals, captions = narration(beats, wav, speed=min(1.25, 0.96 * duration / 87))
            duration = intervals[-1][1]
        if duration > 90 and not args.story:
            raise RuntimeError(f"Grounded narration exceeds the 90-second format: {duration:.1f}s")
        if args.story and not trial(release.title) and not MIN_SECONDS < duration <= MAX_SECONDS:
            # owner, 24/11/2026, after a 53-second video was rendered: "dưới 61s mà vẫn dựng là sao? Chỉ có view
            # demo mới đc dưới 61s thôi": the length is checked on the real voice, before a single frame is drawn
            why = (f"giọng đọc dài {duration:.0f} giây, " + ("dưới 61 giây: cần viết kịch bản dài hơn"
                   if duration <= MIN_SECONDS else "quá 160 giây: cần cắt bớt kịch bản"))
            if env_path := os.environ.get("GITHUB_ENV"):
                with Path(env_path).open("a", encoding="utf-8") as env:
                    env.write(f"WHY={why}\n")
            raise SystemExit(f"error: the voice lasts {duration:.1f} s; a video lasts over {MIN_SECONDS} s and at most "
                             f"{MAX_SECONDS} s (CLAUDE.md, iron rule 3): lengthen or cut the script, or write thử, mẫu, "
                             f"test or demo in the title of a trial. Nothing was rendered.")
        with wave.open(str(wav)) as voice:
            if voice.getnframes() == 0:
                raise RuntimeError("No voice audio produced")
        encode(beats, release, scene_photos, args.demo, intervals, captions, wav, args.out)
    write_subtitles(captions, args.out / "subtitles.srt")
    (args.out / "script-ja.txt").write_text(script, encoding="utf-8")
    report = {
        "demo": args.demo,
        "duration_seconds": round(duration, 2),
        "release": {"url": release.url, "published": release.published.isoformat(),
                    "publisher": release.publisher, "title": release.title},
        "photos": [photo.credit() for photo in photos],
        "voice_credit": VOICE_CREDIT,
        "music": release.music.credit() if release.music else None,
        "scenes": [
            dict(asdict(beat),
                 visual=beat.visual if index in scene_photos or beat.visual != "photo" else "document",
                 image_url=scene_photos[index][0].page if index in scene_photos else None,
                 image_urls=[photo.page for photo in scene_photos.get(index, [])])
            for index, beat in enumerate(beats)
        ],
    }
    (args.out / "sources.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary(f"{release.publisher} · {release.published} · {duration:.1f} s · "
            f"{len(beats)} cảnh · {len(report['photos'])} ảnh.\n\n{release.url}", True)


if __name__ == "__main__":
    main()
