import React, { useState } from "react";
import AuditInput from "./screens/AuditInput.jsx";
import ResultDashboard from "./screens/ResultDashboard.jsx";
import { runAudit, reportUrl } from "./api.js";

const TENANT = "demo-tenant";

export default function App() {
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);

  const run = async ({ url, html }) => {
    setBusy(true);
    try {
      const res = await runAudit(TENANT, { url, html, queries: ["とは 意味", "やり方", "メリット"] });
      setResult(res);
    } catch (e) {
      alert("バックエンド未起動の可能性: " + e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="wrap">
      <h1>GEO診断ツール</h1>
      <AuditInput onRun={run} busy={busy} />
      <ResultDashboard result={result} onOpenReport={(id) => window.open(reportUrl(id), "_blank")} />
    </div>
  );
}
