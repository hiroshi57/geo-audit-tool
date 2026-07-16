"""GEO診断 API(FastAPI). URL/HTML入力 -> 診断 -> 保存 -> HTMLレポート.
テナント分離(X-Tenant-Id)。`uvicorn geo_audit.api:app --reload`
"""
from datetime import datetime, timezone

from . import crawler
from .analysis import score_content, assess
from .db import AuditStore
from .improve import build_plan
from .report_html import build_html_report
from .simulate import MentionSimulator

STORE = AuditStore(":memory:")
DEFAULT_QUERIES = ["とは 意味", "やり方 方法", "メリット"]


def run_audit(tenant: str, *, url: str = "", html_text: str = "", queries=None) -> dict:
    content = crawler.fetch(url) if url else crawler.from_html(html_text, url=url or None)
    score = score_content(content)
    queries = queries or DEFAULT_QUERIES
    sim = MentionSimulator().simulate(content, queries, score=score)
    plan = build_plan(score)
    payload = {"score": score.as_dict(), "simulation": sim.as_dict(), "plan": plan.as_dict()}
    now = datetime.now(timezone.utc).isoformat()
    aid = STORE.save(tenant, url or None, score.total, payload, now)
    return {"audit_id": aid, "total": score.total, **payload}


def create_app():  # pragma: no cover
    from fastapi import Depends, FastAPI, Header, HTTPException
    from fastapi.responses import HTMLResponse
    from pydantic import BaseModel

    app = FastAPI(title="GEO Audit Tool", version="1.0.0")

    def tenant(x_tenant_id: str = Header(...)) -> str:
        if not x_tenant_id:
            raise HTTPException(401, "tenant required")
        return x_tenant_id

    class AuditIn(BaseModel):
        url: str = ""
        html: str = ""
        queries: list[str] | None = None

    @app.post("/v1/audit")
    def audit(body: AuditIn, t: str = Depends(tenant)):
        if not body.url and not body.html:
            raise HTTPException(400, "url or html required")
        return run_audit(t, url=body.url, html_text=body.html, queries=body.queries)

    @app.get("/v1/report/{audit_id}", response_class=HTMLResponse)
    def report(audit_id: int, t: str = Depends(tenant)):
        rec = STORE.get(t, audit_id)
        if rec is None:
            raise HTTPException(404, "audit not found")
        # payload から再構成せず、保存済みスコアで簡易HTML(全文はpayloadにあり)
        from .analysis.structure_score import GeoScore, FactorResult
        p = rec["payload"]["score"]
        score = GeoScore(total=p["total"],
                         factors=[FactorResult(f["name"], f["score"], f["max"], f["note"])
                                  for f in p["factors"]], suggestions=p["suggestions"])
        return build_html_report(score, url=rec["url"])

    @app.get("/v1/history")
    def history(t: str = Depends(tenant)):
        return {"history": STORE.history(t)}

    class SoVIn(BaseModel):
        sites: dict          # {name: html}
        queries: list[str] | None = None
        own_name: str

    @app.post("/v1/share-of-voice")
    def share_of_voice(body: SoVIn, t: str = Depends(tenant)):
        # 生成AI検索における競合間の引用シェア(Share of Voice)
        from . import crawler as _crawler
        from .share_of_voice import compute_share_of_voice
        contents = {name: _crawler.from_html(html, url=None) for name, html in body.sites.items()}
        if body.own_name not in contents:
            raise HTTPException(400, "own_name must be in sites")
        sov = compute_share_of_voice(contents, body.queries or DEFAULT_QUERIES, body.own_name)
        return sov.as_dict()

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    return app


try:  # pragma: no cover
    app = create_app()
except Exception:
    app = None
