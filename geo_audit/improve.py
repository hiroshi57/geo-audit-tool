"""③ 改善提案(期待スコア上昇つき). 因子ごとの伸びしろを定量化し優先順位化する."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .analysis.structure_score import GeoScore

# 因子ごとの改善アクション文言
_ACTION = {
    "answer_upfront": "記事冒頭に3行の結論/要約(TL;DR)を置く",
    "headings": "見出しを疑問形(「〜とは?」)にして問いに直接対応させる",
    "structured": "箇条書き・比較表を追加して要点を抽出しやすくする",
    "qa_format": "FAQ / Q&A セクションを設ける",
    "evidence": "統計・数値と出典を明記する(最重要)",
    "freshness": "公開日/更新日を明記する",
    "entity_clarity": "「XとはYである」形式の定義文を入れる",
}


@dataclass
class ImprovementAction:
    factor: str
    action: str
    current: float
    max_score: float
    expected_uplift: float   # この因子を満点にした場合の加点

    def as_dict(self):
        return {"factor": self.factor, "action": self.action,
                "current": round(self.current, 1), "max": self.max_score,
                "expected_uplift": round(self.expected_uplift, 1)}


@dataclass
class ImprovementPlan:
    current_total: float
    projected_total: float
    actions: List[ImprovementAction]

    def as_dict(self):
        return {"current_total": round(self.current_total, 1),
                "projected_total": round(self.projected_total, 1),
                "actions": [a.as_dict() for a in self.actions]}


def build_plan(score: GeoScore, top_n: int = 3) -> ImprovementPlan:
    """伸びしろ(max-current)が大きい因子から改善アクションを優先順位化."""
    actions = [
        ImprovementAction(f.name, _ACTION.get(f.name, f"{f.name}を改善"),
                          f.score, f.max_score, f.max_score - f.score)
        for f in score.factors if f.max_score - f.score > 0
    ]
    actions.sort(key=lambda a: a.expected_uplift, reverse=True)
    top = actions[:top_n]
    projected = score.total + sum(a.expected_uplift for a in top)
    return ImprovementPlan(current_total=score.total,
                           projected_total=min(100.0, projected), actions=top)
