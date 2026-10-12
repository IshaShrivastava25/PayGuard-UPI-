import { useEffect, useState } from "react";
import * as api from "../api.js";
import { formatTime, money } from "../format.js";
import ResultCard from "./ResultCard.jsx";

const PAGE = 10;

export default function History({ onError, refreshKey }) {
  const [rows, setRows] = useState([]);
  const [offset, setOffset] = useState(0);
  const [label, setLabel] = useState("");
  const [hasNext, setHasNext] = useState(false);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);

  useEffect(() => { setOffset(0); }, [label, refreshKey]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    // ask for one extra row so we know whether a next page exists
    api.listPredictions({ limit: PAGE + 1, offset, label: label || undefined })
      .then((data) => {
        if (cancelled) return;
        setHasNext(data.length > PAGE);
        setRows(data.slice(0, PAGE));
      })
      .catch((e) => !cancelled && onError(e))
      .finally(() => !cancelled && setLoading(false));
    return () => { cancelled = true; };
  }, [offset, label, refreshKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const asResult = (r) => ({ ...r, variant: r.model_variant });

  return (
    <section className="card">
      <div className="row-between">
        <h2>Your scored transactions</h2>
        <label className="inline">Show
          <select value={label} onChange={(e) => setLabel(e.target.value)}>
            <option value="">All</option>
            <option value="fraud">Flagged only</option>
            <option value="not_fraud">Not flagged only</option>
          </select>
        </label>
      </div>

      {loading ? <p className="muted">Loading…</p> : rows.length === 0 ? (
        <p className="muted">Nothing here yet. Score a transaction to see it listed.</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Scored</th><th>Sender → Receiver</th><th>Type</th><th className="num">Amount</th><th className="num">Score</th><th>Result</th></tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id} className={selected?.id === r.id ? "selected" : ""}>
                  <td>{formatTime(r.created_at)}</td>
                  <td className="vpa">{r.sender_vpa} → {r.receiver_vpa}</td>
                  <td>{r.transaction_mode}</td>
                  <td className="num">{money(r.amount)}</td>
                  <td className="num">{(r.risk_score * 100).toFixed(0)}</td>
                  <td><span className={r.label === "fraud" ? "badge flagged" : "badge ok"}>{r.label === "fraud" ? "⚑ Flagged" : "✓ Not flagged"}</span></td>
                  <td><button type="button" className="link" onClick={() => setSelected(selected?.id === r.id ? null : r)}>
                    {selected?.id === r.id ? "Hide" : "Why?"}</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="row-between">
        <button type="button" className="secondary" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE))}>← Newer</button>
        <button type="button" className="secondary" disabled={!hasNext} onClick={() => setOffset(offset + PAGE)}>Older →</button>
      </div>

      {selected && <ResultCard result={asResult(selected)} />}
    </section>
  );
}
