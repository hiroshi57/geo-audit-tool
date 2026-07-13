import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from geo_audit import (  # noqa: E402
    crawler, score_content, MentionSimulator, build_plan, render_full_report, assess,
)

GOOD = """
<html><body>
<h1>GEOとは?</h1>
<p>結論: GEOとは生成AI検索に引用されやすく最適化する施策です。更新日 2026-07-01。</p>
<h2>やり方は?</h2>
<p>調査によると検索の40%が生成AI経由。出典: レポート。効果は2倍。</p>
<ul><li>引用率up</li></ul>
<h2>FAQ</h2><p>Q. SEOとの違いは? A. 引用最適化です。</p>
</body></html>
"""

POOR = "<html><body><p>雑記です。特に結論はありません。</p></body></html>"


def test_simulation_citation_rate_higher_for_good():
    queries = ["GEO とは", "やり方 方法", "効果 引用"]
    good = MentionSimulator().simulate(crawler.from_html(GOOD), queries)
    poor = MentionSimulator().simulate(crawler.from_html(POOR), queries)
    assert good.citation_rate > poor.citation_rate
    assert 0.0 <= good.citation_rate <= 1.0


def test_simulation_cited_query_has_passage():
    sim = MentionSimulator().simulate(crawler.from_html(GOOD), ["GEO とは 引用"])
    r = sim.results[0]
    if r.cited:
        assert r.quoted_passage
        assert r.cite_probability >= 0.5


def test_simulation_unrelated_query_not_cited():
    sim = MentionSimulator().simulate(crawler.from_html(GOOD), ["宇宙 ロケット 打ち上げ"])
    assert sim.results[0].cited is False


def test_improvement_plan_prioritizes_biggest_gap():
    plan = build_plan(score_content(crawler.from_html(POOR)), top_n=3)
    assert plan.projected_total >= plan.current_total
    # 期待加点は降順(伸びしろの大きい順)
    uplifts = [a.expected_uplift for a in plan.actions]
    assert uplifts == sorted(uplifts, reverse=True)
    assert all(a.expected_uplift > 0 for a in plan.actions)


def test_projected_total_capped_at_100():
    plan = build_plan(score_content(crawler.from_html(GOOD)), top_n=7)
    assert plan.projected_total <= 100.0


def test_full_report_contains_all_sections():
    c = crawler.from_html(GOOD)
    score = score_content(c)
    sim = MentionSimulator().simulate(c, ["GEO とは"])
    plan = build_plan(score)
    md = render_full_report(score, url="https://x.test", verdict=assess(score),
                            simulation=sim, plan=plan)
    assert "GEO 診断レポート" in md
    assert "言及シミュレーション" in md
    assert "改善計画" in md
