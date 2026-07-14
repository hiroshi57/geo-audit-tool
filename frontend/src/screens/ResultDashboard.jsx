import React from "react";

// 診断結果ダッシュボード: スコア/因子/言及シミュ/改善計画。
function Bar({ v, mx }) {
  return (
    <div style={{ background: "#e4e7ee", borderRadius: 4, width: 140, height: 12, display: "inline-block" }}>
      <div style={{ background: "#2bb673", height: 12, borderRadius: 4, width: `${(v / mx) * 140}px` }} />
    </div>
  );
}

export default function ResultDashboard({ result, onOpenReport }) {
  if (!result) return <div className="card">結果はまだありません。</div>;
  const { score, simulation, plan } = result;
  return (
    <div className="card">
      <h2>総合GEOスコア</h2>
      <div className="big">{score.total.toFixed(1)} <small>/ 100</small></div>

      <h3>因子別内訳</h3>
      <table><thead><tr><th>因子</th><th>スコア</th><th></th><th>メモ</th></tr></thead>
        <tbody>{score.factors.map((f) => (
          <tr key={f.name}><td>{f.name}</td><td>{f.score}/{f.max}</td>
            <td><Bar v={f.score} mx={f.max} /></td><td>{f.note}</td></tr>))}
        </tbody></table>

      {simulation && (
        <>
          <h3>言及シミュレーション（引用率 {Math.round(simulation.citation_rate * 100)}%）</h3>
          <table><thead><tr><th>クエリ</th><th>引用</th><th>確率</th></tr></thead>
            <tbody>{simulation.results.map((r, i) => (
              <tr key={i}><td>{r.query}</td><td>{r.cited ? "○" : "×"}</td><td>{r.cite_probability}</td></tr>))}
            </tbody></table>
        </>
      )}

      {plan && (
        <>
          <h3>改善計画（{plan.current_total.toFixed(0)} → 見込 {plan.projected_total.toFixed(0)}）</h3>
          <ul>{plan.actions.map((a, i) => (
            <li key={i}>{a.action} <b>(+{a.expected_uplift})</b></li>))}</ul>
        </>
      )}

      {result.audit_id && (
        <button className="primary" onClick={() => onOpenReport(result.audit_id)}>HTMLレポートを開く</button>
      )}
    </div>
  );
}
