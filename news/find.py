"""Find free-to-use pictures on Wikimedia Commons for the searches of a story.

python -m news.find stories/<name>.json <out_dir>
For every entry of "searches" not searched before: up to 8 pictures whose licence allows use in a video
(public domain, CC0, CC BY, CC BY-SA), without small files and repeated scans. Writes <out_dir>/<k>-<n>.jpg,
index.json (file page, licence, author) and sheet_<k>.jpg, a numbered contact sheet to choose from.
"""
from io import BytesIO
import json
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError
from urllib.parse import urlencode

from PIL import Image, ImageDraw, ImageFont

from .custom import read
from .sources import fetch

HOSTS = {"commons.wikimedia.org", "upload.wikimedia.org"}
ALLOWED = re.compile(r"^(public domain|pd|cc0|cc[- ]by(-sa)?[- ]?\d|cc[- ]by(-sa)?$)", re.I)
KEEP, MIN_SIDE = 8, 400


def get(url):
    for attempt in range(4):
        try:
            return fetch(url, HOSTS, limit=12_000_000, timeout=60)
        except HTTPError as error:
            if error.code not in (429, 503) or attempt == 3:
                raise
            time.sleep(10 * (attempt + 1))


def plain(value):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", value or "")).strip()


def search(query):
    params = urlencode({
        "action": "query", "format": "json", "generator": "search", "gsrsearch": query, "gsrnamespace": 6,
        "gsrlimit": 14, "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime", "iiurlwidth": 2000,
    })
    data = json.loads(get(f"https://commons.wikimedia.org/w/api.php?{params}"))
    pages = sorted(data.get("query", {}).get("pages", {}).values(), key=lambda page: page.get("index", 0))
    for page in pages:
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata") or {}
        licence = plain(meta.get("LicenseShortName", {}).get("value"))
        if info.get("mime") not in ("image/jpeg", "image/png") or not ALLOWED.search(licence):
            continue
        if min(info.get("width", 0), info.get("height", 0)) < MIN_SIDE:
            continue
        yield {"title": page["title"], "page": info["descriptionurl"], "thumb": info.get("thumburl") or info["url"],
               "width": info["width"], "height": info["height"], "license": licence,
               "license_url": plain(meta.get("LicenseUrl", {}).get("value")),
               "artist": plain(meta.get("Artist", {}).get("value"))[:120],
               "description": plain(meta.get("ImageDescription", {}).get("value"))[:300]}


def fingerprint(image):
    grey = image.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
    pixels = list(grey.tobytes())
    return sum(1 << i for i in range(64) if pixels[i // 8 * 9 + i % 8] > pixels[i // 8 * 9 + i % 8 + 1])


def sheet(entries, out, path):
    face = ImageFont.load_default(size=17)
    board = Image.new("RGB", (4 * 380, -(-len(entries) // 4) * 400), "#0a0a0c")
    for index, entry in enumerate(entries):
        with Image.open(out / entry["file"]) as picture:
            picture.thumbnail((360, 360))
            board.paste(picture, (index % 4 * 380 + (380 - picture.width) // 2, index // 4 * 400 + 10))
        label = f"#{index + 1}  {entry['width']}x{entry['height']}  {entry['license'].replace('Public domain', 'PD')}"
        ImageDraw.Draw(board).text((index % 4 * 380 + 10, index // 4 * 400 + 374), label[:40], fill="#ffd25a", font=face)
    board.save(path, quality=85)


def main():
    story, out = read(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    index_path = out / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else []
    done = {group["k"]: group["query"] for group in index}
    seen = []
    for name in sorted(out.glob("*-*.jpg")):
        with Image.open(name) as picture:
            seen.append(fingerprint(picture))
    for k, query in enumerate(story.get("searches", []), 1):
        if done.get(k) == query:
            continue
        index = [group for group in index if group["k"] != k]
        for old in out.glob(f"{k}-*.jpg"):
            old.unlink()
        kept = []
        for result in search(query):
            if len(kept) == KEEP:
                break
            try:
                with Image.open(BytesIO(get(result.pop("thumb")))) as original:
                    picture = original.convert("RGB")
            except (OSError, ValueError) as error:
                print(f"  skipped {result['title']}: {error}")
                continue
            finally:
                time.sleep(1)
            mark = fingerprint(picture)
            if any(bin(mark ^ other).count("1") <= 10 for other in seen):
                continue
            seen.append(mark)
            result["file"] = f"{k}-{len(kept) + 1}.jpg"
            picture.save(out / result["file"], quality=90)
            kept.append(result)
        if kept:
            sheet(kept, out, out / f"sheet_{k}.jpg")
        index.append({"k": k, "query": query, "results": kept})
        print(f"{k}. {query}: {len(kept)} pictures")
        time.sleep(2)
    index.sort(key=lambda group: group["k"])
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
