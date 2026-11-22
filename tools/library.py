"""The picture library (owner, 22/11/2026: "Các lần tìm t thấy đc rất nhiều ảnh luôn, tại sao k lưu những ảnh đẹp nhất
lại, lần sau chỉ cần quét trong kho là có sẵn").

Every picture that passed the review of a video is kept in stories/media/library/<subject>/ — one folder for a person,
a couple, a family, a place or an event (masako, naruhito-masako, imperial-family, kumamoto-2026 …) — with its credit
and one line in the folder's README.md saying what it shows. A new video on the same subject starts from the library:
look at the subject's sheet, then take a picture with a search "file:stories/media/library/<subject>/<name>.jpg"
(credited to its first source: news/find.py reads the first line of <name>.credit.txt).

    python tools/library.py list
        the subjects, how many pictures each, and what they show (from the README files)
    python tools/library.py sheet <subject> [<out.jpg>]
        a numbered contact sheet of one subject, with names and sizes: look at it before writing the searches
    python tools/library.py add <find folder> <pick>=<subject>/<name>[#<what it shows>] ...
        keeps the picks of a finished review (the pictures of <find folder>, named as in its index.json), e.g.
        5-7=naruhito-masako/1993-parade-waving#Ngày cưới 1993: hai người vẫy tay trên xe mui trần
        A picture the subject already holds (the same picture, any size) is not kept twice.

Names: ASCII letters, digits and "-" (a year first when it carries the moment: 1993-parade-waving).
"""
import json
import re
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parent.parent
LIBRARY = REPO / "stories" / "media" / "library"
NAME = re.compile(r"[a-z0-9][a-z0-9-]*")
SAME = 10       # fingerprints this close (bits of 64) are the same picture, as in news/find.py
HEADER = """# Kho ảnh: {subject}

Ảnh đã duyệt khi làm video, giữ lại để dùng lại (chủ kênh, 22/11/2026). Dùng trong kịch bản bằng tìm kiếm
`file:stories/media/library/{subject}/<tên file>`; nguồn ảnh đọc từ `<tên>.credit.txt` (dòng đầu là tên ghi trong
video và credits.txt, dòng sau là trang gốc). Ảnh web thuộc bản quyền chủ ảnh: chủ kênh chấp nhận rủi ro, luôn ghi nguồn.

| File | Nội dung | Cỡ | Nguồn | Video |
|---|---|---|---|---|
"""


def fingerprint(image):
    grey = image.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
    pixels = list(grey.tobytes())
    return sum(1 << n for n in range(64) if pixels[n // 8 * 9 + n % 8] > pixels[n // 8 * 9 + n % 8 + 1])


def font(size):
    for path in ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def credit_of(entry):
    """The first line names the author or the site as the video credits it; then where the picture comes from."""
    artist = (entry.get("artist") or "").strip() or "unknown"
    first = f"{artist} / {entry['license']}" if entry.get("license") else artist
    return "\n".join(line for line in (first, entry.get("page") or "", entry.get("title") or "") if line) + "\n"


def readme_rows(subject):
    readme = LIBRARY / subject / "README.md"
    if not readme.is_file():
        return []
    return [line for line in readme.read_text(encoding="utf-8").splitlines() if line.startswith("| `")]


def write_index():
    subjects = sorted(path.name for path in LIBRARY.iterdir() if path.is_dir()) if LIBRARY.is_dir() else []
    lines = ["# Kho ảnh (chủ kênh, 22/11/2026)", "",
             "Mỗi thư mục là một chủ đề (một người, một cặp, một gia đình, một nơi, một sự kiện). Xem `python tools/library.py",
             "list` và `python tools/library.py sheet <chủ đề>` trước khi viết tìm kiếm cho video mới; ảnh đã duyệt của mỗi video",
             "được thêm bằng `python tools/library.py add …` (xem đầu tệp `tools/library.py`).", "",
             "| Chủ đề | Số ảnh |", "|---|---|"]
    for subject in subjects:
        count = len(list((LIBRARY / subject).glob("*.jpg")))
        lines.append(f"| [{subject}]({subject}/README.md) | {count} |")
    (LIBRARY / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def add(find, items):
    find = Path(find)
    index = {}
    for group in json.loads((find / "index.json").read_text(encoding="utf-8")):
        for result in group.get("results", []):
            index[Path(result.get("file", "")).stem] = result
    story = find.parent.name if find.name == "find" else find.name
    for item in items:
        target, _, note = item.partition("#")
        pick, _, place = target.partition("=")
        subject, _, name = place.partition("/")
        if not (NAME.fullmatch(subject) and NAME.fullmatch(name)):
            sys.exit(f"{item!r}: write <pick>=<subject>/<name> in lower-case ASCII letters, digits and '-'")
        if pick not in index or not (find / f"{pick}.jpg").is_file():
            sys.exit(f"{item!r}: no picture {pick} in {find}")
        folder = LIBRARY / subject
        folder.mkdir(parents=True, exist_ok=True)
        with Image.open(find / f"{pick}.jpg") as opened:
            picture = opened.convert("RGB")
        mark = fingerprint(picture)
        twin = None
        for kept in folder.glob("*.jpg"):
            with Image.open(kept) as other:
                if bin(fingerprint(other) ^ mark).count("1") <= SAME:
                    twin = kept.name
                    break
        if twin:
            print(f"{pick}: already in {subject}/ as {twin}, not kept twice")
            continue
        if (folder / f"{name}.jpg").exists():
            sys.exit(f"{item!r}: {subject}/{name}.jpg is another picture already: choose another name")
        picture.save(folder / f"{name}.jpg", quality=93)
        entry = index[pick]
        (folder / f"{name}.credit.txt").write_text(credit_of(entry), encoding="utf-8")
        readme = folder / "README.md"
        if not readme.is_file():
            readme.write_text(HEADER.format(subject=subject), encoding="utf-8")
        source = credit_of(entry).splitlines()[0].replace("|", "/")
        with readme.open("a", encoding="utf-8") as out:
            out.write(f"| `{name}.jpg` | {note.strip().replace('|', '/') or entry.get('title', '')[:60]} | "
                      f"{picture.width}×{picture.height} | {source} | {story} |\n")
        print(f"{pick} -> {subject}/{name}.jpg ({picture.width}x{picture.height}, {source})")
    write_index()


def sheet(subject, out=None):
    folder = LIBRARY / subject
    files = sorted(folder.glob("*.jpg"))
    if not files:
        sys.exit(f"no pictures in {folder}")
    tile, label, columns = 360, 52, 4
    rows = (len(files) + columns - 1) // columns
    board = Image.new("RGB", (columns * (tile + 10) + 10, rows * (tile + label + 10) + 10), "#111")
    draw, small = ImageDraw.Draw(board), font(18)
    for number, path in enumerate(files):
        x, y = 10 + number % columns * (tile + 10), 10 + number // columns * (tile + label + 10)
        with Image.open(path) as picture:
            size = f"{picture.width}x{picture.height}"
            thumb = picture.convert("RGB")
            thumb.thumbnail((tile, tile))
        board.paste(thumb, (x + (tile - thumb.width) // 2, y + (tile - thumb.height) // 2))
        draw.text((x, y + tile + 4), f"#{number + 1} {path.stem}", font=small, fill="#ffd27a")
        draw.text((x, y + tile + 26), size, font=small, fill="#bbb")
    out = Path(out) if out else Path(tempfile.gettempdir()) / f"library-{subject}.jpg"
    board.save(out, quality=85)
    print(f"{len(files)} pictures of {subject}: {out}")


def listing():
    if not LIBRARY.is_dir():
        sys.exit("the library is empty")
    for folder in sorted(path for path in LIBRARY.iterdir() if path.is_dir()):
        rows = readme_rows(folder.name)
        print(f"{folder.name}: {len(list(folder.glob('*.jpg')))} pictures")
        for row in rows:
            cells = [cell.strip() for cell in row.strip("|").split("|")]
            print(f"  {cells[0]:<52} {cells[2]:<11} {cells[1]}")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("list", "sheet", "add"):
        sys.exit(__doc__)
    if sys.argv[1] == "list":
        listing()
    elif sys.argv[1] == "sheet":
        sheet(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    else:
        add(sys.argv[2], sys.argv[3:])


if __name__ == "__main__":
    main()
