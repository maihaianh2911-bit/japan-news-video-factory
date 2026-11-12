"""Load a story written by hand (stories/<name>.json) with the pictures chosen for it."""
from datetime import date
import json
from pathlib import Path

from PIL import Image, ImageOps

from .sources import Release
from .story import Beat
from .visuals import Photo


def read(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not data.get("scenes"):
        raise ValueError("The story has no scenes")
    return data


def load_story(path, pictures=None):
    data = read(path)
    release = Release(data.get("source_url", ""), data["title"], date.fromisoformat(data["date"]),
                      data.get("source", ""), ())
    found = {}
    if pictures and (Path(pictures) / "index.json").exists():
        for group in json.loads((Path(pictures) / "index.json").read_text(encoding="utf-8")):
            for number, result in enumerate(group["results"], 1):
                found[f"{group['k']}-{number}"] = result
    beats, photos = [], {}
    for index, scene in enumerate(data["scenes"]):
        lines = [line if isinstance(line, str) else line["text"] for line in scene["lines"]]
        say = [line if isinstance(line, str) else line.get("say", line["text"]) for line in scene["lines"]]
        if not lines or not all(lines):
            raise ValueError(f"Scene {index + 1} has an empty line")
        pick = scene.get("photo")
        if isinstance(pick, str):
            pick = {"pick": pick}
        visual = "photo" if pick else "data" if scene.get("value") else "document"
        beats.append(Beat(scene.get("label", "ニュース"), scene["headline"], tuple(lines), visual,
                          scene.get("value", ""), scene.get("evidence", ""), tuple(say) if say != lines else ()))
        if pick:
            if pick["pick"] not in found:
                raise ValueError(f"Scene {index + 1}: picture {pick['pick']} is not among the found pictures")
            entry = found[pick["pick"]]
            with Image.open(Path(pictures) / entry["file"]) as original:
                image = ImageOps.exif_transpose(original).convert("RGB")
            photos[index] = Photo(image, entry["page"], entry["title"].removeprefix("File:"),
                                  entry.get("artist") or "Wikimedia Commons", entry["license"],
                                  entry.get("license_url", ""), tuple(pick.get("focus", (0.5, 0.5))),
                                  pick.get("fit", "cover"))
    return release, beats, photos
