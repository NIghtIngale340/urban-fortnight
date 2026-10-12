import numpy as np
import matplotlib.pyplot as plt
from src.config import FAMILIES


def _finalize(fig, path):
    if path:
        fig.savefig(path, dpi=120)
    plt.show()
    plt.close(fig)


def plot_macro_f1_box(results, path=None):
    names = list(results.keys())
    data = [results[n]["macro_f1"].values for n in names]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.boxplot(data)
    for i, d in enumerate(data):
        ax.scatter(np.full(len(d), i + 1), d, color="black", zorder=3, s=25)
    ax.set_xticks(range(1, len(names) + 1))
    ax.set_xticklabels(names, rotation=20, ha="right")
    ax.set_ylabel("macro-F1")
    ax.set_title("Per-fold macro-F1 by model (5 CV folds)")
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    _finalize(fig, path)


def plot_per_class_recall(results, path=None):
    names = list(results.keys())
    n = len(names)
    x = np.arange(len(FAMILIES))
    width = 0.8 / n
    fig, ax = plt.subplots(figsize=(10, 5))
    for i, name in enumerate(names):
        df = results[name]
        means = [df[f"recall_{fam}"].mean() for fam in FAMILIES]
        sds = [df[f"recall_{fam}"].std() for fam in FAMILIES]
        offset = (i - n / 2 + 0.5) * width
        ax.bar(x + offset, means, width, yerr=sds, capsize=2, label=name)
    ax.set_xticks(x)
    ax.set_xticklabels(FAMILIES)
    ax.set_ylabel("recall (mean ± SD)")
    ax.set_title("Per-class recall by model")
    ax.legend()
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    _finalize(fig, path)


def plot_fpr_fnr(results, fpr_limit=0.005, path=None):
    names = list(results.keys())
    fprs = [results[n]["fpr"].mean() for n in names]
    fnrs = [results[n]["fnr"].mean() for n in names]
    x = np.arange(len(names))
    w = 0.35
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(x - w / 2, fprs, w, label="FPR")
    ax.bar(x + w / 2, fnrs, w, label="FNR")
    ax.axhline(fpr_limit, color="red", linestyle="--", label=f"FPR limit ({fpr_limit})")
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=20, ha="right")
    ax.set_ylabel("rate")
    ax.set_title("FPR vs FNR by model")
    ax.legend()
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    _finalize(fig, path)


def plot_fit_time(results, path=None):
    names = list(results.keys())
    fit = [results[n]["fit_time"].mean() for n in names]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(names, fit, color="steelblue")
    ax.set_ylabel("fit time (s)")
    ax.set_title("Mean CV fit time by model")
    ax.tick_params(axis="x", rotation=20)
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    _finalize(fig, path)


def plot_predict_time(results, path=None):
    names = list(results.keys())
    pred = [results[n]["predict_time_per_1k"].mean() for n in names]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(names, pred, color="coral")
    ax.set_ylabel("predict time per 1k rows (s)")
    ax.set_title("Mean predict latency by model")
    ax.tick_params(axis="x", rotation=20)
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    _finalize(fig, path)