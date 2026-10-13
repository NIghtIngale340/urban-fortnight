"""Fit the selected pipeline on ALL training rows and save it with its model card.

    python scripts/train_final.py

Reads (never recomputes) the frozen decisions and results:
  models/selection_decision.json          Phase 17 winner + default/tuned choice
  models/best_params.json                 Phase 16 params (applied only if the winner is "tuned")
  reports/metrics/phase17_selection_summary.csv, p18_threshold_sweep.csv,
  reports/metrics/test_results.json, test_gap_table.csv, .test_evaluated (Phase 19)
Writes:
  models/final_pipeline.joblib, models/model_card.json

The locked test set is never loaded: no load_test(), no test_idx. Test metrics are
copied from the Phase 19 outputs; if any frozen artifact is missing this script stops.
"""
import hashlib
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import joblib
import lightgbm
import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import f1_score

from src.config import (ALERT_TAU, CATEGORICAL_COLS, FAMILIES, FAMILY_COL, METRICS_DIR,
                        MODELS_DIR, RAW_PATH, SEED, USE_CLASS_WEIGHT, USE_ENGINEERED)
from src.data import clean, load_raw, load_train
from src.evaluation import wilson_ci
from src.features import ENGINEERED_COLS
from src.models import get_models
from src.predict import FINAL_PIPELINE_PATH, REQUIRED_COLS

MODEL_CARD_PATH = MODELS_DIR / "model_card.json"
REQUIRED_ARTIFACTS = [
    MODELS_DIR / "selection_decision.json",
    MODELS_DIR / "best_params.json",
    METRICS_DIR / "phase17_selection_summary.csv",
    METRICS_DIR / "p18_threshold_sweep.csv",
    METRICS_DIR / ".test_evaluated",
    METRICS_DIR / "test_results.json",
    METRICS_DIR / "test_gap_table.csv",
]


def _jsonable(d: dict) -> dict:
    return {k: (v if isinstance(v, (str, int, float, bool, type(None))) else repr(v))
            for k, v in d.items()}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_final_pipeline():
    """Return (unfitted pipeline, winner, config_choice, decision) from the frozen Phase 17 record."""
    decision = json.loads((MODELS_DIR / "selection_decision.json").read_text())
    winner = decision["winner"]
    choice = decision["chosen_config"][winner]
    pipe = get_models(class_weight=USE_CLASS_WEIGHT, engineered=USE_ENGINEERED)[winner]
    if choice == "tuned":
        best = json.loads((MODELS_DIR / "best_params.json").read_text())
        pipe.set_params(**best[winner])
    return pipe, winner, choice, decision


def main() -> None:
    missing = [str(p) for p in REQUIRED_ARTIFACTS if not p.exists()]
    if missing:
        sys.exit("Missing frozen artifacts (run the notebooks through Phase 19 first; "
                 f"this script will not evaluate anything itself): {missing}")

    pipe, winner, choice, decision = build_final_pipeline()

    # ---- train rows only ------------------------------------------------------
    X_train, y_train, _ = load_train()

    t0 = time.perf_counter()
    pipe.fit(X_train, y_train)
    fit_seconds = time.perf_counter() - t0
    assert list(X_train.columns) == REQUIRED_COLS, "train columns drifted from src.predict.REQUIRED_COLS"

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, FINAL_PIPELINE_PATH)

    # Reproducibility check against the Phase 19 refit (same data, settings, seed).
    t0 = time.perf_counter()
    train_pred = pipe.predict(X_train)
    predict_ms_per_1k = (time.perf_counter() - t0) / len(X_train) * 1e6
    train_f1 = f1_score(y_train, train_pred, average="macro", labels=FAMILIES, zero_division=0)
    gap = pd.read_csv(METRICS_DIR / "test_gap_table.csv").set_index("model")
    phase19_train_f1 = float(gap.loc[winner, "train_macro_f1"])

    # ---- frozen results, copied not recomputed --------------------------------
    cv = pd.read_csv(METRICS_DIR / "phase17_selection_summary.csv").set_index("model").loc[winner]
    sweep = pd.read_csv(METRICS_DIR / "p18_threshold_sweep.csv")
    oof_at_tau = sweep.iloc[(sweep["tau"] - ALERT_TAU).abs().argmin()]
    test = json.loads((METRICS_DIR / "test_results.json").read_text())

    # Class support on test = total - train (labels only; the test rows themselves are not used).
    total = clean(load_raw())[0][FAMILY_COL].value_counts()
    support = (total - y_train.value_counts()).astype(int).to_dict()

    def rare_ci(metrics: dict) -> dict:
        out = {}
        for fam in ["U2R", "R2L"]:
            n = support[fam]
            k = int(round(metrics[f"recall_{fam}"] * n))
            out[f"recall_{fam}"] = {"k": k, "n": n, "recall": k / n, "wilson95": wilson_ci(k, n)}
        n = support["Normal"]
        k = int(round(metrics["fpr"] * n))
        out["fpr"] = {"false_alarms": k, "n_normal": n, "fpr": k / n, "wilson95": wilson_ci(k, n)}
        return out

    a, t = test[winner], test[f"{winner}_tau"]
    pre = pipe.named_steps["pre"]
    enc = pre.named_transformers_["cat"]
    card = {
        "model_name": "Network Guardian IDS - final pipeline",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "artifact": {"path": str(FINAL_PIPELINE_PATH.relative_to(MODELS_DIR.parent)),
                     "build_command": "python scripts/train_final.py",
                     "inference_module": "src/predict.py"},
        "architecture": {
            "model_id": winner,
            "estimator": type(pipe.named_steps["clf"]).__name__,
            "pipeline_steps": [name for name, _ in pipe.steps],
            "config": choice,
            "hyperparameters": _jsonable(pipe.named_steps["clf"].get_params()),
        },
        "selection": {
            "rule": "Phase 13/17 pre-registered: FPR gate (<=0.5% mean CV FPR) -> rank by mean "
                    "macro-F1 -> if top-2 gap < pooled fold SD, tie-break (a) R2L+U2R recall, "
                    "(b) lower FPR, (c) speed. Tuned replaces default only if it wins >=12/15 "
                    "paired folds.",
            "decision": decision,
        },
        "frozen_settings": {"USE_CLASS_WEIGHT": USE_CLASS_WEIGHT, "USE_ENGINEERED": USE_ENGINEERED,
                            "SEED": SEED, "ALERT_TAU": ALERT_TAU},
        "input_schema": {
            "required_fields": REQUIRED_COLS,
            "categorical_fields": {c: [str(v) for v in cats]
                                   for c, cats in zip(CATEGORICAL_COLS, enc.categories_)},
            "numeric_fields": "all other required fields; finite and >= 0",
            "ignored_fields": ["num_outbound_cmds", "is_host_login", "any other extra field"],
            "unseen_categories": "encoded as all-zeros (OneHotEncoder handle_unknown='ignore'); "
                                 "reported per row by src.predict",
        },
        "preprocessing": {
            "engineered_features": {
                "bytes_ratio": "log1p(src_bytes) - log1p(dst_bytes)",
                "zero_payload": "1 if src_bytes == 0 and dst_bytes == 0",
                "content_activity": "sum of hot, num_failed_logins, num_compromised, num_root, "
                                    "num_file_creations, num_shells, num_access_files",
                "privilege_flag": "1 if root_shell > 0 or su_attempted > 0 or num_root > 0",
            } if USE_ENGINEERED else {},
            "column_transformer": "one-hot(protocol_type, service, flag); binary/numeric passthrough "
                                  "(tree model, no scaling)",
            "n_model_features": int(len(pre.get_feature_names_out())),
            "engineered_cols": ENGINEERED_COLS if USE_ENGINEERED else [],
        },
        "classes": {"family_order": FAMILIES,
                    "estimator_classes_": [str(c) for c in pipe.named_steps["clf"].classes_]},
        "decision_policy": {
            "attack_score": "1 - P(Normal)",
            "rule": "attack_score < tau -> no alert (Normal); attack_score >= tau -> alert, "
                    "family = argmax over DoS/Probe/R2L/U2R",
            "tau": ALERT_TAU,
            "tau_selection": "Phase 18: lowest tau on a 1000-point grid with OOF FPR <= 0.1% "
                             "(5x margin under the 0.5% gate); chosen on train OOF only",
            "oof_at_tau": {k: float(oof_at_tau[k]) for k in
                           ["fpr", "fnr", "macro_f1", "recall_R2L", "recall_U2R"]},
        },
        "training_data": {
            "dataset": "KDD Cup 1999 10% (kddcup.csv), deduplicated, conflicts removed",
            "raw_sha256": _sha256(RAW_PATH),
            "n_train": int(len(X_train)),
            "train_class_counts": {k: int(v) for k, v in y_train.value_counts().items()},
        },
        "cross_validation": {
            "protocol": "5x3 repeated stratified CV on train (Phase 17)",
            "macro_f1_mean": float(cv["macro_f1_mean"]), "macro_f1_sd": float(cv["macro_f1_sd"]),
            "fpr_mean": float(cv["fpr_mean"]), "fnr_mean": float(cv["fnr_mean"]),
            **{f"recall_{f}_mean": float(cv[f"recall_{f}_mean"]) for f in FAMILIES},
            **{f"recall_{f}_sd": float(cv[f"recall_{f}_sd"]) for f in ["R2L", "U2R"]},
        },
        "held_out_test": {
            "source": "reports/metrics/test_results.json (Phase 19, single evaluation, frozen)",
            "evaluated_at": (METRICS_DIR / ".test_evaluated").read_text().strip().splitlines()[0],
            "class_support": support,
            "argmax": {"metrics": test[winner], "rare_class_uncertainty": rare_ci(test[winner])},
            "tau_policy": {"metrics": test[f"{winner}_tau"],
                           "rare_class_uncertainty": rare_ci(test[f"{winner}_tau"])},
        },
        "timing": {
            "final_fit_seconds": round(fit_seconds, 2),
            "train_set_predict_ms_per_1k_rows": round(predict_ms_per_1k, 3),
            "cv_fit_seconds_mean": float(cv["fit_time_mean"]),
            "cv_predict_seconds_per_1k_mean": float(cv["predict_time_per_1k_mean"]),
            "machine": platform.platform(),
        },
        "reproducibility_check": {
            "train_macro_f1_this_fit": float(train_f1),
            "train_macro_f1_phase19": phase19_train_f1,
            "match": bool(abs(train_f1 - phase19_train_f1) < 1e-9),
        },
        "limitations": [
            "Benchmark result on KDD Cup 1999 (1998 simulated traffic); not a guarantee of real-world security.",
            "No zero-day or concept-drift evaluation: attack types absent from training are not covered.",
            "U2R has 42 training and 10 test rows; its recall CI is wide (see held_out_test).",
            "Probabilities come from a class-weighted model and are not calibrated; attack_score is a ranking score.",
            f"tau={ALERT_TAU} trades false alarms for recall: on test, FPR {a['fpr']:.3%} (argmax) -> "
            f"{t['fpr']:.3%} (tau), FNR {a['fnr']:.4%} -> {t['fnr']:.4%}, macro-F1 {a['macro_f1']:.3f} -> "
            f"{t['macro_f1']:.3f}, U2R precision {a['precision_U2R']:.2f} -> {t['precision_U2R']:.2f}. "
            "The 0.1% FPR target was set on train OOF; check the test FPR above against it.",
            "Unseen categorical values are silently zero-encoded by the model; src.predict reports them.",
            "Single model, single machine timing; not load-tested.",
        ],
        "software": {"python": platform.python_version(), "scikit-learn": sklearn.__version__,
                     "lightgbm": lightgbm.__version__, "numpy": np.__version__,
                     "pandas": pd.__version__, "joblib": joblib.__version__},
    }
    MODEL_CARD_PATH.write_text(json.dumps(card, indent=2))

    print(f"winner={winner} ({choice}); fit {fit_seconds:.1f}s on {len(X_train)} train rows")
    print(f"saved {FINAL_PIPELINE_PATH}")
    print(f"saved {MODEL_CARD_PATH}")
    print(f"train macro-F1 {train_f1:.6f} vs Phase 19 {phase19_train_f1:.6f} "
          f"-> {'MATCH' if card['reproducibility_check']['match'] else 'MISMATCH'}")


if __name__ == "__main__":
    main()
