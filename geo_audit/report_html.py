"""GEO診断 HTMLレポート(標準ライブラリのみ)."""
from __future__ import annotations

import html
from typing import Dict, Optional

from .analysis.structure_score import GeoScore
from .improve import ImprovementPlan
from .simulate import SimulationReport


def _bar(v: float, mx: float, width: int = 140) -> str:
    w = int(max(0, min(1, v / mx)) * width) if mx else 0
    return (f'<div style="background:#e4e7ee;border-radius:4px;width:{width}px;height:12px;display:inline-block">'
            f'<div style="background:#2bb673;height:12px;border-radius:4px;width:{w}px"></div></div>')


def build_html_report(score: GeoScore, url: Optional[str] = None,
                      simulation: Optional[SimulationReport] = None,
                      plan: Optional[ImprovementPlan] = None) -> str:
    u = html.escape(url or "-")
    factors = "".join(
        f'<tr><td>{html.escape(f.name)}</td><td>{f.score:.0f}/{f.max_score:.0f}</td>'
        f'<td>{_bar(f.score, f.max_score)}</td><td>{html.escape(f.note)}</td></tr>'
        for f in score.factors)
    sim_html = ""
    if simulation is not None:
        rows = "".join(
            f'<tr><td>{html.escape(r.query)}</td><td>{"○" if r.cited else "×"}</td>'
            f'<td>{r.cite_probability:.2f}</td><td>{html.escape(r.quoted_passage or "-")}</td></tr>'
            for r in simulation.results)
        sim_html = (f'<h2>生成AI検索 言及シミュレーション</h2><p>引用率: {simulation.citation_rate:.0%}</p>'
                    f'<table><tr><th>クエリ</th><th>引用</th><th>確率</th><th>一節</th></tr>{rows}</table>')
    plan_html = ""
    if plan is not None:
        rows = "".join(
            f'<tr><td>{i}</td><td>{html.escape(a.action)}</td><td>{a.current:.0f}/{a.max_score:.0f}</td>'
            f'<td>+{a.expected_uplift:.0f}</td></tr>'
            for i, a in enumerate(plan.actions, 1))
        plan_html = (f'<h2>改善計画</h2><p>現在 {plan.current_total:.1f} → 施策後(見込) '
                     f'<b>{plan.projected_total:.1f}</b> / 100</p>'
                     f'<table><tr><th>優先</th><th>施策</th><th>現在→満点</th><th>期待加点</th></tr>{rows}</table>')

    return f"""<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8">
<title>GEO診断レポート</title>
<style>body{{font-family:system-ui,sans-serif;margin:24px;color:#1a1a2e}}
h1{{color:#2bb673}} table{{border-collapse:collapse;margin:8px 0}}
th,td{{border:1px solid #dde;padding:6px 10px}} th{{background:#eafaf1}}
.big{{font-size:40px;color:#2bb673;font-weight:bold}}</style></head><body>
<h1>GEO診断レポート</h1>
<p>対象: {u}</p>
<p>総合GEOスコア: <span class="big">{score.total:.1f}</span> / 100</p>
<h2>因子別内訳</h2>
<table><tr><th>因子</th><th>スコア</th><th></th><th>メモ</th></tr>{factors}</table>
{sim_html}
{plan_html}
</body></html>"""
