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
from scipy.stats import binomtest

from sklearn.model_selection import StratifiedKFold

from sklearn.model_selection import RepeatedStratifiedKFold
from scipy.stats import binomtest



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


# Replace your evaluate_cv signature/body with this (adds return_oof):
def evaluate_cv(pipeline, X, y, cv, return_oof: bool = True):
    """Run CV. Returns (fold_df, oof_pred, oof_proba) if return_oof else fold_df.

    Use return_oof=False for repeated CV (a row would otherwise get several OOF
    predictions). Pass TRAIN data only.
    """
    fold_rows = []
    if return_oof:
        oof_pred = np.full(len(y), None, dtype=object)
        oof_proba = np.full((len(y), len(FAMILIES)), np.nan)

    for fold_i, (tr_idx, va_idx) in enumerate(cv.split(X, y)):
        X_tr, X_va = X.iloc[tr_idx], X.iloc[va_idx]
        y_tr, y_va = y.iloc[tr_idx], y.iloc[va_idx]
        est = clone(pipeline)
        t0 = time.perf_counter(); est.fit(X_tr, y_tr); fit_time = time.perf_counter() - t0
        t0 = time.perf_counter(); y_pred = est.predict(X_va); pred_time = time.perf_counter() - t0

        row = {"fold": fold_i, "fit_time": fit_time,
               "predict_time_per_1k": pred_time / len(y_va) * 1000.0}
        row.update(multiclass_metrics(y_va, y_pred, labels=FAMILIES))
        row.update(binary_view(y_va, y_pred))
        fold_rows.append(row)

        if return_oof:
            proba = _reorder_proba_to_families(est.predict_proba(X_va),
                                               est.named_steps["clf"].classes_)
            oof_pred[va_idx] = y_pred
            oof_proba[va_idx] = proba

    fold_df = pd.DataFrame(fold_rows)
    if return_oof:
        assert not np.isnan(oof_proba).any(), "OOF probabilities contain NaN"
        assert not pd.isna(oof_pred).any(), "OOF predictions contain unfilled rows"
        return fold_df, oof_pred, oof_proba
    return fold_df


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


def wilson_ci(k: int, n: int, conf: float = 0.95):
    if n == 0:
        return (np.nan, np.nan)
    res = binomtest(int(k), int(n))
    ci = res.proportion_ci(confidence_level=conf, method="wilson")
    return float(ci.low), float(ci.high)


def per_attack_recall(meta_attack, y_pred, family, attack_to_family):
    meta = np.asarray(meta_attack)
    y_pred = np.asarray(y_pred)
    attacks = [a for a, f in attack_to_family.items() if f == family and a != "normal"]

    rows = []
    for attack in attacks:
        mask = meta == attack
        n = int(mask.sum())
        if n == 0:
            continue
        k = int((y_pred[mask] == family).sum())
        lo, hi = wilson_ci(k, n)
        wrong = y_pred[mask][y_pred[mask] != family]
        most_wrong = pd.Series(wrong).value_counts().idxmax() if len(wrong) else "-"
        rows.append({"attack": attack, "family": family, "n": n, "k_correct": k,
                     "recall": k / n, "ci_low": lo, "ci_high": hi,
                     "most_common_wrong": most_wrong})
    return pd.DataFrame(rows).sort_values("n", ascending=False).reset_index(drop=True)

def missed_destinations(y_true_family, y_pred, family):
    """Where rows of `family` that were MISSED got predicted instead."""
    y_true_family = np.asarray(y_true_family)
    y_pred = np.asarray(y_pred)
    mask = (y_true_family == family) & (y_pred != family)
    return pd.Series(y_pred[mask]).value_counts()


def fp_breakdown(oof_pred, y_true_family, X, by=("service", "flag")):
    """Break down false positives (true Normal predicted as attack) by categorical value."""
    oof_pred = np.asarray(oof_pred)
    y_true_family = np.asarray(y_true_family)
    fp_mask = (y_true_family == "Normal") & (oof_pred != "Normal")
    n_fp = int(fp_mask.sum())
    X_fp = X.iloc[fp_mask]                      # positional alignment
    frames = []
    for col in by:
        f = X_fp[col].value_counts().reset_index()
        f.columns = [col, "n_fp"]
        f["share_of_fp"] = f["n_fp"] / n_fp if n_fp else np.nan
        f["by"] = col
        frames.append(f)
    return pd.concat(frames, ignore_index=True), n_fp



def get_repeated_cv(n_splits=5, n_repeats=3, seed=SEED):
    return RepeatedStratifiedKFold(n_splits=n_splits, n_repeats=n_repeats, random_state=seed)


def sign_test(a, b) -> dict:
    deltas = np.asarray(a) - np.asarray(b)
    wins = int((deltas > 0).sum())
    losses = int((deltas < 0).sum())
    ties = int((deltas == 0).sum())
    n = wins + losses
    p = binomtest(wins, n, 0.5, alternative="greater").pvalue if n else 1.0
    return {"wins": wins, "losses": losses, "ties": ties, "n_non_tie": n, "p_value": float(p)}


def apply_selection_rule(summary: pd.DataFrame, fpr_limit: float = 0.005) -> dict:
    s = summary.copy()
    discarded = s.loc[s["fpr_mean"] > fpr_limit, "model"].tolist()
    s = s[s["fpr_mean"] <= fpr_limit].copy()
    if s.empty:
        return {"winner": None, "step": "all models failed FPR gate", "discarded": discarded}

    
    s["rare_recall"] = s["recall_R2L_mean"] + s["recall_U2R_mean"]
    s["total_time"] = s["fit_time_mean"] + s["predict_time_per_1k_mean"]
    s = s.sort_values("macro_f1_mean", ascending=False).reset_index(drop=True)

    if len(s) == 1:
        return {"winner": s.iloc[0]["model"], "step": "single model passed FPR gate",
                "discarded": discarded}

    top, second = s.iloc[0], s.iloc[1]
    gap = float(top["macro_f1_mean"] - second["macro_f1_mean"])
    pooled_sd = float((top["macro_f1_sd"] + second["macro_f1_sd"]) / 2)
    base = {"gap": gap, "pooled_sd": pooled_sd, "runner_up": second["model"],
            "discarded": discarded}

    if gap > pooled_sd:
        return {"winner": top["model"], "step": "macro-F1 lead exceeds 1 fold SD", **base}
    if top["rare_recall"] != second["rare_recall"]:
        w = top if top["rare_recall"] > second["rare_recall"] else second
        return {"winner": w["model"], "step": "tie-break (a) R2L+U2R recall",
                "runner_up": (second if w is top else top)["model"], **base}
    if top["fpr_mean"] != second["fpr_mean"]:
        w = top if top["fpr_mean"] < second["fpr_mean"] else second
        return {"winner": w["model"], "step": "tie-break (b) lower FPR",
                "runner_up": (second if w is top else top)["model"], **base}
    w = top if top["total_time"] < second["total_time"] else second
    return {"winner": w["model"], "step": "tie-break (c) speed",
            "runner_up": (second if w is top else top)["model"], **base}