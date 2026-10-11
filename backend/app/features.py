"""
Live feature builder for PayGuard.

Mirrors notebook 03 (feature engineering) one-to-one so that a single incoming
transaction is turned into EXACTLY the same 21 features the model was trained on.
If you change feature logic in notebook 03, change it here too, then re-run
tests/parity_check.py.

History features (sender_txn_count_so_far, sender_avg_amount_so_far,
is_new_receiver) use the same defaults the training data effectively had:
100% of senders in the 80k sample appeared once, so these were constant and the
model assigns them zero importance (SHAP = 0). No database lookup is needed.
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd

TRANSACTION_MODES = ["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]

# Training-time defaults (notebook 03, section 1). DEFAULT_AVG_AMOUNT is the global
# mean transaction amount of the adapted dataset, printed in notebook 03 output.
DEFAULT_TXN_COUNT = 0
DEFAULT_AVG_AMOUNT = 182181.324356
DEFAULT_IS_NEW_RECEIVER = 1


def build_raw_features(tx: dict) -> dict:
    """tx -> dict of the 21 UNSCALED features (keys match the training columns)."""
    mode = tx["transaction_mode"]
    if mode not in TRANSACTION_MODES:
        raise ValueError(f"transaction_mode must be one of {TRANSACTION_MODES}, got {mode!r}")

    amount = float(tx["amount"])
    sbb = float(tx["sender_balance_before"])
    sba = float(tx["sender_balance_after"])
    rbb = float(tx["receiver_balance_before"])
    rba = float(tx["receiver_balance_after"])
    ts: datetime = tx["timestamp"]
    hour = ts.hour

    feats = {
        "amount": amount,
        "receiver_is_merchant": int(tx["receiver_is_merchant"]),
        "sender_balance_before": sbb,
        "sender_balance_after": sba,
        "receiver_balance_before": rbb,
        "receiver_balance_after": rba,
        "sender_txn_count_so_far": DEFAULT_TXN_COUNT,
        "sender_avg_amount_so_far": DEFAULT_AVG_AMOUNT,
        "amount_deviation_ratio": amount / DEFAULT_AVG_AMOUNT,
        "is_new_receiver": DEFAULT_IS_NEW_RECEIVER,
        "hour_of_day": hour,
        "is_off_hours": int(1 <= hour <= 4),
        "sender_balance_error": (sbb - amount) - sba,
        "receiver_balance_delta": rba - rbb,
        # clean balance_ratio: capped at 10, zero-balance case handled by the flag below
        "balance_ratio": min(amount / sbb, 10.0) if sbb != 0 else 0.0,
        "sender_balance_zero": int(sbb == 0),
    }
    for m in TRANSACTION_MODES:
        feats[f"mode_{m}"] = int(mode == m)
    return feats


def to_model_frame(raw_feats: dict, feature_cols: list[str], scaler):
    """Return (raw_df, scaled_df), both one row, columns in the model's training order."""
    raw_df = pd.DataFrame([raw_feats])[feature_cols].astype(float)
    scaled_df = pd.DataFrame(scaler.transform(raw_df), columns=feature_cols)
    return raw_df, scaled_df
