"""Run the Japanese news video factory."""
import argparse
from dataclasses import asdict
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import tempfile
import wave

from .demo import DEMO
from .render import encode, write_subtitles
from .sources import JST, discover, get_release
from .story import VOICE_CREDIT, build_story
from .visuals import find_photo
from .voice import narration


def prepare(args, today):
    if args.demo:
        return DEMO, build_story(DEMO)
    if args.url:
        release = get_release(args.url)
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
    mode.add_argument("--url", help="Official METI or Bank of Japan HTML release URL")
    parser.add_argument("--out", type=Path, default=Path("dist"))
    parser.add_argument("--plan-only", action="store_true", help="Print the selected source and Japanese script")
    args = parser.parse_args()
    today = datetime.now(JST).date()
    release, beats = prepare(args, today)
    if not beats:
        summary(f"Không có thông cáo đủ mới và đủ dữ kiện ngày {today} (JST).", False)
        return
    script = "\n\n".join("\n".join(beat.lines) for beat in beats) + "\n"
    print(f"{release.published} | {release.publisher} | {release.url}")
    if args.plan_only:
        print(script)
        return

    photo = find_photo(release.publisher)
    if args.demo and photo is None:
        raise RuntimeError("Demo could not retrieve the verified Bank of Japan archival photograph")

    args.out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="news-") as scratch:
        wav = Path(scratch) / "voice.wav"
        intervals, captions = narration(beats, wav, speed=0.96)
        duration = intervals[-1][1]
        if duration > 90:
            intervals, captions = narration(beats, wav, speed=min(1.25, 0.96 * duration / 87))
            duration = intervals[-1][1]
        if duration > 90:
            raise RuntimeError(f"Grounded narration exceeds the 90-second format: {duration:.1f}s")
        with wave.open(str(wav)) as voice:
            if voice.getnframes() == 0:
                raise RuntimeError("No voice audio produced")
        encode(beats, release, photo, args.demo, intervals, captions, wav, args.out)
    write_subtitles(captions, args.out / "subtitles.srt")
    (args.out / "script-ja.txt").write_text(script, encoding="utf-8")
    report = {
        "demo": args.demo,
        "duration_seconds": round(duration, 2),
        "release": {"url": release.url, "published": release.published.isoformat(),
                    "publisher": release.publisher, "title": release.title},
        "photos": [photo.credit()] if photo else [],
        "voice_credit": VOICE_CREDIT,
        "scenes": [dict(asdict(beat), visual=beat.visual if photo or beat.visual != "photo" else "document")
                   for beat in beats],
    }
    (args.out / "sources.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary(f"{release.publisher} · {release.published} · {duration:.1f} s · "
            f"{len(beats)} cảnh · {len(report['photos'])} ảnh tư liệu.\n\n{release.url}", True)


if __name__ == "__main__":
    main()
