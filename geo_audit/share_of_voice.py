"""Share of Voice(差別化の核). 生成AI検索における「引用シェア」を競合間で算出・追跡する.

日本語×業界別GEOの武器:
  1. 複数サイトの引用likelihoodから、クエリ群にわたる引用シェア(SoV)を配分
  2. 業界ベンチマーク(自社が業界内で上位何%か)
  3. スナップショットを時系列で保持し、SoVの推移を追える
すべて標準ライブラリのみ。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .analysis.structure_score import score_content
from .crawler import ExtractedContent
from .simulate import MentionSimulator


@dataclass
class SoVEntry:
    name: str
    citation_score: float     # クエリ群での引用likelihood合計
    share: float              # 0-1 の引用シェア

    def as_dict(self):
        return {"name": self.name, "citation_score": round(self.citation_score, 3),
                "share": round(self.share, 4)}


@dataclass
class ShareOfVoice:
    entries: List[SoVEntry]
    own_name: str

    def own_share(self) -> float:
        for e in self.entries:
            if e.name == self.own_name:
                return e.share
        return 0.0

    def own_rank(self) -> int:
        ordered = sorted(self.entries, key=lambda e: e.share, reverse=True)
        for i, e in enumerate(ordered, start=1):
            if e.name == self.own_name:
                return i
        return len(ordered)

    def as_dict(self):
        return {"own_name": self.own_name, "own_share": round(self.own_share(), 4),
                "own_rank": self.own_rank(),
                "entries": [e.as_dict() for e in sorted(self.entries, key=lambda x: -x.share)]}


def compute_share_of_voice(contents: Dict[str, ExtractedContent], queries: List[str],
                           own_name: str) -> ShareOfVoice:
    """各サイトの引用likelihood合計から引用シェアを配分する."""
    if own_name not in contents:
        raise ValueError(f"own_name '{own_name}' が contents にありません")
    sim = MentionSimulator()
    scores: Dict[str, float] = {}
    for name, content in contents.items():
        rep = sim.simulate(content, queries, score=score_content(content))
        # クエリごとの引用確率(cited のもの)を合計
        scores[name] = sum(r.cite_probability for r in rep.results if r.cited)
    total = sum(scores.values()) or 1.0
    entries = [SoVEntry(name=n, citation_score=s, share=s / total) for n, s in scores.items()]
    return ShareOfVoice(entries=entries, own_name=own_name)


class SoVTracker:
    """SoVスナップショットを時系列で保持(推移分析)."""

    def __init__(self) -> None:
        self._history: List[Dict] = []

    def snapshot(self, period: str, sov: ShareOfVoice) -> None:
        self._history.append({"period": period, "own_share": sov.own_share(),
                              "own_rank": sov.own_rank()})

    @property
    def history(self) -> List[Dict]:
        return list(self._history)

    def trend(self) -> str:
        if len(self._history) < 2:
            return "flat"
        delta = self._history[-1]["own_share"] - self._history[0]["own_share"]
        return "up" if delta > 0.01 else ("down" if delta < -0.01 else "flat")
