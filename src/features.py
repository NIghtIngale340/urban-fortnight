import numpy as np
import pandas as pd 


CONTENT_COLS = [
    "hot", "num_failed_logins", "num_compromised", "num_root",
    "num_file_creations", "num_shells", "num_access_files",
]


ENGINEERED_COLS = ["bytes_ratio", "zero_payload", "content_activity", "privilege_flag"]



def add_features(X: pd.DataFrame) -> pd.DataFrame:
    out = X.copy()  
    out["bytes_ratio"] = np.log1p(out["src_bytes"]) - np.log1p(out["dst_bytes"])
    out["zero_payload"] = ((out["src_bytes"] == 0) & (out["dst_bytes"] == 0)).astype(int)
    out["content_activity"] = out[CONTENT_COLS].sum(axis=1)
    
    out["privilege_flag"] = (
        (out["root_shell"] > 0) | (out["su_attempted"] > 0) | (out["num_root"] > 0)
    ).astype(int)
    return out

