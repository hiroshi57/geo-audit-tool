# geo-audit-tool

自社/クライアントのコンテンツが**生成AI検索(ChatGPT・Perplexity 等)で引用・要約されやすいか**を
診断し、改善提案を出す **GEO(Generative Engine Optimization)診断ツール**の最小版。

## 差別化ポイント

競合の GEO 診断が「定性的なコンサルコメント」中心なのに対し、本ツールは:

1. **構造スコアの数値化** — 引用されやすさを 7 因子・100点満点で**再現性のあるルールベース**採点。
   LLM はスコアを動かさず定性補足のみに使うため、診断結果がブレない。
2. **競合比較** — 複数サイトを並べて GEO スコアをランキングし、**首位との因子別ギャップ**を提示。
3. **引用likelihood 判定** — 「事実性(数値/出典)」と「冒頭の直接回答」を重み付けし、
   引用される確率を 0-1 で出力。

いずれも**ネットワーク・API キー不要**(rule-based)で動作するため clone 直後に試せる。

## スコア因子(合計100)

| 因子 | 満点 | 見るもの |
|------|-----:|---------|
| answer_upfront | 15 | 冒頭の結論/要約 |
| headings | 15 | 見出し階層 + 疑問形見出し |
| structured | 15 | 箇条書き・表 |
| qa_format | 15 | FAQ / Q&A |
| **evidence** | **20** | 統計・数値 + 出典(最重要) |
| freshness | 10 | 公開日/更新日 |
| entity_clarity | 10 | 定義文「XとはYである」 |

## 全機能(3ステップ)

| # | 機能 | 実装 |
|---|------|------|
| ① | 対象URLのコンテンツ取得 | `crawler.fetch` / `from_file` / `from_html` |
| ② | 生成AI検索での**言及シミュレーション分析** | `simulate.MentionSimulator`(引用率・引用される一節・模擬回答) |
| ③ | **改善レポート生成**(期待スコア上昇つき) | `improve.build_plan` + `report.render_full_report` |

## 本番構成（SQLite + HTMLレポート + Vite 2画面）

- **DB**: `geo_audit/db.py`（SQLite・標準ライブラリ）診断履歴保存＋**テナント分離**（越境不可を自動テスト）
- **API**: `geo_audit/api.py`（FastAPI）。/v1/audit（URL/HTML診断）/v1/report（HTML）/v1/history
- **HTMLレポート**: `geo_audit/report_html.py`（スコア＋因子＋言及シミュ＋改善計画、XSSエスケープ）
- **フロント**: `frontend/`（React+Vite）。**URL入力**画面＋**結果ダッシュボード**の2画面。ビルド不要は `frontend/standalone.html`
- **CI**: `.github/workflows/ci.yml`

```bash
uvicorn geo_audit.api:app --reload
cd frontend && npm install && npm run dev     # or: open frontend/standalone.html
python -m pytest -q                            # テスト21件(DB/テナント分離/HTMLレポート/API E2E含む)
```

## クイックスタート

```bash
# デモ(ネットワーク不要): 良質記事 vs 競合を診断してレポート出力
python demo.py

# CLI: URL / ファイルを診断(スコア + 言及シミュレーション + 改善計画)
python -m geo_audit --file page.html --query "GEO とは" --query "やり方"
python -m geo_audit --url https://example.com

# テスト(16件)
python -m pytest -q
```

## 構成

```
geo_audit/
  crawler.py               # URL取得 + HTML構造抽出(from_html/from_file/fetch)
  analysis/
    structure_score.py     # ★差別化コア: 7因子GEOスコア + 改善提案
    citation_check.py       # 引用likelihood 判定
    competitor.py           # 競合比較 + 首位ギャップ
  report.py                # Markdown レポート生成
  prompts/analysis_prompt.md  # LLM定性補足用(スコアは変えない)
demo.py
tests/                     # 外部依存なしで PASS
```
