"""Find reusable photographs of the source institution and retain attribution."""
from dataclasses import dataclass
from hashlib import md5
from io import BytesIO
import json
import re
from urllib.parse import quote, urlencode

from lxml import html
from PIL import Image, ImageOps

from .sources import fetch

COMMONS = "commons.wikimedia.org"
UPLOAD = "upload.wikimedia.org"
CATEGORIES = {
    "日本銀行": "Bank of Japan Head Office",
    "経済産業省": "Ministry of Economy, Trade and Industry Main Building",
}
BOJ_FILENAME = "Bank_of_Japan_headquarters_in_Tokyo,_Japan.jpg"


@dataclass(frozen=True)
class Photo:
    image: Image.Image
    page: str
    title: str
    creator: str
    license: str
    license_url: str

    def credit(self):
        return {key: getattr(self, key)
                for key in ("page", "title", "creator", "license", "license_url")}


def text_field(metadata, key):
    value = metadata.get(key, {}).get("value", "")
    return html.fragment_fromstring(value, create_parent="div").text_content().strip() if value else ""


def load_photo(url, page, title, creator, license_name, license_url):
    data = fetch(url, {UPLOAD, "thumb.wikimedia.org"}, limit=9_000_000, timeout=12)
    with Image.open(BytesIO(data)) as original:
        if original.format not in ("JPEG", "PNG", "WEBP") or original.width * original.height > 30_000_000:
            raise ValueError("Unsupported photograph")
        image = ImageOps.exif_transpose(original).convert("RGB")
    if min(image.size) < 540:
        raise ValueError("Photograph resolution is too low")
    return Photo(image, page, title, creator, license_name, license_url)


def candidates(category):
    params = urlencode({
        "action": "query", "format": "json", "generator": "categorymembers",
        "gcmtitle": f"Category:{category}", "gcmtype": "file", "gcmlimit": 20,
        "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata",
        "iiextmetadatafilter": "LicenseShortName|LicenseUrl|Artist|ImageDescription",
        "iiurlwidth": 1600,
    })
    data = json.loads(fetch(f"https://{COMMONS}/w/api.php?{params}", {COMMONS}, timeout=12))
    results = []
    for page in data.get("query", {}).get("pages", {}).values():
        info = (page.get("imageinfo") or [{}])[0]
        metadata = info.get("extmetadata", {})
        license_name = text_field(metadata, "LicenseShortName")
        creator = text_field(metadata, "Artist")
        description = text_field(metadata, "ImageDescription")
        title = page.get("title", "").removeprefix("File:")
        license_url = text_field(metadata, "LicenseUrl")
        if info.get("mime") != "image/jpeg" or min(info.get("width", 0), info.get("height", 0)) < 600:
            continue
        if license_name not in ("Public domain", "CC0", "CC BY 4.0", "CC BY 3.0", "CC BY 2.0"):
            continue
        if license_name.startswith("CC BY") and (not creator or not license_url.startswith("https://creativecommons.org/")):
            continue
        if not re.search(r"bank of japan|日本銀行|経済産業省|ministry of economy", title + " " + description, re.I):
            continue
        if re.search(r"interior|floor plan|model|stamp|logo|館内|模型", title, re.I):
            continue
        results.append((abs(info["width"] / info["height"] - 1.15),
                        info.get("thumburl") or info["url"], info["descriptionurl"], title,
                        creator or "Wikimedia Commons contributor", license_name, license_url))
    return sorted(results)


def find_photos(publisher, count):
    category = CATEGORIES.get(publisher)
    if category is None or not count:
        return []
    photos = []
    try:
        for _, *photo in candidates(category)[:4]:
            try:
                photos.append(load_photo(*photo))
            except (OSError, ValueError) as error:
                print(f"Skipping Commons image: {error}")
            if len(photos) == count:
                return photos
    except (OSError, ValueError) as error:
        print(f"Commons category unavailable: {error}")
    if publisher == "日本銀行" and len(photos) < count and not any(BOJ_FILENAME in p.page for p in photos):
        digest = md5(BOJ_FILENAME.encode(), usedforsecurity=False).hexdigest()
        filename = quote(BOJ_FILENAME, safe=",")
        try:
            photos.append(load_photo(
                f"https://{UPLOAD}/wikipedia/commons/{digest[0]}/{digest[:2]}/{filename}",
                f"https://{COMMONS}/wiki/File:{filename}", BOJ_FILENAME.replace("_", " "),
                "Wikimedia Commons contributor", "Public domain", "",
            ))
        except (OSError, ValueError) as error:
            print(f"Commons reference photo unavailable: {error}")
    return photos
