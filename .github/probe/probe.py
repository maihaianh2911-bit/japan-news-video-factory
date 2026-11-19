"""TEMPORARY probe of the wider picture search on a GitHub runner (work branch only, removed before main)."""
from collections import Counter
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from news import find as F   # noqa: E402


def main():
    print("\n===== jps: on this runner =====", flush=True)
    with tempfile.TemporaryDirectory() as scratch:
        out = Path(scratch)
        for words in ("黒船来航", "土偶", "富士山 浮世絵", "西太后", "明治天皇", "関東大震災", "紫禁城"):
            start = time.time()
            try:
                found = F.japan_search(words)
                asked = time.time() - start
                kept, _ = F.find("jps:" + words, 1, out, {})
                print(f"{words}: {len(found)} records with a free picture (asked in {asked:.0f}s), kept {len(kept)} "
                      f"in {time.time() - start:.0f}s | licences {dict(Counter(c[3]['license'] for c in found))} "
                      f"| held by {dict(Counter(c[3]['artist'] for c in found).most_common(4))} "
                      f"| sizes {', '.join('%dx%d' % (e['width'], e['height']) for e in kept[:8])}", flush=True)
            except Exception as error:
                print(f"{words}: FAILED {type(error).__name__}: {str(error)[:200]}", flush=True)
            F.clear(out, 1, {})
            time.sleep(2)


if __name__ == "__main__":
    main()
