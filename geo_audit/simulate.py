"""② 生成AI検索での言及シミュレーション分析.

想定クエリ群に対し、生成AI検索(ChatGPT/Perplexity)がこのコンテンツを
「引用・要約するか」をシミュレートする。構造スコアとクエリ関連度から
引用確率を出し、引用されそうな一節と模擬回答を提示する。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List

from .analysis.structure_score import GeoScore, score_content
from .crawler import ExtractedContent

_TOKEN_RE = re.compile(r"[a-zA-Z0-9]+|[぀-ヿ一-鿿々〆ぁ-んァ-ヶ]{2,}")


def _tokens(text: str) -> List[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


def _relevance(query: str, text: str) -> float:
    q = set(_tokens(query))
    if not q:
        return 0.0
    body = set(_tokens(text))
    return len(q & body) / len(q)


def _best_passage(query: str, text: str) -> str:
    q = set(_tokens(query))
    best, best_score = "", -1
    for sent in re.split(r"[。\n.!?！？]", text):
        s = sent.strip()
        if not s:
            continue
        overlap = len(q & set(_tokens(s)))
        if overlap > best_score:
            best, best_score = s, overlap
    return best[:120]


@dataclass
class QuerySimulation:
    query: str
    cited: bool
    cite_probability: float
    quoted_passage: str
    mock_answer: str

    def as_dict(self):
        return self.__dict__


@dataclass
class SimulationReport:
    citation_rate: float
    results: List[QuerySimulation] = field(default_factory=list)

    def as_dict(self):
        return {"citation_rate": round(self.citation_rate, 2),
                "results": [r.as_dict() for r in self.results]}


class MentionSimulator:
    def __init__(self, threshold: float = 0.5) -> None:
        self.threshold = threshold

    def simulate(self, content: ExtractedContent, queries: List[str],
                 score: GeoScore = None) -> SimulationReport:
        score = score or score_content(content)
        base = score.total / 100.0
        results: List[QuerySimulation] = []
        for q in queries:
            rel = _relevance(q, content.text)
            # 引用確率 = 構造スコア(引用適性) と クエリ関連度 の合成
            prob = round(0.6 * base + 0.4 * rel, 2)
            cited = prob >= self.threshold and rel > 0
            passage = _best_passage(q, content.text) if cited else ""
            answer = (f"生成AIは「{passage}」を引用して回答を生成する可能性が高い"
                      if cited else "このコンテンツは引用されにくい(要約対象に留まる)")
            results.append(QuerySimulation(q, cited, prob, passage, answer))
        rate = sum(1 for r in results if r.cited) / len(results) if results else 0.0
        return SimulationReport(citation_rate=rate, results=results)
