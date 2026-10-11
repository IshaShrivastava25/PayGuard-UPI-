"""
PayGuard shared evaluation utilities.

Place this file at: notebooks/evaluation.py
Import from any model notebook with:
    from evaluation import evaluate_model, print_comparison_table
"""

import numpy as np
import pandas as pd
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score,
)


def evaluate_model(y_true, y_pred, model_name: str, variant_name: str = "", y_score=None):
    """
    Compute and print a consistent set of metrics for one model + preprocessing variant.

    Parameters
    ----------
    y_true : array-like of true labels (0 = not fraud, 1 = fraud)
    y_pred : array-like of predicted labels (0/1)
    model_name : e.g. "Logistic Regression"
    variant_name : e.g. "SMOTE", "Undersampling", "Class-Weighted", "" (for unsupervised models)
    y_score : optional, predicted probability/anomaly score for ROC-AUC

    Returns
    -------
    dict of metrics, so results can be collected into one comparison table across all five models.
    """
    label = f"{model_name}" + (f" ({variant_name})" if variant_name else "")
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"{'=' * 60}")

    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)

    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()

    print(f"Precision: {precision:.4f}   Recall: {recall:.4f}   F1: {f1:.4f}")
    print(f"\nConfusion Matrix:")
    print(f"                 Predicted Not Fraud   Predicted Fraud")
    print(f"Actual Not Fraud        {tn:>8}              {fp:>6}")
    print(f"Actual Fraud            {fn:>8}              {tp:>6}")

    roc_auc = None
    if y_score is not None:
        try:
            roc_auc = roc_auc_score(y_true, y_score)
            print(f"\nROC-AUC: {roc_auc:.4f}")
        except ValueError:
            pass  # happens if y_score is degenerate (e.g. all same value)

    print(f"\nFull classification report:")
    print(classification_report(y_true, y_pred, target_names=["Not Fraud", "Fraud"], zero_division=0))

    return {
        "model": model_name,
        "variant": variant_name if variant_name else "N/A",
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "roc_auc": round(roc_auc, 4) if roc_auc is not None else None,
        "true_positives": int(tp),
        "false_positives": int(fp),
        "true_negatives": int(tn),
        "false_negatives": int(fn),
    }


def print_comparison_table(results_list):
    """
    Take a list of dicts (each from evaluate_model) and print/return a single
    comparison DataFrame sorted by F1 (not raw recall).

    Why F1 and not raw recall: sorting by recall alone rewards degenerate models
    that flag almost everything as fraud (e.g. heavy undersampling can hit high
    recall by producing huge numbers of false positives). F1 balances precision
    and recall, so the "best" variant is actually usable, not just high-recall.
    Recall is still shown as a column and matters for the final writeup, but it's
    read alongside precision/F1 rather than used as the sole ranking criterion.
    """
    df = pd.DataFrame(results_list)
    df = df.sort_values("f1", ascending=False).reset_index(drop=True)
    print("\n" + "=" * 70)
    print("  MODEL COMPARISON (sorted by F1)")
    print("=" * 70)
    print(df.to_string(index=False))
    return df
