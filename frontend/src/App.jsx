import { useEffect, useState } from "react";
import * as api from "./api.js";
import AuthPanel from "./components/AuthPanel.jsx";
import History from "./components/History.jsx";
import ResultCard from "./components/ResultCard.jsx";
import TransactionForm from "./components/TransactionForm.jsx";

export default function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(Boolean(api.getToken()));
  const [tab, setTab] = useState("score");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [historyKey, setHistoryKey] = useState(0);

  function signOut(message = "") {
    api.logout();
    setUser(null);
    setResult(null);
    setError(message);
  }

  // an expired or invalid token sends the analyst back to sign in
  function handleError(e) {
    if (e.status === 401) signOut("Your session has expired. Please sign in again.");
    else setError(e.message);
  }

  async function loadUser() {
    try { setUser(await api.me()); setError(""); }
    catch (e) { api.logout(); if (e.status !== 401) setError(e.message); }
    finally { setChecking(false); }
  }

  useEffect(() => { if (api.getToken()) loadUser(); }, []);

  async function score(tx) {
    setBusy(true);
    setError("");
    try {
      const r = await api.predict(tx);
      setResult({ ...r, id: r.prediction_id, variant: r.preprocessing_variant });
      setHistoryKey((k) => k + 1);
    } catch (e) { handleError(e); }
    finally { setBusy(false); }
  }

  if (checking) return <main className="shell"><p className="muted">Checking your session…</p></main>;

  return (
    <main className="shell">
      <header className="top">
        <div>
          <h1>PayGuard</h1>
          <p className="muted">Fraud-risk review for UPI transactions</p>
        </div>
        {user && (
          <div className="user">
            <span>Signed in as <strong>{user.username}</strong></span>
            <button type="button" className="secondary" onClick={() => signOut()}>Sign out</button>
          </div>
        )}
      </header>

      {error && <p className="error banner" role="alert">{error}</p>}

      {!user ? (
        <AuthPanel onLoggedIn={loadUser} />
      ) : (
        <>
          <nav className="tabs" aria-label="Sections">
            <button type="button" className={tab === "score" ? "tab active" : "tab"} onClick={() => setTab("score")}>Score a transaction</button>
            <button type="button" className={tab === "history" ? "tab active" : "tab"} onClick={() => setTab("history")}>History</button>
          </nav>
          {tab === "score" ? (
            <div className="two-col">
              <TransactionForm onSubmit={score} busy={busy} />
              {result ? <ResultCard result={result} /> : (
                <section className="card placeholder"><p className="muted">The risk score and the reasons behind it will appear here.</p></section>
              )}
            </div>
          ) : (
            <History onError={handleError} refreshKey={historyKey} />
          )}
        </>
      )}
      <footer className="muted small">Scores come from a model trained on simulated data. They support an analyst's judgement and do not replace it.</footer>
    </main>
  );
}
