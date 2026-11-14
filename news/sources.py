"""Fetch and parse Japanese primary sources."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from email.utils import parsedate_to_datetime
import re
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from xml.etree import ElementTree as ET
from zoneinfo import ZoneInfo

from lxml import html

JST = ZoneInfo("Asia/Tokyo")
USER_AGENT = "JapanNewsVideoFactory/1.0 (https://github.com/maihaianh2911-bit/japan-news-video-factory)"
PUBLISHERS = {
    "www.boj.or.jp": "日本銀行",
    "www.meti.go.jp": "経済産業省",
    "www.stat.go.jp": "総務省統計局",
}
FEEDS = (
    "https://www.boj.or.jp/rss/whatsnew.xml",
    "https://www.meti.go.jp/ml_index_release_atom.xml",
)
METI_INDEX = "https://www.meti.go.jp/press/index.html"
CPI_INDEX = "https://www.stat.go.jp/data/cpi/sokuhou/tsuki/index-z.html"
TOPICS = re.compile(r"物価|賃金|補助|税制|予算|金利|金融政策|金融市場調節|国債|貿易|ガソリン|電気料金|エネルギー|鉱工業|生産指数|商業動態|消費|設備投資|景気|産業|経済|雇用")
EXCLUDED = re.compile(r"開催案内|傍聴|入札|人事|採用|挨拶|挨さつ|募集開始|議事要旨|主な意見|訂正|公募")
DATE_PATTERN = r"(20\d{2})年\s*(\d{1,2})月\s*(\d{1,2})日"


@dataclass(frozen=True)
class Entry:
    url: str
    title: str
    published: date


@dataclass(frozen=True)
class Release:
    url: str
    title: str
    published: date
    publisher: str
    paragraphs: tuple[str, ...]
    style: str = "news"          # frame: "news" (dark blue) or "paper" (pale yellow old newspaper)
    kicker: str = ""             # red tag at the top; "" shows 日本のニュース


def compact(value):
    return re.sub(r"\s+", " ", value).strip()


def fetch(url, hosts, *, limit=2_000_000, timeout=18):
    def check(candidate):
        parts = urlsplit(candidate)
        if (parts.scheme != "https" or parts.hostname not in hosts
                or parts.username or parts.password or parts.port not in (None, 443)):
            raise ValueError(f"Unsupported URL: {candidate}")

    class Redirect(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            check(newurl)
            return super().redirect_request(req, fp, code, msg, headers, newurl)

    check(url)
    opener = build_opener(Redirect())
    with opener.open(Request(url, headers={"User-Agent": USER_AGENT}), timeout=timeout) as response:
        content = response.read(limit + 1)
        if len(content) > limit:
            raise ValueError(f"Response exceeds size limit: {url}")
        return content


def release_url(url):
    parts = urlsplit(url)
    boj = parts.hostname == "www.boj.or.jp" and re.fullmatch(
        r"/(?:mopo|statistics|research|announcements|about)/[\w/-]+\.html?", parts.path
    )
    meti = parts.hostname == "www.meti.go.jp" and re.fullmatch(
        r"/press/20\d{2}/\d{2}/20\d{9}/20\d{9}\.html", parts.path
    )
    cpi = parts.hostname == "www.stat.go.jp" and parts.path in (
        "/data/cpi/sokuhou/tsuki/index-z.htm", "/data/cpi/sokuhou/tsuki/index-z.html"
    )
    if parts.scheme not in ("http", "https") or not (boj or meti or cpi) or parts.username or parts.password:
        raise ValueError(f"URL is outside the supported release pages: {url}")
    return CPI_INDEX if cpi else urlunsplit(("https", parts.hostname, parts.path, "", ""))


def parse_date(value):
    if not value:
        return None
    match = re.search(DATE_PATTERN, value)
    try:
        if match:
            return date(*(int(part) for part in match.groups()))
        try:
            stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            stamp = parsedate_to_datetime(value)
        return stamp.astimezone(JST).date() if stamp.tzinfo else stamp.date()
    except (TypeError, ValueError):
        return None


def parse_feed(content, source):
    root = ET.fromstring(content)
    entries = []
    for item in root.iter():
        if item.tag.rsplit("}", 1)[-1] not in ("entry", "item"):
            continue
        fields = {child.tag.rsplit("}", 1)[-1]: child for child in item}
        link = next((child for child in item if child.tag.rsplit("}", 1)[-1] == "link"
                     and child.get("rel", "alternate") == "alternate"), None)
        if link is None:
            continue
        title = compact("".join(fields["title"].itertext())) if "title" in fields else ""
        published = next((value for key in ("published", "pubDate", "date", "updated")
                          if key in fields and (value := parse_date(fields[key].text))), None)
        try:
            url = release_url(urljoin(source, (link.get("href") or link.text or "").strip()))
        except ValueError:
            continue
        if published and title:
            entries.append(Entry(url, title, published))
    return entries


def meti_index():
    document = html.fromstring(fetch(METI_INDEX, PUBLISHERS))
    entries = []
    for link in document.xpath("//a[@href]"):
        try:
            url = release_url(urljoin(METI_INDEX, link.get("href")))
            published = datetime.strptime(url.rsplit("/", 1)[1][:8], "%Y%m%d").date()
        except ValueError:
            continue
        entries.append(Entry(url, compact(link.text_content()), published))
    return entries


def discover(today, *, previous_day_only=False):
    def retrieve(url):
        try:
            if url == METI_INDEX:
                return meti_index()
            if url == CPI_INDEX:
                release = get_release(url)
                return [Entry(release.url, release.title, release.published)]
            return parse_feed(fetch(url, PUBLISHERS), url)
        except (OSError, ValueError, ET.ParseError) as error:
            print(f"Source unavailable: {url} ({error})")
            return None

    with ThreadPoolExecutor(max_workers=4) as pool:
        batches = list(pool.map(retrieve, (*FEEDS, METI_INDEX, CPI_INDEX)))
    if all(batch is None for batch in batches):
        raise RuntimeError("All primary sources are unavailable")
    earliest = today - timedelta(days=1)
    latest = earliest if previous_day_only else today
    found = {item.url: item for batch in reversed(batches) for item in (batch or [])
             if earliest <= item.published <= latest and TOPICS.search(item.title)
             and not EXCLUDED.search(item.title)}
    def rank(item):
        decision = bool(re.search(r"金融市場調節方針|当面の金融政策運営|消費者物価|補助金|賃上げ", item.title))
        return item.published, decision, len(set(TOPICS.findall(item.title)))
    return sorted(found.values(), key=rank, reverse=True)


def get_release(url, fallback=None):
    url = release_url(url)
    publisher = PUBLISHERS[urlsplit(url).hostname]
    doc = html.fromstring(fetch(url, PUBLISHERS))
    main_nodes = doc.xpath("//main | //*[@id='main' or @id='contents' or @id='content']")
    area = next((node for node in main_nodes if node.xpath(".//h1")), main_nodes[0] if main_nodes else doc)
    headings = area.xpath(".//h1") or doc.xpath("//h1")
    title = next((compact(heading.text_content()) for heading in headings
                  if compact(heading.text_content())), fallback.title if fallback else "")
    if not title:
        raise ValueError("Release headline not found")
    body = area.xpath(".//*[self::p or self::li or self::dd or self::td]")
    paragraphs = []
    for node in body:
        if node.xpath("./p | ./li | ./ul | ./ol | ./table"):
            continue
        if node.xpath("ancestor::nav | ancestor::footer | ancestor::aside"):
            continue
        for decoration in node.xpath(".//sup | .//script | .//style"):
            decoration.drop_tree()
        value = compact(node.text_content())
        if value and value not in paragraphs:
            paragraphs.append(value)
    page_dates = area.xpath(".//time/@datetime | .//meta[@itemprop='datePublished']/@content")
    if url == CPI_INDEX:
        page_dates.insert(0, title)
    page_dates += paragraphs[:14]
    published = next((value for raw in page_dates if (value := parse_date(raw))), None)
    if published is None and publisher == "経済産業省":
        published = datetime.strptime(url.rsplit("/", 1)[1][:8], "%Y%m%d").date()
    published = published or (fallback.published if fallback else None)
    if published is None:
        raise ValueError("Release date not found")
    return Release(url, title, published, publisher, tuple(paragraphs))
