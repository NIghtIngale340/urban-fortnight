# urban-fortnight — Network Guardian: Detecting Network Intrusions with Machine Learning

A machine-learning-based prototype of an Intrusion Detection System (IDS) trained on the KDD Cup 1999 dataset to classify network connections into Normal traffic and four attack families: **Denial of Service (DoS)**, **Remote to Local (R2L)**, **User to Root (U2R)**, and **Probe**.

Developed for **CCINSYSL (Introduction to Intelligent Systems)** course project.

---

## Repository Structure

```
├── .venv/                         # Python 3.12 virtual environment (local, ignored)
├── requirements.txt               # Pinned Python package dependencies
├── .gitignore                     # Git ignore rules for venv, caches, and large data
├── data/
│   ├── raw/                       # Raw metadata and dataset reference (kddcup.names.txt, etc.)
│   └── processed/                 # Generated indices and processed metadata
├── notebooks/                     # Jupyter notebooks (01 to 05)
├── src/                           # Core modular Python packages
├── models/                        # Serialized model pipelines and model card
├── reports/
│   ├── metrics/                   # Evaluation tables (CSV / JSON)
│   └── figures/                   # Visualizations (fig01 to fig18)
├── docs/
│   └── discovery_log.md           # Engineering discovery log
├── Document.md                    # Course project documentation template
├── Project_Specs.md               # Course project specifications and rubrics
└── new.md                         # Reference architecture and design specification
```

---

## Environment Setup

The virtual environment is managed using Python 3.12:

```bash
# Activate the virtual environment
source .venv/bin/activate

# Or install dependencies in a new environment
uv venv .venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
```

---

## Key Experimental Findings & Focus Areas

1. **Duplicate Elimination:** 70.5% of rows in the raw KDD Cup 1999 10% dataset are exact duplicates. Splitting raw data at random causes 73.5% test contamination, resulting in a counterfeit 99.96% accuracy. Deduplication is performed *before* train/test splitting.
2. **Evaluation Metrics:** Class imbalance is severe (U2R has only 52 instances). Multi-class **Macro-F1** is the primary evaluation metric.
3. **Operational IDS Constraint:** The binary false-positive rate target of **FPR ≤ 0.5%** is an explicit engineering design choice to mitigate alert fatigue.
4. **Core Models Compared:**
   - **M0:** Dummy Classifier (sanity floor)
   - **M1:** Logistic Regression (linear baseline)
   - **M2:** Decision Tree (interpretable baseline)
   - **M3:** Random Forest (bagging ensemble)
   - **M4:** LightGBM (boosting ensemble)
   - **X1 [Optional]:** Isolation Forest (semi-supervised anomaly detection, trained on Normal only)

---

## 18-Phase Implementation Roadmap

1. **Inspect Raw File** (`notebooks/01_data_understanding.ipynb`)
2. **`load_raw` & Schema Validation** (`src/data.py`, `src/validate.py`)
3. **Map Labels, Dedupe, Drop Conflicts** (Normalized labels, metadata attack names)
4. **Leakage Demonstration** (Decision tree on raw split vs. deduplicated split)
5. **Stratified Split & Leakage Assertions** (80/20 train/test split, locked test set)
6. **Train-Only Exploratory Data Analysis** (Distributions, correlations, feature ideas)
7. **Preprocessor & Feature Transformers** (Encapsulated in scikit-learn `Pipeline`)
8. **Evaluation Harness + Dummy Baseline** (Macro-F1, binary FPR/FNR, confusion matrix)
9. **Default M1–M4 Models on Train** (5-fold stratified CV on train)
10. **Ablations & Out-of-Fold Analysis** (Class weights, engineered features, rare-class recall)
11. **Equal-Budget Hyperparameter Tuning** (`RandomizedSearchCV`)
12. **Pre-Registered Selection Rule & 5×3 Repeated CV** (Declared *before* final comparison)
13. **Single Locked Test Evaluation** (Re-fit winner on 100% train, evaluate test once)
14. **Error & Overfitting Analysis** (Threshold tuning from out-of-fold probabilities)
15. **Semi-Supervised Isolation Forest** (`notebooks/05_optional_anomaly_detection.ipynb`)
16. **Pipeline Serialization & `src/predict.py`** (Save `final_pipeline.joblib` and model card)
17. **Reproducibility Audit** (Kernel Restart & Run All verification)
18. **Final Metrics, Figures & Documentation** (Fill `Document.md` and `docs/discovery_log.md`)

