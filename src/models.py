from sklearn.utils import class_weight
from src.config import SEED
from sklearn.dummy import DummyClassifier
from src.preprocessing import build_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from lightgbm import LGBMClassifier



def get_models() -> dict:
    return{
        "M0_dummy": build_pipeline(
            DummyClassifier(strategy="most_frequent"),
            scale=False,
            engineered=False,
        ),
        "M1_logreg": build_pipeline(
            LogisticRegression(
                solver="lbfgs",
                class_weight="balanced",
                max_iter=3000,
                random_state=SEED,
        ),
        scale=True, engineered=False
        ),
        "M2_tree": build_pipeline(
            DecisionTreeClassifier(
                class_weight="balanced",
                min_samples_leaf=2,
                random_state=SEED,
                max_depth=None,
            ),
            scale=False,
            engineered=False,
        ),
        "M2_dt": build_pipeline(
            DecisionTreeClassifier(
                class_weight="balanced",
                min_samples_leaf=2,
                random_state=SEED,
                max_depth=None,
            ),
            scale=False,
            engineered=False,
        ),
        "M3_rf": build_pipeline(
            RandomForestClassifier(
                n_estimators=300,
                class_weight="balanced_subsample",
                max_features="sqrt",
                min_samples_leaf=2,
                oob_score=True,
                n_jobs=-1,
                random_state=SEED,
            ),
            scale=False, engineered=False
        ),
        "M4_lgbm": build_pipeline(
            LGBMClassifier(
                n_estimators=300,
                learning_rate=0.05,
                num_leaves=31,
                min_child_samples=10,
                subsample=0.8,
                subsample_freq=1,
                colsample_bytree=0.8,
                class_weight="balanced",
                deterministic=True,
                force_row_wise=True,
                random_state=SEED,
                n_jobs=-1,
                verbose=-1,
            ),
            scale=False, engineered=False
        )
    }