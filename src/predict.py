"""Production inference for the frozen Network Guardian pipeline.

Usage:
    from src.predict import predict_connection, predict_batch
    predict_connection({...41 raw KDD fields...})  -> dict
    predict_batch(df)                               -> list[dict]
Decision rule (Phase 18, frozen):
    attack_score = 1 - P(Normal)
    attack_score <  ALERT_TAU -> no alert, family "Normal"
    attack_score >= ALERT_TAU -> alert, family = argmax over the four attack classes
"""
import json
import sys
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from src.config import (ALERT_TAU, CATEGORICAL_COLS, CONSTANT_COLS, FAMILIES,
                        FEATURE_NAMES, MODELS_DIR)
from src.evaluation import _reorder_proba_to_families, attack_score, decide

FINAL_PIPELINE_PATH = MODELS_DIR / "final_pipeline.joblib"

# The 39 raw columns the pipeline was fitted on, in training order.
# CONSTANT_COLS are part of a raw KDD record but were dropped in cleaning; they are accepted and ignored.
REQUIRED_COLS: list[str] = [c for c in FEATURE_NAMES if c not in CONSTANT_COLS]
NUMERIC_INPUT_COLS: list[str] = [c for c in REQUIRED_COLS if c not in CATEGORICAL_COLS]


class SchemaError(ValueError):
    """Raised when an input record does not match the raw feature schema."""


@lru_cache(maxsize=4)
def load_model(path: Path | str = FINAL_PIPELINE_PATH) -> Pipeline:
    """Load the fitted pipeline (feature engineering + preprocessing + classifier)."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Build it with: python scripts/train_final.py")
    model = joblib.load(path)
    classes = list(model.named_steps["clf"].classes_)
    if sorted(classes) != sorted(FAMILIES):
        raise ValueError(f"Model classes {classes} do not match FAMILIES {FAMILIES}")
    return model


def validate_input(df: pd.DataFrame) -> pd.DataFrame:
    """Return the REQUIRED_COLS of df in training order with numeric dtypes, or raise SchemaError."""
    if not isinstance(df, pd.DataFrame):
        raise SchemaError(f"Expected a pandas DataFrame, got {type(df).__name__}")
    if df.empty:
        raise SchemaError("Input has no rows")

    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise SchemaError(f"Missing required fields: {missing}")

    X = df[REQUIRED_COLS].copy()

    for c in CATEGORICAL_COLS:
        bad = X[c].isna() | ~X[c].map(lambda v: isinstance(v, str))
        if bad.any():
            raise SchemaError(f"Field '{c}' must be a non-null string; bad rows: {X.index[bad].tolist()[:5]}")

    for c in NUMERIC_INPUT_COLS:
        num = pd.to_numeric(X[c], errors="coerce")
        bad = num.isna() | ~np.isfinite(num) | (num < 0)
        if bad.any():
            raise SchemaError(
                f"Field '{c}' must be a finite, non-negative number; bad rows: {X.index[bad].tolist()[:5]}")
        X[c] = num
    return X


def _unseen_categories(model: Pipeline, X: pd.DataFrame) -> list[dict]:
    """Per row, categorical values the encoder never saw in training (they encode to all zeros)."""
    enc = model.named_steps["pre"].named_transformers_["cat"]
    known = {c: set(cats) for c, cats in zip(CATEGORICAL_COLS, enc.categories_)}
    return [{c: v for c, v in zip(CATEGORICAL_COLS, row) if v not in known[c]}
            for row in X[CATEGORICAL_COLS].itertuples(index=False)]


def predict_batch(df: pd.DataFrame, model: Pipeline | None = None,
                  tau: float = ALERT_TAU) -> list[dict]:
    """Score a batch of raw connection records with one predict_proba call.

    Returns one JSON-serializable dict per row, in input order.
    """
    model = model if model is not None else load_model()
    X = validate_input(df)

    proba = _reorder_proba_to_families(model.predict_proba(X), model.named_steps["clf"].classes_)
    scores = attack_score(proba)
    families = decide(proba, tau)
    unseen = _unseen_categories(model, X)
    ts = datetime.now(timezone.utc).isoformat()

    return [
        {
            "alert": bool(families[i] != "Normal"),
            "predicted_family": str(families[i]),
            "attack_score": float(scores[i]),
            "threshold": float(tau),
            "probabilities": {f: float(proba[i, j]) for j, f in enumerate(FAMILIES)},
            "unseen_categories": unseen[i],
            "timestamp": ts,
        }
        for i in range(len(X))
    ]


def predict_connection(record: dict, model: Pipeline | None = None,
                       tau: float = ALERT_TAU) -> dict:
    """Score a single raw connection record given as {field: value}."""
    if not isinstance(record, dict):
        raise SchemaError(f"Expected a dict, got {type(record).__name__}")
    return predict_batch(pd.DataFrame([record]), model=model, tau=tau)[0]


if __name__ == "__main__":
    text = Path(sys.argv[1]).read_text() if len(sys.argv) > 1 else sys.stdin.read()
    payload = json.loads(text)
    try:
        out = (predict_connection(payload) if isinstance(payload, dict)
               else predict_batch(pd.DataFrame(payload)))
    except SchemaError as e:
        sys.exit(f"Schema error: {e}")
    print(json.dumps(out, indent=2))
