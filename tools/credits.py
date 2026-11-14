"""credits.txt for the video description, from dist/sources.json: news source, pictures (author, licence, page),
voice. Usage: python tools/credits.py dist/sources.json dist/credits.txt"""
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
release = data.get("release") or {}
lines = []
if release.get("publisher") or release.get("url"):
    lines += ["出典 / Nguồn tin", "- " + " ".join(x for x in (release.get("publisher"), release.get("url")) if x), ""]
photos = data.get("photos") or []
if photos:
    lines.append("写真 / Ảnh")
    for photo in photos:
        licence = photo.get("license") or ""
        lines.append(f"- {photo.get('title', '')} — {photo.get('creator') or 'không rõ tác giả'}"
                     f"{', ' + licence if licence else ''}{' (' + photo['license_url'] + ')' if photo.get('license_url') else ''}"
                     f" — {photo.get('page', '')}")
    lines.append("")
lines.append(data.get("voice_credit") or "VOICEVOX:青山龍星")
open(sys.argv[2], "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("\n".join(lines))
