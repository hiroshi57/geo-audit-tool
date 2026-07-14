"""診断履歴の永続化(SQLite, 標準ライブラリ). テナント分離."""
from __future__ import annotations

import json
import sqlite3
from typing import Dict, List, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS audits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,
    url TEXT,
    total REAL NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


class AuditStore:
    def __init__(self, path: str = ":memory:") -> None:
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def save(self, tenant_id: str, url: Optional[str], total: float,
             payload: Dict, created_at: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO audits(tenant_id, url, total, payload, created_at) VALUES (?,?,?,?,?)",
            (tenant_id, url, total, json.dumps(payload, ensure_ascii=False), created_at))
        self.conn.commit()
        return cur.lastrowid

    def get(self, tenant_id: str, audit_id: int) -> Optional[Dict]:
        row = self.conn.execute(
            "SELECT id, url, total, payload, created_at FROM audits WHERE id=? AND tenant_id=?",
            (audit_id, tenant_id)).fetchone()
        if not row:
            return None    # 越境不可
        return {"id": row["id"], "url": row["url"], "total": row["total"],
                "payload": json.loads(row["payload"]), "created_at": row["created_at"]}

    def history(self, tenant_id: str, limit: int = 20) -> List[Dict]:
        rows = self.conn.execute(
            "SELECT id, url, total, created_at FROM audits WHERE tenant_id=? "
            "ORDER BY id DESC LIMIT ?", (tenant_id, limit)).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        self.conn.close()
