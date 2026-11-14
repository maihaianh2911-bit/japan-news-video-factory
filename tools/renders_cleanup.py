"""Delete the folders of old videos in a checkout of the renders branch (run from that folder).

python tools/renders_cleanup.py <stories folder of main>     (env: KEEP_DAYS, GITHUB_REPOSITORY, GH_TOKEN for gh)

A story folder <name>/ is deleted when
- its issue (the "issue" of stories/<name>.json on main) was closed more than 2 days ago, or had no activity for
  KEEP_DAYS days; or
- it has no issue (no story file on main any more, or a story without "issue") and was last published more than
  KEEP_DAYS days ago (status.json).
Always kept: mau-boj (the code check draws its stills from mau-boj/find), a folder whose issue or date cannot be
read, and files at the top level. Prints what it did; the last line is "removed=<count>".
"""
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ALWAYS = {"mau-boj"}
CLOSED_GRACE = timedelta(days=2)


def when(text):
    return datetime.fromisoformat(text.strip().replace("Z", "+00:00"))


def issue_of(story):
    try:
        number = json.loads(story.read_text(encoding="utf-8")).get("issue")
    except (OSError, ValueError, AttributeError):
        return None
    return number if isinstance(number, int) and not isinstance(number, bool) and number > 0 else None


def issue_state(number):
    """(state, last activity, closed at) of an issue, or None when it cannot be read."""
    result = subprocess.run(["gh", "api", f"repos/{os.environ['GITHUB_REPOSITORY']}/issues/{number}", "--jq",
                             '[.state, .updated_at, (.closed_at // "")] | join(" ")'], capture_output=True, text=True)
    try:
        state, updated, *closed = result.stdout.split()
        return state, when(updated), when(closed[0]) if closed else None
    except (ValueError, IndexError):
        return None


def published(folder):
    """The newest publish time in the status files of a story folder, or None."""
    times = []
    for status in (folder / "status.json", folder / "find" / "status.json"):
        try:
            times.append(when(json.loads(status.read_text(encoding="utf-8"))["published_utc"]))
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            pass
    return max(times, default=None)


def verdict(folder, stories, now, keep):
    """Why the folder is deleted, or None to keep it (the second value says why it is kept)."""
    if folder.name in ALWAYS:
        return None, "always kept"
    number = issue_of(stories / f"{folder.name}.json")
    if number:
        state = issue_state(number)
        if state is None:
            return None, f"issue #{number} could not be read"
        if state[0] == "closed" and (state[2] is None or now - state[2] > CLOSED_GRACE):
            return f"issue #{number} is closed", None
        if now - state[1] > keep:
            return f"issue #{number} had no activity for {keep.days} days", None
        return None, f"issue #{number} is active"
    last = published(folder)
    if last is None:
        return None, "no issue and no readable status.json"
    if now - last > keep:
        return f"no issue, published {last:%Y-%m-%d}", None
    return None, f"no issue, published {last:%Y-%m-%d}"


def main():
    stories = Path(sys.argv[1])
    keep = timedelta(days=int(os.environ.get("KEEP_DAYS") or 14))
    now = datetime.now(timezone.utc)
    removed = 0
    for folder in sorted(Path(".").iterdir()):
        if not folder.is_dir() or folder.is_symlink() or folder.name == ".git":
            continue
        why, kept = verdict(folder, stories, now, keep)
        if why:
            shutil.rmtree(folder)
            removed += 1
            print(f"deleted {folder.name}: {why}")
        else:
            print(f"kept    {folder.name}: {kept}")
    print(f"removed={removed}")


if __name__ == "__main__":
    main()
