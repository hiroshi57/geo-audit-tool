import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from geo_audit import crawler, score_content, assess, compare, MAX_SCORES  # noqa: E402

GOOD = """
<html><body>
<h1>GEOとは?</h1>
<p>結論: GEOとは生成AI検索に引用されやすく最適化する施策です。要点を解説します。更新日 2026-07-01。</p>
<h2>なぜ重要か?</h2>
<p>調査によると検索の40%が生成AI経由になると予測されています。出典: レポート。売上は2倍。</p>
<ul><li>引用率2.5倍</li></ul>
<h2>FAQ</h2>
<p>Q. SEOとの違いは? A. 引用最適化です。</p>
<table><tr><td>x</td></tr></table>
</body></html>
"""

POOR = """
<html><body>
<p>今日は天気が良かったので散歩しました。まとまりのない雑記です。特に結論はありません。</p>
</body></html>
"""


def test_extract_structure():
    c = crawler.from_html(GOOD)
    assert len(c.headings[1]) == 1
    assert len(c.headings[2]) == 2
    assert c.list_count == 1
    assert c.table_count == 1


def test_good_scores_higher_than_poor():
    good = score_content(crawler.from_html(GOOD))
    poor = score_content(crawler.from_html(POOR))
    assert good.total > poor.total
    assert good.total >= 70
    assert poor.total <= 40


def test_score_within_bounds_and_factor_caps():
    s = score_content(crawler.from_html(GOOD))
    assert 0 <= s.total <= 100
    for f in s.factors:
        assert 0 <= f.score <= f.max_score
        assert f.max_score == MAX_SCORES[f.name]
    assert sum(MAX_SCORES.values()) == 100


def test_poor_content_generates_suggestions():
    s = score_content(crawler.from_html(POOR))
    assert len(s.suggestions) >= 3  # 改善余地が多いので提案が出る


def test_citation_verdict():
    good = assess(score_content(crawler.from_html(GOOD)))
    poor = assess(score_content(crawler.from_html(POOR)))
    assert good.likelihood > poor.likelihood
    assert good.likely_cited is True
    assert poor.likely_cited is False


def test_competitor_ranking_and_gaps():
    contents = {
        "own": crawler.from_html(GOOD),
        "rival": crawler.from_html(POOR),
    }
    report = compare(contents, own_name="own")
    assert report.rows[0].name == "own"   # GOOD が首位
    assert report.own_rank == 1
    # 自社が首位なので首位比ギャップは空
    assert report.gaps_vs_leader() == {}


def test_competitor_gaps_when_behind():
    contents = {
        "own": crawler.from_html(POOR),
        "rival": crawler.from_html(GOOD),
    }
    report = compare(contents, own_name="own")
    assert report.rows[0].name == "rival"
    assert report.own_rank == 2
    gaps = report.gaps_vs_leader()
    assert gaps  # 劣後している因子がある
    assert "evidence" in gaps


def test_own_name_must_exist():
    try:
        compare({"a": crawler.from_html(GOOD)}, own_name="missing")
        assert False
    except ValueError:
        pass
