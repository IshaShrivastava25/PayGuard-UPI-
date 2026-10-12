import { useState } from "react";

const MODES = ["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"];

const EMPTY = {
  sender_vpa: "", receiver_vpa: "", timestamp: "", transaction_mode: "TRANSFER",
  amount: "", sender_balance_before: "", sender_balance_after: "",
  receiver_balance_before: "", receiver_balance_after: "",
};

const EXAMPLES = {
  drained: {
    sender_vpa: "user12345678@okaxis", receiver_vpa: "user87654321@ybl", timestamp: "2026-01-05T03:15",
    transaction_mode: "TRANSFER", amount: "181000", sender_balance_before: "181000", sender_balance_after: "0",
    receiver_balance_before: "0", receiver_balance_after: "0",
  },
  routine: {
    sender_vpa: "user11112222@oksbi", receiver_vpa: "merchant33334444@paytm", timestamp: "2026-01-05T14:30",
    transaction_mode: "PAYMENT", amount: "450", sender_balance_before: "25000", sender_balance_after: "24550",
    receiver_balance_before: "0", receiver_balance_after: "0",
  },
};

const MONEY_FIELDS = [
  ["amount", "Amount (₹)", true],
  ["sender_balance_before", "Sender balance before (₹)"],
  ["sender_balance_after", "Sender balance after (₹)"],
  ["receiver_balance_before", "Receiver balance before (₹)"],
  ["receiver_balance_after", "Receiver balance after (₹)"],
];

export default function TransactionForm({ onSubmit, busy }) {
  const [f, setF] = useState(EMPTY);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  function submit(e) {
    e.preventDefault();
    const tx = { ...f };
    for (const [k] of MONEY_FIELDS) tx[k] = Number(f[k]);
    onSubmit(tx);
  }

  return (
    <form className="card" onSubmit={submit}>
      <h2>Score a transaction</h2>
      <div className="examples">
        <span className="muted small">Fill with an example:</span>
        <button type="button" className="link" onClick={() => setF(EXAMPLES.drained)}>balance drained at 3 AM</button>
        <button type="button" className="link" onClick={() => setF(EXAMPLES.routine)}>small merchant payment</button>
      </div>

      <div className="grid">
        <label>Sender VPA
          <input value={f.sender_vpa} onChange={set("sender_vpa")} required minLength={3} maxLength={100} placeholder="user12345678@okaxis" />
        </label>
        <label>Receiver VPA
          <input value={f.receiver_vpa} onChange={set("receiver_vpa")} required minLength={3} maxLength={100} placeholder="merchant12345678@paytm" />
        </label>
        <label>Transaction time (local)
          <input type="datetime-local" value={f.timestamp} onChange={set("timestamp")} required />
        </label>
        <label>Type
          <select value={f.transaction_mode} onChange={set("transaction_mode")}>
            {MODES.map((m) => <option key={m}>{m}</option>)}
          </select>
        </label>
        {MONEY_FIELDS.map(([k, label, positive]) => (
          <label key={k}>{label}
            <input type="number" inputMode="decimal" step="0.01" min={positive ? "0.01" : "0"}
                   value={f[k]} onChange={set(k)} required />
          </label>
        ))}
      </div>
      <p className="muted small">
        Receivers whose VPA starts with “merchant” are treated as merchants. The hour is taken exactly as entered.
      </p>
      <button type="submit" disabled={busy}>{busy ? "Scoring…" : "Score transaction"}</button>
    </form>
  );
}
