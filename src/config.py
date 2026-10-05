from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"


RAW_PATH = RAW_DIR / "kddcup.csv"
NAMES_PATH = RAW_DIR / "kddcup.names.txt"
ATTACK_TYPES_PATH = RAW_DIR / "training_attack_types.txt"




SEED = 42

LABEL_COL = "label"
FAMILY_COL = "family"

FEATURE_NAMES: list[str] = [
    "duration", "protocol_type", "service", "flag", "src_bytes",
    "dst_bytes", "land", "wrong_fragment", "urgent", "hot",
    "num_failed_logins", "logged_in", "num_compromised", "root_shell",
    "su_attempted", "num_root", "num_file_creations", "num_shells",
    "num_access_files", "num_outbound_cmds", "is_host_login",
    "is_guest_login", "count", "srv_count", "serror_rate",
    "srv_serror_rate", "rerror_rate", "srv_rerror_rate", "same_srv_rate",
    "diff_srv_rate", "srv_diff_host_rate", "dst_host_count",
    "dst_host_srv_count", "dst_host_same_srv_rate",
    "dst_host_diff_srv_rate", "dst_host_same_src_port_rate",
    "dst_host_srv_diff_host_rate", "dst_host_serror_rate",
    "dst_host_srv_serror_rate", "dst_host_rerror_rate",
    "dst_host_srv_rerror_rate",
]
CATEGORICAL_COLS = ["protocol_type", "service", "flag"]

# Confirmed in Phase 1: these columns have nunique() == 1.
CONSTANT_COLS = ["num_outbound_cmds", "is_host_login"]
FAMILIES = ["Normal", "DoS", "Probe", "R2L", "U2R"]

# Confirmed in Phase 6 on train: features with nunique() == 2
BINARY_COLS = ["is_guest_login", "land", "logged_in", "root_shell"]

# Derived numeric columns (excluding constant, categorical, and binary)
NUMERIC_COLS = [c for c in FEATURE_NAMES if c not in CATEGORICAL_COLS + CONSTANT_COLS + BINARY_COLS]

# Heavy-tailed columns on train: numeric columns with skewness > 5.0
HEAVY_TAILED_COLS = [
    "diff_srv_rate", "dst_bytes", "dst_host_srv_diff_host_rate", "duration",
    "hot", "num_access_files", "num_compromised", "num_failed_logins",
    "num_file_creations", "num_root", "num_shells", "src_bytes",
    "srv_count", "su_attempted", "urgent", "wrong_fragment"
]

# Strongly correlated feature pairs (|r| > 0.95) on train
CORRELATED_PAIRS = [
    ("srv_serror_rate", "dst_host_srv_serror_rate", 0.9983),
    ("serror_rate", "dst_host_serror_rate", 0.9967),
    ("serror_rate", "srv_serror_rate", 0.9963),
    ("dst_host_serror_rate", "dst_host_srv_serror_rate", 0.9959),
    ("num_compromised", "num_root", 0.9955),
    ("srv_serror_rate", "dst_host_serror_rate", 0.9951),
    ("serror_rate", "dst_host_srv_serror_rate", 0.9950),
    ("rerror_rate", "srv_rerror_rate", 0.9913),
    ("rerror_rate", "dst_host_rerror_rate", 0.9755),
    ("srv_rerror_rate", "dst_host_srv_rerror_rate", 0.9753),
    ("rerror_rate", "dst_host_srv_rerror_rate", 0.9727),
    ("dst_host_rerror_rate", "dst_host_srv_rerror_rate", 0.9714),
    ("srv_rerror_rate", "dst_host_rerror_rate", 0.9673),
]



ATTACK_TO_FAMILY: dict[str, str] = {
    "back": "DoS",
    "buffer_overflow": "U2R",
    "ftp_write": "R2L",
    "guess_passwd": "R2L",
    "imap": "R2L",
    "ipsweep": "Probe",
    "land": "DoS",
    "loadmodule": "U2R",
    "multihop": "R2L",
    "neptune": "DoS",
    "nmap": "Probe",
    "normal": "Normal",
    "perl": "U2R",
    "phf": "R2L",
    "pod": "DoS",
    "portsweep": "Probe",
    "rootkit": "U2R",
    "satan": "Probe",
    "smurf": "DoS",
    "spy": "R2L",
    "teardrop": "DoS",
    "warezclient": "R2L",
    "warezmaster": "R2L",
}