"""Build grounded Japanese narration and captions from a primary release."""
from dataclasses import dataclass
import re
import unicodedata

from .sources import Release

NUMBER = re.compile(r"[+＋−-]?\d+(?:[,.]\d+)*(?:\s*兆円|\s*億円|\s*万円|\s*円|\s*%|\s*％|\s*ポイント|\s*万件|\s*万人)")
BOJ_TARGET = re.compile(r"無担保コールレート.{0,32}?([+−-]?\d+(?:\.\d+)?)\s*%\s*程度")
BOJ_LENDING = re.compile(r"基準貸付利率.{0,26}?([+−-]?\d+(?:\.\d+)?)\s*%\s*とする")
BOJ_DEPOSIT = re.compile(r"付利金利.{0,12}?([+−-]?\d+(?:\.\d+)?)\s*%\s*とする")
BOJ_EFFECTIVE = re.compile(r"新たな金融市場調節方針は、翌営業日[（(](\d{1,2}月\d{1,2}日)[）)]から適用")
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
    say: tuple[str, ...] = ()   # what the voice reads when it differs from the caption (kanji readings)
    cut: str = ""               # how the scene arrives: a name of news/edits.py CUTS; "" = the cut of the frame
    why: str = ""               # why these edits were chosen (for the owner's list, never drawn)


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
    effective = BOJ_EFFECTIVE.search(body)
    if vote:
        lines = [f"この金融市場調節方針は、賛成{vote[1]}、反対{vote[2]}で決まりました。"]
        evidence = f"賛成 {vote[1]} / 反対 {vote[2]}"
        if effective:
            lines.append(f"新しい方針の適用は、翌営業日の{effective[1]}からです。")
            evidence += f" / 適用開始 {effective[1]}"
        beats.append(Beat("決定会合", "政策委員会の\n採決結果",
                          tuple(lines), "document", evidence=evidence))
    lending, deposit = BOJ_LENDING.search(body), BOJ_DEPOSIT.search(body)
    if lending and deposit:
        beats.append(Beat("適用金利", "日銀の貸し出しと\n当座預金への付利",
                          (f"日銀が金融機関に貸し出す際の基準貸付利率は、{lending[1]}パーセント。",
                           f"所要準備額にあたる部分を除いた当座預金への付利は、{deposit[1]}パーセントです。"),
                          "data", f"{lending[1]}％", lending[0] + " / " + deposit[0]))
    if "2%の「物価安定の目標」" in body and "金融緩和の度合いを調整" in body:
        beats.append(Beat("決定の背景", "日銀が掲げる\n物価安定の目標",
                          ("日銀は、2パーセントの物価安定目標を持続的に実現するため、金融緩和の度合いを調整すると説明しています。",
                           "住宅ローンの適用金利は、金融機関や借り入れの契約によって異なります。"),
                          "photo", evidence="2％の物価安定目標 / 金融緩和の度合いを調整"))
    else:
        beats.append(Beat("確認ポイント", "住宅ローンの金利は\n契約ごとに確認",
                          ("日銀が公表した金利の目安は、短期金融市場に関するものです。",
                           "住宅ローンの適用金利は、金融機関や借り入れの契約によって異なります。"),
                          "photo", evidence=rate[0]))
    return beats


CPI_ROW = re.compile(
    r"(総合|生鮮食品を除く総合|生鮮食品及びエネルギーを除く総合)指数は"
    r"(?:20\d{2}年を100として)?\s*(\d+(?:\.\d+)?)\s+"
    r"前年同月比は\s*(?:(\d+(?:\.\d+)?)\s*%\s*の)?(上昇|下落|横ばい|変わらず)"
)


def consumer_prices(release):
    if release.publisher != "総務省統計局":
        return []
    title = unicodedata.normalize("NFKC", release.title)
    month = re.search(r"(20\d{2})年\s*(?:\([^)]*\))?\s*(\d{1,2})月分", title)
    base = re.search(r"(20\d{2})年基準", title)
    body = unicodedata.normalize("NFKC", " ".join(release.paragraphs))
    rows = {match[1]: match for match in CPI_ROW.finditer(body)}
    names = ("総合", "生鮮食品を除く総合", "生鮮食品及びエネルギーを除く総合")
    if not month or not base or not all(name in rows for name in names):
        return []
    period = f"{month[1]}年{month[2]}月"
    def change(row):
        return f"{row[3]}パーセント{row[4]}" if row[3] else "横ばい"
    def display(row):
        if not row[3]:
            return "横ばい"
        sign = "＋" if row[4] == "上昇" else "−"
        return f"{sign}{row[3]}％"
    total, core, stripped = (rows[name] for name in names)
    return [
        Beat("物価", "全国の消費者物価\n前年同月との比較",
             (f"{period}の全国の消費者物価は、前年の同じ月と比べて{change(total)}でした。",
              f"総務省統計局が{japanese_date(release)}に発表しました。"),
             "data", display(total), f"総合指数 {total[2]} / 前年同月比"),
        Beat("総合指数", "基準年を100とした\n全国の物価水準",
             (f"総合指数は{total[2]}。基準の{base[1]}年の平均を100とした値です。",
              "指数は基準年から見た水準で、前年同月比は一年前からの変化を表します。"),
             "document", evidence=f"{base[1]}年平均 = 100 / {period} {total[2]}"),
        Beat("生鮮食品を除く", "生鮮食品を除く\n総合指数",
             (f"生鮮食品を除く総合指数は{core[2]}でした。",
              f"一年前との比較では、{change(core)}です。"),
             "data", display(core), f"指数 {core[2]} / 前年同月比"),
        Beat("生鮮食品・エネルギーを除く", "生鮮食品とエネルギーを\n除いた場合",
             (f"生鮮食品とエネルギーの両方を除いた指数は、{stripped[2]}。",
              f"前年の同じ月と比べて、{change(stripped)}でした。"),
             "data", display(stripped), f"指数 {stripped[2]} / 前年同月比"),
        Beat("確認ポイント", "集計範囲をそろえて\n物価の変化を見る",
             ("消費者物価指数は、集計に含める品目によって値が変わります。",
              "月ごとの動きを比べるときは、同じ範囲の指数を確認してください。"),
             evidence="総合 / 生鮮食品を除く総合 / 生鮮食品及びエネルギーを除く総合"),
    ]


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
    for sentence in selected:
        beats.append(Beat("発表資料", headline, (sentence,), evidence=sentence))
    if sum(len(line) for beat in beats for line in beat.lines) < 255:
        return []
    return beats


def build_story(release):
    return boj_policy(release) or consumer_prices(release) or generic_release(release)
