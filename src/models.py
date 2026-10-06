from sklearn.dummy import DummyClassifier
from src.preprocessing import build_pipeline

def get_models() -> dict:
    return{
        "M0_dummy": build_pipeline(
            DummyClassifier(strategy="most_frequent"),
            scale=False,
            engineered=False,
        ),
    }