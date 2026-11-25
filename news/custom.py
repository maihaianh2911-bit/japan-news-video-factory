"""Load a story written by hand (stories/<name>.json) with the pictures chosen for it.

python -m news.custom stories/<name>.json [<find folder>]   checks a story (and its picks against the find index)
"""
from dataclasses import dataclass
from datetime import date
from difflib import get_close_matches
import json
from pathlib import Path
import re
import sys

from PIL import Image, ImageOps

from .captions import caption_path, check as check_caption
from .clips import Clip
from .edits import cut_problems, move_problems
from .sources import Release
from .story import Beat
from .visuals import Footage, Photo

STORY_KEYS = {"stage", "title", "date", "source", "source_url", "searches", "scenes", "issue", "style", "kicker",
              "music", "pace", "fx", "voice", "masthead", "speaker"}
STYLES = ("news", "paper", "story", "history", "full", "band", "album", "magazine", "goods")
SCENE_KEYS = {"label", "headline", "lines", "value", "evidence", "photo", "cut", "why", "era", "product"}
LINE_KEYS = {"text", "say", "quote"}
QUOTE_MOST = 42   # characters of a quote line: 3 rows on the picture (owner, 21/11/2026)
PHOTO_KEYS = {"pick", "focus", "fit", "move", "tone", "depth", "start", "seconds"}
FX_KEYS = {"motion", "depth", "text", "face"}
TONES = ("sepia", "mono", "color")
MUSIC_KEYS = {"pick", "volume", "start"}
PACE_KEYS = {"speed", "line_pause", "scene_pause"}
PACE_LIMITS = {"speed": (0.7, 1.3), "line_pause": (0.0, 2.0), "scene_pause": (0.0, 3.0)}


@dataclass(frozen=True)
class Music:
    """A quiet piece under the voice: a file of the find folder (search "music:…") and its credit."""
    path: str
    title: str
    page: str
    creator: str
    license: str
    volume: float = 1.0   # 1 = the usual level under the voice (about 17 dB below it); 0.5 quieter, 1.5 louder
    start: float = 0.0    # seconds of the recording skipped (a silence or a noise at its beginning)

    def credit(self):
        return {"title": self.title, "page": self.page, "creator": self.creator, "license": self.license}
PICK = re.compile(r"^([1-9][0-9]*)-([1-9][0-9]*)$")
NAME = re.compile(r"^[A-Za-z0-9._-]+$")
# prefixes of a search; without one: Commons words
SEARCH_KINDS = ("file", "music", "video", "web", "url", "page", "jps", "wiki", "geo")
WISH = "=>"                                                     # "<search> => <what the picture must show>"
GEO = re.compile(r"^(-?\d+(?:\.\d+)?)\s*[,; ]\s*(-?\d+(?:\.\d+)?)(?:\s+(\d+)\s*m?)?$")
NOT_LATIN = re.compile(r"[^\x00-\u024f\u2000-\u206f]")          # Japanese, Chinese, Cyrillic …: the ranking reads English


class StoryError(ValueError):
    """A story file that cannot be used; the message lists every problem found."""


def unknown(keys, allowed, where):
    problems = []
    for key in sorted(set(keys) - allowed):
        guess = get_close_matches(key, allowed, n=1)
        hint = f" (did you mean {guess[0]!r}?)" if guess else f" (allowed: {', '.join(sorted(allowed))})"
        problems.append(f"{where}: unknown key {key!r}{hint}")
    return problems


def text_problem(value, where, *, required=True):
    if value is None and not required:
        return []
    if not isinstance(value, str) or (required and not value.strip()):
        return [f"{where} must be a non-empty string, got {value!r}"]
    return []


def search_parts(search):
    """(kind, words, wish) of a search: "wiki:美空ひばり => a singer on a stage" → ("wiki", "美空ひばり",
    "a singer on a stage"). The kind is the prefix ("commons" without one); the wish is what the picture must show,
    in English, and is empty when the search has none. url:, file: and music: are taken whole (no wish)."""
    kind, words, wish = "commons", search, ""
    for name in SEARCH_KINDS:
        if search.startswith(name + ":"):
            kind, words = name, search[len(name) + 1:]
            break
    if kind not in ("file", "music", "video", "url"):
        words, _, wish = words.partition(WISH)
    return kind, words.strip(), wish.strip()


def search_problems(search, where):
    """The problems of the new search syntax (wiki:, geo:, the wish after "=>"); old searches have none."""
    kind, words, wish = search_parts(search)
    if kind in ("file", "music", "video", "url"):
        if f" {WISH} " in search:
            return [f'{where}: a wish ("{WISH} …") works with Commons words, web:, page:, jps:, wiki: and geo:, not with {kind}:']
        return []
    problems = []
    if WISH in search:
        if not words:
            problems.append(f'{where}: nothing to search before "{WISH}", got {search!r}')
        if not wish:
            problems.append(f'{where}: after "{WISH}" write what the picture must show, in English, got {search!r}')
        elif NOT_LATIN.search(wish):
            problems.append(f'{where}: the wish after "{WISH}" must be in English (the ranking reads English only; '
                            f"the search words before it may be Japanese), got {wish!r}")
    if kind == "wiki" and not words:
        problems.append(f'{where}: "wiki:" needs a name or a Wikidata item, e.g. "wiki:美空ひばり" or "wiki:Q467982"')
    if kind == "jps" and not words:
        problems.append(f'{where}: "jps:" needs words to look for in Japan Search, e.g. "jps:黒船来航"')
    if kind == "page" and not re.fullmatch(r"https?://\S+", words):
        problems.append(f'{where}: "page:" needs the address of one article, e.g. "page:https://www.example.jp/'
                        f'articles/123", got {search!r}')
    if kind == "geo" and not GEO.match(words):
        problems.append(f'{where}: "geo:" must be "geo:<lat>,<lon> <metres>", e.g. "geo:35.6852,139.7528 400", '
                        f"got {search!r}")
    return problems


def picks_of(scene):
    """The pictures of a scene as a list of {"pick": …} (a scene may have one picture or a list of them)."""
    photo = scene.get("photo")
    picks = [] if photo is None else [{"pick": item} if isinstance(item, str) else item
                                      for item in (photo if isinstance(photo, list) else [photo])]
    product = scene.get("product")   # "goods": the product's card at the top of the frame
    if product is not None:
        picks.append({**({"pick": product} if isinstance(product, str) else product), "role": "product"})
    return picks


def check_photos(photo, where, searches):
    if isinstance(photo, list):
        if not 1 <= len(photo) <= 4:
            return [f'{where}: "photo" as a list must have 1 to 4 pictures, got {len(photo)}']
        return [problem for number, item in enumerate(photo, 1)
                for problem in check_photo(item, f"{where}, picture {number}", searches)]
    return check_photo(photo, where, searches)


def check_photo(photo, where, searches):
    problems = []
    if isinstance(photo, str):
        photo = {"pick": photo}
    if not isinstance(photo, dict):
        return [f'{where}: "photo" must be "<k>-<n>" or {{"pick": "<k>-<n>", ...}}, got {photo!r}']
    problems += unknown(photo, PHOTO_KEYS, where + ".photo")
    pick = photo.get("pick")
    match = PICK.match(pick) if isinstance(pick, str) else None
    if not match:
        problems.append(f'{where}: "pick" must look like "5-6" (search 5, picture 6), got {pick!r}')
    elif int(match[1]) > len(searches):
        problems.append(f"{where}: picture {pick} refers to search {match[1]}, but the story has only "
                        f"{len(searches)} searches")
    if "focus" in photo:
        focus = photo["focus"]
        if (not isinstance(focus, list) or len(focus) != 2
                or not all(isinstance(v, (int, float)) and not isinstance(v, bool) and 0 <= v <= 1 for v in focus)):
            problems.append(f'{where}: "focus" must be [x, y] with numbers from 0 to 1, got {focus!r}')
    if "fit" in photo and photo["fit"] not in ("cover", "contain"):
        problems.append(f'{where}: "fit" must be "cover" or "contain", got {photo["fit"]!r}')
    if "depth" in photo and not isinstance(photo["depth"], bool):
        problems.append(f'{where}: "depth" must be true or false (false: a flat picture such as a document), got {photo["depth"]!r}')
    if "start" in photo and (not isinstance(photo["start"], (int, float)) or isinstance(photo["start"], bool)
                             or photo["start"] < 0):
        problems.append(f'{where}: "start" (seconds into a clip where it begins to play) must be a number from 0, '
                        f'got {photo["start"]!r}')
    if "tone" in photo and photo["tone"] not in TONES:
        problems.append(f'{where}: "tone" must be one of {", ".join(TONES)}, got {photo["tone"]!r}')
    for key, most in (("start", 600), ("seconds", 20)):   # of a clip (a video: search)
        if key in photo and (not isinstance(photo[key], (int, float)) or isinstance(photo[key], bool)
                             or not 0 <= photo[key] <= most or (key == "seconds" and photo[key] < 1)):
            problems.append(f'{where}: "{key}" must be a number of seconds (of a clip), got {photo[key]!r}')
    problems += move_problems(photo, where)
    return problems


def validate(data, name=None):
    """Return the list of problems of a story (empty when it is usable)."""
    problems = []
    if name is not None and not NAME.match(name):
        problems.append(f"file name {name!r}: use only ASCII letters, digits, '.', '_' and '-' "
                        "(no spaces, no Japanese or Vietnamese characters), e.g. 2026-11-12-boj-rate.json")
    if not isinstance(data, dict):
        return problems + ["the story must be a JSON object"]
    problems += unknown(data, STORY_KEYS, "story")
    problems += text_problem(data.get("title"), '"title"')
    try:
        date.fromisoformat(data.get("date"))
    except (TypeError, ValueError):
        problems.append(f'"date" must be YYYY-MM-DD, got {data.get("date")!r}')
    if data.get("stage", "find") not in ("find", "render"):
        problems.append(f'"stage" must be "find" or "render", got {data.get("stage")!r}')
    issue = data.get("issue")
    if issue is not None and (not isinstance(issue, int) or isinstance(issue, bool) or issue < 1):
        problems.append(f'"issue" must be the issue number (a whole number), got {issue!r}')
    problems += text_problem(data.get("source"), '"source"', required=False)
    problems += text_problem(data.get("source_url"), '"source_url"', required=False)
    problems += text_problem(data.get("kicker"), '"kicker"', required=False)
    problems += text_problem(data.get("masthead"), '"masthead"', required=False)
    if isinstance(data.get("masthead"), str) and len(data["masthead"]) > 9:
        problems.append(f'"masthead": the big title at the top of the "band" frame, 9 characters at most, got '
                        f'{len(data["masthead"])}')
    if data.get("style", "news") not in STYLES:
        problems.append(f'"style" must be one of {", ".join(STYLES)}, got {data.get("style")!r}')
    searches = data.get("searches", [])
    if not isinstance(searches, list) or not all(isinstance(s, str) and s.strip() for s in searches):
        problems.append(f'"searches" must be a list of non-empty strings, got {searches!r}')
        searches = []
    for number, search in enumerate(searches, 1):
        problems += search_problems(search, f"search {number}")
    music = data.get("music")
    if music is not None:
        if not isinstance(music, dict):
            problems.append(f'"music" must be {{"pick": "<k>-<n>", "volume": 1}}, got {music!r}')
        else:
            problems += unknown(music, MUSIC_KEYS, "music")
            match = PICK.match(music.get("pick", "")) if isinstance(music.get("pick"), str) else None
            if not match:
                problems.append(f'"music": "pick" must look like "25-1", got {music.get("pick")!r}')
            elif int(match[1]) > len(searches) or not searches[int(match[1]) - 1].startswith("music:"):
                problems.append(f'"music": pick {music["pick"]} must come from a "music:…" search')
            volume = music.get("volume", 1.0)
            if not isinstance(volume, (int, float)) or isinstance(volume, bool) or not 0.2 <= volume <= 3:
                problems.append(f'"music": "volume" must be a number from 0.2 to 3, got {volume!r}')
            start = music.get("start", 0.0)
            if not isinstance(start, (int, float)) or isinstance(start, bool) or not 0 <= start <= 120:
                problems.append(f'"music": "start" must be seconds from 0 to 120, got {start!r}')
    fx = data.get("fx")
    if fx is not None:
        if not isinstance(fx, dict):
            problems.append(f'"fx" must be {{"motion": true, "depth": true, "text": true, "face": true}}, got {fx!r}')
        else:
            problems += unknown(fx, FX_KEYS, "fx")
    speaker = data.get("speaker", "")   # the VOICEVOX voice (owner, 25/11/2026: male or female, whichever fits)
    if not isinstance(speaker, str) or (speaker and not re.fullmatch(r"[^/\s]{1,30}(/[^/\s]{1,20})?", speaker)):
        problems.append(f'"speaker" must be a VOICEVOX voice "<name>" or "<name>/<style>" (e.g. "四国めたん" or '
                        f'"玄野武宏/ノーマル"), got {speaker!r}')
    voice = data.get("voice", 1.0)
    if not isinstance(voice, (int, float)) or isinstance(voice, bool) or not 0.5 <= voice <= 2.5:
        problems.append(f'"voice" must be a number from 0.5 to 2.5 (1.7 = 70 % louder), got {voice!r}')
    pace = data.get("pace")
    if pace is not None:
        if not isinstance(pace, dict):
            problems.append(f'"pace" must be {{"speed": 0.9, "line_pause": 0.3, "scene_pause": 0.6}}, got {pace!r}')
        else:
            problems += unknown(pace, PACE_KEYS, "pace")
            for key, (low, high) in PACE_LIMITS.items():
                value = pace.get(key, low)
                if not isinstance(value, (int, float)) or isinstance(value, bool) or not low <= value <= high:
                    problems.append(f'"pace": "{key}" must be a number from {low} to {high}, got {value!r}')
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        return problems + ['"scenes" must be a non-empty list']
    for number, scene in enumerate(scenes, 1):
        where = f"scene {number}"
        if not isinstance(scene, dict):
            problems.append(f"{where} must be an object")
            continue
        problems += unknown(scene, SCENE_KEYS, where)
        problems += text_problem(scene.get("headline"), f'{where}: "headline"')
        for key in ("label", "value", "evidence", "era"):
            problems += text_problem(scene.get(key), f'{where}: "{key}"', required=False)
        lines = scene.get("lines")
        if not isinstance(lines, list) or not lines:
            problems.append(f'{where}: "lines" must be a non-empty list of sentences, got {lines!r}')
        else:
            for index, line in enumerate(lines, 1):
                at = f"{where}, line {index}"
                if isinstance(line, dict):
                    problems += unknown(line, LINE_KEYS, at)
                    problems += text_problem(line.get("text"), f'{at}: "text"')
                    problems += text_problem(line.get("say"), f'{at}: "say"', required=False)
                    if "quote" in line and not isinstance(line["quote"], bool):
                        problems.append(f'{at}: "quote" must be true or false, got {line["quote"]!r}')

                else:
                    problems += text_problem(line, at)
        if "photo" in scene:
            problems += check_photos(scene["photo"], where, searches)
        if "product" in scene:
            if data.get("style") != "goods":
                problems.append(f'{where}: "product" (the card of the product) belongs to the "goods" style')
            problems += check_photo(scene["product"], f"{where}, product", searches)
        problems += cut_problems(scene, where)
    return problems


def hook_warnings(data):
    """The hook rules of 21/11/2026 for a story with "fx" (owner: "quá dài rồi, chỉ nên để 3 dòng thôi, ảnh hook
    đầu không quá 5s"): a quote is printed on at most 3 rows, so it has at most QUOTE_MOST characters; and the
    first picture stays at most 5 seconds, so a first scene read longer than that needs a second picture (about
    0.15 s a character). Warnings, not problems: stories finished before the rule still validate."""
    scenes = data.get("scenes")
    if not data.get("fx") or not isinstance(scenes, list) or not scenes or not isinstance(scenes[0], dict):
        return []
    warnings = []
    for number, scene in enumerate(scenes, 1):
        for index, line in enumerate(scene.get("lines") or [], 1) if isinstance(scene, dict) else ():
            if isinstance(line, dict) and line.get("quote") and len(line.get("text") or "") > QUOTE_MOST:
                warnings.append(f"scene {number}, line {index}: a quote is printed on at most 3 rows, so at most "
                                f"{QUOTE_MOST} characters (this one has {len(line['text'])}): make the quote the first "
                                f"part of the sentence and give the rest as the next line, not a quote")
    first = scenes[0]
    photo = first.get("photo")
    count = len(photo) if isinstance(photo, list) else 1 if photo else 0
    lines = first.get("lines") if isinstance(first.get("lines"), list) else []
    chars = sum(len(line if isinstance(line, str) else line.get("text") or "") for line in lines
                if isinstance(line, (str, dict)))
    if count == 1 and chars * 0.15 > 5.5:
        warnings.append(f"scene 1: it is read about {round(chars * 0.15)} s and the hook picture stays at most 5 s: "
                        f"give the scene a second picture")
    return warnings


def read(path):
    """Read and check a story; raises StoryError listing every problem."""
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise StoryError(f"{path}: not valid JSON: {error}") from None
    problems = validate(data, path.stem)
    if problems:
        raise StoryError(f"{path} has {len(problems)} problem(s):\n  - " + "\n  - ".join(problems))
    return data


def found_pictures(data, pictures):
    """The pictures of the find index by pick ("k-n"), after checking the picks still match the searches."""
    index_path = Path(pictures) / "index.json" if pictures else None
    if not index_path or not index_path.exists():
        return None
    groups = {group["k"]: group for group in json.loads(index_path.read_text(encoding="utf-8"))}
    searches = data.get("searches", [])
    problems = []
    for number, scene in enumerate(data["scenes"], 1):
        for item in picks_of(scene):
            pick = item["pick"]
            k, n = map(int, PICK.match(pick).groups())
            group = groups.get(k)
            if group is None:
                problems.append(f"scene {number}: picture {pick}: search {k} has not been run yet (stage find)")
            elif group["query"] != searches[k - 1]:
                problems.append(f"scene {number}: picture {pick} was found by search {k} = {group['query']!r}, but "
                                f"searches[{k}] in the story is now {searches[k - 1]!r}. Searches must only be "
                                "appended; put the old search back or pick again after a new find")
            elif group.get("error") and not group["results"]:
                problems.append(f"scene {number}: picture {pick}: search {k} failed ({group['error']})")
            elif group.get("unusable"):
                problems.append(f"scene {number}: picture {pick}: search {k} cannot be used as written "
                                f"({group['unusable']}); append another search")
            elif n > len(group["results"]):
                problems.append(f"scene {number}: picture {pick} is not among the {len(group['results'])} "
                                f"pictures found by search {k}")
            elif "start" in item and not group["results"][n - 1].get("clip"):
                problems.append(f'scene {number}: picture {pick} has "start", but it is a still picture, not a clip')
            elif group["results"][n - 1].get("clip") and item.get("start", 0) >= group["results"][n - 1]["seconds"]:
                problems.append(f'scene {number}: picture {pick}: "start" {item["start"]} is past the end of the '
                                f'clip ({group["results"][n - 1]["seconds"]} s)')
    if isinstance(data.get("music"), dict):
        k, n = map(int, PICK.match(data["music"]["pick"]).groups())
        group = groups.get(k)
        if group is None or not group["results"] or n > len(group["results"]):
            problems.append(f"music {data['music']['pick']}: not among the files found by search {k} (stage find)")
    if problems:
        raise StoryError(f"{len(problems)} pick problem(s):\n  - " + "\n  - ".join(problems))
    return {f"{k}-{number}": result for k, group in groups.items()
            for number, result in enumerate(group["results"], 1)}


def without_picture(data):
    return [(number, scene.get("label", ""), "value" in scene)
            for number, scene in enumerate(data["scenes"], 1) if "photo" not in scene]


def report_without_picture(data):
    missing = without_picture(data)
    if not missing:
        print("Every scene has a picture.")
        return
    print(f"{len(missing)} scene(s) without a picture (text card) — tell the owner which and why:")
    for number, label, has_value in missing:
        print(f"  scene {number} {label}" + ("" if has_value else "  (no value: not a pure-figure scene)"))


def toned(image, tone):
    """Old-photograph tones: "sepia" (warm brown, as old prints), "mono" (black and white), "color" (as it is)."""
    if tone == "color":
        return image
    grey = ImageOps.autocontrast(image.convert("L"), cutoff=1)
    if tone == "mono":
        return grey.convert("RGB")
    return ImageOps.colorize(grey, black="#1d130a", mid="#8c6c47", white="#f6e8cb")


def load_story(path, pictures=None):
    data = read(path)
    found = found_pictures(data, pictures)
    music = None
    if data.get("music"):
        if found is None:
            raise StoryError("the story has music, but no find folder with index.json was given (--pictures)")
        entry = found[data["music"]["pick"]]
        music = Music(str(Path(pictures) / entry["file"]), entry["title"].removeprefix("File:"), entry["page"],
                      entry.get("artist") or "Wikimedia Commons", entry.get("license", ""),
                      float(data["music"].get("volume", 1.0)), float(data["music"].get("start", 0.0)))
    pace = data.get("pace") or {}
    release = Release(data.get("source_url", ""), data["title"], date.fromisoformat(data["date"]),
                      data.get("source", ""), (), data.get("style", "news"), data.get("kicker", ""), music,
                      float(pace.get("speed", 0.96)), float(pace.get("line_pause", 0.0)),
                      float(pace.get("scene_pause", 0.0)), data.get("fx"), float(data.get("voice", 1.0)),
                      data.get("masthead", ""), data.get("speaker", ""))
    report_without_picture(data)
    beats, photos = [], {}
    for index, scene in enumerate(data["scenes"]):
        lines = [line if isinstance(line, str) else line["text"] for line in scene["lines"]]
        say = [line if isinstance(line, str) else line.get("say", line["text"]) for line in scene["lines"]]
        picks = picks_of(scene)
        visual = "photo" if picks else "data" if scene.get("value") else "document"
        beats.append(Beat(scene.get("label", "ニュース"), scene["headline"], tuple(lines), visual,
                          scene.get("value", ""), scene.get("evidence", ""), tuple(say) if say != lines else (),
                          scene.get("cut", ""), scene.get("why", ""), scene.get("era", ""),
                          tuple(number for number, line in enumerate(scene["lines"])
                                if isinstance(line, dict) and line.get("quote"))))
        if picks:
            if found is None:
                raise StoryError(f"Scene {index + 1} picks picture {picks[0]['pick']}, but no find folder with "
                                 "index.json was given (--pictures)")
            photos[index] = []
            for pick in picks:
                entry = found[pick["pick"]]
                tone = pick.get("tone", "color")
                if entry.get("clip"):   # a clip of the repository (file:…mp4, news/clips.py)
                    clip = Clip(Path(pictures) / entry["clip"], pick.get("start", 0.0))
                    image = toned(clip.at(0.0).copy(), tone)
                    photos[index].append(Photo(image, entry["page"], entry["title"].removeprefix("File:"),
                                               entry.get("artist") or "Wikimedia Commons", entry.get("license", ""),
                                               entry.get("license_url", ""), tuple(pick.get("focus", (0.5, 0.5))),
                                               pick.get("fit", "cover"), pick.get("move", ""), False,
                                               clip=clip, tone=tone, role=pick.get("role", "")))
                    continue
                if entry["file"].endswith(".mp4"):   # a clip: cut to the picture box of the frame, around its focus
                    from .render import W, box_height
                    footage = Footage(Path(pictures) / entry["file"], float(pick.get("start", 0.0)),
                                      float(pick.get("seconds", 6.0)) + 0.6, W, box_height(release.style),
                                      tuple(pick.get("focus", (0.5, 0.5))),
                                      None if tone == "color" else lambda picture, tone=tone: toned(picture, tone))
                    photos[index].append(Photo(footage.frame(len(footage.files) // 2), entry["page"],
                                               entry["title"].removeprefix("File:"),
                                               entry.get("artist") or "Wikimedia Commons", entry.get("license", ""),
                                               entry.get("license_url", ""), (0.5, 0.5), "cover", "hold", False,
                                               footage, role=pick.get("role", "")))
                    continue
                with Image.open(Path(pictures) / entry["file"]) as original:
                    image = toned(ImageOps.exif_transpose(original).convert("RGB"), tone)
                photos[index].append(Photo(image, entry["page"], entry["title"].removeprefix("File:"),
                                           entry.get("artist") or "Wikimedia Commons", entry.get("license", ""),
                                           entry.get("license_url", ""), tuple(pick.get("focus", (0.5, 0.5))),
                                           pick.get("fit", "cover"), pick.get("move", ""),
                                           pick.get("depth", True), role=pick.get("role", "")))
    return release, beats, photos


def main():
    if len(sys.argv) not in (2, 3):
        sys.exit("usage: python -m news.custom stories/<name>.json [<find folder>]")
    try:
        data = read(sys.argv[1])
        if len(sys.argv) == 3:
            if found_pictures(data, sys.argv[2]) is None:
                print(f"note: no index.json in {sys.argv[2]}; picks not checked against the find results")
    except StoryError as error:
        sys.exit(f"error: {error}")
    report_without_picture(data)
    for warning in hook_warnings(data):
        print(f"warning: {warning}")
    caption = caption_path(sys.argv[1])
    if caption.exists():
        if problems := check_caption(caption):
            sys.exit("error: " + "\n  - ".join([f"{len(problems)} caption problem(s):"] + problems))
        print(f"{caption}: OK")
    else:
        print(f"note: no posting caption yet ({caption}); write it before the closing comment")
    print(f"{sys.argv[1]}: OK")


if __name__ == "__main__":
    main()
