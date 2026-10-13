import json
import numpy as np
import pandas as pd
from sklearn.metrics import make_scorer, f1_score
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold

from src.config import SEED, FAMILIES, METRICS_DIR, MODELS_DIR



MACRO_F1 = make_scorer(f1_score, average="macro", labels=FAMILIES, zero_division=0)


def tune_model(name, pipe , space, X, y, n_iter, seed=SEED):

    inner_cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=seed + 1)
    search = RandomizedSearchCV(
        pipe, space, 
        n_iter=n_iter,
        cv=inner_cv,
        scoring=MACRO_F1,
        refit=False,
        error_score="raise",
        n_jobs=1,
        random_state=seed,
    )
    search.fit(X, y)
    return search
    

def save_tuning(name, search, out_dir=METRICS_DIR):
    out_dir.mkdir(parents=True, exist_ok=True)
    cv_results = pd.DataFrame(search.cv_results_)
    path = out_dir / f"tuning_{name}.csv"
    cv_results.to_csv(path, index=False)
    return path, cv_results


sav_tuning = save_tuning


def save_best_params(searches, out_dir=MODELS_DIR):
    out_dir.mkdir(parents=True, exist_ok=True)
    best = {name: s.best_params_ for name, s in searches.items()}
    path = out_dir / "best_params.json"
    with open(path, "w") as f:
        json.dump(best, f, indent=2)
    return path



