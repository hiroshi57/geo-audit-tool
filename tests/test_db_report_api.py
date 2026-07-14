import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402

from geo_audit import crawler, score_content  # noqa: E402
from geo_audit.db import AuditStore  # noqa: E402
from geo_audit.report_html import build_html_report  # noqa: E402
from geo_audit.simulate import MentionSimulator  # noqa: E402
from geo_audit.improve import build_plan  # noqa: E402

HTML = "<html><body><h1>GEOとは?</h1><p>結論: 生成AI最適化です。数値50%。出典あり。更新日 2026-07-01。</p><ul><li>a</li></ul><h2>FAQ</h2><p>Q. A.</p></body></html>"


def test_audit_store_roundtrip_and_history():
    st = AuditStore(":memory:")
    aid = st.save("t-a", "https://x.test", 72.0, {"score": {"total": 72.0}}, "2026-07-09")
    got = st.get("t-a", aid)
    assert got["total"] == 72.0
    assert len(st.history("t-a")) == 1


def test_audit_store_tenant_isolation():
    st = AuditStore(":memory:")
    aid = st.save("t-a", None, 50.0, {}, "2026-07-09")
    assert st.get("t-b", aid) is None       # 越境不可
    assert st.history("t-b") == []


def test_html_report_sections():
    c = crawler.from_html(HTML)
    score = score_content(c)
    sim = MentionSimulator().simulate(c, ["GEO とは"])
    plan = build_plan(score)
    html = build_html_report(score, url="https://x.test", simulation=sim, plan=plan)
    assert "GEO診断レポート" in html and "因子別内訳" in html
    assert "言及シミュレーション" in html and "改善計画" in html


def test_html_report_escapes_url():
    score = score_content(crawler.from_html(HTML))
    html = build_html_report(score, url="<script>")
    assert "<script>" not in html and "&lt;script&gt;" in html


def test_api_e2e_and_tenant_isolation():
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient
    from geo_audit.api import create_app
    c = TestClient(create_app())
    ha, hb = {"X-Tenant-Id": "t-a"}, {"X-Tenant-Id": "t-b"}
    res = c.post("/v1/audit", json={"html": HTML, "queries": ["GEO とは"]}, headers=ha).json()
    assert res["total"] > 0
    aid = res["audit_id"]
    assert c.get(f"/v1/report/{aid}", headers=hb).status_code == 404   # 越境不可
    r = c.get(f"/v1/report/{aid}", headers=ha)
    assert r.status_code == 200 and "GEO診断レポート" in r.text
