"""A dated sample based on the Bank of Japan's January 2025 decision."""
from datetime import date

from .sources import Release

DEMO = Release(
    "https://www.boj.or.jp/mopo/mpmdeci/state_2025/k250124a.htm",
    "金融市場調節方針の変更について",
    date(2025, 1, 24),
    "日本銀行",
    (
        "金融市場調節方針を決定した（賛成8反対1）。",
        "無担保コールレート（オーバーナイト物）を、0.5％程度で推移するよう促す。",
        "日本銀行当座預金のうち所要準備額相当部分を除いた付利金利は0.5％とする。",
        "基準貸付利率を0.75％とする。",
    ),
)
