# urban-fortnight — Network Guardian: Detecting Network Intrusions with Machine Learning

A machine-learning-based Intrusion Detection System (IDS) prototype trained on the KDD Cup 1999 dataset to classify network connections into Normal traffic and four attack families: **Denial of Service (DoS)**, **Remote to Local (R2L)**, **User to Root (U2R)**, and **Probe**.

Developed for the **CCINSYSL (Introduction to Intelligent Systems)** course project.

---

## Executive Summary & Selected Architecture

- **Selected Model:** `M4_lgbm` (LightGBM Classifier, default configuration).
- **Frozen Feature Engineering:** Log-byte payload ratio (`bytes_ratio`), zero-payload indicator (`zero_payload`), content activity counter (`content_activity`), privilege escalation flag (`privilege_flag`).
- **Frozen Preprocessing:** Balanced class weights, one-hot categorical encoding with zero-vector unseen handling, passthrough numeric/binary features (no unneeded tree scaling).
- **Operational Decision Policy:** Calibrated alert threshold $\tau = 0.002002$ ($S_{\text{attack}} = 1.0 - P(\text{Normal}) \ge \tau$), decoupling perimeter alarm sensitivity from multi-class taxonomy.
- **Key Empirical Results (Held-Out Test Set, $N=29,117$):**
  - **Attack Detection:** $99.98\%$ overall detection rate ($\text{FNR} = 0.0173\%$, cutting missed intrusions by $60\%$ over argmax).
  - **Rare-Class Sensitivity:** $90.0\%$ U2R recall ($9/10$, Wilson 95% CI: $[59.6\%, 98.2\%]$), $99.0\%$ R2L recall ($198/200$, Wilson 95% CI: $[96.4\%, 99.7\%]$).
  - **False Alarm Control:** $0.1082\%$ false positive rate ($19$ false alarms among $17,567$ normal connections, well within the $0.50\%$ operational ceiling).
  - **Multi-Class Performance:** Macro-F1 $= 0.9543$ under argmax, $0.9201$ under the calibrated $\tau$ policy.

---

## Repository Structure

```
├── .venv/                         # Python 3.12 virtual environment (local, git-ignored)
├── requirements.txt               # Pinned Python package dependencies
├── .gitignore                     # Git ignore rules (caches, virtual environments, .joblib)
├── data/
│   ├── raw/                       # Raw KDD Cup 1999 metadata & symlinked dataset
│   └── processed/                 # Deduplicated indices, split metadata, and audit logs
├── notebooks/                     # Canonical Jupyter research notebooks (run in order)
│   ├── data_understanding.ipynb   # Phase 1 & Phase 6: Exploratory Data Analysis & schemas
│   ├── data_preparation.ipynb     # Phases 2–5: Cleaning, deduplication, split & leakage audit
│   ├── modeling.ipynb             # Phases 7–17: Baseline models, CV, ablations, tuning, selection
│   └── rare_class_analysis.ipynb  # Phases 18–19: Threshold calibration, importance, test evaluation
├── src/                           # Core modular Python package
│   ├── config.py                  # Frozen project settings, constants, and ALERT_TAU
│   ├── data.py                    # Dataset loading, cleaning, and train/test partitioning
│   ├── validate.py                # Schema validation and split integrity assertions
│   ├── preprocessing.py           # Scikit-learn preprocessing pipelines and transformers
│   ├── features.py                # Row-wise engineered interaction features
│   ├── models.py                  # Model definitions (M0–M4) and hyperparameter setups
│   ├── train.py                   # Equal-budget tuning routines and search spaces
│   ├── evaluation.py              # Cross-validation, metric computation, and threshold sweep
│   ├── plots.py                   # Publication-quality figure generation functions
│   └── predict.py                 # Production inference module with schema validation
├── scripts/
│   ├── train_final.py             # Deterministic pipeline refit on train data -> model card
│   └── run_notebook.py            # Fresh-kernel notebook execution runner
├── tests/
│   ├── test_predict.py            # 14-point unittest suite for pipeline and inference
│   └── example_record.json        # Sample raw network connection record
├── models/
│   ├── final_pipeline.joblib      # Serialized fitted pipeline artifact (rebuilt via script)
│   ├── model_card.json            # Machine-readable model architecture, schema, and verified metrics
│   ├── selection_decision.json    # Phase 17 pre-registered repeated-CV selection record
│   └── best_params.json           # Phase 16 hyperparameter tuning results
├── reports/
│   ├── metrics/                   # Tabular evaluation results, test metrics, and OOF arrays
│   └── figures/                   # Visualizations and diagnostic plots
├── docs/
│   └── discovery_log.md           # Engineering discovery log (Entries 1–18, Findings 1–53)
├── Document.md                    # Course project formal documentation report
└── Project_Specs.md               # CCINSYSL course project specifications and rubrics
```

---

## 20-Phase Implementation Roadmap & Milestones

The project was executed across 20 structured phases adhering strictly to scientific rigor, pre-registered decision rules, and leakage-prevention protocols.

### I. Data Understanding & Integrity Foundation
- **Phase 1: Raw File Inspection & Format Validation** (`notebooks/data_understanding.ipynb`) — Confirmed 41 feature columns plus target label; identified 2 constant columns (`num_outbound_cmds`, `is_host_login`).
- **Phase 2: Schema Validation & Defensive Ingestion** (`src/data.py`, `src/validate.py`) — Enforced column types, non-negativity, $[0, 1]$ rate ranges, and dot-stripped attack labels.
- **Phase 3: Label Harmonization & Deduplication** (`src/data.py`, `notebooks/data_preparation.ipynb`) — Mapped 23 raw attacks to 5 families; removed 348,435 exact duplicates and resolved 3 label conflict rows.
- **Phase 4: Data Leakage Demonstration** (`notebooks/data_preparation.ipynb`) — Proved that random splitting on un-deduplicated data produces $73.5\%$ test contamination and a counterfeit $99.96\%$ accuracy.
- **Phase 5: Partitioning & Split Integrity Verification** (`src/validate.py`) — Constructed 80/20 stratified split ($N_{\text{train}}=116,466$, $N_{\text{test}}=29,117$); verified zero feature row overlap and locked test set.
- **Phase 6: Train-Only Exploratory Data Analysis** (`notebooks/data_understanding.ipynb`) — Analyzed distributions, high skewness, heavy-tailed features, and protocol interactions strictly on training data.

### II. Preprocessing, Baselines & Candidate Modeling
- **Phase 7: Preprocessing Pipeline Encapsulation** (`src/preprocessing.py`) — Built leak-free column transformers with one-hot encoding for categoricals and passthrough for tree numericals.
- **Phase 8: Evaluation Harness & Dummy Baseline** (`src/evaluation.py`, `notebooks/modeling.ipynb`) — Implemented Macro-F1, binary FPR/FNR, and validated sanity floor (`M0_dummy`: Macro-F1 $= 0.1505$).
- **Phase 9: Linear Baseline (`M1_logreg`)** (`src/models.py`) — Logistic Regression with standard scaling and balanced class weights (Macro-F1 $= 0.8071$).
- **Phase 10: Interpretable Tree Baseline (`M2_tree`)** — Decision Tree with `min_samples_leaf=2` (Macro-F1 $= 0.9183$).
- **Phase 11: Bagging Ensemble (`M3_rf`)** — Random Forest with 300 estimators and balanced subsampling (Macro-F1 $= 0.9535$).
- **Phase 12: Gradient Boosting Ensemble (`M4_lgbm`)** — LightGBM Classifier with 300 iterations (Macro-F1 $= 0.9606$).
- **Phase 13: 5-Fold Cross-Validation Model Comparison** (`notebooks/modeling.ipynb`) — Comparative benchmarking establishing ensemble dominance.

### III. Ablations, Optimization & Selection
- **Phase 14: Controlled Ablation Studies** (`notebooks/modeling.ipynb`) — Tested class weighting ($+0.1652$ mean gain on minority recall) and 4 interaction features ($+0.0054$ mean Macro-F1 gain, 0 regressions); adopted both globally.
- **Phase 15: Rare-Class Diagnostic Breakdown** (`notebooks/rare_class_analysis.ipynb`) — Dissected R2L/U2R confusion matrix and per-attack Wilson 95% confidence intervals on out-of-fold predictions.
- **Phase 16: Equal-Budget Hyperparameter Tuning** (`src/train.py`) — Randomized search across all 4 architectures with pre-registered iteration budgets and 3-fold inner CV.
- **Phase 17: Pre-Registered Repeated Cross-Validation & Decision** (`src/evaluation.py`, `models/selection_decision.json`) — 5x3 repeated stratified CV with strict sign tests. Selected **`M4_lgbm` (default configuration)** via rare-class recall tie-break over `M3_rf`.

### IV. Operational Defense & Held-Out Test Evaluation
- **Phase 18: Operational Alert Threshold Calibration** (`notebooks/rare_class_analysis.ipynb`) — Calibrated $\tau = 0.002002$ from training OOF probabilities to satisfy $\text{FPR} \le 0.10\%$ while lifting U2R recall to $90.48\%$. Analyzed permutation importance ($r_s = 0.4864, p < 0.01$ vs MDI).
- **Phase 19: Single Locked Test Set Evaluation** (`reports/metrics/test_results.json`) — Executed exactly once under strict idempotent file-locking (`.test_evaluated`). Confirmed generalization gaps $\le 0.63$ percentage points across all architectures.

### V. Productionization & Code Freeze
- **Phase 20: Productionization, Inference Module, Model Card & Code Freeze** — Built `src/predict.py` (single/batch inference with schema validation), `scripts/train_final.py` (deterministic refitting), `models/model_card.json`, and 14 passing automated unit tests (`tests/test_predict.py`). Formal coding freeze declared.
- *(Note on Isolation Forest: Evaluated as optional exploratory work in the project specifications; excluded from the primary supervised pipeline in favor of the calibrated threshold ensemble).*

---

## Step-by-Step Reproduction Instructions

### 1. Environment Setup

Ensure Python 3.12 is installed, then activate the existing virtual environment:

```bash
# Activate virtual environment
source .venv/bin/activate
```

Alternatively, to recreate the environment from scratch using `uv`:

```bash
uv venv .venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 2. Full Notebook Reproducibility Check

Execute the research notebooks sequentially from a clean kernel:

1. `notebooks/data_understanding.ipynb` — Raw schema checks, metadata verification, and exploratory analysis.
2. `notebooks/data_preparation.ipynb` — Data cleaning, deduplication, 80/20 stratified partitioning, and leakage proofs.
3. `notebooks/modeling.ipynb` — Cross-validation of M0–M4, ablations, hyperparameter tuning, and Phase 17 repeated-CV model selection.
4. `notebooks/rare_class_analysis.ipynb` — Phase 18 threshold calibration, permutation importance, and Phase 19 held-out test evaluation.

> [!NOTE]
> **Test-Lock Protection:** Phase 19 is protected by `reports/metrics/.test_evaluated`. When the lock exists, notebook re-execution automatically reloads the verified frozen metrics from disk and refuses to evaluate the held-out test set again, safeguarding evaluation integrity.

To execute all notebooks in batch from fresh kernels:

```bash
python scripts/run_notebook.py notebooks/data_understanding.ipynb
python scripts/run_notebook.py notebooks/data_preparation.ipynb
python scripts/run_notebook.py notebooks/modeling.ipynb
python scripts/run_notebook.py notebooks/rare_class_analysis.ipynb
```

### 3. Rebuilding the Final Model Pipeline

The production pipeline can be deterministically rebuilt from the full training set (116,466 rows) in approximately 10 seconds:

```bash
python scripts/train_final.py
```

This script:
- Loads the frozen Phase 17 champion selection (`M4_lgbm`, default configuration).
- Fits the complete feature engineering, preprocessing, and LightGBM pipeline strictly on training rows.
- Serializes `models/final_pipeline.joblib`.
- Generates `models/model_card.json` containing the input schema, hyperparameter hashes, and verified Phase 19 metrics.
- Confirms that the training macro-F1 strictly matches the recorded Phase 19 refit score ($1.000000$).

### 4. Running the Inference Module

The inference module `src/predict.py` provides production-grade single and batch scoring with strict schema validation, unknown categorical reporting, and the frozen $\tau = 0.002002$ alert decision rule:

```bash
# Single record prediction (JSON payload)
python src/predict.py tests/example_record.json

# Or using module syntax
python -m src.predict tests/example_record.json
```

**Python API Example:**

```python
import pandas as pd
from src.predict import predict_connection, predict_batch

# Single record inference
record = {
    "duration": 0, "protocol_type": "tcp", "service": "http", "flag": "SF",
    "src_bytes": 181, "dst_bytes": 5450, "land": 0, "wrong_fragment": 0,
    # ... remaining KDD fields ...
}
result = predict_connection(record)
print(result["alert"])             # True if attack_score >= ALERT_TAU, else False
print(result["predicted_family"])  # 'Normal', 'DoS', 'Probe', 'R2L', or 'U2R'
print(result["attack_score"])      # 1.0 - P(Normal)

# Batch inference
df = pd.DataFrame([record, record])
batch_results = predict_batch(df)
```

### 5. Running Automated Unit Tests

Run the 14 automated unit tests covering pipeline serialization, class index mapping, threshold boundary behavior, schema rejection, unseen categorical handling, and deterministic output:

```bash
python -m unittest discover -s tests -v
```

---

## Saved Model Artifact Policy

In accordance with version control best practices for open-source repositories:
- Binary model weights (`models/*.joblib`) are excluded by `.gitignore` to keep the repository lightweight (~4.6 MB saved per commit).
- The pipeline artifact `models/final_pipeline.joblib` is deterministically regenerated on demand using `python scripts/train_final.py`.
- Comprehensive model specifications, hyperparameters, categorical dictionaries, and verified test metrics are tracked in version control via `models/model_card.json`.

---

## Key Deliverables & Documentation Index

| Deliverable | File Path | Description |
| :--- | :--- | :--- |
| **Final Documentation** | [`Document.md`](file:///home/nightingale/My_Projects/is_project/Document.md) | Course project formal documentation report |
| **Discovery Log** | [`docs/discovery_log.md`](file:///home/nightingale/My_Projects/is_project/docs/discovery_log.md) | Chronological log of 53 empirical research findings across 18 entries |
| **Model Card** | [`models/model_card.json`](file:///home/nightingale/My_Projects/is_project/models/model_card.json) | Comprehensive schema, architecture, and verified metrics specification |
| **Selection Decision** | [`models/selection_decision.json`](file:///home/nightingale/My_Projects/is_project/models/selection_decision.json) | Pre-registered repeated-CV statistical selection record |
| **Final Test Metrics** | [`reports/metrics/test_results.json`](file:///home/nightingale/My_Projects/is_project/reports/metrics/test_results.json) | Frozen single-pass held-out test evaluation results |
| **Policy Comparison** | [`reports/metrics/operational_policy_comparison.csv`](file:///home/nightingale/My_Projects/is_project/reports/metrics/operational_policy_comparison.csv) | Argmax vs Calibrated $\tau$ test trade-off metrics |
| **Generalization Gaps** | [`reports/metrics/test_gap_table.csv`](file:///home/nightingale/My_Projects/is_project/reports/metrics/test_gap_table.csv) | Consistent Train vs CV vs Test generalization analysis |
| **Diagnostic Figures** | [`reports/figures/`](file:///home/nightingale/My_Projects/is_project/reports/figures/) | 22 high-resolution diagnostic plots and learning curves |
