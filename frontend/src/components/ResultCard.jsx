import { formatValue } from "../format.js";

const ARC = "M 10 100 A 90 90 0 0 1 190 100";

function Gauge({ score, threshold }) {
  const pct = Math.max(0, Math.min(1, score)) * 100;
  const a = Math.PI * (1 - threshold);
  const tick = {
    x1: 100 + 80 * Math.cos(a), y1: 100 - 80 * Math.sin(a),
    x2: 100 + 100 * Math.cos(a), y2: 100 - 100 * Math.sin(a),
  };
  const flagged = score >= threshold;
  return (
    <svg viewBox="0 0 200 115" className="gauge" role="img"
         aria-label={`Risk score ${pct.toFixed(0)} out of 100, flag threshold ${(threshold * 100).toFixed(0)}`}>
      <path d={ARC} pathLength="100" className="gauge-track" />
      <path d={ARC} pathLength="100" className={flagged ? "gauge-fill flagged" : "gauge-fill ok"}
            strokeDasharray={`${pct} 100`} />
      <line {...tick} className="gauge-tick" />
      <text x="100" y="92" textAnchor="middle" className="gauge-number">{pct.toFixed(0)}</text>
      <text x="100" y="110" textAnchor="middle" className="gauge-sub">risk score / 100</text>
    </svg>
  );
}

function Contributor({ c, maxAbs }) {
  const width = maxAbs > 0 ? (Math.abs(c.contribution) / maxAbs) * 100 : 0;
  const up = c.direction === "toward_fraud";
  return (
    <li className="contrib">
      <div className="contrib-text">
        <span className="contrib-label">{c.label}</span>
        <span className="contrib-value">{formatValue(c.feature, c.value)}</span>
      </div>
      <div className="bar-row" aria-hidden="true">
        <div className="bar-half left">{!up && <div className="bar normal" style={{ width: `${width}%` }} />}</div>
        <div className="bar-axis" />
        <div className="bar-half right">{up && <div className="bar fraud" style={{ width: `${width}%` }} />}</div>
      </div>
      <span className="contrib-note">
        {up ? "raises risk" : "lowers risk"} ({c.contribution > 0 ? "+" : ""}{c.contribution.toFixed(2)})
      </span>
    </li>
  );
}

export default function ResultCard({ result }) {
  const flagged = result.label === "fraud";
  const maxAbs = Math.max(...result.top_contributors.map((c) => Math.abs(c.contribution)), 0);
  return (
    <section className="card result" aria-live="polite">
      <div className="result-head">
        <span className={flagged ? "badge flagged" : "badge ok"}>
          {flagged ? "⚑ Flagged for review" : "✓ Not flagged"}
        </span>
        {result.id != null && <span className="muted">Prediction #{result.id}</span>}
      </div>

      <Gauge score={result.risk_score} threshold={result.threshold} />
      <p className="muted center">
        Flagged when the score is at least {(result.threshold * 100).toFixed(0)}. This is a model score, not a
        calibrated probability of fraud, and it never blocks a payment by itself.
      </p>

      <h3>Why this score</h3>
      <ul className="contrib-list">
        {result.top_contributors.map((c) => <Contributor key={c.feature} c={c} maxAbs={maxAbs} />)}
      </ul>
      <p className="muted small">
        Bars show each factor's influence on the model (log-odds, not percentages). Longer means stronger.
        The five strongest factors are shown.
      </p>
      <p className="muted small">Model: {result.model_name} ({result.variant})</p>
    </section>
  );
}
