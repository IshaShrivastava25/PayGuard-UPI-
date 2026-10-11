"""
Parity check: does app/features.py reproduce the training features exactly?

Run from the backend/ folder:   python tests/parity_check.py

It takes real rows from the saved test set, undoes the scaling to recover the raw
transaction fields, pushes them through the LIVE feature builder, and compares the
result (and the model's risk score) with what the notebooks produced.
Rows from the handful of repeat senders are skipped, because live scoring uses the
first-time-sender defaults for history features.
"""
import sys
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.features import TRANSACTION_MODES, build_raw_features, to_model_frame  # noqa: E402

train_bundle = joblib.load(REPO_ROOT / "data" / "processed" / "train_test_variants.pkl")
inf = joblib.load(REPO_ROOT / "models" / "inference_bundle.pkl")

feature_cols, scaler, model = inf["feature_cols"], inf["scaler"], inf["model"]
X_test_scaled, y_test = train_bundle["X_test_scaled"], train_bundle["y_test"]

rng = np.random.default_rng(0)
fraud_pos = np.where(y_test.values == 1)[0]
other_pos = rng.choice(np.where(y_test.values == 0)[0], size=500, replace=False)
positions = np.concatenate([fraud_pos, other_pos])

expected_scaled = X_test_scaled.iloc[positions].reset_index(drop=True)
unscaled = pd.DataFrame(scaler.inverse_transform(expected_scaled), columns=feature_cols)

uses_defaults = (unscaled["sender_txn_count_so_far"].round() == 0) & (unscaled["is_new_receiver"].round() == 1)
print(f"Rows checked: {int(uses_defaults.sum())}  (skipped {int((~uses_defaults).sum())} repeat-sender rows)")

mode_cols = [f"mode_{m}" for m in TRANSACTION_MODES]
rebuilt = []
for _, row in unscaled[uses_defaults].iterrows():
    tx = {
        "amount": round(row["amount"], 2),
        "receiver_is_merchant": int(round(row["receiver_is_merchant"])),
        "sender_balance_before": round(row["sender_balance_before"], 2),
        "sender_balance_after": round(row["sender_balance_after"], 2),
        "receiver_balance_before": round(row["receiver_balance_before"], 2),
        "receiver_balance_after": round(row["receiver_balance_after"], 2),
        "timestamp": datetime(2026, 1, 5, int(round(row["hour_of_day"])), 0, 0),
        "transaction_mode": TRANSACTION_MODES[int(np.argmax(row[mode_cols].values))],
    }
    _, scaled = to_model_frame(build_raw_features(tx), feature_cols, scaler)
    rebuilt.append(scaled.iloc[0].values)

rebuilt = pd.DataFrame(rebuilt, columns=feature_cols)
expected = expected_scaled[uses_defaults.values].reset_index(drop=True)

col_diff = (rebuilt - expected).abs().max()
print("\nLargest scaled-feature difference per column:")
print(col_diff.sort_values(ascending=False).head(6).to_string())

proba_diff = np.abs(model.predict_proba(rebuilt)[:, 1] - model.predict_proba(expected)[:, 1]).max()
print(f"\nLargest risk-score difference: {proba_diff:.2e}")

ok = col_diff.max() < 1e-5 and proba_diff < 1e-5
print("\nPARITY OK: live features match training." if ok else "\nPARITY FAILED: see the columns above.")
sys.exit(0 if ok else 1)
