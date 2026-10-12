from sklearn.utils import class_weight
from src.config import SEED
from sklearn.dummy import DummyClassifier
from src.preprocessing import build_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier


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
    }