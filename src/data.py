import pandas as pd 
import json
import numpy as np 
from sklearn.model_selection import train_test_split
from pathlib import Path
from src.config import (
    RAW_PATH, FEATURE_NAMES, LABEL_COL, FAMILY_COL,
    ATTACK_TO_FAMILY, CONSTANT_COLS,PROCESSED_DIR, SEED,
)


def load_raw(path: Path = RAW_PATH) -> pd.DataFrame:
    """ Read the KDD CUP 1999 CSV, name the column, strip the trailing '.'"""
    columns = FEATURE_NAMES + [LABEL_COL]
    df = pd.read_csv(path, header=None, names=columns)
    df = df.assign(**{LABEL_COL: df[LABEL_COL].str.replace(r"\.$", "", regex=True)})
    return df


def add_family(df: pd.DataFrame) -> pd.DataFrame:
    """Add a 'family' column via ATTACK_TO_FAMILY. Keep 'label' as the attack name.

    Asserts that no family is NaN, so an unmapped label fails loudly instead of
    silently becoming NaN.
    """

    family = df[LABEL_COL].map(ATTACK_TO_FAMILY)
    unmapped = df.loc[family.isna(), LABEL_COL].unique().tolist()
    assert not unmapped, f"Unmapped attack labels: {unmapped}"
    return df.assign(**{FAMILY_COL: family})


def drop_duplicates_and_conflicts(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Remove exact duplicates and resolve rows that share an identical feature vector.

    - exact duplicate  = identical features AND identical label -> keep first
    - conflict         = identical features but DIFFERENT family -> drop whole group
    - same family, different attack name = identical features, same family,
      different label -> keep first (the 'family' target is unambiguous)

    Returns (cleaned_df, report_dict).
    """

    n_start = len(df)
    family_counts_before = df[FAMILY_COL].value_counts().to_dict()
    attack_counts_before = df[LABEL_COL].value_counts().to_dict()

    feature_cols = [c for  c in FEATURE_NAMES if c in df.columns]


    deduped = df.drop_duplicates(subset=feature_cols + [LABEL_COL], keep="first")
    n_exact_removed = n_start - len(deduped)


    keys = pd.util.hash_pandas_object(deduped[feature_cols], index=False)
    deduped = deduped.assign(_key=keys)

    families_per_key = deduped.groupby("_key")[FAMILY_COL].nunique()
    conflict_keys = families_per_key[families_per_key > 1].index
    is_conflict = deduped["_key"].isin(conflict_keys)
    n_conflict_removed = int(is_conflict.sum())


    non_conflict = deduped.loc[~is_conflict]
    cleaned = non_conflict.drop_duplicates(subset="_key", keep="first")
    n_same_family_removed = len(non_conflict) - len(cleaned)


    cleaned = cleaned.drop(columns="_key")


    report = {
        "raw_rows": n_start,
        "exact_duplicates_removed": int(n_exact_removed),
        "conflict_rows_removed": n_conflict_removed,
        "same_family_diff_attack_removed": int(n_same_family_removed),
        "final_rows": len(cleaned),
        "family_counts_before": family_counts_before,
        "family_counts_after": cleaned[FAMILY_COL].value_counts().to_dict(),
        "attack_counts_before": attack_counts_before,
        "attack_counts_after": cleaned[LABEL_COL].value_counts().to_dict(),
    }
    return cleaned, report

def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Full cleaning: add_family -> dedupe/conflicts -> drop constants -> reset index.

    The returned index is a fresh 0..n-1 RangeIndex. Do NOT change it again —
    the Phase 5 split indices depend on it.
    """
    df = add_family(df)
    df, report = drop_duplicates_and_conflicts(df)
    # errors="ignore" keeps clean() idempotent (constants are gone on a re-clean).
    df = df.drop(columns=CONSTANT_COLS, errors="ignore")
    df = df.reset_index(drop=True)
    report["dropped_constant_cols"] = list(CONSTANT_COLS)
    return df, report



def split_xy(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Split X, y and return a JSON-serializable split report.
    
    X = feature columns only. y = family. meta = attack name (label). """

    feature_cols = [c for c in FEATURE_NAMES if c in df.columns]
    X = df[feature_cols].copy()
    y = df[FAMILY_COL].copy()
    meta = df[LABEL_COL].copy() # Attack name kept as metadata, never fed to models
    return X, y, meta

def make_split(y: pd.Series, test_size: float = 0.2, seed: int = SEED) -> tuple[np.ndarray, np.ndarray]:
    """Return (train_idx, test_idx), positional, stratified on y (family)."""
    train_idx, test_idx = train_test_split(
        np.arange(len(y)),
        test_size=test_size,
        random_state=seed,
        stratify=y,
    )    
    return train_idx, test_idx

def save_split(train_idx: np.ndarray, test_idx: np.ndarray, n_rows: int, seed: int, out_dir: Path = PROCESSED_DIR) -> None:


    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(out_dir / "train_idx.npy", train_idx)
    np.save(out_dir / "test_idx.npy", test_idx)
    

    meta = {
        "n_rows": int(n_rows),
        "seed": int(seed),
        "train_size": int(len(train_idx)),
        "test_size": int(len(test_idx)),
    }
    with open(out_dir / "split_meta.json", "w") as f:
        json.dump(meta, f, indent=2)





def load_split(out_dir: Path = PROCESSED_DIR, n_rows: int = None) -> tuple[np.ndarray, np.ndarray, dict]:
    train_idx = np.load(out_dir / "train_idx.npy")
    test_idx = np.load(out_dir / "test_idx.npy")

    
    with open(out_dir / "split_meta.json", "r") as f:
        meta = json.load(f)
    
    if n_rows is not None:
        assert meta["n_rows"] == n_rows, (
            f"Saved split was for {meta['n_rows']} rows, but current data has {n_rows}."
        )
        
    return train_idx, test_idx, meta




def load_train() -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Return (X_train, y_train, meta_train). Use this everywhere until final evaluation."""
    raw = load_raw()
    cleaned, _ = clean(raw)
    X, y, meta = split_xy(cleaned)
    train_idx, _, _ = load_split(n_rows=len(X))
    return (
        X.iloc[train_idx].reset_index(drop=True),
        y.iloc[train_idx].reset_index(drop=True),
        meta.iloc[train_idx].reset_index(drop=True),
    )


def load_test() -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Return (X_test, y_test, meta_test). LOCKED — final evaluation only."""
    raw = load_raw()
    cleaned, _ = clean(raw)
    X, y, meta = split_xy(cleaned)
    _, test_idx, _ = load_split(n_rows=len(X))
    return (
        X.iloc[test_idx].reset_index(drop=True),
        y.iloc[test_idx].reset_index(drop=True),
        meta.iloc[test_idx].reset_index(drop=True),
    )