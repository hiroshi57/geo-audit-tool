import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402

from geo_audit import crawler, compute_share_of_voice, SoVTracker  # noqa: E402

GOOD = """
<html><body>
<h1>GEOとは?</h1>
<p>結論: GEOとは生成AI検索に引用されやすく最適化する施策です。更新日 2026-07-01。</p>
<h2>やり方は?</h2><p>調査によると検索の40%が生成AI経由。出典: レポート。効果は2倍。</p>
<ul><li>引用率up</li></ul><h2>FAQ</h2><p>Q. SEOとの違いは? A. 引用最適化です。</p>
</body></html>
"""
POOR = "<html><body><p>雑記です。特に結論はありません。</p></body></html>"


def _contents():
    return {
        "自社": crawler.from_html(GOOD),
        "競合A": crawler.from_html(POOR),
        "競合B": crawler.from_html("<html><body><h1>用語とは</h1><p>結論を先に述べます。出典あり。</p></body></html>"),
    }


def test_share_of_voice_sums_to_one():
    queries = ["GEO とは", "やり方 方法", "効果 引用"]
    sov = compute_share_of_voice(_contents(), queries, own_name="自社")
    total = sum(e.share for e in sov.entries)
    assert abs(total - 1.0) < 1e-6


def test_good_content_wins_higher_share():
    queries = ["GEO とは", "やり方 方法", "効果 引用"]
    sov = compute_share_of_voice(_contents(), queries, own_name="自社")
    shares = {e.name: e.share for e in sov.entries}
    assert shares["自社"] > shares["競合A"]
    assert sov.own_rank() == 1


def test_own_name_must_exist():
    with pytest.raises(ValueError):
        compute_share_of_voice(_contents(), ["x"], own_name="存在しない")


def test_sov_tracker_trend():
    queries = ["GEO とは"]
    tracker = SoVTracker()
    sov = compute_share_of_voice(_contents(), queries, own_name="自社")
    tracker.snapshot("2026-05", sov)
    tracker.snapshot("2026-06", sov)
    assert len(tracker.history) == 2
    assert tracker.trend() in ("up", "down", "flat")


def test_sov_as_dict_shape():
    sov = compute_share_of_voice(_contents(), ["GEO とは"], own_name="自社")
    d = sov.as_dict()
    assert "own_share" in d and "own_rank" in d and "entries" in d
    assert d["entries"] == sorted(d["entries"], key=lambda e: -e["share"])
