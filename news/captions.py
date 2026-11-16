"""The posting caption of a video: captions/<story name>.txt, published as <name>/caption.txt beside video.mp4.

python -m news.captions captions/<name>.txt   checks one caption file (no other dependency than Python)

Format (owner, 16/11/2026), UTF-8, Japanese, at most 2000 characters:
    line 1        a hook title, at most 80 characters, true to the script
    lines 2-5     2 to 4 short sentences on the video (one block, no blank line inside)
    blank line
    one line      5 to 8 hashtags, e.g. #皇室 #昭和 #歴史 #shorts
    blank line
    last line     the credit line, starting with 画像出典 (e.g. 画像出典: … ／ 詳しくは credits.txt; say 元動画 when
                  pictures of the source video are used)
"""
from pathlib import Path
import re
import sys

LIMIT, TITLE_LIMIT = 2000, 80
HASHTAG = re.compile(r"^#[^\s#]+$")


def caption_path(story_path):
    """captions/<name>.txt of stories/<name>.json (the folders sit side by side in the repository)."""
    story_path = Path(story_path)
    return story_path.parent.parent / "captions" / f"{story_path.stem}.txt"


def problems(text):
    """The problems of a caption (empty when it is usable)."""
    found = []
    if len(text) > LIMIT:
        found.append(f"the caption has {len(text)} characters, at most {LIMIT}")
    blocks = [block.strip("\n") for block in re.split(r"\n[ \t　]*\n", text.strip("\n"))]
    if len(blocks) != 3:
        return found + [f"the caption must be 3 blocks separated by one blank line (title and sentences / hashtags / "
                        f"credit line), found {len(blocks)}"]
    head, tags, credit = blocks
    lines = head.split("\n")
    title, sentences = lines[0].strip(), [line for line in lines[1:] if line.strip()]
    if not title:
        found.append("line 1 (the title) is empty")
    elif len(title) > TITLE_LIMIT:
        found.append(f"line 1 (the title) has {len(title)} characters, at most {TITLE_LIMIT}")
    if not 1 <= len(sentences) <= 4 or not 2 <= sum(max(1, line.count("。")) for line in sentences) <= 4:
        found.append(f"after the title come 2 to 4 short sentences, found {len(sentences)} line(s): {sentences!r}")
    words = tags.split()
    if "\n" in tags.strip() or not all(HASHTAG.match(word) for word in words):
        found.append(f"the hashtags are one line of #words separated by spaces, got {tags!r}")
    elif not 5 <= len(words) <= 8:
        found.append(f"5 to 8 hashtags, found {len(words)}")
    elif len(set(words)) != len(words):
        found.append("a hashtag appears twice")
    if "\n" in credit or not credit.startswith("画像出典"):
        found.append(f"the last line is the credit line, starting with 画像出典, got {credit!r}")
    return found


def check(path):
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [f"{path}: not UTF-8"]
    return [f"{path}: {problem}" for problem in problems(text)]


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: python -m news.captions captions/<name>.txt")
    found = check(sys.argv[1])
    if found:
        sys.exit("error: " + "\n  - ".join([f"{len(found)} caption problem(s):"] + found))
    print(f"{sys.argv[1]}: OK")


if __name__ == "__main__":
    main()
