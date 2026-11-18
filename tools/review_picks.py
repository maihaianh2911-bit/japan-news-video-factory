"""The picture review (owner, 18/11/2026: "đọc lại hình ảnh đã chọn xem đã phù hợp với nội dung cần thể hiện chưa,
chưa thì chọn lại, duyệt lại, khi nào ổn mới lấy").

Every chosen picture on one row: the frame as it will be seen (from the stills preview), the whole picture as found,
the words spoken while it is on screen (a scene's pictures share its time evenly, so the words are its share of the
scene's text), and where it comes from (title and site in the find index). Claude reads every row and checks that
the picture shows what the words say at that moment, then re-picks and runs this again until every row passes.

Usage:
    python -m news --story stories/<name>.json --pictures <find folder> --stills <stills>
    python tools/review_picks.py stories/<name>.json <find folder> <stills> [<out folder>]
Writes <out>/review-<page>.jpg (six rows a page) and <out>/review.md (one line a picture, with an empty verdict).
"""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROW, STILL_W, WHOLE_W, WIDTH = 520, 292, 420, 1700


def cjk_font(size):
    for name in ("Noto Sans CJK JP:style=Bold", "Noto Sans CJK JP", "Noto Serif CJK JP"):
        try:
            path = subprocess.run(["fc-match", "-f", "%{file}", name], capture_output=True, text=True).stdout
            if path and "CJK" in path:
                return ImageFont.truetype(path, size)
        except OSError:
            break
    return ImageFont.load_default(size)


def pictures_of(scene):
    photo = scene.get("photo")
    entries = photo if isinstance(photo, list) else [photo] if photo else []
    return [{"pick": entry} if isinstance(entry, str) else entry for entry in entries]


def line_text(line):
    return line if isinstance(line, str) else line["text"]


def sources(find):
    found = {}
    for group in json.loads((find / "index.json").read_text(encoding="utf-8")):
        for result in group.get("results", []):
            name = Path(result.get("file", "")).stem
            found[name] = {"title": result.get("title") or "", "page": result.get("page") or result.get("source") or "",
                           "query": group.get("query", "")}
    return found


def wrapped(text, font, width):
    rows, row = [], ""
    for char in text:
        if char == "\n" or font.getlength(row + char) > width:
            rows.append(row)
            row = "" if char == "\n" else char
        else:
            row += char
    return rows + ([row] if row else [])


def fitted(image, width, height):
    image = image.convert("RGB")
    image.thumbnail((width, height))
    return image


def main():
    story, find, stills = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    out = Path(sys.argv[4]) if len(sys.argv) > 4 else stills
    out.mkdir(parents=True, exist_ok=True)
    data = json.loads(story.read_text(encoding="utf-8"))
    found = sources(find)
    big, small = cjk_font(30), cjk_font(22)
    rows, notes = [], ["| Cảnh | Ảnh | Lời đọc lúc ảnh hiện | Nguồn | Đạt? |", "|---|---|---|---|---|"]
    for index, scene in enumerate(data["scenes"]):
        picks = pictures_of(scene)
        words = "".join(line_text(line) for line in scene["lines"])
        for number, entry in enumerate(picks):
            share = words[len(words) * number // len(picks): len(words) * (number + 1) // len(picks)]
            still = stills / (f"scene-{index + 1:02}-{number + 1}.jpg" if len(picks) > 1 else f"scene-{index + 1:02}.jpg")
            whole = find / f"{entry['pick']}.jpg"
            source = found.get(entry["pick"], {})
            rows.append((index, number, entry, share, still, whole, source))
            notes.append(f"| {index + 1} {scene.get('label', '')} | {entry['pick']} {entry.get('move', '')} | {share} | "
                         f"{source.get('title', '')[:60]} | [ ] |")
    pages = [rows[start:start + 6] for start in range(0, len(rows), 6)]
    for page_number, page in enumerate(pages, 1):
        sheet = Image.new("RGB", (WIDTH, ROW * len(page)), "white")
        draw = ImageDraw.Draw(sheet)
        for row_index, (index, number, entry, share, still, whole, source) in enumerate(page):
            top = row_index * ROW
            if still.exists():
                sheet.paste(fitted(Image.open(still), STILL_W, ROW - 20), (10, top + 10))
            if whole.exists():
                picture = Image.open(whole)
                size = f"{picture.width}x{picture.height}"
                sheet.paste(fitted(picture, WHOLE_W, ROW - 20), (STILL_W + 30, top + 10))
            else:
                size = "missing"
            x, y = STILL_W + WHOLE_W + 60, top + 14
            scene = data["scenes"][index]
            draw.text((x, y), f"Cảnh {index + 1} · ảnh {number + 1} · {entry['pick']} ({size}) · {entry.get('move', '')}"
                      f"{' · ' + entry['tone'] if entry.get('tone') else ''}", font=small, fill="#555")
            y += 38
            draw.text((x, y), f"{scene.get('era', '')}  {scene.get('headline', '').replace(chr(10), ' ')}",
                      font=small, fill="#a33")
            y += 40
            for text_row in wrapped(f"「{share}」", big, WIDTH - x - 20)[:7]:
                draw.text((x, y), text_row, font=big, fill="black")
                y += 42
            y += 10
            for text_row in wrapped(f"{source.get('title', '')}  —  {source.get('page', '')}", small, WIDTH - x - 20)[:3]:
                draw.text((x, y), text_row, font=small, fill="#246")
                y += 30
            draw.line((0, top + ROW - 1, WIDTH, top + ROW - 1), fill="#ccc", width=2)
        sheet.save(out / f"review-{page_number}.jpg", quality=85)
    (out / "review.md").write_text("\n".join(notes) + "\n", encoding="utf-8")
    print(f"{len(rows)} pictures, {len(pages)} pages: {out}/review-1.jpg … review.md")


if __name__ == "__main__":
    main()
