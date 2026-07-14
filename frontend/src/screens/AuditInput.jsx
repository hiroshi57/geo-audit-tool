import React, { useState } from "react";

// URL入力/HTML貼付 画面。
export default function AuditInput({ onRun, busy }) {
  const [url, setUrl] = useState("");
  const [htmlText, setHtmlText] = useState("");
  return (
    <div className="card">
      <h2>診断対象を入力</h2>
      <label>URL<br />
        <input style={{ width: "100%" }} placeholder="https://example.com/article"
          value={url} onChange={(e) => setUrl(e.target.value)} />
      </label>
      <p style={{ textAlign: "center", color: "#889" }}>または</p>
      <label>HTMLを貼り付け<br />
        <textarea rows="5" style={{ width: "100%" }} value={htmlText}
          onChange={(e) => setHtmlText(e.target.value)} />
      </label>
      <button className="primary" disabled={busy}
        onClick={() => onRun({ url, html: htmlText })}>
        {busy ? "診断中..." : "GEO診断を実行"}
      </button>
    </div>
  );
}
