"""TEMPORARY probe of the wider picture search on a GitHub runner (work branch only, removed before main)."""
import json
import sys
import tempfile
import time
from io import BytesIO
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from PIL import Image   # noqa: E402

from news import find as F   # noqa: E402

UA = {"User-Agent": F.BROWSER, "Accept-Language": "ja,en;q=0.8", "Accept": "application/json,*/*"}


def raw(url, timeout=30):
    with urlopen(Request(url, headers=UA), timeout=timeout) as response:
        return response.status, response.read(6_000_000)


def size(url):
    try:
        with Image.open(BytesIO(raw(url, 25)[1])) as picture:
            return "%dx%d" % picture.size
    except Exception as error:
        return f"{type(error).__name__}: {str(error)[:60]}"


def shape(node, depth=0):
    """The keys of a JSON answer, a few levels down."""
    if isinstance(node, dict) and depth < 3:
        return {key: shape(value, depth + 1) for key, value in list(node.items())[:40]}
    if isinstance(node, list):
        return [f"{len(node)} items", shape(node[0], depth + 1)] if node else []
    return str(node)[:90]


def section(title):
    print(f"\n===== {title} =====", flush=True)


def japan_search():
    section("Japan Search")
    base = "https://jpsearch.go.jp/api/item/search/jps-cross?"
    for params in ({"keyword": "黒船来航", "size": 3}, {"keyword": "黒船来航", "size": 3, "f-contents": "thumb"},
                   {"keyword": "西太后", "size": 3, "f-rights": "pdm"}, {"keyword": "土偶", "size": 3, "f-db": "cobas"},
                   {"keyword": "昭和天皇", "size": 3, "f-type": "image"}):
        try:
            status, body = raw(base + urlencode(params))
            data = json.loads(body)
            items = data.get("list", [])
            print(f"{params} -> {status}, hit={data.get('hit')}, top keys={list(data)[:8]}, items={len(items)}")
            for item in items[:3]:
                common = item.get("common", {})
                print("   ", json.dumps({key: common.get(key) for key in (
                    "title", "thumbnailUrl", "contentsUrl", "linkUrl", "contentsRightsType", "contentsAccess",
                    "provider", "database", "ownerOrg")}, ensure_ascii=False)[:600])
        except Exception as error:
            print(f"{params} -> FAILED {type(error).__name__}: {str(error)[:200]}")
        time.sleep(1)
    try:
        status, body = raw(base + urlencode({"keyword": "黒船来航", "size": 8}))
        items = json.loads(body).get("list", [])
        if items:
            print("first item, whole:", json.dumps(items[0], ensure_ascii=False)[:2500])
            print("all common keys:", sorted({key for item in items for key in item.get("common", {})}))
        for item in items[:8]:
            common = item.get("common", {})
            thumb = common.get("thumbnailUrl")
            thumb = thumb[0] if isinstance(thumb, list) and thumb else thumb
            print("   thumb", size(thumb) if thumb else "none", "| contents",
                  (size(common["contentsUrl"]) if isinstance(common.get("contentsUrl"), str) else common.get("contentsUrl")),
                  "|", common.get("contentsRightsType"), "|", (common.get("title") or "")[:30], "|", item.get("id"))
        if items:
            status, body = raw("https://jpsearch.go.jp/api/item/" + items[0]["id"])
            print("item detail shape:", json.dumps(shape(json.loads(body)), ensure_ascii=False)[:2500])
    except Exception as error:
        print(f"detail FAILED {type(error).__name__}: {str(error)[:200]}")


def library_of_congress():
    section("Library of Congress")
    for url in ("https://www.loc.gov/photos/?" + urlencode({"q": "Tokyo 1945", "fo": "json", "c": 5, "at": "results"}),
                "https://www.loc.gov/pictures/search/?" + urlencode({"q": "Empress Dowager Cixi", "fo": "json", "c": 5})):
        try:
            status, body = raw(url, 40)
            data = json.loads(body)
            results = data.get("results", [])
            print(f"{url[:70]} -> {status}, keys={list(data)[:8]}, results={len(results)}")
            for result in results[:3]:
                print("   ", json.dumps({key: result.get(key) for key in (
                    "title", "url", "image_url", "image", "links", "date", "contributor", "creator", "rights",
                    "access_restricted", "original_format", "online_format")}, ensure_ascii=False)[:900])
            first = results[0] if results else {}
            big = (first.get("image_url") or [None])[-1] or (first.get("image") or {}).get("full")
            if big:
                print("   largest listed:", big[:120], "->", size(big.split("#")[0]))
        except Exception as error:
            print(f"{url[:70]} -> FAILED {type(error).__name__}: {str(error)[:200]}")
        time.sleep(2)


def web_and_pages():
    section("web: on this runner")
    calls = {"own": 0, "copy": 0}
    real = F.web_picture

    def counted(address, referer=None):
        calls["copy" if "yimg.jp" in address else "own"] += 1
        return real(address, referer)
    F.web_picture = counted
    with tempfile.TemporaryDirectory() as scratch:
        out = Path(scratch)
        for words in ("木村拓哉 工藤静香 結婚", "エリザベス女王 戴冠式 1953"):
            start = time.time()
            try:
                candidates = F.web_search(words, out)
                kept, _ = F.find("web:" + words, 1, out, {})
                print(f"{words}: {len(candidates)} candidates, kept {len(kept)} in {time.time() - start:.0f}s; "
                      f"asked the picture's own site {calls['own']} times, the engine's copy {calls['copy']} times")
            except Exception as error:
                print(f"{words}: FAILED {type(error).__name__}: {str(error)[:200]}")
            calls.update(own=0, copy=0)
            F.clear(out, 1, {})
        section("page: on this runner")
        pages = []
        try:
            for candidate in F.web_search("木村拓哉 工藤静香 結婚 記事", out):
                if candidate[1] not in pages and F.site(candidate[1]) not in {F.site(page) for page in pages}:
                    pages.append(candidate[1])
        except Exception as error:
            print(f"no pages to try: {error}")
        for page in pages[:8]:
            start = time.time()
            try:
                found = F.page_pictures(page)
                kept, _ = F.find("page:" + page, 2, out, {})
                print(f"{F.site(page)}: {len(found)} pictures named on the page, kept {len(kept)} "
                      f"({', '.join('%dx%d' % (entry['width'], entry['height']) for entry in kept[:6])}) "
                      f"in {time.time() - start:.0f}s | {page[:90]}")
            except Exception as error:
                print(f"{F.site(page)}: {type(error).__name__}: {str(error)[:160]} | {page[:90]}")
            F.clear(out, 2, {})


if __name__ == "__main__":
    for part in (japan_search, library_of_congress, web_and_pages):
        try:
            part()
        except Exception as error:   # one part must not lose the others
            print(f"{part.__name__} FAILED {type(error).__name__}: {error}")
