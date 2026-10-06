import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler, FunctionTransformer


from src.config import CATEGORICAL_COLS, BINARY_COLS, NUMERIC_COLS, HEAVY_TAILED_COLS
from src.features import add_features, ENGINEERED_COLS



ENGINEERED_BINARY = ["zero_payload", "privilege_flag"]
ENGINEERED_HEAVY_TAILED = ["content_activity"]
ENGINEERED_OTHER_NUMERIC = ["bytes_ratio"]  



def build_preprocessor(scale: bool, engineered: bool=False) -> ColumnTransformer:
    
    binary_cols = list(BINARY_COLS)
    heavy_cols = list(HEAVY_TAILED_COLS)
    other_numeric = [c for c in NUMERIC_COLS if c not in HEAVY_TAILED_COLS]


    if engineered:
        binary_cols = binary_cols + ENGINEERED_BINARY
        heavy_cols = heavy_cols +ENGINEERED_HEAVY_TAILED
        other_numeric = other_numeric + ENGINEERED_OTHER_NUMERIC

    
    transformers = [
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_COLS),
        ("binary", "passthrough", binary_cols),
    ]

    if scale:
        heavy_pipe = Pipeline([
            ("log", FunctionTransformer(np.log1p, validate=False, feature_names_out="one-to-one")),
            ("scaler", StandardScaler()),
        ])
        transformers.append(("heavy", heavy_pipe, heavy_cols))
        transformers.append(("num", StandardScaler(), other_numeric))
    else:
        transformers.append(("heavy", "passthrough", heavy_cols))
        transformers.append(("num", "passthrough", other_numeric))

    return ColumnTransformer(transformers, remainder="drop")




def _engineered_feature_names_out(transformers, input_features):
    return np.array(list(input_features) + ENGINEERED_COLS)



def build_pipeline(clf, scale:bool, engineered: bool=False) -> Pipeline:
    steps = []
    if engineered:
        steps.append((
            "features",
            FunctionTransformer(add_features, validate=False,
            feature_names_out = _engineered_feature_names_out),
        ))
    steps.append(("pre", build_preprocessor(scale, engineered)))
    steps.append(("clf", clf))
    return Pipeline(steps)