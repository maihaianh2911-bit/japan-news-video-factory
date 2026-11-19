"""TEMPORARY probe of the wider picture search on a GitHub runner (work branch only, removed before main)."""
from collections import Counter
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from news import find as F   # noqa: E402


def main():
    print("\n===== jps: on this runner (pictures first, no book covers) =====", flush=True)
    with tempfile.TemporaryDirectory() as scratch:
        out = Path(scratch)
        for words in ("富士山 浮世絵", "西太后", "明治天皇", "関東大震災", "土偶", "紫禁城"):
            start = time.time()
            try:
                found = F.japan_search(words)
                kept, _ = F.find("jps:" + words, 1, out, {})
                print(f"{words}: {len(found)} records ({sum(c[3]['picture'] for c in found)} catalogued as pictures), "
                      f"kept {len(kept)} in {time.time() - start:.0f}s | kept from "
                      f"{dict(Counter(e['artist'] for e in kept))} | sizes "
                      f"{', '.join('%dx%d' % (e['width'], e['height']) for e in kept[:8])}", flush=True)
                for entry in kept[:4]:
                    print(f"     {entry['title'][:40]} | {entry['license']} | {entry['page'][:80]}", flush=True)
            except Exception as error:
                print(f"{words}: FAILED {type(error).__name__}: {str(error)[:200]}", flush=True)
            F.clear(out, 1, {})
            time.sleep(2)
        try:
            import re
            raw = F.web_get("https://colbase.nich.go.jp/collection_items/kyuhaku/J486", limit=8_000_000)
            text = raw.decode("utf-8", "replace")
            print(f"ColBase page: {len(raw)} bytes; picture-like addresses in it: "
                  f"{sorted(set(re.findall(r'[^\\s\"<>]*(?:media|image|iiif)[^\\s\"<>]*', text)))[:12]}")
        except Exception as error:
            print(f"ColBase page: {type(error).__name__}: {str(error)[:200]}")


if __name__ == "__main__":
    main()
