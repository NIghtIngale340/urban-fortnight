# Network Guardian — Project Context & Handoff Prompt

> **Instructions:** Copy and paste the block below into any new chat or handoff conversation to instantly give full technical context to an AI assistant or teammate.

```markdown
### PROJECT CONTEXT & HANDOFF PROMPT

**1. Project Overview**
- **Course:** CCINSYSL (Introduction to Intelligent Systems) — Term 1 AY 2026–2027.
- **Project Title:** Network Guardian: Detecting Network Intrusions with Machine Learning.
- **GitHub Repository:** https://github.com/NIghtIngale340/urban-fortnight.git (Branch: `main`).
- **Workspace Directory:** `/home/nightingale/My_Projects/is_project/`.
- **Dataset:** KDD Cup 1999 10% subset (494,021 rows, 41 raw features, 22 attack types + 1 normal label).
- **Core Objective:** Build, evaluate, tune, and operationalize a multiclass Network Intrusion Detection System (IDS) prototype to classify network traffic into `Normal` and four attack families: `DoS`, `Probe`, `R2L`, and `U2R`. The system also derives an operational binary view ($P(\text{attack}) = 1 - P(\text{Normal})$) with an engineering false-positive constraint ($FPR \le 0.5\%$) to mitigate alert fatigue.

---

**2. Key Empirical Findings & Methodological Rules**
- **The 70.5% Duplicate Trap:** 348,435 out of 494,021 raw rows are exact duplicates. Splitting raw data naively causes 73.5% test set contamination, allowing a basic decision tree to memorize rows and report a fake 99.96% accuracy. Deduplication is performed *before* splitting (collapsing the dataset to ~145,586 unique rows).
- **Severe Class Imbalance:** After deduplication, `U2R` has only 52 instances in total, `R2L` has 999, `Probe` has 2,131, `DoS` has 54,572, and `Normal` has 87,832. Primary metric is **Macro-F1**, and rare classes are evaluated using pooled out-of-fold cross-validation and Wilson 95% confidence intervals.
- **Data Split Architecture:** Stratified 80/20 train/test split. Test set (~29,117 rows) is locked and touched **only once** at the very end. 5-fold Stratified CV on the training split (~116,468 rows) serves as the validation mechanism (no separate 3-way validation split, which would starve U2R).
- **Two-Stage EDA (Zero Data Snooping):** Phase 1 inspects raw format and duplicates. All subsequent EDA, feature correlation, and preprocessing decisions are conducted **strictly on train**.
- **Scikit-Learn Pipeline Integrity:** Preprocessing (`ColumnTransformer`, `OneHotEncoder`, scaling) and row-wise feature engineering are enclosed inside `Pipeline` objects from the start to prevent fold leakage during CV.
- **Pre-Registered Selection Rule:** Formal model selection rule (FPR $\le 0.5\%$, repeated CV Macro-F1, paired-fold sign test $p \approx 0.02$) is declared *before* final model comparison.
- **Out-of-Fold Threshold Calibration:** Operational decision thresholds ($t_{\text{alert}}$, $t_{\text{review}}$) are tuned strictly using out-of-fold probabilities on train, never on the test set.
- **Models Included:**
  - `M0`: Dummy Classifier (sanity floor)
  - `M1`: Logistic Regression (linear baseline; multinomial, balanced)
  - `M2`: Decision Tree (interpretable baseline; demonstrates depth overfitting)
  - `M3`: Random Forest (bagging ensemble; low-FPR contender)
  - `M4`: LightGBM (boosting ensemble; expected primary candidate)
  - `X1`: Isolation Forest (semi-supervised anomaly detection trained on Normal only; negative result study)

---

**3. Current State of the Repository**
- **Virtual Environment (`.venv`):** Python 3.12 managed via `uv`, with dependencies installed and pinned in `requirements.txt` (`pandas`, `numpy`, `scikit-learn`, `lightgbm`, `matplotlib`, `seaborn`, `joblib`, `scipy`, `ipykernel`).
- **Scaffolded Folders:** `data/raw/`, `data/processed/`, `notebooks/`, `src/`, `models/`, `reports/metrics/`, `reports/figures/`, `docs/`.
- **Git State:** Initial scaffold and roadmap committed and pushed to `origin/main`.
- **Current Code Status:** **Zero code written yet.** The user is implementing the code themselves following the project philosophy: *"Notebooks explore and verify first; modular code graduates to `src/` once proven and understood."*

---

**4. Where We Are Right Now (Immediate Next Step)**
- **Current Phase:** **Phase 1** of the 18-phase implementation roadmap.
- **Active Task:** Open `notebooks/01_data_understanding.ipynb`, inspect the raw data file (`data/raw/kddcup.csv`), parse headers from `kddcup.names.txt`, and verify the row dimensions `(494021, 42)` and the duplicate row count (`348,435` duplicates).
- **Next Transition:** Graduate verified loading and schema assertion code into `src/data.py` (`load_raw`) and `src/validate.py` (`validate_raw_schema`) in **Phase 2**.
```
