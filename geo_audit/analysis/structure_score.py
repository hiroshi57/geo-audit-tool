"""GEO 構造スコア(本ツールの差別化コア).

「生成AI検索(ChatGPT/Perplexity)に引用されやすい構造か」を 0-100 で数値化する。
競合の GEO 診断が定性コメント中心なのに対し、本ツールは
再現性のあるルールベース採点 + 因子別内訳 + 具体的改善提案を返す。

因子と満点(合計100):
  answer_upfront  15  冒頭に結論/要約があるか(AIは冒頭を引用しやすい)
  headings        15  見出し階層 + 疑問形見出し(問いに直接答える構造)
  structured      15  箇条書き・表(抽出しやすい構造化)
  qa_format       15  FAQ / Q&A パターン
  evidence        20  統計・数値 + 出典/参照(引用に足る事実性) ★最重要
  freshness       10  日付・更新情報(鮮度)
  entity_clarity  10  定義文(「XとはYである」)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List

from ..crawler import ExtractedContent

MAX_SCORES = {
    "answer_upfront": 15,
    "headings": 15,
    "structured": 15,
    "qa_format": 15,
    "evidence": 20,
    "freshness": 10,
    "entity_clarity": 10,
}

_SUMMARY_MARKERS = ("結論", "要約", "まとめ", "tl;dr", "summary", "この記事では", "ポイントは")
_QUESTION_MARKERS = ("とは", "なぜ", "どうやって", "方法", "?", "？", "how", "what", "why", "できる")
_QA_MARKERS = ("q.", "q:", "質問", "faq", "よくある質問", "a.", "a:", "回答")
_DATE_RE = re.compile(r"(20\d{2})[年/\-.](\d{1,2})|更新日|公開日|最終更新|updated")
_NUMBER_RE = re.compile(r"\d+(\.\d+)?\s*(%|％|円|人|件|倍|位|万|億|kg|km|時間|分|秒)")
_SOURCE_MARKERS = ("出典", "参照", "引用", "according to", "source", "調査", "によると")
_DEFINITION_RE = re.compile(r".{2,40}(とは|というのは).{2,}(です|である|を指す|のこと)")


@dataclass
class FactorResult:
    name: str
    score: float
    max_score: float
    note: str


@dataclass
class GeoScore:
    total: float                        # 0-100
    factors: List[FactorResult]
    suggestions: List[str]

    def as_dict(self) -> Dict:
        return {
            "total": round(self.total, 1),
            "factors": [
                {"name": f.name, "score": round(f.score, 1),
                 "max": f.max_score, "note": f.note}
                for f in self.factors
            ],
            "suggestions": self.suggestions,
        }


def _contains_any(text: str, markers) -> bool:
    low = text.lower()
    return any(m in low for m in markers)


def score_content(content: ExtractedContent) -> GeoScore:
    text = content.text
    low = text.lower()
    factors: List[FactorResult] = []
    suggestions: List[str] = []

    # 1. answer_upfront
    fb = content.first_block.lower()
    if _contains_any(fb, _SUMMARY_MARKERS) or (30 <= len(content.first_block) <= 400):
        s = MAX_SCORES["answer_upfront"]
        note = "冒頭に結論/要約ブロックあり"
    else:
        s = 5.0
        note = "冒頭の結論が弱い"
        suggestions.append("記事冒頭に3行程度の結論/要約(TL;DR)を置くと引用されやすくなる")
    factors.append(FactorResult("answer_upfront", s, MAX_SCORES["answer_upfront"], note))

    # 2. headings
    h1, h2, h3 = (content.headings.get(i, []) for i in (1, 2, 3))
    heading_total = len(h1) + len(h2) + len(h3)
    question_headings = sum(1 for h in (h1 + h2 + h3) if _contains_any(h, _QUESTION_MARKERS))
    hs = 0.0
    if heading_total >= 1:
        hs += 6
    if len(h2) + len(h3) >= 2:
        hs += 5
    if question_headings >= 1:
        hs += 4
    hs = min(hs, MAX_SCORES["headings"])
    if hs < MAX_SCORES["headings"]:
        suggestions.append("見出しを疑問形(例:「〜とは?」)にすると質問クエリに直接マッチする")
    factors.append(FactorResult("headings", hs, MAX_SCORES["headings"],
                                f"見出し{heading_total}個(疑問形{question_headings})"))

    # 3. structured
    struct = min(content.list_count * 4 + content.table_count * 5, MAX_SCORES["structured"])
    if struct < 8:
        suggestions.append("箇条書き・比較表を追加すると要点が抽出されやすい")
    factors.append(FactorResult("structured", float(struct), MAX_SCORES["structured"],
                                f"リスト{content.list_count}/表{content.table_count}"))

    # 4. qa_format
    qa = MAX_SCORES["qa_format"] if _contains_any(low, _QA_MARKERS) else 3.0
    if qa < MAX_SCORES["qa_format"]:
        suggestions.append("FAQ / Q&A セクションを設けると生成AIが回答を組み立てやすい")
    factors.append(FactorResult("qa_format", qa, MAX_SCORES["qa_format"],
                                "FAQ/Q&Aあり" if qa > 3 else "Q&A構造なし"))

    # 5. evidence(★最重要)
    num_hits = len(_NUMBER_RE.findall(text))
    has_source = _contains_any(low, _SOURCE_MARKERS) or content.link_count >= 2
    ev = min(num_hits * 3, 12) + (8 if has_source else 0)
    ev = min(ev, MAX_SCORES["evidence"])
    if ev < MAX_SCORES["evidence"]:
        suggestions.append("統計・数値と出典を明記すると事実引用の対象になりやすい(最重要)")
    factors.append(FactorResult("evidence", float(ev), MAX_SCORES["evidence"],
                                f"数値{num_hits}箇所/出典{'あり' if has_source else 'なし'}"))

    # 6. freshness
    fr = MAX_SCORES["freshness"] if _DATE_RE.search(text) else 2.0
    if fr < MAX_SCORES["freshness"]:
        suggestions.append("公開日/更新日を明記すると鮮度シグナルになる")
    factors.append(FactorResult("freshness", fr, MAX_SCORES["freshness"],
                                "日付あり" if fr > 2 else "日付なし"))

    # 7. entity_clarity
    ec = MAX_SCORES["entity_clarity"] if _DEFINITION_RE.search(text) else 3.0
    if ec < MAX_SCORES["entity_clarity"]:
        suggestions.append("「XとはYである」形式の定義文を入れるとエンティティ理解が上がる")
    factors.append(FactorResult("entity_clarity", ec, MAX_SCORES["entity_clarity"],
                                "定義文あり" if ec > 3 else "定義文なし"))

    total = sum(f.score for f in factors)
    return GeoScore(total=total, factors=factors, suggestions=suggestions)
