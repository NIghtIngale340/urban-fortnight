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

def _reorder_proba_to_families(proba, classes):
    classes = list(classes)
    out = np.zeros((len(proba), len(FAMILIES)), dtype=float)
    for i, f in enumerate(FAMILIES):
        if f in classes:
            out[:, i] = proba[:, classes.index(f)]
    return out


def evaluate_cv(pipeline, X, y, cv) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """Run CV. Returns (fold_df, oof_pred, oof_proba). Pass TRAIN data only.

    oof_pred : (n,) array of predicted family labels
    oof_proba: (n, 5) array, columns reordered into FAMILIES order
    """
    fold_rows = []
    oof_pred = np.full(len(y), None, dtype=object)
    oof_proba = np.full((len(y), len(FAMILIES)), np.nan)

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

        proba = est.predict_proba(X_va)
        proba = _reorder_proba_to_families(proba, est.named_steps["clf"].classes_)

        row = {
            "fold": fold_i,
            "fit_time": fit_time,
            "predict_time_per_1k": pred_time_per_1k,
        }
        row.update(multiclass_metrics(y_va, y_pred, labels=FAMILIES))
        row.update(binary_view(y_va, y_pred))
        fold_rows.append(row)

        oof_pred[va_idx] = y_pred
        oof_proba[va_idx] = proba

    assert not np.isnan(oof_proba).any(), "OOF probabilities contain NaN (unfilled rows)"
    assert not pd.isna(oof_pred).any(), "OOF predictions contain unfilled rows"

    return pd.DataFrame(fold_rows), oof_pred, oof_proba


def save_results(name: str, fold_df: pd.DataFrame, out_dir=METRICS_DIR):
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"cv_results_{name}.csv"
    fold_df.to_csv(path, index=False)
    return path


def save_oof(name: str, y_pred, y_proba, out_dir=METRICS_DIR):
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"oof_{name}.npz"
    np.savez_compressed(path, y_pred=y_pred, y_proba=y_proba)
    return path


def load_oof(name: str, out_dir=METRICS_DIR):
    data = np.load(out_dir / f"oof_{name}.npz", allow_pickle=True)
    return data["y_pred"], data["y_proba"]



def summarize_cv(results: dict, fpr_limit: float = 0.005) ->pd.DataFrame:
    rows = []

    for name, df in results.items():
        row = {
            "model": name,
            "n_folds": len(df),
            "macro_f1_mean": df["macro_f1"].mean(),
            "macro_f1_sd": df["macro_f1"].std(),
            "accuracy_mean": df["accuracy"].mean(),
            "fpr_mean": df["fpr"].mean(),
            "fnr_mean": df["fnr"].mean(),
            "fit_time_mean": df["fit_time"].mean(),
            "predict_time_per_1k_mean": df["predict_time_per_1k"].mean(),
            "passes_fpr": bool(df["fpr"].mean() <= fpr_limit),
        }
        for fam in FAMILIES:
            row[f"recall_{fam}_mean"] = df[f"recall_{fam}"].mean()
            row[f"recall_{fam}_sd"] = df[f"recall_{fam}"].std()
        rows.append(row)
    return pd.DataFrame(rows)


def paired_diff(a: pd.DataFrame, b: pd.DataFrame, metric: str) -> dict:
    """Per-fold paired comparison (a - b). a and b must share identical folds.

    Returns per-fold deltas, mean delta, and win counts.
    """
    assert len(a) == len(b), "fold count mismatch"
    assert (a["fold"].values == b["fold"].values).all(), "fold indices don't match"
    deltas = a[metric].values - b[metric].values
    return {
        "deltas": deltas,
        "mean_delta": float(deltas.mean()),
        "wins_a": int((deltas > 0).sum()),
        "wins_b": int((deltas < 0).sum()),
        "ties": int((deltas == 0).sum()),
        "n_folds": len(deltas),
    }