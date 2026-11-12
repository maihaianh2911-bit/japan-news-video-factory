"""Find free-to-use pictures on Wikimedia Commons for the searches of a story.

python -m news.find stories/<name>.json <out_dir>
For every entry of "searches" not searched before: up to 8 pictures whose licence allows use in a video
(public domain, CC0, CC BY, CC BY-SA), without small files and repeated scans. Writes <out_dir>/<k>-<n>.jpg,
index.json (file page, licence, author) and sheet_<k>.jpg, a numbered contact sheet to choose from.
A search with no usable picture has no sheet. A search that fails (network, Commons refusing) is recorded in
index.json with "error" and no results, is tried again on the next run, and makes the exit status 3; the other
searches still run and index.json is written after every search, so what was found can still be published.
"""
from io import BytesIO
import json
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

from PIL import Image, ImageDraw, ImageFont

from .custom import StoryError, read
from .sources import fetch

HOSTS = {"commons.wikimedia.org", "upload.wikimedia.org"}
ALLOWED = re.compile(r"^(public domain|pd|cc0|cc[- ]by(-sa)?[- ]?\d|cc[- ]by(-sa)?$)", re.I)
KEEP, MIN_SIDE = 8, 400


def get(url):
    """Fetch from Commons, waiting and trying again on rate limits, server errors and network errors."""
    for attempt in range(4):
        try:
            return fetch(url, HOSTS, limit=12_000_000, timeout=60)
        except HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == 3:
                raise
        except (URLError, TimeoutError, ConnectionError) as error:
            if attempt == 3:
                raise
            print(f"  network error, trying again: {error}")
        time.sleep(10 * (attempt + 1))


def plain(value):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", value or "")).strip()


def search(query):
    params = urlencode({
        "action": "query", "format": "json", "generator": "search", "gsrsearch": query, "gsrnamespace": 6,
        "gsrlimit": 30, "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime", "iiurlwidth": 2000,
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


def save_index(index, path):
    index.sort(key=lambda group: group["k"])
    path.write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def find(query, k, out, seen):
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
        if any(bin(mark ^ other).count("1") <= 10 for other in seen.values()):
            continue
        result["file"] = f"{k}-{len(kept) + 1}.jpg"
        seen[result["file"]] = mark
        picture.save(out / result["file"], quality=90)
        kept.append(result)
    return kept


def clear(out, k, seen):
    for old in [*out.glob(f"{k}-*.jpg"), out / f"sheet_{k}.jpg"]:
        old.unlink(missing_ok=True)
        seen.pop(old.name, None)


def main():
    try:
        story = read(sys.argv[1])
    except StoryError as error:
        sys.exit(f"error: {error}")
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    index_path = out / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else []
    done = {group["k"]: group["query"] for group in index if not group.get("error")}
    seen = {}   # file name -> fingerprint, to skip the same picture found again by another search
    for name in sorted(out.glob("*-*.jpg")):
        with Image.open(name) as picture:
            seen[name.name] = fingerprint(picture)
    failed = []
    for k, query in enumerate(story.get("searches", []), 1):
        if done.get(k) == query:
            continue
        index = [group for group in index if group["k"] != k]
        clear(out, k, seen)
        group = {"k": k, "query": query, "results": []}
        try:
            group["results"] = find(query, k, out, seen)
        except Exception as error:   # one failed search must not lose the others
            clear(out, k, seen)
            group["error"] = f"{type(error).__name__}: {error}"
            failed.append(k)
            print(f"{k}. {query}: FAILED ({group['error']})")
        else:
            if group["results"]:
                sheet(group["results"], out, out / f"sheet_{k}.jpg")
            print(f"{k}. {query}: {len(group['results'])} pictures" + ("" if group["results"] else " (no sheet)"))
        index.append(group)
        save_index(index, index_path)
        time.sleep(2)
    save_index(index, index_path)
    empty = [group["k"] for group in index if not group["results"] and not group.get("error")]
    if empty:
        print(f"Searches with no picture (no sheet): {', '.join(map(str, empty))}")
    if failed:
        print(f"Searches that failed (tried again next run): {', '.join(map(str, failed))}")
        sys.exit(3)


if __name__ == "__main__":
    main()
