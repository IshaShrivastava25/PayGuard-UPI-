# PayGuard frontend

React (Vite) dashboard for the PayGuard API: analyst login, transaction scoring with a risk gauge
and SHAP-based reasons, and a per-analyst history.

## Run (needs Node 18+; the backend must be running on http://127.0.0.1:8000)

    cd frontend
    npm install
    npm run dev          # opens http://localhost:5173

If your API is elsewhere, copy `.env.example` to `.env.local` and change VITE_API_URL.
Build for production with `npm run build` (output in `dist/`).

## Notes

- The login token is kept in sessionStorage (cleared when the tab closes). A production system should
  use httpOnly cookies.
- The gauge shows the model's score, not a calibrated probability: the model was trained on
  SMOTE-resampled data, so its scores are inflated relative to the real fraud rate.
- Bars in "Why this score" are SHAP values in log-odds, not percentages.
