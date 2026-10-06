from sklearn.metrics import precision_recall_fscore_support
import time 
from pathlib import Path
import numpy as np
import pandas as pd 
from sklearn.base import clone
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from src.config import SEED, FAMILIES, METRICS_DIR

from sklearn.model_selection import StratifiedKFold



def get_cv(n_splits: int = 5, seed: int = SEED) -> StratifiedKFold:
    return StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)

def multiclass_metrics(y_true, y_pred, labels=FAMILIES) -> dict:
    p, r, f, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, zero_division=0)
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro",
                                   labels=labels, zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted",
                                      labels=labels, zero_division=0)),
        "balanced_acc": float(np.mean(r)),
        **{f"precision_{lbl}": float(p[i]) for i, lbl in enumerate(labels)},
        **{f"recall_{lbl}": float(r[i]) for i, lbl in enumerate(labels)},
        **{f"f1_{lbl}": float(f[i]) for i, lbl in enumerate(labels)},
    }


def binary_view(y_true, y_pred) -> dict:
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    true_normal = (y_true == "Normal")
    pred_normal = (y_pred == "Normal")

    n_normal = int(true_normal.sum())
    n_attack = int((~true_normal).sum())

    fpr = float((true_normal & ~pred_normal).sum() / n_normal) if n_normal else 0.0
    fnr = float(((~true_normal) & pred_normal).sum() / n_attack) if n_attack else 0.0
    return {"fpr": fpr, "fnr": fnr}

def evaluate_cv(pipeline, X, y, cv) -> tuple[pd.DataFrame, np.ndarray]:
    """Run CV. Returns (fold_df, oof_predictions). Pass TRAIN data only.

    Manual loop (instead of cross_val_predict) so we can time fit/predict per fold.
    The estimator is cloned each fold so no state leaks between folds.
    """
    fold_rows = []
    oof = np.full(len(y), None, dtype=object)

    for fold_i, (tr_idx, va_idx) in enumerate(cv.split(X, y)):
        X_tr, X_va = X.iloc[tr_idx], X.iloc[va_idx]
        y_tr, y_va = y.iloc[tr_idx], y.iloc[va_idx]

        est = clone(pipeline)

        t0 = time.perf_counter()
        est.fit(X_tr, y_tr)
        fit_time = time.perf_counter() - t0

        t0 = time.perf_counter()
        y_pred = est.predict(X_va)
        pred_time = time.perf_counter() - t0
        pred_time_per_1k = pred_time / len(y_va) * 1000.0

        row = {"fold": fold_i,
               "fit_time": fit_time,
               "predict_time_per_1k": pred_time_per_1k}
        row.update(multiclass_metrics(y_va, y_pred, labels=FAMILIES))
        row.update(binary_view(y_va, y_pred))
        fold_rows.append(row)

        oof[va_idx] = y_pred

    return pd.DataFrame(fold_rows), oof


def save_results(name: str, fold_df: pd.DataFrame, out_dir=METRICS_DIR):
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"cv_results_{name}.csv"
    fold_df.to_csv(path, index=False)
    return path