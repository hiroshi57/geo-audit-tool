"""コンテンツ取得 + HTML 構造抽出.

ネットワーク非依存でも動くよう、URL 取得(urllib)に加えて
`from_html` / `from_file` を用意。抽出結果は構造スコアリングの入力になる。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Dict, List, Optional


@dataclass
class ExtractedContent:
    """スコアリングに使う構造化特徴量."""

    url: Optional[str]
    text: str
    headings: Dict[int, List[str]]      # {1: [...], 2: [...], 3: [...]}
    list_count: int
    table_count: int
    link_count: int
    first_block: str                    # 冒頭ブロックのテキスト
    raw_html_len: int

    @property
    def word_count(self) -> int:
        # 日本語は空白区切りでないため文字数ベースも併用
        return max(len(self.text.split()), len(self.text) // 4)


class _StructureParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.headings: Dict[int, List[str]] = {1: [], 2: [], 3: []}
        self.list_count = 0
        self.table_count = 0
        self.link_count = 0
        self._text_parts: List[str] = []
        self._current_heading: Optional[int] = None
        self._skip = False  # script/style 内はスキップ

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip = True
        elif tag in ("h1", "h2", "h3"):
            self._current_heading = int(tag[1])
        elif tag in ("ul", "ol"):
            self.list_count += 1
        elif tag == "table":
            self.table_count += 1
        elif tag == "a":
            self.link_count += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip = False
        elif tag in ("h1", "h2", "h3"):
            self._current_heading = None

    def handle_data(self, data):
        if self._skip:
            return
        text = data.strip()
        if not text:
            return
        self._text_parts.append(text)
        if self._current_heading in (1, 2, 3):
            self.headings[self._current_heading].append(text)

    @property
    def text(self) -> str:
        return "\n".join(self._text_parts)


def from_html(html: str, url: Optional[str] = None) -> ExtractedContent:
    parser = _StructureParser()
    parser.feed(html)
    text = parser.text
    first_block = ""
    for part in text.split("\n"):
        if len(part) >= 20:  # 見出しでない実質的な段落
            first_block = part
            break
    return ExtractedContent(
        url=url,
        text=text,
        headings=parser.headings,
        list_count=parser.list_count,
        table_count=parser.table_count,
        link_count=parser.link_count,
        first_block=first_block or (text[:200] if text else ""),
        raw_html_len=len(html),
    )


def from_file(path: str, url: Optional[str] = None) -> ExtractedContent:
    with open(path, "r", encoding="utf-8") as f:
        return from_html(f.read(), url=url or path)


def fetch(url: str, timeout: float = 10.0) -> ExtractedContent:
    """URL からコンテンツを取得(ネットワーク必要). 失敗時は例外."""
    import urllib.request

    req = urllib.request.Request(url, headers={"User-Agent": "geo-audit-tool/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
        charset = resp.headers.get_content_charset() or "utf-8"
        html = resp.read().decode(charset, errors="replace")
    return from_html(html, url=url)
