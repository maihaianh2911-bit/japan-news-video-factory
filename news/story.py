"""Build grounded Japanese narration and captions from a primary release."""
from dataclasses import dataclass
import re
import unicodedata

from .sources import Release

NUMBER = re.compile(r"[+＋−-]?\d+(?:[,.]\d+)*(?:\s*兆円|\s*億円|\s*万円|\s*円|\s*%|\s*％|\s*ポイント|\s*万件|\s*万人)")
BOJ_TARGET = re.compile(r"無担保コールレート.{0,32}?(\d+(?:\.\d+)?)\s*%\s*程度")
BOJ_LENDING = re.compile(r"基準貸付利率.{0,26}?(\d+(?:\.\d+)?)\s*%\s*とする")
BOJ_DEPOSIT = re.compile(r"(?:付利金利|適用利率).{0,38}?(\d+(?:\.\d+)?)\s*%\s*とする")
VOTE = re.compile(r"賛成\s*(\d+)\s*反対\s*(\d+)")
VOICE_CREDIT = "VOICEVOX:青山龍星"


@dataclass(frozen=True)
class Beat:
    label: str
    headline: str
    lines: tuple[str, ...]
    visual: str = "document"
    value: str = ""
    evidence: str = ""


def japanese_date(release):
    d = release.published
    return f"{d.year}年{d.month}月{d.day}日"


def boj_policy(release):
    body = unicodedata.normalize("NFKC", " ".join(release.paragraphs))
    rate = BOJ_TARGET.search(body)
    if not rate or not re.search(r"金融市場調節方針|当面の金融政策運営", release.title):
        return []
    target = rate[1]
    beats = [
        Beat("金融政策", "日銀が示した\n短期金利の目安",
             (f"日本銀行が、短期金利を{target}パーセント程度に誘導する方針を公表しました。",
              "どの金利の話なのか、日銀の発表から確認します。"),
             "photo", f"{target}％", rate[0]),
        Beat("政策金利", "金融機関どうしの\n翌日物の金利",
             ("対象は、無担保コールレートの翌日物です。",
              "金融機関が担保なしで、翌営業日まで資金を借りる際の金利を指します。",
              f"日銀は、この金利が{target}パーセント程度で推移するよう促します。"),
             "data", f"{target}％程度", rate[0]),
    ]
    vote = VOTE.search(body)
    if vote:
        beats.append(Beat("決定会合", "政策委員会の\n採決結果",
                          (f"この金融市場調節方針は、賛成{vote[1]}、反対{vote[2]}で決まりました。",
                           f"発表は、{japanese_date(release)}の金融政策決定会合に基づくものです。"),
                          "document", evidence=vote[0]))
    lending, deposit = BOJ_LENDING.search(body), BOJ_DEPOSIT.search(body)
    if lending and deposit:
        beats.append(Beat("適用金利", "日銀の貸し出しと\n当座預金への付利",
                          (f"日銀が金融機関に貸し出す際の基準貸付利率は、{lending[1]}パーセント。",
                           f"所要準備額にあたる部分を除いた当座預金への付利は、{deposit[1]}パーセントです。"),
                          "data", f"{lending[1]}％", lending[0] + " / " + deposit[0]))
    beats.append(Beat("確認ポイント", "住宅ローンの金利は\n契約ごとに確認",
                      ("この発表の数字は、金融機関の間で動く金利の目安です。",
                       "住宅ローンの適用金利を確認するときは、借入先の案内や契約条件を見てください。"),
                      "document", evidence=rate[0]))
    return beats


def generic_release(release: Release):
    cleaned = []
    for paragraph in release.paragraphs:
        if re.search(r"お問い合わせ|お問合せ|担当課|電話番号|E-mail|PDF形式|ダウンロード|関連リンク", paragraph):
            continue
        for sentence in re.findall(r"[^。！？]+[。！？]", paragraph):
            sentence = re.sub(r"^(?:[0-9０-９]+[.．、)）]|[（(]注\d*[）)])\s*", "", sentence.strip())
            if (28 <= len(sentence) <= 130 and re.search(r"[ぁ-ん]", sentence)
                    and not any(sentence in previous or previous in sentence for previous in cleaned)):
                cleaned.append(sentence)
    if len(cleaned) < 4:
        return []
    # Read short, attributed excerpts. Never splice numbers into a new claim.
    selected = [cleaned[0]]
    for sentence in cleaned[1:]:
        if NUMBER.search(sentence) or len(selected) < 3:
            selected.append(sentence)
        if len(selected) >= 5:
            break
    if len(selected) < 4:
        selected.extend(sentence for sentence in cleaned if sentence not in selected)
        selected = selected[:5]
    headline = re.sub(r"(を公表しました|を発表しました|を取りまとめました|について)$", "", release.title)
    beats = [
        Beat("公表内容", headline,
             (f"{release.publisher}が、{japanese_date(release)}に、「{release.title}」を公表しました。",
              "発表資料に記載された内容を確認します。"), "photo"),
    ]
    for index, sentence in enumerate(selected):
        value = NUMBER.search(sentence)
        beats.append(Beat("発表資料", "発表資料の記載", (sentence,),
                          "data" if value else "document", value[0] if value else "", sentence))
    if sum(len(line) for beat in beats for line in beat.lines) < 255:
        return []
    return beats


def build_story(release):
    return boj_policy(release) or generic_release(release)
