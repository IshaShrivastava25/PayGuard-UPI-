"""Loads the champion model once and turns a raw transaction into score + explanation."""
from __future__ import annotations

import os
from pathlib import Path

import joblib
import numpy as np
import shap

from .features import build_raw_features, to_model_frame

# backend/app/model_service.py -> parents[2] is the repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BUNDLE_PATH = REPO_ROOT / "models" / "inference_bundle.pkl"

FEATURE_LABELS = {
    "amount": "Transaction amount",
    "receiver_is_merchant": "Receiver is a merchant",
    "sender_balance_before": "Sender balance before",
    "sender_balance_after": "Sender balance after",
    "receiver_balance_before": "Receiver balance before",
    "receiver_balance_after": "Receiver balance after",
    "sender_txn_count_so_far": "Sender's prior transactions",
    "sender_avg_amount_so_far": "Sender's historical average amount",
    "amount_deviation_ratio": "Amount vs. sender's average",
    "is_new_receiver": "First payment to this receiver",
    "hour_of_day": "Hour of day",
    "is_off_hours": "Off-hours (1-4 AM)",
    "sender_balance_error": "Sender balance mismatch",
    "receiver_balance_delta": "Receiver balance change",
    "balance_ratio": "Amount as share of sender balance",
    "sender_balance_zero": "Sender balance was zero",
    "mode_CASH_IN": "Type: CASH_IN",
    "mode_CASH_OUT": "Type: CASH_OUT",
    "mode_DEBIT": "Type: DEBIT",
    "mode_PAYMENT": "Type: PAYMENT",
    "mode_TRANSFER": "Type: TRANSFER",
}


class ModelService:
    def __init__(self, bundle_path: str | os.PathLike | None = None):
        path = Path(bundle_path or os.getenv("PAYGUARD_BUNDLE", DEFAULT_BUNDLE_PATH))
        bundle = joblib.load(path)
        self.model = bundle["model"]
        self.scaler = bundle["scaler"]
        self.feature_cols = list(bundle["feature_cols"])
        self.threshold = float(bundle.get("decision_threshold", 0.5))
        self.model_name = bundle.get("model_name", "unknown")
        self.variant = bundle.get("preprocessing_variant", "unknown")
        # rebuilt at startup instead of pickled, avoiding SHAP version mismatches
        self.explainer = shap.TreeExplainer(self.model)

    def predict(self, tx: dict, top_n: int = 5) -> dict:
        raw = build_raw_features(tx)
        raw_df, scaled_df = to_model_frame(raw, self.feature_cols, self.scaler)

        risk = float(self.model.predict_proba(scaled_df)[0, 1])
        shap_row = np.asarray(self.explainer.shap_values(scaled_df))[0]

        order = np.argsort(-np.abs(shap_row))[:top_n]
        contributors = []
        for i in order:
            name = self.feature_cols[i]
            contrib = float(shap_row[i])
            contributors.append({
                "feature": name,
                "label": FEATURE_LABELS.get(name, name),
                "value": float(raw_df.iloc[0][name]),
                "contribution": round(contrib, 4),
                "direction": "toward_fraud" if contrib > 0 else "toward_normal",
            })

        return {
            "risk_score": round(risk, 4),
            "label": "fraud" if risk >= self.threshold else "not_fraud",
            "threshold": self.threshold,
            "model_name": self.model_name,
            "preprocessing_variant": self.variant,
            "top_contributors": contributors,
        }
