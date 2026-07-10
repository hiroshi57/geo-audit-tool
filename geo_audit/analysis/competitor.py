"""競合比較(差別化ポイント). 複数コンテンツの GEO スコアを並べて順位付けする."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from ..crawler import ExtractedContent
from .structure_score import GeoScore, score_content


@dataclass
class CompetitorRow:
    name: str
    total: float
    factor_scores: Dict[str, float]


@dataclass
class CompetitorReport:
    rows: List[CompetitorRow]           # total 降順
    own_name: str

    @property
    def own_rank(self) -> int:
        for i, row in enumerate(self.rows, start=1):
            if row.name == self.own_name:
                return i
        return -1

    def gaps_vs_leader(self) -> Dict[str, float]:
        """自社と首位の因子別差分(正=首位が優位)."""
        leader = self.rows[0]
        own = next((r for r in self.rows if r.name == self.own_name), None)
        if own is None or own.name == leader.name:
            return {}
        return {k: round(leader.factor_scores[k] - own.factor_scores.get(k, 0), 1)
                for k in leader.factor_scores
                if leader.factor_scores[k] - own.factor_scores.get(k, 0) > 0}


def compare(contents: Dict[str, ExtractedContent], own_name: str) -> CompetitorReport:
    if own_name not in contents:
        raise ValueError(f"own_name '{own_name}' が contents に含まれていません")
    rows: List[CompetitorRow] = []
    for name, content in contents.items():
        s: GeoScore = score_content(content)
        rows.append(CompetitorRow(
            name=name, total=s.total,
            factor_scores={f.name: f.score for f in s.factors},
        ))
    rows.sort(key=lambda r: r.total, reverse=True)
    return CompetitorReport(rows=rows, own_name=own_name)
