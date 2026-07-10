"""GEO 診断デモ(ネットワーク不要). `python demo.py`"""
from geo_audit import crawler, score_content, assess, compare, render_report

# GEO 最適化された記事(結論冒頭・疑問形見出し・数値/出典・FAQ・定義)
GOOD = """
<html><body>
<h1>生成AI検索対策(GEO)とは?</h1>
<p>結論: GEOとは生成AI検索に引用されやすくコンテンツを最適化する施策です。
本記事では要点を3つにまとめて解説します。更新日 2026-07-01。</p>
<h2>GEOはなぜ重要なのか?</h2>
<p>ある調査によると検索の40%が生成AI経由になると予測されています(出典: 業界レポート)。</p>
<ul><li>引用率が2.5倍</li><li>流入が30%増</li></ul>
<h2>よくある質問(FAQ)</h2>
<p>Q. SEOとどう違う? A. 引用最適化が中心です。</p>
<table><tr><td>比較</td></tr></table>
</body></html>
"""

# 最適化されていない記事(結論なし・見出し弱・数値/出典なし)
POOR = """
<html><body>
<p>今日は天気が良かったので散歩に行きました。いろいろ考えごとをしていました。
なんとなく思ったことをつらつらと書いていきます。特にまとまりはありません。</p>
</body></html>
"""

def main():
    own = crawler.from_html(GOOD, url="https://example.com/geo")
    score = score_content(own)
    verdict = assess(score)

    contents = {
        "自社記事": own,
        "競合A": crawler.from_html(POOR, url="https://competitor-a.com"),
    }
    comp = compare(contents, own_name="自社記事")

    print(render_report(score, url="https://example.com/geo",
                        verdict=verdict, competitors=comp))


if __name__ == "__main__":
    main()
