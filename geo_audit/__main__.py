"""CLI: URL / ファイルを GEO 診断。 `python -m geo_audit --url https://...`"""
from __future__ import annotations

import argparse
import sys

from . import crawler
from .analysis import score_content, assess
from .improve import build_plan
from .report import render_full_report
from .simulate import MentionSimulator

DEFAULT_QUERIES = ["とは 意味", "やり方 方法", "メリット デメリット"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="geo_audit", description="GEO診断ツール")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--url", help="診断対象URL(要ネットワーク)")
    src.add_argument("--file", help="診断対象HTMLファイル")
    ap.add_argument("--query", action="append", help="言及シミュレーション用クエリ(複数可)")
    args = ap.parse_args(argv)

    try:
        content = crawler.fetch(args.url) if args.url else crawler.from_file(args.file)
    except Exception as e:  # noqa: BLE001
        print(f"取得失敗: {e}", file=sys.stderr)
        return 1

    score = score_content(content)
    queries = args.query or DEFAULT_QUERIES
    sim = MentionSimulator().simulate(content, queries, score=score)
    plan = build_plan(score)
    print(render_full_report(score, url=args.url or args.file, verdict=assess(score),
                             simulation=sim, plan=plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
