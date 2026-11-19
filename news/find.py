"""Find pictures for the searches of a story.

python -m news.find stories/<name>.json <out_dir>
For every entry of "searches" not searched before:
- "wiki:<name or Wikidata item>": every picture about one thing (a person, a place, a building, an event), found
  through its Wikidata item: the item's own pictures, the pictures of its Japanese and English Wikipedia articles,
  the files of its Wikimedia Commons category (and sub-categories), the photos taken at its coordinates. Up to 24,
  the most to the point first, all with a licence that allows use and their author. index.json says which item the
  name was read as ("wikidata"): check it is the right one. "wiki:美空ひばり", "wiki:Q17".
- "geo:<lat>,<lon> [<metres>]": Commons photos taken around a point, nearest first, whatever they are called
  (default 500 m, 10 km at most), up to 12: "geo:35.6852,139.7528 400".
- "<words>": Wikimedia Commons full-text search, up to 8 pictures whose licence allows use in a video (public
  domain, CC0, CC BY, CC BY-SA), without small files and repeated scans.
- "web:<words>": a free web image search (Yahoo! JAPAN, three pages of results; else Bing, else DuckDuckGo), up to
  20 pictures from any site, without stock sites (watermarks). The licence is unknown: the owner chose to use such
  pictures (14/11/2026); the site is credited on screen and in credits.txt. A picture its own site does not give
  is taken from the search engine's own copy of it.
- "page:<address of one article>": the pictures that article shows, up to 20, largest version of each, without
  the furniture of the page (19/11/2026). Credited to the site, as web:.
- "jps:<words>": Japan Search (jpsearch.go.jp), the shared catalogue of Japan's archives, libraries and museums:
  up to 12 pictures of records whose rights allow use, credited to the holding site with the licence (19/11/2026).
- "url:<picture address> [<page address>]": that one picture.
- "file:stories/media/<story>/<name>.jpg": a picture kept in the repository (e.g. cut out of the owner's source
  video, owner 16/11/2026), credited as 元動画 (the source video).
- "music:<words>": recordings on Wikimedia Commons (public domain, CC0, CC BY, CC BY-SA), up to 4 files of at most
  12 MB, for a quiet piece under the voice (story key "music"). No sheet: index.json gives title, length, licence.

A wish (17/11/2026): "<search> => <what the picture must show, in English>" on a wiki:, geo:, Commons, web:,
page: or jps: search, e.g. "web:美空ひばり 東京ドーム 1988 => a woman singing on a large stage in a feathered dress". The search then
looks at more candidates than it keeps (Commons 50, web 45, wiki: 60), scores each against the wish with CLIP
(open_clip ViT-B/32, MIT; weights from its GitHub release) and keeps the best, best first; pictures that do not show
the wish (score under 0.18) or look unsuitable are left out, so a group can come back small or empty. The score is
"match" in index.json and on the contact sheet (about 0.30 and more: it shows the thing; near 0.20: doubtful). The
search words alone are never ranked (they are often Japanese; CLIP reads English). Without torch and open_clip
installed, or with FIND_RANK=0, the wish is ignored ("ranked": false in index.json) and the search keeps the first
pictures as a search without a wish does. A search without a wish keeps the order of its source.

Writes <out_dir>/<k>-<n>.jpg, index.json (file page, licence, author; for a wish: "want", "ranked", "candidates"
and each picture's "match"; for wiki: the item found) and sheet_<k>.jpg, a numbered contact sheet to choose from.
Commons pictures are taken in the standard thumbnail sizes (up to 1920 px wide; other sizes and originals are
rate-limited), pictures are downloaded a few at a time, and a Wikimedia site or a web search engine that keeps
answering 429 (too many requests) is not asked again in the same run.
A search with no usable picture has no sheet. A search that fails because its source did not answer (network,
Commons refusing, no web search engine answering) is recorded in index.json with "error" and no results, is tried
again on the next run, and makes the exit status 3; the other searches still run and index.json is written after
every search, so what was found can still be published.
A search that cannot work as it is written (19/11/2026) is not a failure: a wiki: name that names nothing, a url:
picture the site refuses, that is too small, is not a picture, or did not load in two tries. Running it again would
change nothing, and the list of searches is only ever appended to, so such a search used to fail every run of its
story. It is recorded with "unusable" (the reason) and no results, never tried again, and the exit status stays 0:
append another search instead. A url: picture that another search already found is kept all the same (it was asked
for by name, often as the larger copy), with "same_as" naming the pick it repeats.
"""
from concurrent.futures import ThreadPoolExecutor
from html import unescape
from io import BytesIO
import json
import os
from pathlib import Path
import re
import sys
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urljoin, urlsplit
from urllib.request import Request, urlopen, urlretrieve

from lxml import html

from PIL import Image, ImageDraw, ImageFont, ImageOps

from .custom import GEO, StoryError, read, search_parts
from .sources import fetch

COMMONS = "https://commons.wikimedia.org/w/api.php"
JAPAN_SEARCH = "https://jpsearch.go.jp/api/item/search/jps-cross"
# the rights Japan Search gives a record that allow use in a video, as the Commons licences kept (ALLOWED)
JPS_RIGHTS = {"pdm": "Public domain", "cc0": "CC0", "ccby": "CC BY", "ccbysa": "CC BY-SA"}
WIKIDATA = "https://www.wikidata.org/w/api.php"
LANGS = ("ja", "en")   # the Wikipedias wiki: reads, the channel's language first
HOSTS = {"commons.wikimedia.org", "upload.wikimedia.org", "thumb.wikimedia.org", "www.wikidata.org",
         *(f"{lang}.wikipedia.org" for lang in LANGS)}
ALLOWED = re.compile(r"^(public domain|pd|cc0|cc[- ]by(-sa)?[- ]?\d|cc[- ]by(-sa)?$)", re.I)
KEEP, WEB_KEEP, MIN_SIDE, LARGEST = 8, 20, 400, 2400
KEEP_WIKI, KEEP_GEO = 24, 12           # pictures kept by wiki: and geo:
DEEP, WEB_DEEP, WIKI_DEEP = 50, 45, 60 # candidates looked at when a wish ranks them (wiki: also without a wish)
YAHOO_PAGES = 3                        # result pages of 20 asked of Yahoo! JAPAN for one web: search
PAGE_KEEP, PAGE_DEEP = 20, 60          # pictures kept from one article (page:), and looked at on it
JPS_KEEP, JPS_DEEP, JPS_ASK = 12, 40, 100   # Japan Search (jps:): kept, looked at, records asked for at a time
STANDARD = (960, 1280, 1920)           # widths Commons serves freely (https://w.wiki/GHai); 1920 is enough here
SMALL = 330                            # the small version looked at for the ranking (a standard width too)
MATCH_MIN, UNFIT_MIN = 0.18, 0.21      # CLIP: under MATCH_MIN the picture does not show the wish; see Clip.UNFIT
MUSIC_KEEP, MUSIC_LIMIT = 4, 12_000_000
AUDIO = {"application/ogg": "ogg", "audio/ogg": "ogg", "audio/mpeg": "mp3", "audio/webm": "webm",
         "audio/x-flac": "flac", "audio/flac": "flac", "audio/wav": "wav", "audio/x-wav": "wav"}
BROWSER = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
STOCK = re.compile(r"gettyimages|alamy|shutterstock|istockphoto|dreamstime|123rf|depositphotos|pixta|aflo|"
                   r"stock\.adobe|agefotostock|bridgemanimages|pinimg|pinterest", re.I)
# page furniture of Wikipedia articles and maps that show no place: never a picture of the thing
ICON = re.compile(r"(?i)(commons-logo|wik\w*[- ]logo|qsicon|oojs|red pog|loca\w+ map|\bicon\b|flag of|disambig|"
                  r"padlock|question book|ambox|edit-ltr|symbol \w+ vote|speaker|nuvola|crystal clear|\.svg$)")

# page furniture of any site, by the name of the file: never a picture of the article (page:)
FURNITURE = re.compile(r"(?i)(logo|icon|sprite|banner|bnr|button|btn[_-]|avatar|spacer|blank|loading|placeholder|"
                       r"no[_-]?image|pixel|share|sns[_-]|twitter|facebook|hatena|line[_-]|\.svg$|\.gif$)")

GATE = threading.BoundedSemaphore(2)   # Wikimedia asks for few requests at a time, whatever runs in parallel here
REFUSED = set()   # Wikimedia hosts and web search engines that kept answering 429 in this run: not asked again


class Refused(RuntimeError):
    """A Wikimedia site keeps answering 429 (too many requests): the search fails and is tried again next run."""


class Unusable(RuntimeError):
    """The search cannot give a picture as it is written, and running it again changes nothing (a wiki: name that
    names nothing, a url: picture that is refused, too small or not a picture): recorded in index.json with
    "unusable", not tried again, and not a failure of the run. The remedy is another search, appended."""


class TooSmall(Unusable):
    """A web picture under MIN_SIDE: common among the candidates of a web: search, where it is passed over
    without a word."""


def retry_after(error):
    try:
        return float(error.headers.get("Retry-After") or 0)
    except (AttributeError, TypeError, ValueError):
        return 0.0


def get(url, tries=4, timeout=60, pause=10, limit=12_000_000):
    """Fetch from a Wikimedia site, waiting and trying again on rate limits (as long as the site asks, when it
    says), server errors and network errors. A site that still answers 429 after waiting, or asks for more than a
    minute, is not asked again in this run (Refused): hammering it only makes the refusal last."""
    host = urlsplit(url).hostname
    for attempt in range(tries):
        if host in REFUSED:
            raise Refused(f"{host} answered 429 (too many requests) in this run and is not asked again")
        wait = pause * (attempt + 1)
        try:
            with GATE:
                return fetch(url, HOSTS, limit=limit, timeout=timeout)
        except HTTPError as error:
            last = attempt == tries - 1
            asked = retry_after(error) if error.code == 429 else 0
            if error.code == 429 and tries > 1 and (last or asked > 60):
                REFUSED.add(host)
                print(f"  {host} answers 429 (too many requests): not asked again in this run", flush=True)
                raise Refused(f"{host} answers 429 (too many requests)") from None
            if error.code not in (429, 500, 502, 503, 504) or last:
                raise
            wait = max(wait, asked)
        except (URLError, TimeoutError, ConnectionError) as error:
            if attempt == tries - 1:
                raise
            print(f"  network error, trying again: {error}")
        time.sleep(wait)


def api(base=COMMONS, tries=4, timeout=60, **params):
    return json.loads(get(base + "?" + urlencode({"format": "json", **params}), tries=tries, timeout=timeout))


def web_get(url, referer=None, limit=12_000_000, timeout=30):
    """Fetch any public http(s) address the way a browser does (web searches and their pictures)."""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname or parts.username or parts.password \
            or parts.hostname == "localhost" or re.fullmatch(r"[0-9.:\[\]]+", parts.hostname):
        raise ValueError(f"Unsupported URL: {url}")
    headers = {"User-Agent": BROWSER, "Accept-Language": "ja,en;q=0.8"}
    if referer:
        headers["Referer"] = referer
    with urlopen(Request(url, headers=headers), timeout=timeout) as response:
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
    """Yahoo! JAPAN image search: the first YAHOO_PAGES pages of 20 (19/11/2026; one page before). Each result
    comes with what Yahoo knows of it: the size of the picture, and the address of Yahoo's own full-size copy,
    used when the picture's own site refuses to give it (see web_load)."""
    seen = set()

    def walk(node):
        if isinstance(node, dict):
            original = node.get("original")
            if isinstance(original, dict) and isinstance(original.get("url"), str):
                copy = node.get("main") if isinstance(node.get("main"), dict) else {}
                more = {"mirror": copy.get("url") if not copy.get("isNotFound") else None,
                        "width": original.get("width"), "height": original.get("height")}
                yield (original["url"], node.get("refererUrl") or node.get("url") or original["url"],
                       plain(node.get("title") or ""), more)
                return
            for value in node.values():
                yield from walk(value)
        elif isinstance(node, list):
            for value in node:
                yield from walk(value)

    for number in range(YAHOO_PAGES):
        params = {"p": query, "ei": "UTF-8", **({"b": number * 20 + 1} if number else {})}
        try:
            page = web_get("https://search.yahoo.co.jp/image/search?" + urlencode(params))
        except (OSError, ValueError) as error:
            if not number:
                raise
            print(f"  yahoo: page {number + 1} not read ({type(error).__name__}: {error})", flush=True)
            return   # the first page is enough to go on with
        if not number:
            DEBUG["yahoo"] = page
        match = re.search(rb'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', page, re.S)
        fresh = [result for result in walk(json.loads(match[1]))
                 if result[0] not in seen and not seen.add(result[0])] if match else []
        yield from fresh   # the page data holds every result twice: each address once
        if not fresh:
            return
        if number + 1 < YAHOO_PAGES:
            time.sleep(1)


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
    """Candidates (picture address, page address, title[, what the engine knows: "mirror", "width", "height"]) of
    a web image search, from the first engine that gives any, stock sites left out."""
    results = []
    DEBUG.clear()
    for engine in (yahoo, bing, duckduckgo):   # Yahoo! JAPAN first: Bing and DuckDuckGo give a program nothing
        if engine.__name__ in REFUSED:   # it answered 429 earlier in this run: asking again only prolongs it
            continue
        try:
            results = list(engine(query))
        except (OSError, ValueError) as error:
            print(f"  {engine.__name__} failed: {type(error).__name__}: {error}", flush=True)
            if isinstance(error, HTTPError) and error.code == 429:
                REFUSED.add(engine.__name__)
                print(f"  {engine.__name__} answers 429 (too many requests): not asked again in this run", flush=True)
        print(f"  {engine.__name__}: {len(results)} results", flush=True)
        if results:
            break
    if not results:
        if out:
            for name, page in DEBUG.items():
                (out / f"debug_{name}.html").write_bytes(page[:400_000])
        raise RuntimeError("no web image search answered")
    return [result for result in results if not STOCK.search(result[0] + " " + result[1])]


def plain(value):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", value or "")).strip()


def fingerprint(image):
    grey = image.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
    pixels = list(grey.tobytes())
    return sum(1 << i for i in range(64) if pixels[i // 8 * 9 + i % 8] > pixels[i // 8 * 9 + i % 8 + 1])


def shot(picture, mark, small=False):
    """A loaded picture as it will be kept: JPEG bytes, size, fingerprint (and a small copy for the ranking)."""
    data = BytesIO()
    picture.save(data, "JPEG", quality=90)
    made = {"data": data.getvalue(), "size": picture.size, "mark": mark}
    if small:
        made["small"] = picture.copy()
        made["small"].thumbnail((448, 448))
    return made


def upright(original):
    """The picture turned the way its camera held it (a phone photo is often stored lying on its side, with a
    note saying so; saving it again here would lose the note and leave it lying)."""
    try:
        return ImageOps.exif_transpose(original)
    except Exception:   # an unreadable note: the picture as stored
        return original


def web_picture(address, referer=None):
    """The picture at a web address. Raises Unusable when the address can never give one (the site refuses it or
    has no such file, the file is not a picture), and the error itself when the site only did not answer (a
    timeout, a server error), which another try may change."""
    try:
        data = web_get(address, referer=referer, timeout=20)
    except HTTPError as error:
        if 400 <= error.code < 500 and error.code not in (408, 425, 429):   # refused or gone, not "try later"
            raise Unusable(f"HTTPError: HTTP Error {error.code}: {error.reason}") from None
        raise
    except ValueError as error:   # not a public http(s) address, or a file over the size limit
        raise Unusable(f"ValueError: {error}") from None
    try:
        with Image.open(BytesIO(data)) as original:
            original.draft("RGB", (LARGEST, LARGEST))
            return upright(original).convert("RGB")
    except Exception as error:   # the address answered, with something that is not a readable picture
        raise Unusable(f"{type(error).__name__}: {error}") from None


def web_load(entry, small=False):
    """The picture of a web candidate as it will be kept; raises as web_picture does, and TooSmall for a picture
    under MIN_SIDE (not even loaded when the search engine already gave its size). A picture its own site does not
    give (hotlink refused, a page instead of a picture, no answer) is taken from the search engine's copy of it
    when there is one ("mirror", 19/11/2026): the same picture in the same size, still credited to its site."""
    hint = entry.get("hint")
    if hint and 0 < min(hint) < MIN_SIDE:
        raise TooSmall(f"the picture is only {hint[0]} x {hint[1]} px (the smaller side must be {MIN_SIDE} or more)")
    try:
        picture = web_picture(entry["image"], entry["page"])
    except Exception as error:
        if not entry.get("mirror"):
            raise
        try:
            picture = web_picture(entry["mirror"])
        except Exception:
            raise error from None   # the picture's own site says why
    if min(picture.size) < MIN_SIDE:
        raise TooSmall(f"the picture is only {picture.width} x {picture.height} px (the smaller side must be "
                       f"{MIN_SIDE} or more)")
    mark = fingerprint(picture)
    picture.thumbnail((LARGEST, LARGEST))
    return shot(picture, mark, small)


def web_shot(entry, small=False):
    """The picture of a web candidate, or None for a dead link, an odd file or a small picture."""
    try:
        return web_load(entry, small)
    except TooSmall:
        return None
    except Unusable as error:   # a dead link or an odd file: skip it
        print(f"  skipped {entry['image'][:120]}: {error}")
    except Exception as error:
        print(f"  skipped {entry['image'][:120]}: {type(error).__name__}: {error}")
    return None


def url_shot(entry):
    """The one picture of a url: search, or Unusable with the reason. An address that does not answer is tried
    twice and then given up for good too: one address that keeps failing would fail every run of its story, and
    the same url: can always be appended again as a new search."""
    for attempt in (1, 2):
        try:
            return web_load(entry)
        except Unusable:
            raise
        except Exception as error:
            last = f"{type(error).__name__}: {error}"
            if attempt == 1:
                print(f"  url: {last}; trying once more")
                time.sleep(5)
    raise Unusable(f"the picture did not load in two tries ({last})")


def commons_shot(entry):
    """The picture of a Commons file in its standard size, or None when it cannot be had (short tries: an
    address that does not answer costs about a minute at most, not five)."""
    try:
        with Image.open(BytesIO(get(entry["thumb"], tries=3, timeout=20, pause=5))) as original:
            picture = original.convert("RGB")
    except (OSError, ValueError) as error:
        print(f"  skipped {entry['title']}: {error}")
        return None
    return shot(picture, fingerprint(picture))


def commons_small(entry):
    """The small version of a Commons file, for the ranking."""
    try:
        with Image.open(BytesIO(get(entry["preview"], tries=2, timeout=15, pause=5))) as original:
            return original.convert("RGB")
    except (OSError, ValueError):
        return None


def batches(entries, load, workers, size=6):
    """(entry, load(entry)) in the order of the entries, loading a few at a time; nothing more is loaded once the
    caller has enough."""
    for start in range(0, len(entries), size):
        chunk = entries[start:start + size]
        with ThreadPoolExecutor(workers) as pool:
            loaded = list(pool.map(load, chunk))
        yield from zip(chunk, loaded)


def twin(mark, seen):
    """The file name of a picture kept before that is the same picture (nearly the same fingerprint), or None."""
    return next((name for name, other in seen.items() if bin(mark ^ other).count("1") <= 10), None)


def keep(entries, load, k, out, seen, limit, workers=3, repeats=False):
    """Save the first `limit` pictures of the entries, in their order, that load and were not kept before (by this
    or an earlier search; `repeats` keeps those too); returns their records for index.json."""
    kept = []
    for entry, made in batches(entries, load, workers):
        if len(kept) == limit:
            break
        if made is None or (not repeats and twin(made["mark"], seen)):
            continue
        record = {key: value for key, value in entry.items()
                  if key not in ("thumb", "preview", "shot", "mirror", "hint")}
        if "image" in record:   # a web picture: the size of the file kept (Commons: the size of the original)
            record["width"], record["height"] = made["size"]
        record["file"] = f"{k}-{len(kept) + 1}.jpg"
        seen[record["file"]] = made["mark"]
        (out / record["file"]).write_bytes(made["data"])
        kept.append(record)
    return kept


class Clip:
    """Scores how well a picture fits a text (open_clip ViT-B/32, weights from its GitHub release, on the CPU).
    Optional: without torch and open_clip, or with FIND_RANK=0, ready() is False and nothing is ranked."""
    URL = ("https://github.com/mlfoundations/open_clip/releases/download/v0.2-weights/"
           "vit_b_32-quickgelu-laion400m_e32-46683a32.pt")
    # what a video for a general audience must not show by accident (a web search brings everything): pictures
    # that look like one of these (UNFIT_MIN and more; ordinary pictures stay under 0.18) are left out when ranking
    UNFIT = ("a nude person", "a woman in lingerie or underwear", "an erotic photo")
    model = None
    failed = False
    unfit = None

    @classmethod
    def ready(cls):
        if cls.model is None and not cls.failed:
            try:
                if os.environ.get("FIND_RANK", "1") == "0":
                    raise RuntimeError("FIND_RANK=0")
                import open_clip
                import torch
                path = Path(os.environ.get("CLIP_MODEL")
                            or Path.home() / ".cache/find-images/vit_b_32-quickgelu-laion400m_e32.pt")
                if not path.exists():
                    path.parent.mkdir(parents=True, exist_ok=True)
                    part = path.with_name(path.name + ".part")
                    urlretrieve(cls.URL, part)
                    part.replace(path)
                model, _, cls.pre = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained=str(path))
                cls.tokens, cls.torch = open_clip.get_tokenizer("ViT-B-32-quickgelu"), torch
                cls.model = model.eval()
            except Exception as error:   # no torch, no weights, no memory: the search goes on without ranking
                cls.failed = True
                print(f"ranking off, wishes are ignored ({type(error).__name__}: {str(error)[:90]})", flush=True)
        return cls.model is not None

    @classmethod
    def scores(cls, images, text):
        """For every picture: how well it fits the text, and how much it looks like something not to show."""
        torch = cls.torch
        with torch.no_grad():
            seen = torch.cat([cls.model.encode_image(torch.stack([cls.pre(image) for image in images[at:at + 32]]))
                              for at in range(0, len(images), 32)])
            seen /= seen.norm(dim=-1, keepdim=True)
            wish = cls.model.encode_text(cls.tokens([text, "a photo of " + text]))
            wish /= wish.norm(dim=-1, keepdim=True)
            if cls.unfit is None:
                cls.unfit = cls.model.encode_text(cls.tokens(list(cls.UNFIT)))
                cls.unfit /= cls.unfit.norm(dim=-1, keepdim=True)
            return (seen @ wish.T).max(dim=1).values.tolist(), (seen @ cls.unfit.T).max(dim=1).values.tolist()


def ranked(entries, wish, small, workers=3):
    """The entries that show the wish, best first: CLIP scores each one's small picture (small(entry) → image or
    None) against the wish; the order of the source counts a little (0.004 a place: it decides between pictures
    CLIP finds alike, as for a name it does not know). Sets "match". Entries under MATCH_MIN and pictures that look
    unsuitable (Clip.UNFIT) are left out; entries whose small picture could not be loaded come last, unscored.
    Returns (entries, number left out)."""
    with ThreadPoolExecutor(workers) as pool:
        images = list(pool.map(small, entries))
    scored = [(place, entry, image) for place, (entry, image) in enumerate(zip(entries, images)) if image is not None]
    if not scored:
        return entries, 0
    fit, unfit = Clip.scores([image for _, _, image in scored], wish)
    good = []
    for (place, entry, _), match, bad in zip(scored, fit, unfit):
        entry["match"] = round(match, 3)
        if match >= MATCH_MIN and bad < UNFIT_MIN:
            good.append((-(match - 0.004 * place), place, entry))
    unseen = [entry for entry, image in zip(entries, images) if image is None]
    return [entry for _, _, entry in sorted(good, key=lambda item: item[:2])] + unseen, len(scored) - len(good)


# the name of a Commons thumbnail: 330px-Name.jpg, and for a scan lossy-page1-330px-Name.tif.jpg
THUMB = re.compile(r"/((?:lossy-|lossless-)?(?:page\d+-)?)\d+px-([^/]+)$")
INFO = {"action": "query", "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime", "iiurlwidth": SMALL}


def sized(info):
    """The address of the picture to keep: the largest standard width up to 1920 px that the file has (Commons
    serves these freely; other sizes and originals are rate-limited). A file under 960 px is taken whole."""
    small = (info.get("thumburl") or "").split("?")[0]
    widths = [width for width in STANDARD if width <= info.get("width", 0)]
    if widths and THUMB.search(small):   # a real thumbnail: the same file in another standard width
        return THUMB.sub(lambda match: f"/{match[1]}{widths[-1]}px-{match[2]}", small)
    return info["url"].split("?")[0]


def commons_entries(pages, source=None):
    """The usable pictures among the file pages of a Commons answer asked with INFO, in the order given: JPEG or
    PNG, a licence that allows use in a video, not small."""
    entries = []
    for page in pages:
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata") or {}
        licence = plain(meta.get("LicenseShortName", {}).get("value"))
        if info.get("mime") not in ("image/jpeg", "image/png") or not ALLOWED.search(licence):
            continue
        if min(info.get("width", 0), info.get("height", 0)) < MIN_SIDE:
            continue
        entry = {"title": page["title"], "page": info["descriptionurl"], "thumb": sized(info),
                 "preview": (info.get("thumburl") or info["url"]).split("?")[0],
                 "width": info["width"], "height": info["height"], "license": licence,
                 "license_url": plain(meta.get("LicenseUrl", {}).get("value")),
                 "artist": plain(meta.get("Artist", {}).get("value"))[:120],
                 "description": plain(meta.get("ImageDescription", {}).get("value"))[:300]}
        if source:
            entry["source"] = source
        entries.append(entry)
    return entries


def search(query, limit=30):
    """Commons full-text search, best match first."""
    data = api(generator="search", gsrsearch=query, gsrnamespace=6, gsrlimit=limit, **INFO)
    pages = sorted(data.get("query", {}).get("pages", {}).values(), key=lambda page: page.get("index", 0))
    return commons_entries(pages)


def chunks(titles, most=50, length=3000):
    """The titles in groups one request can carry: 50 at most, and a short enough address (Japanese file names
    take nine characters a letter in an address)."""
    chunk, size = [], 0
    for title in titles:
        cost = len(quote(title)) + 3
        if chunk and (len(chunk) == most or size + cost > length):
            yield chunk
            chunk, size = [], 0
        chunk.append(title)
        size += cost
    if chunk:
        yield chunk


def commons_files(titles, source, enough=WIKI_DEEP):
    """The usable pictures among a list of Commons file titles, in that order, up to 50 titles a request, until
    there are enough. A file that is not on Commons (kept on one Wikipedia only: not free) does not come back."""
    entries = []
    for chunk in chunks(titles):
        if len(entries) >= enough:
            break
        place = {title.replace("_", " "): number for number, title in enumerate(chunk)}
        pages = api(titles="|".join(chunk), **INFO).get("query", {}).get("pages", {}).values()
        entries += commons_entries(sorted(pages, key=lambda page: place.get(page.get("title", ""), len(chunk))), source)
    return entries


def geo(words, limit=50):
    """Commons photos taken around a point, nearest first: "<lat>,<lon> [<metres>]" (500 m when not given, 10 km
    at most). Of a series of photos that differ in their numbers only (survey tiles, a photo walk), one is taken."""
    match = GEO.match(words)
    if not match:
        raise ValueError(f'geo: expects "<lat>,<lon> [<metres>]", got {words!r}')
    radius = min(10000, max(10, int(match[3] or 500)))
    data = api(action="query", list="geosearch", gscoord=f"{match[1]}|{match[2]}", gsradius=radius, gsnamespace=6,
               gslimit=limit * 2)
    titles, series = [], set()
    for place in data.get("query", {}).get("geosearch", []):
        key = re.sub(r"\d+", "#", place["title"])
        if key not in series:
            series.add(key)
            titles.append(place["title"])
    return commons_files(titles, "commons/geo", limit)


def wiki(name):
    """Every picture about one thing, through its Wikidata item; returns (entries, the item found). Most to the
    point first: the item's own pictures, the pictures of its Wikipedia articles (the lead picture first), the
    files of its Commons category and sub-categories, then photos taken at its coordinates."""
    item = name if re.fullmatch(r"Q\d+", name) else None
    silent = []   # the Wikipedias that did not answer: without them "no such name" is not certain
    for lang in LANGS:   # the exact title of a Wikipedia article first: "信子" alone is many people, an article one
        if item:
            break
        try:   # one short try: a Wikipedia that does not answer must not stop the search
            pages = api(f"https://{lang}.wikipedia.org/w/api.php", tries=1, timeout=15, action="query", titles=name,
                        prop="pageprops", redirects=1).get("query", {}).get("pages", {}).values()
        except (OSError, ValueError, Refused) as error:
            print(f"  wiki: {lang}.wikipedia.org did not answer ({str(error)[:80]})")
            silent.append(f"{lang}.wikipedia.org")
            continue
        for page in pages:
            props = page.get("pageprops") or {}
            if props.get("wikibase_item") and "disambiguation" not in props:
                item = props["wikibase_item"]
    for lang in LANGS:   # else the Wikidata item called so
        if item:
            break
        hits = api(WIKIDATA, action="wbsearchentities", search=name, language=lang, uselang=lang, type="item",
                   limit=3).get("search", [])
        if hits:
            item = hits[0]["id"]
    if not item:
        reason = (f"wiki: no Wikidata item named {name!r} (try the title of its Wikipedia article, its "
                  "Wikidata item Q…, or a web: search)")
        if silent:   # an article of that title may exist where nobody answered: a failure, tried again next run
            raise RuntimeError(f"{reason}; {' and '.join(silent)} did not answer")
        raise Unusable(reason)
    entity = api(WIKIDATA, action="wbgetentities", ids=item, props="claims|sitelinks|labels|descriptions",
                 languages="|".join(LANGS))["entities"][item]
    claims, links = entity.get("claims") or {}, entity.get("sitelinks") or {}

    def values(prop):
        return [claim["mainsnak"]["datavalue"]["value"] for claim in claims.get(prop, [])
                if claim.get("mainsnak", {}).get("datavalue")]

    def first(texts):
        return next((texts[lang]["value"] for lang in LANGS if lang in texts), "")

    coord = next((value for value in values("P625") if isinstance(value, dict)), None)
    about = {"id": item, "label": first(entity.get("labels") or {}),
             "description": first(entity.get("descriptions") or {})}
    if coord:
        about["coord"] = [round(coord["latitude"], 5), round(coord["longitude"], 5)]
    # the item's own pictures: image, image of grave, of the interior, aerial view, nighttime view
    own = ["File:" + value for prop in ("P18", "P1442", "P5775", "P8592", "P3451") for value in values(prop)
           if isinstance(value, str)]
    article = []
    for lang in LANGS:
        if f"{lang}wiki" not in links:
            continue
        try:
            pages = api(f"https://{lang}.wikipedia.org/w/api.php", tries=1, timeout=15, action="query",
                        titles=links[f"{lang}wiki"]["title"], prop="images|pageimages", imlimit=500, piprop="name",
                        redirects=1).get("query", {}).get("pages", {}).values()
        except (OSError, ValueError, Refused) as error:
            print(f"  wiki: {lang}.wikipedia.org did not answer ({str(error)[:80]})")
            continue
        for page in pages:   # the article's lead picture, then the others (the namespace is ファイル: in Japanese)
            lead = ["File:" + page["pageimage"]] if page.get("pageimage") else []
            article += lead + ["File:" + image["title"].split(":", 1)[1] for image in page.get("images", [])]
    category = next(iter(values("P373")), "") or links.get("commonswiki", {}).get("title", "").partition("Category:")[2]

    def members(of, kind, limit):
        data = api(action="query", list="categorymembers", cmtitle="Category:" + of, cmtype=kind, cmlimit=limit)
        return [member["title"] for member in data.get("query", {}).get("categorymembers", [])]

    entries, seen = [], set()

    def add(titles, source):
        titles = [title for title in dict.fromkeys(title.replace("_", " ") for title in titles)
                  if title not in seen and not ICON.search(title)]
        seen.update(titles)
        entries.extend(commons_files(titles, source, WIKI_DEEP - len(entries)))

    add(own, "commons/wiki")
    add(article, "commons/wiki")
    if category and len(entries) < WIKI_DEEP:
        add(members(category, "file", 100), "commons/category")
        for sub in members(category, "subcat", 12) if len(entries) < WIKI_DEEP else []:
            if len(entries) >= WIKI_DEEP:
                break
            add(members(sub.partition(":")[2], "file", 50), "commons/category")
    if coord and len(entries) < WIKI_DEEP:   # the place itself, whatever the photos are called
        try:
            entries += [entry for entry in geo(f"{coord['latitude']},{coord['longitude']} 400", 20)
                        if entry["title"] not in seen]
        except (OSError, ValueError) as error:
            print(f"  wiki: no photos around the place ({str(error)[:80]})")
    return entries[:WIKI_DEEP], about


def sheet(entries, out, path):
    face = ImageFont.load_default(size=17)
    board = Image.new("RGB", (4 * 380, -(-len(entries) // 4) * 400), "#0a0a0c")
    for index, entry in enumerate(entries):
        with Image.open(out / entry["file"]) as picture:
            picture.thumbnail((360, 360))
            board.paste(picture, (index % 4 * 380 + (380 - picture.width) // 2, index // 4 * 400 + 10))
        where = entry["license"].replace("Public domain", "PD") or entry.get("artist", "")
        fit = f"~{entry['match']:.2f}  " if "match" in entry else ""   # how well it shows the wish (no "≈" in the font)
        label = f"#{index + 1}  {fit}{entry['width']}x{entry['height']}  {where}"
        ImageDraw.Draw(board).text((index % 4 * 380 + 10, index // 4 * 400 + 374), label[:40], fill="#ffd25a", font=face)
    board.save(path, quality=85)


def save_index(index, path):
    index.sort(key=lambda group: group["k"])
    path.write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def music_search(query):
    """Recordings on Commons with a licence that allows use, smallest first among the best matches."""
    params = urlencode({
        "action": "query", "format": "json", "generator": "search", "gsrsearch": f"{query} filetype:audio",
        "gsrnamespace": 6, "gsrlimit": 20, "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime",
    })
    data = json.loads(get(f"https://commons.wikimedia.org/w/api.php?{params}"))
    pages = sorted(data.get("query", {}).get("pages", {}).values(), key=lambda page: page.get("index", 0))
    for page in pages:
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata") or {}
        licence = plain(meta.get("LicenseShortName", {}).get("value"))
        if info.get("mime") not in AUDIO or not ALLOWED.search(licence) or info.get("size", 0) > MUSIC_LIMIT:
            continue
        yield {"title": page["title"], "page": info["descriptionurl"], "url": info["url"],
               "ext": AUDIO[info["mime"]], "size": info.get("size", 0), "license": licence,
               "license_url": plain(meta.get("LicenseUrl", {}).get("value")),
               "artist": plain(meta.get("Artist", {}).get("value"))[:120],
               "description": plain(meta.get("ImageDescription", {}).get("value"))[:300]}


def seconds_of(path):
    """Length of an audio file in seconds (ffprobe), or None."""
    try:
        import subprocess
        result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                 str(path)], capture_output=True, text=True, timeout=30, check=True)
        return round(float(result.stdout.strip()), 1)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def music_find(query, k, out):
    kept = []
    for result in music_search(query):
        if len(kept) == MUSIC_KEEP:
            break
        try:
            data = get(result.pop("url"))
        except (OSError, ValueError) as error:
            print(f"  skipped {result['title']}: {error}")
            continue
        finally:
            time.sleep(1)
        result["file"] = f"{k}-{len(kept) + 1}.{result.pop('ext')}"
        (out / result["file"]).write_bytes(data)
        result["seconds"] = seconds_of(out / result["file"])
        kept.append(result)
    return kept


REPO = Path(__file__).resolve().parent.parent


def file_find(path, k, out):
    """One picture kept in the repository under stories/media/."""
    source = (REPO / path).resolve()
    if not str(source).startswith(str((REPO / "stories" / "media").resolve()) + "/") or not source.is_file():
        raise ValueError(f"file: must name a picture under stories/media/, got {path!r}")
    with Image.open(source) as original:
        picture = original.convert("RGB")
    picture.thumbnail((LARGEST, LARGEST))
    entry = {"title": source.name, "page": "", "width": picture.width, "height": picture.height, "license": "",
             "license_url": "", "artist": "元動画", "description": f"from the source video: {path}",
             "file": f"{k}-1.jpg"}
    picture.save(out / entry["file"], quality=93)
    return [entry]


def web_entries(candidates):
    """The candidates of a web search as entries. What the engine knows of a picture rides along and is not
    recorded: "mirror" (the engine's own copy of it) and "hint" (the size the engine gives)."""
    entries = []
    for image, page, title, *more in candidates:
        entry = {"title": title or image.rsplit("/", 1)[-1][:100], "page": page, "image": image, "width": 0,
                 "height": 0, "license": "", "license_url": "", "artist": site(page), "description": title}
        known = more[0] if more else {}
        if known.get("mirror"):
            entry["mirror"] = known["mirror"]
        if isinstance(known.get("width"), int) and isinstance(known.get("height"), int):
            entry["hint"] = (known["width"], known["height"])
        entry.update({key: known[key] for key in ("license", "artist") if known.get(key)})   # an archive says
        entries.append(entry)
    return entries


def largest(srcset):
    """The largest picture of a srcset ("a.jpg 320w, b.jpg 1280w" → "b.jpg"); the last one when none says."""
    best, size = "", -1.0
    for part in re.split(r",\s+", srcset.strip()):
        address, _, mark = part.strip().partition(" ")
        try:
            width = float(mark.strip()[:-1] or 0)
        except ValueError:
            width = 0.0
        if address and width >= size:
            best, size = address, width
    return best


def larger(address, width=1600):
    """A IIIF picture address asked in a larger size ("…/full/256,/0/default.jpg" → "…/full/1600,/0/default.jpg":
    the archives give Japan Search a small preview of a large scan); any other address as it is."""
    return re.sub(r"/(full|square)/(?:!?\d*,\d*|max|full|pct:[\d.]+)/(\d+)/(default|color|native)\.(jpe?g|png)$",
                  rf"/\1/{width},/\2/\3.\4", address)


def japan_search(words):
    """Japan Search (jpsearch.go.jp, jps:, 19/11/2026): the shared catalogue of Japan's archives, libraries and
    museums (the National Diet Library, ColBase of the national museums, the Tokyo museums, university
    collections…), old prints, paintings, photographs, objects. Returns web candidates for the records that carry
    a picture and rights that allow use (public domain, CC0, CC BY, CC BY-SA), in the order of the catalogue; each
    is credited to the site that holds it, with its licence. A book or a paper is left out: its picture is the scan
    of its cover or first page (most of what a person's name brings from the National Diet Library). Tried on
    GitHub on 19/11/2026: the pictures of ColBase (404, the catalogue's addresses are out of date and its pages are
    built by script) and of museumcollection.tokyo (403) cannot be had; those records are passed over."""
    found, seen = [], set()
    for start in (0, JPS_ASK):
        data = json.loads(web_get(JAPAN_SEARCH + "?" + urlencode({"keyword": words, "size": JPS_ASK, "from": start}),
                                  timeout=40))
        records = data.get("list") or []
        for record in records:
            common = record.get("common") or {}
            licence = JPS_RIGHTS.get(common.get("contentsRightsType"))

            def addresses(key):
                value = common.get(key) or []
                return [item for item in ([value] if isinstance(value, str) else value) if isinstance(item, str)]
            full = [item for item in addresses("contentsUrl")
                    if re.search(r"(?i)\.(jpe?g|png|webp)$", urlsplit(item).path)]
            small = addresses("thumbnailUrl")
            if not licence or not (full or small):
                continue
            image = full[0] if full else larger(small[0])
            picture = common.get("contentsType") == "image"
            if image in seen or (not picture and not full and image != small[0]):   # the page scan of a book
                continue
            seen.add(image)
            page = common.get("linkUrl") or f"https://jpsearch.go.jp/item/{record.get('id', '')}"
            more = {"mirror": small[0] if small and small[0] != image else None, "license": licence,
                    "artist": site(page) or "jpsearch.go.jp", "picture": picture}
            found.append((image, page, plain(common.get("title") or ""), more))
        if len(found) >= JPS_DEEP * 2 or len(records) < JPS_ASK or start + JPS_ASK >= (data.get("hit") or 0):
            break
        time.sleep(1)
    # records catalogued as pictures (paintings, prints, photographs, objects) before the others; the order of
    # the catalogue within each
    found.sort(key=lambda candidate: not candidate[3]["picture"])
    return found[:JPS_DEEP]


def page_text(raw):
    """The text of a page: in the charset it declares, else UTF-8, else the older Japanese ones."""
    declared = re.search(rb"""(?i)charset=["']?\s*([\w-]+)""", raw[:4000])
    for name in ([declared[1].decode("ascii", "replace")] if declared else []) + ["utf-8", "cp932", "euc_jp"]:
        try:
            return raw.decode(name)
        except (LookupError, UnicodeDecodeError):
            continue
    return raw.decode("utf-8", "replace")


def page_pictures(address):
    """The pictures an article shows (page:, 19/11/2026), as web candidates (picture address, page address,
    title): the picture the page names as its own first (og:image), then the pictures in the order of the page,
    each in its largest version (a link to the full picture around it, srcset, the attributes of lazy loading).
    The pictures of the page's header, footer, menus and side columns are left out, and page furniture by the name
    of its file; small pictures fall out when loaded. A page the site refuses cannot be used (Unusable)."""
    try:
        raw = web_get(address, limit=8_000_000)
    except HTTPError as error:
        if 400 <= error.code < 500 and error.code not in (408, 425, 429):
            raise Unusable(f"page: the site answers {error.code} ({error.reason}) for {address}") from None
        raise
    except ValueError as error:
        raise Unusable(f"page: {error}") from None
    try:
        tree = html.fromstring(re.sub(r"^\s*<\?xml[^>]*\?>", "", page_text(raw)))
    except Exception as error:
        raise Unusable(f"page: {address} is not a page a program can read ({type(error).__name__})") from None
    title = plain(tree.findtext(".//title") or "")
    found, seen = [], set()

    def add(link, text=""):
        link = urljoin(address, (link or "").strip())
        if link.startswith("http") and link not in seen and not FURNITURE.search(urlsplit(link).path):
            seen.add(link)
            found.append((link, address, plain(text) or title))
    for own in tree.xpath('//meta[@property="og:image" or @property="og:image:secure_url" or @name="twitter:image" '
                          'or @name="twitter:image:src"]/@content'):
        add(own)
    for node in tree.iter("img", "source"):
        parent = node.getparent()
        if node.tag == "source" and (parent is None or parent.tag != "picture"):
            continue
        if next(node.iterancestors("header", "footer", "nav", "aside"), None) is not None:
            continue
        text = node.get("alt") or ""
        around = next(node.iterancestors("a"), None)
        if around is not None and re.search(r"(?i)\.(jpe?g|png|webp)(\?|$)", around.get("href") or ""):
            add(around.get("href"), text)   # the picture links to its full version
        add(largest(node.get("srcset") or node.get("data-srcset") or "") or node.get("data-src")
            or node.get("data-original") or node.get("data-lazy-src") or (node.get("src") if node.tag == "img" else ""),
            text)
    return found[:PAGE_DEEP]


def find(query, k, out, seen):
    """The pictures of one search, saved as <k>-<n>.jpg: (their records, more keys for the search's group in
    index.json — the wish and whether it ranked, the Wikidata item of a wiki: search)."""
    kind, words, wish = search_parts(query)
    if kind == "file":
        return file_find(words, k, out), {}
    if kind == "music":
        return music_find(words, k, out), {}
    if kind == "url":
        image, _, page = words.partition(" ")
        entry = web_entries([(image, page.strip() or image, "")])[0]
        try:
            made = url_shot(entry)
        except Unusable as error:
            raise Unusable(f"url: could not use the picture {image}: {error}") from None
        same = twin(made["mark"], seen)   # found by another search too: kept all the same, it was asked for by name
        return (keep([entry], lambda entry: made, k, out, seen, 1, repeats=True),
                {"same_as": Path(same).stem} if same else {})
    rank = bool(wish) and Clip.ready()
    notes = {"want": wish, "ranked": rank} if wish else {}
    left_out = 0
    if kind in ("web", "page", "jps"):
        if kind == "web":
            entries, limit = web_entries(web_search(words, out)), WEB_KEEP
        elif kind == "page":
            entries, limit = web_entries(page_pictures(words)), PAGE_KEEP
        else:
            entries, limit = web_entries(japan_search(words)), JPS_KEEP
        if rank:   # a web picture has no small version: the candidates are loaded, then scored
            entries = entries[:WEB_DEEP]
            for entry, made in batches(entries, lambda entry: web_shot(entry, small=True), 6):
                entry["shot"] = made
            entries = [entry for entry in entries if entry["shot"]]
            notes["candidates"] = len(entries)
            entries, left_out = ranked(entries, wish, lambda entry: entry["shot"].pop("small"))
        kept = keep(entries, (lambda entry: entry["shot"]) if rank else web_shot, k, out, seen, limit, 6)
    else:
        if kind == "wiki":
            (entries, notes["wikidata"]), limit = wiki(words), KEEP_WIKI
        elif kind == "geo":
            entries, limit = geo(words), KEEP_GEO
        else:
            entries, limit = search(words, DEEP if rank else 30), KEEP
        if rank:
            notes["candidates"] = len(entries)
            entries, left_out = ranked(entries, wish, commons_small)
        kept = keep(entries, commons_shot, k, out, seen, limit)
    if rank:
        notes["left_out"] = left_out
    return kept, notes


def clear(out, k, seen):
    for old in [*out.glob(f"{k}-*.*"), out / f"sheet_{k}.jpg"]:
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
            group["results"], notes = find(query, k, out, seen)
        except Unusable as error:   # the search as written can never work: noted, not tried again, no failure
            clear(out, k, seen)
            group["unusable"] = str(error)
            print(f"{k}. {query}: UNUSABLE ({error})")
        except Exception as error:   # one failed search must not lose the others
            clear(out, k, seen)
            group["error"] = f"{type(error).__name__}: {error}"
            failed.append(k)
            print(f"{k}. {query}: FAILED ({group['error']})")
        else:
            group.update(notes)
            if group["results"] and not query.startswith("music:"):
                sheet(group["results"], out, out / f"sheet_{k}.jpg")
            about = notes.get("wikidata")
            print(f"{k}. {query}: {len(group['results'])} pictures" + ("" if group["results"] else " (no sheet)")
                  + (f" = {about['id']} {about['label']}: {about['description']}" if about else "")
                  + (f" (the same picture as {notes['same_as']})" if notes.get("same_as") else "")
                  + (f" (the best of {notes['candidates']} for the wish, {notes['left_out']} left out)"
                     if notes.get("ranked") else " (wish ignored: ranking off)" if "ranked" in notes else ""))
        index.append(group)
        save_index(index, index_path)
        if not query.startswith("file:"):   # a picture of the repository asks nobody: no pause
            time.sleep(2)
    save_index(index, index_path)
    unusable = [group["k"] for group in index if group.get("unusable")]
    empty = [group["k"] for group in index
             if not group["results"] and not group.get("error") and not group.get("unusable")]
    if empty:
        print(f"Searches with no picture (no sheet): {', '.join(map(str, empty))}")
    if unusable:
        print("Searches that cannot work as written (not tried again; append another search): "
              f"{', '.join(map(str, unusable))}")
    if failed:
        print(f"Searches that failed (tried again next run): {', '.join(map(str, failed))}")
        sys.exit(3)


if __name__ == "__main__":
    main()
