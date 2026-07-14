const BASE = import.meta.env?.VITE_API || "http://localhost:8000";
const h = (t) => ({ "Content-Type": "application/json", "X-Tenant-Id": t });

export async function runAudit(tenant, { url = "", html = "", queries = null }) {
  const r = await fetch(`${BASE}/v1/audit`, {
    method: "POST", headers: h(tenant), body: JSON.stringify({ url, html, queries }),
  });
  return r.json();
}
export function reportUrl(auditId) { return `${BASE}/v1/report/${auditId}`; }
