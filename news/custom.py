"""Load a story written by hand (stories/<name>.json) with the pictures chosen for it.

python -m news.custom stories/<name>.json [<find folder>]   checks a story (and its picks against the find index)
"""
from datetime import date
from difflib import get_close_matches
import json
from pathlib import Path
import re
import sys

from PIL import Image, ImageOps

from .edits import cut_problems, move_problems
from .sources import Release
from .story import Beat
from .visuals import Photo

STORY_KEYS = {"stage", "title", "date", "source", "source_url", "searches", "scenes", "issue", "style", "kicker"}
STYLES = ("news", "paper")
SCENE_KEYS = {"label", "headline", "lines", "value", "evidence", "photo", "cut", "why"}
LINE_KEYS = {"text", "say"}
PHOTO_KEYS = {"pick", "focus", "fit", "move"}
PICK = re.compile(r"^([1-9][0-9]*)-([1-9][0-9]*)$")
NAME = re.compile(r"^[A-Za-z0-9._-]+$")


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


def picks_of(scene):
    """The pictures of a scene as a list of {"pick": …} (a scene may have one picture or a list of them)."""
    photo = scene.get("photo")
    if photo is None:
        return []
    return [{"pick": item} if isinstance(item, str) else item for item in (photo if isinstance(photo, list) else [photo])]


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
    if data.get("style", "news") not in STYLES:
        problems.append(f'"style" must be one of {", ".join(STYLES)}, got {data.get("style")!r}')
    searches = data.get("searches", [])
    if not isinstance(searches, list) or not all(isinstance(s, str) and s.strip() for s in searches):
        problems.append(f'"searches" must be a list of non-empty strings, got {searches!r}')
        searches = []
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
        for key in ("label", "value", "evidence"):
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
                else:
                    problems += text_problem(line, at)
        if "photo" in scene:
            problems += check_photos(scene["photo"], where, searches)
        problems += cut_problems(scene, where)
    return problems


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
        for pick in (item["pick"] for item in picks_of(scene)):
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
            elif n > len(group["results"]):
                problems.append(f"scene {number}: picture {pick} is not among the {len(group['results'])} "
                                f"pictures found by search {k}")
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


def load_story(path, pictures=None):
    data = read(path)
    release = Release(data.get("source_url", ""), data["title"], date.fromisoformat(data["date"]),
                      data.get("source", ""), (), data.get("style", "news"), data.get("kicker", ""))
    found = found_pictures(data, pictures)
    report_without_picture(data)
    beats, photos = [], {}
    for index, scene in enumerate(data["scenes"]):
        lines = [line if isinstance(line, str) else line["text"] for line in scene["lines"]]
        say = [line if isinstance(line, str) else line.get("say", line["text"]) for line in scene["lines"]]
        picks = picks_of(scene)
        visual = "photo" if picks else "data" if scene.get("value") else "document"
        beats.append(Beat(scene.get("label", "ニュース"), scene["headline"], tuple(lines), visual,
                          scene.get("value", ""), scene.get("evidence", ""), tuple(say) if say != lines else (),
                          scene.get("cut", ""), scene.get("why", "")))
        if picks:
            if found is None:
                raise StoryError(f"Scene {index + 1} picks picture {picks[0]['pick']}, but no find folder with "
                                 "index.json was given (--pictures)")
            photos[index] = []
            for pick in picks:
                entry = found[pick["pick"]]
                with Image.open(Path(pictures) / entry["file"]) as original:
                    image = ImageOps.exif_transpose(original).convert("RGB")
                photos[index].append(Photo(image, entry["page"], entry["title"].removeprefix("File:"),
                                           entry.get("artist") or "Wikimedia Commons", entry.get("license", ""),
                                           entry.get("license_url", ""), tuple(pick.get("focus", (0.5, 0.5))),
                                           pick.get("fit", "cover"), pick.get("move", "")))
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
    print(f"{sys.argv[1]}: OK")


if __name__ == "__main__":
    main()
