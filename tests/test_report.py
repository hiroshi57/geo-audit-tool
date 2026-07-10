import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from geo_audit import crawler, score_content, compare, render_report  # noqa: E402

HTML = "<html><body><h1>GEOとは?</h1><p>結論: 生成AI最適化です。数値は50%。出典あり。更新日 2026-07-01。</p><ul><li>a</li></ul></body></html>"


def test_report_contains_key_sections():
    c = crawler.from_html(HTML)
    md = render_report(score_content(c), url="https://x.test")
    assert "GEO 診断レポート" in md
    assert "総合 GEO スコア" in md
    assert "因子別内訳" in md
    assert "https://x.test" in md


def test_report_includes_competitor_table():
    contents = {"own": crawler.from_html(HTML),
                "rival": crawler.from_html("<html><body><p>雑記です。</p></body></html>")}
    report = compare(contents, own_name="own")
    md = render_report(score_content(contents["own"]), competitors=report)
    assert "競合比較" in md
    assert "★自社" in md
