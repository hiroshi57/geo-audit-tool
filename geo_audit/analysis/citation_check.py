"""引用されやすさの判定. 構造スコアの因子から「引用likelihood」を算出する."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .structure_score import GeoScore


@dataclass
class CitationVerdict:
    likely_cited: bool
    likelihood: float          # 0.0-1.0
    reasons: List[str]

    def as_dict(self):
        return {"likely_cited": self.likely_cited,
                "likelihood": round(self.likelihood, 2),
                "reasons": self.reasons}


def assess(score: GeoScore) -> CitationVerdict:
    """evidence と answer_upfront を重視した引用likelihood.

    生成AI検索は「出典に足る事実」「問いへの直接回答」を優先的に引用するため、
    総合点だけでなくこの 2 因子の充足を重み付けする。
    """
    by_name = {f.name: f for f in score.factors}
    reasons: List[str] = []

    base = score.total / 100.0
    evidence = by_name["evidence"].score / by_name["evidence"].max_score
    answer = by_name["answer_upfront"].score / by_name["answer_upfront"].max_score

    likelihood = 0.5 * base + 0.3 * evidence + 0.2 * answer
    likelihood = max(0.0, min(1.0, likelihood))

    if evidence >= 0.6:
        reasons.append("数値・出典が揃っており事実引用の対象になりやすい")
    else:
        reasons.append("事実性(数値/出典)が弱く、引用より要約対象に留まりやすい")
    if answer >= 0.6:
        reasons.append("冒頭に直接回答があり、抜粋引用されやすい")
    else:
        reasons.append("冒頭回答が弱く、引用箇所を特定されにくい")

    return CitationVerdict(likely_cited=likelihood >= 0.6,
                           likelihood=likelihood, reasons=reasons)
