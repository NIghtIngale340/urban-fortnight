from src.config import SEED
from sklearn.dummy import DummyClassifier
from src.preprocessing import build_pipeline
from sklearn.linear_model import LogisticRegression

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
    }