"""Offline checks of the picture search (news/find.py): no network, no torch. The Wikimedia answers, the web
pictures and the CLIP scores are stand-ins, so only the logic is checked: the search syntax (wiki:, geo:, the wish
after "=>"), standard picture sizes, the order kept, the ranking, what happens on 429, the searches that cannot
work as written (unusable: no failure), and a whole run with its index.json. Usage: python tools/find_test.py"""
from io import BytesIO
import json
from pathlib import Path
from random import Random
import sys
import tempfile
import time
from urllib.error import HTTPError
from urllib.parse import parse_qs, unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image   # noqa: E402

from news import find as F   # noqa: E402
from news.custom import StoryError, found_pictures, search_parts, search_problems, validate   # noqa: E402

REPO = Path(__file__).resolve().parent.parent


def blocks(seed, size, corner=None):
    """A picture unlike the others: 8 x 8 grey blocks drawn from the seed (and a corner block of one colour)."""
    dice = Random(seed)
    small = Image.new("L", (8, 8))
    small.putdata([dice.randrange(256) for _ in range(64)])
    picture = small.resize(size, Image.Resampling.NEAREST).convert("RGB")
    if corner:
        picture.paste(corner, (0, 0, size[0] // 16, size[1] // 16))
    return picture


def jpeg(seed, size=(640, 480), exif=None):
    data = BytesIO()
    blocks(seed, size).save(data, "JPEG", quality=90, **({"exif": exif} if exif else {}))
    return data.getvalue()


def page(title, width, height, licence="CC BY-SA 4.0", mime="image/jpeg", index=0):
    """A file page as the Commons API gives it (thumbnails come from thumb.wikimedia.org)."""
    name = title[5:].replace(" ", "_")
    small = (f"https://thumb.wikimedia.org/wikipedia/commons/thumb/a/ab/{name}/330px-{name}" if width > 330
             else f"https://upload.wikimedia.org/wikipedia/commons/a/ab/{name}")
    return {"title": title, "index": index, "imageinfo": [{
        "mime": mime, "width": width, "height": height, "thumburl": small,
        "url": f"https://upload.wikimedia.org/wikipedia/commons/a/ab/{name}",
        "descriptionurl": f"https://commons.wikimedia.org/wiki/{name}",
        "extmetadata": {"LicenseShortName": {"value": licence}, "Artist": {"value": "<b>Someone</b>"}}}]}


def syntax():
    assert search_parts("web:寛仁親王 若い頃") == ("web", "寛仁親王 若い頃", "")
    assert search_parts("wiki:美空ひばり => a singer on a stage") == ("wiki", "美空ひばり", "a singer on a stage")
    assert search_parts('incategory:"Bank of Japan Head Office" exterior')[0] == "commons"
    assert search_parts("Tokyo houses => rows of small houses") == ("commons", "Tokyo houses", "rows of small houses")
    assert search_parts("url:https://a.example/x.jpg https://a.example/") == (
        "url", "https://a.example/x.jpg https://a.example/", "")
    for good in ("geo:35.6852,139.7528 400", "geo: 35.68, 139.75", "wiki:Q17", "web:着物 => a woman in a kimono"):
        assert search_problems(good, "s") == [], good
    for bad in ("wiki:", "geo:Tokyo", "web:x =>", "web:x => 着物の女性", "=> a house", "music:Satie => calm"):
        assert search_problems(bad, "s"), bad
    # every story of the repository still validates, and none of their searches reads differently than before
    for path in sorted((REPO / "stories").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert validate(data, path.stem) == [], path
        for search in data.get("searches", []):
            kind, words, wish = search_parts(search)
            if kind in ("wiki", "geo") or wish:   # the kinds of search added on 17/11/2026: new stories use them
                continue
            assert words == (search if kind == "commons" else search[len(kind) + 1:]).strip(), (path, search)


def sizes():
    found = F.commons_entries([
        page("File:Big.jpg", 5100, 3000, index=1), page("File:Mid.jpg", 1400, 900, index=2),
        page("File:Small.jpg", 640, 480, index=3), page("File:Tiny.jpg", 300, 300, index=4),
        page("File:Press.jpg", 3000, 2000, licence="All rights reserved", index=5),
        page("File:Map.svg", 3000, 2000, mime="image/svg+xml", index=6)])
    assert [entry["title"] for entry in found] == ["File:Big.jpg", "File:Mid.jpg", "File:Small.jpg"], found
    assert found[0]["thumb"].endswith("/1920px-Big.jpg") and found[0]["preview"].endswith("/330px-Big.jpg")
    assert found[1]["thumb"].endswith("/1280px-Mid.jpg") and found[2]["thumb"].endswith("/ab/Small.jpg")
    assert found[0]["artist"] == "Someone" and "source" not in found[0]
    assert all(urlsplit(entry[key]).hostname in F.HOSTS for entry in found for key in ("thumb", "preview"))
    scan = {"width": 4000, "url": "https://upload.wikimedia.org/wikipedia/commons/a/ab/Scan.tif", "thumburl":
            "https://thumb.wikimedia.org/wikipedia/commons/thumb/a/ab/Scan.tif/lossy-page1-330px-Scan.tif.jpg"}
    assert F.sized(scan).endswith("/Scan.tif/lossy-page1-1920px-Scan.tif.jpg")   # the name of a scan's thumbnail
    assert [len(chunk) for chunk in F.chunks([f"File:{n}.jpg" for n in range(120)])] == [50, 50, 20]
    assert max(len(chunk) for chunk in F.chunks(["File:昭和天皇と香淳皇后の写真.jpg"] * 60)) < 25   # a short address


def refusals():
    """A Wikimedia site that keeps answering 429 is asked `tries` times, waits as long as it says, then not again
    in the run; a web search engine that answers 429 is skipped by the next searches."""
    asked, slept = [], []
    real = F.fetch, F.time.sleep, F.bing, F.yahoo, F.duckduckgo

    def refuse(url, hosts, **options):
        asked.append(url)
        raise HTTPError(url, 429, "Too Many Requests", {"Retry-After": "25"}, None)
    try:
        F.fetch, F.time.sleep = refuse, slept.append
        F.REFUSED.clear()
        for _ in range(2):
            try:
                F.get("https://commons.wikimedia.org/w/api.php?x=1")
                raise AssertionError("a refused request must fail")
            except F.Refused:
                pass
        assert len(asked) == 4 and slept == [25, 25, 30] and F.REFUSED == {"commons.wikimedia.org"}, (asked, slept)
        F.REFUSED.clear()
        asked.clear()
        try:   # one short try (wiki: asking a Wikipedia): the error is passed on, the site is not struck off
            F.get("https://ja.wikipedia.org/w/api.php?x=1", tries=1)
            raise AssertionError("a refused request must fail")
        except HTTPError:
            assert len(asked) == 1 and not F.REFUSED

        def busy(query):
            asked.append("yahoo " + query)
            raise HTTPError("https://search.yahoo.co.jp/", 429, "Too Many Requests", {}, None)
            yield
        busy.__name__ = "yahoo"   # the engine asked first
        F.yahoo, F.bing = busy, lambda query: iter([("https://a.example/1.jpg", "https://a.example/", "one")])
        asked.clear()
        assert F.web_search("first") == F.web_search("second") and asked == ["yahoo first"], asked
        F.bing = F.duckduckgo = lambda query: iter(())
        try:
            F.web_search("third")
            raise AssertionError("a web search nobody answers must fail")
        except RuntimeError:
            pass
    finally:
        F.fetch, F.time.sleep, F.bing, F.yahoo, F.duckduckgo = real
        F.REFUSED.clear()


def order(out):
    """Web pictures are loaded a few at a time, and the ones kept are the same as one by one: the first 20 that
    load, are large enough and were not kept before, in the order of the search engine."""
    pictures = {f"https://a.example/{n}.jpg": jpeg(n) for n in range(30)}
    pictures["https://a.example/3.jpg"] = b"not a picture"
    pictures["https://a.example/5.jpg"] = jpeg(5, (300, 300))    # too small
    pictures["https://a.example/7.jpg"] = pictures["https://a.example/2.jpg"]   # the same picture again
    tall = Image.Exif()
    tall[0x0112] = 6   # stored lying on its side
    pictures["https://a.example/0.jpg"] = jpeg(0, (800, 500), tall.tobytes())
    real = F.web_get, F.web_search

    def slow(url, referer=None, limit=0, timeout=0):
        time.sleep(0.15)
        return pictures[url]
    try:
        F.web_get = slow
        F.web_search = lambda words, out=None: [(url, "https://a.example/page", f"t{n}") for n, url in enumerate(pictures)]
        seen = {}
        start = time.monotonic()
        kept, notes = F.find("web:anything", 4, out, seen)
        took = time.monotonic() - start
    finally:
        F.web_get, F.web_search = real
    assert F.WEB_KEEP == 20
    assert [entry["image"].rsplit("/", 1)[1] for entry in kept] == [f"{n}.jpg" for n in (0, 1, 2, 4, 6, *range(8, 23))]
    assert [entry["file"] for entry in kept] == [f"4-{n}.jpg" for n in range(1, 21)] and notes == {}
    assert list(kept[1]) == ["title", "page", "image", "width", "height", "license", "license_url", "artist",
                             "description", "file"] and kept[1]["artist"] == "a.example", kept[1]
    assert (kept[0]["width"], kept[0]["height"]) == (500, 800) == Image.open(out / "4-1.jpg").size   # stood up
    assert took < 0.15 * 24 * 0.6, f"24 pictures of 0.15 s took {took:.2f} s: not loaded side by side"
    return took


def wider(out):
    """The wider web search (19/11/2026): Yahoo! JAPAN is asked for three pages and gives each address once, with
    the size of the picture and the address of its own copy; a later page that cannot be read costs nothing; a
    picture its own site refuses is taken from that copy; one the engine says is small is not even loaded; and
    neither note is recorded in index.json."""
    asked = []

    def result(n, width=1200, height=800):
        return {"title": f"t{n}", "refererUrl": f"https://site.example/page{n}",
                "original": {"url": f"https://site.example/{n}.jpg", "width": width, "height": height},
                "main": {"url": f"https://copy.example/{n}", "width": width, "height": height, "isNotFound": False},
                "thumbnail": {"url": f"https://copy.example/small{n}", "width": 168, "height": 112}}

    def results_page(numbers):
        algos = [result(n) for n in numbers]   # the page data holds the results twice, as the real one does
        data = {"props": {"initialProps": {"pageProps": {"algos": algos}}, "initialState": {"algos": algos}}}
        return (b'<html><script id="__NEXT_DATA__" type="application/json">' + json.dumps(data).encode()
                + b"</script></html>")
    pages = {None: results_page(range(20)), "21": results_page(range(20, 40)), "41": results_page(range(35, 50))}

    def search_page(url, referer=None, limit=0, timeout=0):
        asked.append(url)
        start = parse_qs(urlsplit(url).query).get("b", [None])[0]
        if isinstance(pages[start], Exception):
            raise pages[start]
        return pages[start]
    real = F.web_get, F.time.sleep
    try:
        F.web_get, F.time.sleep = search_page, lambda seconds: None
        found = list(F.yahoo("犬"))
        assert len(asked) == 3 and [urlsplit(url).query.count("b=") for url in asked] == [0, 1, 1], asked
        assert [result[0] for result in found] == [f"https://site.example/{n}.jpg" for n in range(50)]
        assert found[3][1:] == ("https://site.example/page3", "t3",
                                {"mirror": "https://copy.example/3", "width": 1200, "height": 800})
        pages["21"] = HTTPError("https://search.yahoo.co.jp/", 429, "Too Many Requests", {}, None)
        assert len(list(F.yahoo("犬"))) == 20   # the first page is enough to go on with
        pages[None] = pages["21"]
        try:
            list(F.yahoo("犬"))
            raise AssertionError("a first page that cannot be read is the engine failing")
        except HTTPError:
            pass

        files = {"https://copy.example/1": jpeg(41), "https://site.example/2.jpg": jpeg(42),
                 "https://copy.example/2": jpeg(43)}
        asked.clear()

        def picture(url, referer=None, limit=0, timeout=0):
            asked.append(url)
            if url not in files:
                raise HTTPError(url, 403, "Forbidden", {}, None)
            return files[url]
        F.web_get = picture
        entries = F.web_entries([("https://site.example/1.jpg", "https://site.example/p", "one",
                                  {"mirror": "https://copy.example/1", "width": 900, "height": 700}),
                                 ("https://site.example/2.jpg", "https://site.example/p", "two",
                                  {"mirror": "https://copy.example/2", "width": 900, "height": 700}),
                                 ("https://site.example/3.jpg", "https://site.example/p", "small",
                                  {"mirror": "https://copy.example/3", "width": 900, "height": 300}),
                                 ("https://site.example/4.jpg", "https://site.example/p", "gone", {"mirror": None})])
        assert entries[0]["mirror"] == "https://copy.example/1" and entries[0]["hint"] == (900, 700)
        assert "mirror" not in entries[3] and "hint" not in entries[3]
        kept = F.keep(entries, F.web_shot, 8, out, {}, 20)
        assert [entry["title"] for entry in kept] == ["one", "two"], kept   # refused by its site: from the copy
        assert asked.count("https://copy.example/1") == 1 and "https://copy.example/2" not in asked   # own site first
        assert not any("/3" in url for url in asked), asked            # said to be small: not loaded
        assert all("mirror" not in entry and "hint" not in entry for entry in kept)
        assert kept[0]["image"] == "https://site.example/1.jpg" and kept[0]["artist"] == "site.example"
        try:
            F.web_load(entries[3])
            raise AssertionError("a refused picture without a copy cannot be used")
        except F.Unusable as error:
            assert "403" in str(error)
    finally:
        F.web_get, F.time.sleep = real


class FakeClip:
    """Stands in for CLIP: the score of a picture is written in its top-left pixel."""
    ready = staticmethod(lambda: True)

    @staticmethod
    def scores(images, text):
        marks = [image.getpixel((0, 0)) for image in images]
        return [mark[0] / 255 for mark in marks], [mark[1] / 255 for mark in marks]


def ranking(out):
    """With a wish the Commons candidates are scored on their small versions: best first, the ones that do not
    show the wish or look unsuitable left out; without a wish (or without CLIP) the order of the source stays."""
    def marked(match, unfit=0.0):
        data = BytesIO()
        blocks(round(match * 100), (640, 640), (round(match * 255), round(unfit * 255), 0)).save(data, "PNG")
        return data.getvalue()
    wanted = {"A": 0.20, "B": 0.33, "C": 0.10, "D": 0.31, "E": 0.36, "F": 0.25}
    pages = [page(f"File:{name}.png", 2000, 2000, mime="image/png", index=number)
             for number, name in enumerate(wanted, 1)]
    asked = []

    def fetch(url, hosts, **options):
        asked.append(url)
        if "api.php" in url:
            return json.dumps({"query": {"pages": {str(n): entry for n, entry in enumerate(pages)}}}).encode()
        name = url.rsplit("-", 1)[1][0]
        return marked(wanted[name], 0.5 if name == "E" else 0.0)
    real = F.fetch, F.Clip
    try:
        F.fetch, F.Clip = fetch, FakeClip
        kept, notes = F.find("houses => rows of small houses", 2, out, {})
        assert [entry["title"][5] for entry in kept] == ["B", "D", "F", "A"], kept   # C: not it; E: unsuitable
        assert [entry["match"] for entry in kept] == [0.329, 0.31, 0.251, 0.2], kept
        assert notes == {"want": "rows of small houses", "ranked": True, "candidates": 6, "left_out": 2}, notes
        assert "gsrlimit=50" in asked[0] and "gsrsearch=houses&" in asked[0] and "iiurlwidth=330" in asked[0]
        assert sum("/330px-" in url for url in asked) == 6 and sum("/1920px-" in url for url in asked) == 4
        asked.clear()
        kept, notes = F.find("houses", 3, out, {})
        assert [entry["title"][5] for entry in kept] == list("ABCDEF") and notes == {} and "gsrlimit=30" in asked[0]
        assert not any("/330px-" in url for url in asked) and "match" not in kept[0]
        F.Clip = type("NoClip", (), {"ready": staticmethod(lambda: False)})
        kept, notes = F.find("houses => rows of small houses", 5, out, {})
        assert [entry["title"][5] for entry in kept] == list("ABCDEF"), kept
        assert notes == {"want": "rows of small houses", "ranked": False}
    finally:
        F.fetch, F.Clip = real


def wikidata(out):
    """wiki: reads the name as a Wikidata item and brings its own picture, the pictures of its articles, then its
    Commons category; a Wikipedia that does not answer is passed over; geo: brings the nearest photos first."""
    asked = []
    files = {"Own.jpg": 1, "Lead.jpg": 2, "Article.jpg": 3, "Cat 1.jpg": 4, "Sub 1.jpg": 5, "Near 2.jpg": 6, "Far.jpg": 7}

    def fetch(url, hosts, **options):
        asked.append(url)
        params = {key: values[0] for key, values in parse_qs(urlsplit(url).query).items()}
        host = urlsplit(url).hostname
        if host == "ja.wikipedia.org":
            raise OSError("Tunnel connection failed: 403 Forbidden")
        if host == "en.wikipedia.org" and params.get("prop") == "pageprops":
            return b'{"query": {"pages": {"-1": {"title": "x", "missing": ""}}}}'
        if params.get("action") == "wbsearchentities":
            return b'{"search": [{"id": "Q42"}, {"id": "Q43"}]}'
        if params.get("action") == "wbgetentities":
            image = {"mainsnak": {"datavalue": {"value": "Own.jpg"}}}
            point = {"mainsnak": {"datavalue": {"value": {"latitude": 35.123456, "longitude": 139.5}}}}
            return json.dumps({"entities": {"Q42": {
                "labels": {"ja": {"value": "名前"}}, "descriptions": {"en": {"value": "a thing"}},
                "claims": {"P18": [image], "P625": [point], "P373": [{"mainsnak": {"datavalue": {"value": "Cat"}}}]},
                "sitelinks": {"jawiki": {"title": "名前"}, "enwiki": {"title": "Name"}}}}}).encode()
        if host == "en.wikipedia.org":
            return json.dumps({"query": {"pages": {"1": {"pageimage": "Lead.jpg", "images": [
                {"title": "File:Article.jpg"}, {"title": "File:Commons-logo.svg"}, {"title": "File:Lead.jpg"},
                {"title": "File:Own.jpg"}]}}}}).encode()
        if params.get("list") == "categorymembers":
            names = {("file", "Category:Cat"): ["File:Cat 1.jpg", "File:Own.jpg"],
                     ("subcat", "Category:Cat"): ["Category:Sub"],
                     ("file", "Category:Sub"): ["File:Sub 1.jpg"]}[params["cmtype"], params["cmtitle"]]
            return json.dumps({"query": {"categorymembers": [{"title": name} for name in names]}}).encode()
        if params.get("list") == "geosearch":
            return json.dumps({"query": {"geosearch": [{"title": "File:Near 2.jpg"}, {"title": "File:Near 3.jpg"},
                                                       {"title": "File:Far.jpg"}, {"title": "File:Own.jpg"}]}}).encode()
        if "titles" in params:
            titles = params["titles"].split("|")   # answered in another order, without the files not on Commons
            return json.dumps({"query": {"pages": {str(n): page(title, 2000, 1500) for n, title in
                                                   enumerate(reversed(titles)) if title[5:] in files}}}).encode()
        return jpeg(files[unquote(url.rsplit("px-", 1)[1]).replace("_", " ")], (960, 720))
    real = F.fetch
    try:
        F.fetch = fetch
        kept, notes = F.find("wiki:名前", 7, out, {})
        assert [entry["title"][5:] for entry in kept] == ["Own.jpg", "Lead.jpg", "Article.jpg", "Cat 1.jpg",
                                                         "Sub 1.jpg", "Near 2.jpg", "Far.jpg"], kept
        assert [entry["source"] for entry in kept] == ["commons/wiki"] * 3 + ["commons/category"] * 2 + ["commons/geo"] * 2
        assert notes == {"wikidata": {"id": "Q42", "label": "名前", "description": "a thing", "coord": [35.12346, 139.5]}}
        assert kept[0]["license"] == "CC BY-SA 4.0" and kept[0]["page"].endswith("/wiki/Own.jpg")
        asked.clear()
        kept, notes = F.find("wiki:Q42", 8, out, {})   # an item given: nobody is asked for the name
        assert not any("wbsearchentities" in url or "pageprops" in url for url in asked) and len(kept) == 7
        kept, notes = F.find("geo:35.1,139.5 800", 9, out, {})
        assert [entry["title"][5:] for entry in kept] == ["Near 2.jpg", "Far.jpg", "Own.jpg"] and notes == {}
        assert "gsradius=800" in "".join(asked) and "gscoord=35.1%7C139.5" in "".join(asked)
    finally:
        F.fetch = real


def unusable(out):
    """A search that cannot work as written raises Unusable with the reason (no failure of the run): a wiki: name
    that names nothing, a url: picture the site refuses, that is not a picture, is too small or does not load in
    two tries. A name is not "nothing" while a Wikipedia did not answer, and a url: picture found before is kept."""
    silent = []

    def fetch(url, hosts, **options):
        host = urlsplit(url).hostname
        if host in silent:
            raise OSError("Tunnel connection failed: 403 Forbidden")
        if host.endswith("wikipedia.org"):
            return b'{"query": {"pages": {"-1": {"title": "x", "missing": ""}}}}'
        return b'{"search": []}'
    answers = {"https://a.example/gone.jpg": HTTPError("https://a.example/gone.jpg", 404, "Not Found", {}, None),
               "https://a.example/page.jpg": b"<html>not a picture</html>",
               "https://a.example/small.jpg": jpeg(31, (300, 300)),
               "https://a.example/busy.jpg": HTTPError("https://a.example/busy.jpg", 503, "Busy", {}, None),
               "https://a.example/first.jpg": jpeg(32), "https://a.example/again.jpg": jpeg(32)}
    asked, slept = [], []

    def web_get(url, referer=None, limit=0, timeout=0):
        asked.append(url)
        if isinstance(answers[url], Exception):
            raise answers[url]
        return answers[url]

    def refused(query):
        try:
            F.find(query, 5, out, seen)
        except F.Unusable as error:
            return str(error)
        except RuntimeError as error:
            return f"FAILED {error}"
        raise AssertionError(f"{query} must not give a picture")
    real = F.fetch, F.web_get, F.time.sleep
    seen = {}
    try:
        F.fetch, F.web_get, F.time.sleep = fetch, web_get, slept.append
        assert refused("wiki:名無しの邸").startswith("wiki: no Wikidata item named '名無しの邸'")
        silent.append("ja.wikipedia.org")   # an article of that title may exist there: a failure, tried again
        assert refused("wiki:名無しの邸").startswith("FAILED wiki: no Wikidata item named")
        assert "404" in refused("url:https://a.example/gone.jpg https://a.example/")
        assert "UnidentifiedImageError" in refused("url:https://a.example/page.jpg")
        assert "300 x 300" in refused("url:https://a.example/small.jpg")
        assert asked == [f"https://a.example/{name}.jpg" for name in ("gone", "page", "small")] and not slept
        assert "did not load in two tries" in refused("url:https://a.example/busy.jpg")
        assert asked.count("https://a.example/busy.jpg") == 2 and slept == [5]
        kept, notes = F.find("url:https://a.example/first.jpg", 6, out, seen)
        assert [entry["file"] for entry in kept] == ["6-1.jpg"] and notes == {}
        kept, notes = F.find("url:https://a.example/again.jpg", 7, out, seen)   # asked for by name: kept
        assert [entry["file"] for entry in kept] == ["7-1.jpg"] and notes == {"same_as": "6-1"}
        assert F.web_shot({"image": "https://a.example/small.jpg", "page": ""}) is None   # web: passes these over
        assert F.web_shot({"image": "https://a.example/gone.jpg", "page": ""}) is None
    finally:
        F.fetch, F.web_get, F.time.sleep = real


def whole_run(folder):
    """A run over a story: searches done before are left alone, a failed one is recorded with "error" and makes
    the exit status 3, the others are kept, and a picture of the repository costs no pause. A search that cannot
    work as written is recorded with "unusable", is not run again and does not change the exit status."""
    media = sorted((REPO / "stories" / "media").glob("*/*.jpg"))[0].relative_to(REPO)
    story = {"title": "t", "date": "2026-11-17", "searches": [f"file:{media}", "web:broken", "web:fine => a house",
                                                              "url:https://a.example/gone.jpg"],
             "scenes": [{"headline": "h", "lines": ["l"]}]}
    path = folder / "run-test.json"
    path.write_text(json.dumps(story, ensure_ascii=False), encoding="utf-8")
    out = folder / "pictures"
    real = F.web_search, F.web_get, F.Clip, F.time.sleep, sys.argv
    slept = []

    def web_search(words, out=None):
        if words == "broken":
            raise RuntimeError("no web image search answered")
        return [(f"https://a.example/{n}.jpg", "https://a.example/page", "") for n in range(3)]
    gone = []

    def web_get(url, referer=None, limit=0, timeout=0):
        if url.endswith("gone.jpg"):
            gone.append(url)
            raise HTTPError(url, 404, "Not Found", {}, None)
        return jpeg(int(url[-5]))
    try:
        F.web_search, F.web_get = web_search, web_get
        F.Clip, F.time.sleep = type("NoClip", (), {"ready": staticmethod(lambda: False)}), slept.append
        sys.argv = ["find", str(path), str(out)]
        try:
            F.main()
            raise AssertionError("a failed search must make the exit status 3")
        except SystemExit as stop:
            assert stop.code == 3
        index = json.loads((out / "index.json").read_text(encoding="utf-8"))
        assert [(group["k"], len(group["results"]), "error" in group) for group in index] == [(1, 1, False), (2, 0, True), (3, 3, False), (4, 0, False)]
        assert "404" in index[3]["unusable"] and "unusable" not in index[1]
        assert list(index[0]) == ["k", "query", "results"] and index[2]["want"] == "a house" and index[2]["ranked"] is False
        assert (out / "sheet_1.jpg").exists() and (out / "sheet_3.jpg").exists() and not (out / "sheet_2.jpg").exists()
        assert slept == [2, 2, 2], slept   # none after the file: search
        F.web_search = lambda words, out=None: [("https://a.example/9.jpg", "https://a.example/page", "")]
        before = (out / "3-1.jpg").stat().st_mtime_ns
        F.main()   # only the failed search runs again; the unusable one alone leaves the exit status 0
        index = sorted(json.loads((out / "index.json").read_text(encoding="utf-8")), key=lambda group: group["k"])
        assert [len(group["results"]) for group in index] == [1, 1, 3, 0] and (out / "3-1.jpg").stat().st_mtime_ns == before
        assert len(gone) == 1 and "unusable" in index[3]   # asked once, in the first run only
        story["scenes"][0]["photo"] = "4-1"   # a pick from it says why, not "not among the 0 pictures"
        try:
            found_pictures(story, out)
            raise AssertionError("a pick from an unusable search must be refused")
        except StoryError as error:
            assert "search 4 cannot be used as written" in str(error) and "404" in str(error), error
    finally:
        F.web_search, F.web_get, F.Clip, F.time.sleep, sys.argv = real


def main():
    syntax()
    sizes()
    refusals()
    with tempfile.TemporaryDirectory(prefix="find-test-") as scratch:
        scratch = Path(scratch)
        took = order(scratch)
        wider(scratch)
        ranking(scratch)
        wikidata(scratch)
        unusable(scratch)
        whole_run(scratch)
    print(f"picture search checks OK (24 web pictures of 0.15 s each loaded in {took:.2f} s)")


if __name__ == "__main__":
    main()
