"""診断レポート生成(Markdown)."""
from __future__ import annotations

from typing import Optional

from .analysis.citation_check import CitationVerdict, assess
from .analysis.competitor import CompetitorReport
from .analysis.structure_score import GeoScore
from .improve import ImprovementPlan
from .simulate import SimulationReport


def _bar(score: float, maximum: float, width: int = 10) -> str:
    filled = int(round(score / maximum * width)) if maximum else 0
    return "#" * filled + "-" * (width - filled)


def render_report(score: GeoScore, url: Optional[str] = None,
                  verdict: Optional[CitationVerdict] = None,
                  competitors: Optional[CompetitorReport] = None) -> str:
    verdict = verdict or assess(score)
    lines = ["# GEO 診断レポート", ""]
    if url:
        lines.append(f"- 対象: {url}")
    lines.append(f"- **総合 GEO スコア: {score.total:.1f} / 100**")
    lines.append(f"- 生成AI引用likelihood: {verdict.likelihood:.2f} "
                 f"({'引用されやすい' if verdict.likely_cited else '改善余地あり'})")
    lines.append("")

    lines.append("## 因子別内訳")
    lines.append("")
    lines.append("| 因子 | スコア | | メモ |")
    lines.append("|------|-------:|--|------|")
    for f in score.factors:
        lines.append(f"| {f.name} | {f.score:.0f}/{f.max_score:.0f} | "
                     f"`{_bar(f.score, f.max_score)}` | {f.note} |")
    lines.append("")

    lines.append("## 引用likelihood 判定")
    for r in verdict.reasons:
        lines.append(f"- {r}")
    lines.append("")

    if score.suggestions:
        lines.append("## 改善提案")
        for i, s in enumerate(score.suggestions, start=1):
            lines.append(f"{i}. {s}")
        lines.append("")

    if competitors:
        lines.append("## 競合比較")
        lines.append("")
        lines.append("| 順位 | サイト | 総合スコア |")
        lines.append("|-----:|--------|----------:|")
        for i, row in enumerate(competitors.rows, start=1):
            mark = " ★自社" if row.name == competitors.own_name else ""
            lines.append(f"| {i} | {row.name}{mark} | {row.total:.1f} |")
        lines.append("")
        gaps = competitors.gaps_vs_leader()
        if gaps:
            lines.append(f"首位との差が大きい因子(自社=第{competitors.own_rank}位):")
            for k, v in sorted(gaps.items(), key=lambda x: -x[1]):
                lines.append(f"- {k}: 首位比 -{v:.0f}点")
            lines.append("")

    return "\n".join(lines)


def render_full_report(score: GeoScore, url: Optional[str] = None,
                       verdict: Optional[CitationVerdict] = None,
                       competitors: Optional[CompetitorReport] = None,
                       simulation: Optional[SimulationReport] = None,
                       plan: Optional[ImprovementPlan] = None) -> str:
    """①スコア ②言及シミュレーション ③改善計画 を1本にまとめた完全版レポート."""
    parts = [render_report(score, url=url, verdict=verdict, competitors=competitors)]

    if simulation is not None:
        s = ["## 生成AI検索 言及シミュレーション",
             f"引用率: {simulation.citation_rate:.0%}", "",
             "| クエリ | 引用 | 確率 | 引用されうる一節 |",
             "|--------|:---:|----:|----------------|"]
        for r in simulation.results:
            mark = "○" if r.cited else "×"
            s.append(f"| {r.query} | {mark} | {r.cite_probability:.2f} | {r.quoted_passage or '-'} |")
        parts.append("\n".join(s))

    if plan is not None:
        p = ["## 改善計画(期待スコア上昇)",
             f"現在 {plan.current_total:.1f} → 施策後(見込) **{plan.projected_total:.1f}** / 100", "",
             "| 優先 | 施策 | 現在→満点 | 期待加点 |",
             "|-----:|------|:---------:|--------:|"]
        for i, a in enumerate(plan.actions, start=1):
            p.append(f"| {i} | {a.action} | {a.current:.0f}/{a.max_score:.0f} | +{a.expected_uplift:.0f} |")
        parts.append("\n".join(p))

    return "\n\n".join(parts)
