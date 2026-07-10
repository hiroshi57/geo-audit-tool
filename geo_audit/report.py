"""診断レポート生成(Markdown)."""
from __future__ import annotations

from typing import Optional

from .analysis.citation_check import CitationVerdict, assess
from .analysis.competitor import CompetitorReport
from .analysis.structure_score import GeoScore


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
