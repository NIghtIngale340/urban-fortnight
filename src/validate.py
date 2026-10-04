from src.config import FAMILY_COL
import numpy as np 
import pandas as pd 

from src.config import (
    FEATURE_NAMES, LABEL_COL, CATEGORICAL_COLS, ATTACK_TO_FAMILY,
)


def validate_raw(df: pd.DataFrame) -> None:
    """Validate the loaded raw DataFrame.

    Raises AssertionError with a readable message on the first failure.
    Returns None on success.
    """
    
    # colum list and order must match
    expected_cols = FEATURE_NAMES + [LABEL_COL]
    assert list(df.columns) == expected_cols, (
        f"Column mismatch.\n  expected: {expected_cols}\n  got:      {list(df.columns)}"
    )

    # no nananywhere 

    nan_cols = df.columns[df.isna().any()].tolist()
    assert nan_cols == [], f"NaN-having columns: {nan_cols}"

    # columns must be numeric and no inf
    expected_numeric = [c for c in FEATURE_NAMES if c not in CATEGORICAL_COLS]
    non_numeric = [ c for c in expected_numeric if not pd.api.types.is_numeric_dtype(df[c])]
    assert not non_numeric, f"These columns should be numeric but aren't: {non_numeric}"

    inf_cols = [c for c in expected_numeric if np.isinf(df[c].to_numpy()).any()]
    assert not inf_cols, f"Infinite values found in: {inf_cols}"

    # no label ending in '.'
    bad_labels = df.loc[df[LABEL_COL].str.endswith("."), LABEL_COL].unique().tolist()
    assert not bad_labels, f"Labels ending with dot: {bad_labels}"

    # every label must be key in attack to family variable

    unknown = set(df[LABEL_COL].unique()) - set(ATTACK_TO_FAMILY.keys())
    assert not unknown, f"Unknown labels found: {sorted(unknown)}"


    # all _rate columns must lie ot tell 0,1 
    rate_cols = [c for c in FEATURE_NAMES if c.endswith("_rate")]
    for c in rate_cols:
        out_of_range = df[c][(df[c] < 0) | (df[c] > 1)]
        assert out_of_range.empty, (
            f"Column '{c}' has {len(out_of_range)} values outside [0, 1]; "
            f"e.g. {out_of_range.head(3).tolist()}"
        )

    

    # no negative values

    neg_mask = df[expected_numeric] < 0
    neg_cols = neg_mask.columns[neg_mask.any()].tolist()
    assert not neg_cols, f"Negative values found in: {neg_cols}"



def row_overlap(a: pd.DataFrame, b: pd.DataFrame, cols: list[str]) -> int:

    """How many rows of b have an identical feature vector somewhere in a.
    
    Returns the count of overlapping rows.
    """

    # Hash rows for efficient set intersection
    hash_a = pd.util.hash_pandas_object(a[cols], index=False)
    hash_b = pd.util.hash_pandas_object(b[cols], index=False)
    
    return int(np.isin(hash_b, hash_a).sum())



def validate_split(X: pd.DataFrame, y: pd.Series, train_idx: np.ndarray, test_idx: np.ndarray, meta: dict = None) -> None:
    """Validate the train/test split integrity."""
    n_rows = len(X)
    
    # Disjoint sets
    intersection = set(train_idx).intersection(set(test_idx))
    assert not intersection, f"Train and test overlap! {len(intersection)} indices in common."
    
    # Union covers all rows exactly once
    union = set(train_idx).union(set(test_idx))
    assert len(union) == n_rows, f"Train+Test ({len(union)}) != total rows ({n_rows})"
    
    # Sizes add up (if meta provided)
    if meta:
        assert len(train_idx) == meta["train_size"], "Train size mismatch with meta."
        assert len(test_idx) == meta["test_size"], "Test size mismatch with meta."
        assert meta["n_rows"] == n_rows, "n_rows mismatch with meta."
        
    # Stratification check (proportions in train/test match overall)
    overall_props = y.value_counts(normalize=True).sort_index()
    train_props = y.iloc[train_idx].value_counts(normalize=True).sort_index()
    test_props = y.iloc[test_idx].value_counts(normalize=True).sort_index()
    
    for cls in overall_props.index:
        ov = overall_props[cls]
        tr = train_props.get(cls, 0)
        te = test_props.get(cls, 0)
        
        # Absolute tolerance for very small classes (like U2R), relative for large
        tol = max(0.01, 0.05 * ov) 
        assert abs(tr - ov) < tol, f"Train class proportion for {cls} ({tr:.4f}) deviates too much from overall ({ov:.4f})"
        assert abs(te - ov) < tol, f"Test class proportion for {cls} ({te:.4f}) deviates too much from overall ({ov:.4f})"

    # No data leakage (feature overlap)
    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]
    overlap = row_overlap(X_train, X_test, X.columns.tolist())
    assert overlap == 0, f"Data leakage! {overlap} feature rows in test also appear in train."
    
    # X must not contain target or metadata columns
    forbidden = [LABEL_COL, FAMILY_COL]
    present_forbidden = [c for c in forbidden if c in X.columns]
    assert not present_forbidden, f"X contains forbidden target/metadata columns: {present_forbidden}"  