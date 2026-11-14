"""Find pictures for the searches of a story.

python -m news.find stories/<name>.json <out_dir>
For every entry of "searches" not searched before:
- "<words>": Wikimedia Commons, up to 8 pictures whose licence allows use in a video (public domain, CC0, CC BY,
  CC BY-SA), without small files and repeated scans.
- "web:<words>": a free web image search (Bing, else Yahoo! JAPAN, else DuckDuckGo), up to 12 pictures from any site, without stock
  sites (watermarks). The licence is unknown: the owner chose to use such pictures (13/11/2026); the site is
  credited on screen and in credits.txt.
- "url:<picture address> [<page address>]": that one picture. Writes <out_dir>/<k>-<n>.jpg,
index.json (file page, licence, author) and sheet_<k>.jpg, a numbered contact sheet to choose from.
A search with no usable picture has no sheet. A search that fails (network, Commons refusing) is recorded in
index.json with "error" and no results, is tried again on the next run, and makes the exit status 3; the other
searches still run and index.json is written after every search, so what was found can still be published.
"""
from html import unescape
from io import BytesIO
import json
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

from lxml import html

from PIL import Image, ImageDraw, ImageFont

from .custom import StoryError, read
from .sources import fetch

HOSTS = {"commons.wikimedia.org", "upload.wikimedia.org"}
ALLOWED = re.compile(r"^(public domain|pd|cc0|cc[- ]by(-sa)?[- ]?\d|cc[- ]by(-sa)?$)", re.I)
KEEP, WEB_KEEP, MIN_SIDE, LARGEST = 8, 12, 400, 2400
BROWSER = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
STOCK = re.compile(r"gettyimages|alamy|shutterstock|istockphoto|dreamstime|123rf|depositphotos|pixta|aflo|"
                   r"stock\.adobe|agefotostock|bridgemanimages|pinimg|pinterest", re.I)


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


def web_get(url, referer=None, limit=12_000_000):
    """Fetch any public http(s) address the way a browser does (web searches and their pictures)."""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname or parts.username or parts.password \
            or parts.hostname == "localhost" or re.fullmatch(r"[0-9.:\[\]]+", parts.hostname):
        raise ValueError(f"Unsupported URL: {url}")
    headers = {"User-Agent": BROWSER, "Accept-Language": "ja,en;q=0.8"}
    if referer:
        headers["Referer"] = referer
    with urlopen(Request(url, headers=headers), timeout=30) as response:
        content = response.read(limit + 1)
    if len(content) > limit:
        raise ValueError(f"Response exceeds size limit: {url}")
    return content


def site(url):
    return (urlsplit(url).hostname or "").removeprefix("www.")


DEBUG = {}   # engine -> last page received, saved next to the pictures when a web search finds nothing


def bing(query):
    page = web_get("https://www.bing.com/images/search?" + urlencode(
        {"q": query, "form": "HDRSC2", "first": 1, "setlang": "ja", "cc": "JP", "mkt": "ja-JP"}))
    DEBUG["bing"] = page
    text = unescape(page.decode("utf-8", "replace"))
    seen = set()
    for meta in re.finditer(r'\{[^{}]*?"murl":"[^{}]*?\}', text):
        try:
            item = json.loads(meta[0])
        except ValueError:
            continue
        if item.get("murl") and item["murl"] not in seen:
            seen.add(item["murl"])
            yield item["murl"], item.get("purl") or item["murl"], plain(item.get("t") or "")


def yahoo(query):
    page = web_get("https://search.yahoo.co.jp/image/search?" + urlencode({"p": query, "ei": "UTF-8"}))
    DEBUG["yahoo"] = page
    match = re.search(rb'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', page, re.S)
    if not match:
        return

    def walk(node):
        if isinstance(node, dict):
            original = node.get("original")
            if isinstance(original, dict) and isinstance(original.get("url"), str):
                yield (original["url"], node.get("refererUrl") or node.get("url") or original["url"],
                       plain(node.get("title") or ""))
                return
            for value in node.values():
                yield from walk(value)
        elif isinstance(node, list):
            for value in node:
                yield from walk(value)

    yield from walk(json.loads(match[1]))


def duckduckgo(query):
    page = web_get("https://duckduckgo.com/?" + urlencode({"q": query, "iax": "images", "ia": "images"}))
    DEBUG["duckduckgo"] = page
    token = re.search(rb"vqd=[\"']?([0-9-]+)", page)
    if not token:
        raise ValueError("DuckDuckGo gave no search token")
    data = web_get("https://duckduckgo.com/i.js?" + urlencode(
        {"l": "jp-jp", "o": "json", "q": query, "vqd": token[1].decode(), "f": ",,,,,", "p": "1"}),
        referer="https://duckduckgo.com/")
    DEBUG["duckduckgo"] = data
    for item in json.loads(data).get("results", []):
        if item.get("image"):
            yield item["image"], item.get("url") or item["image"], plain(item.get("title") or "")


def web_search(query, out=None):
    """Candidates (picture address, page address, title) of a web image search, stock sites left out."""
    results = []
    DEBUG.clear()
    for engine in (bing, yahoo, duckduckgo):
        try:
            results = list(engine(query))
        except (OSError, ValueError) as error:
            print(f"  {engine.__name__} failed: {type(error).__name__}: {error}", flush=True)
        print(f"  {engine.__name__}: {len(results)} results", flush=True)
        if results:
            break
    if not results:
        if out:
            for name, page in DEBUG.items():
                (out / f"debug_{name}.html").write_bytes(page[:400_000])
        raise RuntimeError("no web image search answered")
    return [result for result in results if not STOCK.search(result[0] + " " + result[1])]


def web_find(candidates, k, out, seen, keep):
    kept = []
    for image, page, title in candidates:
        if len(kept) == keep:
            break
        try:
            with Image.open(BytesIO(web_get(image, referer=page))) as original:
                original.draft("RGB", (LARGEST, LARGEST))
                picture = original.convert("RGB")
        except Exception as error:   # a dead link or an odd file: skip it
            print(f"  skipped {image[:120]}: {type(error).__name__}: {error}")
            continue
        if min(picture.size) < MIN_SIDE:
            continue
        mark = fingerprint(picture)
        if any(bin(mark ^ other).count("1") <= 10 for other in seen.values()):
            continue
        picture.thumbnail((LARGEST, LARGEST))
        entry = {"title": title or image.rsplit("/", 1)[-1][:100], "page": page, "image": image,
                 "width": picture.width, "height": picture.height, "license": "", "license_url": "",
                 "artist": site(page), "description": title, "file": f"{k}-{len(kept) + 1}.jpg"}
        seen[entry["file"]] = mark
        picture.save(out / entry["file"], quality=90)
        kept.append(entry)
    return kept


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
        where = entry["license"].replace("Public domain", "PD") or entry.get("artist", "")
        label = f"#{index + 1}  {entry['width']}x{entry['height']}  {where}"
        ImageDraw.Draw(board).text((index % 4 * 380 + 10, index // 4 * 400 + 374), label[:40], fill="#ffd25a", font=face)
    board.save(path, quality=85)


def save_index(index, path):
    index.sort(key=lambda group: group["k"])
    path.write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def find(query, k, out, seen):
    if query.startswith("web:"):
        return web_find(web_search(query[4:].strip(), out), k, out, seen, WEB_KEEP)
    if query.startswith("url:"):
        image, _, page = query[4:].strip().partition(" ")
        kept = web_find([(image, page.strip() or image, "")], k, out, seen, 1)
        if not kept:
            raise RuntimeError(f"could not load the picture {image}")
        return kept
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
