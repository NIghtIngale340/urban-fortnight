from sklearn.utils import class_weight
from src.config import SEED
from sklearn.dummy import DummyClassifier
from src.preprocessing import build_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from lightgbm import LGBMClassifier



def get_models(class_weight: bool = True, engineered: bool = False) -> dict:
    """Return {name: pipeline}.

    class_weight: True -> balanced / balanced_subsample; False -> None.
    engineered:   True -> add the 4 row-wise engineered features.
    Defaults reproduce the Phase 9–12 baseline (weights on, engineered off).
    """
    cw = {
       "M1_logreg": "balanced" if class_weight else None,
       "M2_tree": "balanced" if class_weight else None, 
       "M3_rf": "balanced_subsample" if class_weight else None, 
       "M4_lgbm": "balanced" if class_weight else None,
    }

    return {
        "M0_dummy": build_pipeline(
            DummyClassifier(strategy="most_frequent"),
            scale=False, engineered=False),
        "M1_logreg": build_pipeline(
            LogisticRegression(solver="lbfgs", class_weight=cw["M1_logreg"],
                               max_iter=3000, random_state=SEED),
            scale=True, engineered=engineered),
        "M2_tree": build_pipeline(
            DecisionTreeClassifier(class_weight=cw["M2_tree"], min_samples_leaf=2,
                                   max_depth=None, random_state=SEED),
            scale=False, engineered=engineered),
        "M3_rf": build_pipeline(
            RandomForestClassifier(n_estimators=300, class_weight=cw["M3_rf"],
                                   max_features="sqrt", min_samples_leaf=2,
                                   oob_score=True, n_jobs=-1, random_state=SEED),
            scale=False, engineered=engineered),
        "M4_lgbm": build_pipeline(
            LGBMClassifier(n_estimators=300, learning_rate=0.05, num_leaves=31,
                           min_child_samples=10, subsample=0.8, subsample_freq=1,
                           colsample_bytree=0.8, class_weight=cw["M4_lgbm"],
                           deterministic=True, force_row_wise=True, n_jobs=-1,
                           random_state=SEED, verbose=-1),
            scale=False, engineered=engineered),       
    }


def params_diff(est_a, est_b):
    pa, pb = est_a.get_params(), est_b.get_params()
    diffs = []
    for k in set(pa) | set(pb):
        va, vb = pa.get(k), pb.get(k)
        if hasattr(va, "get_params") or hasattr(vb, "get_params"):
            continue
        if repr(va) != repr(vb):
            diffs.append(k)
    return sorted(diffs)