# Discovery Log — Network Guardian IDS Project

This log records our actual development journey, empirical observations, failures, wrong turns, and key decisions throughout the project.

---

## Log Entries

### Entry 1: Data Understanding & The Duplicate Row Discovery (Phase 1)
- **Date:** October 5, 2026
- **Question Raised:** What does the raw KDD Cup 1999 10% dataset actually contain? Can we use standard random splitting as-is?
- **Observation / Finding:** 
  - The dataset has no header row; 41 features plus 1 label column (42 columns total) were parsed from `kddcup.names.txt`.
  - Raw row count is exactly 494,021 with 0 NaN values.
  - Raw labels end with a trailing period (e.g., `normal.`, `neptune.`), which must be stripped before processing.
  - A staggering **70.53% of rows (348,435 out of 494,021)** are exact duplicates across all features and target label.
  - Duplicate density varies wildly across attacks: `smurf` has 280,149 duplicates (99.77% duplicate rate!), `neptune` has 55,381 duplicates, and `normal` has 9,447 duplicates. In contrast, rare attack types like `buffer_overflow` (30 rows), `loadmodule` (9 rows), `perl` (3 rows), and `rootkit` (10 rows) have zero duplicates.
- **Action Taken:** Strip trailing periods from labels, map attack types to the 5 major families, and deduplicate prior to any train/test split.
- **Impact on Results:** Total dataset size collapses from 494,021 down to 145,583 instances.

---

### Entry 2: Label Mapping & Conflict Resolution Rules (Phases 2 & 3)
- **Date:** October 5, 2026
- **Question Raised:** What happens if identical feature vectors have different labels? How should ties and conflicts be resolved?
- **Investigation & Rules Formulated:**
  1. **Exact Duplicates:** Identical feature vector AND identical label $\rightarrow$ keep first occurrence (348,435 rows removed).
  2. **Conflicting Labels:** Identical feature vector but DIFFERENT attack family $\rightarrow$ ambiguous threat signals; drop the entire conflict group (2 rows removed).
  3. **Same Family, Different Attack Name:** Identical feature vector and same target family, but differing sub-attack names (e.g. `portsweep` vs `satan`) $\rightarrow$ keep first occurrence because the macro family target is unambiguous (1 row removed).
  4. **Constant Columns:** Confirmed that `num_outbound_cmds` and `is_host_login` have zero variance (`nunique() == 1`, all values 0). Both columns were dropped.
- **Verification:** Built a 6-row synthetic unit test (`make_synthetic`) in `notebooks/data_preparation.ipynb` validating that exact duplicates, family conflicts, and same-family sub-attack ties behave exactly as specified.
- **Resulting Post-Cleaning Family Counts (145,583 total rows):**
  - **Normal:** 87,831 rows
  - **DoS:** 54,571 rows
  - **Probe:** 2,130 rows
  - **R2L:** 999 rows
  - **U2R:** 52 rows (extreme rarity; 10 rows in a 20% test split)
- **Saved Artifact:** Exported `data/processed/dedup_summary.csv` tracking before/after/removed counts for all 23 attack types.

---

### Entry 3: The 99.96% Fake Leakage Demonstration (Phase 4)
- **Date:** October 5, 2026
- **Question Raised:** What actually happens if someone trains a decision tree on raw, non-deduplicated data with a standard random 80/20 train/test split?
- **Experiment:** Trained a default `DecisionTreeClassifier(random_state=42)` on raw split vs. cleaned deduplicated split.
- **Empirical Results:**
  - **RAW (Leaked) Data:**
    - Test row contamination: **72,652 out of 98,805 test rows (73.53%)** appeared word-for-word in the training set!
    - Raw Test Accuracy: **99.96%**
    - Raw Test Macro-F1: **0.9333**
    - Honest evaluation (filtering out the 73.5% leaked rows): Accuracy dropped, demonstrating that the apparent "near-perfect" score was an illusion created by row memorization rather than generalized attack pattern recognition.
  - **CLEAN (Deduplicated) Data:**
    - Test row contamination: **0 rows (0.00% overlap)**.
    - True decision tree baseline Macro-F1: ~0.91.
- **Key Takeaway for Report & Video:**
  - This is our central empirical proof for Section II: **"If a model looks 99.96% perfect, you should be deeply suspicious."** High raw accuracy was driven entirely by memorizing repeated `smurf` and `neptune` flood packets.

---

### Entry 4: Stratified 80/20 Train/Test Split & Leakage Assertions (Phase 5)
- **Date:** October 5, 2026
- **Question Raised:** How do we partition the data so rare classes are representative and test data remains completely uncontaminated?
- **Design Decisions:**
  - Stratified 80/20 split based on the 5-family target:
    - **Train Set (80%):** 116,466 rows (Normal: 70,265; DoS: 43,657; Probe: 1,704; R2L: 799; U2R: 42)
    - **Test Set (20%):** 29,117 rows (Normal: 17,566; DoS: 10,914; Probe: 426; R2L: 200; U2R: 10)
  - Saved split indices to disk (`data/processed/train_idx.npy`, `data/processed/test_idx.npy`) and recorded metadata in `data/processed/split_meta.json`.
  - Locked the test set: created `load_train()` and `load_test()` in `src/data.py` so subsequent modeling and EDA phases strictly ingest `X_train, y_train, meta_train`.
- **Integrity & Fault Injection Tests (`src/validate.py`):**
  - Verified index disjointness (`intersection == 0`).
  - Verified exact row union (`union == 145,583`).
  - Proved zero feature vector leakage (`row_overlap(X_train, X_test) == 0`).
  - Verified that fault injection tests (injecting intentional overlap or missing indices) raise `AssertionError` and pass break tests.

---

### Entry 5: Train-Only Exploratory Data Analysis & Feature Typology (Phase 6)
- **Date:** October 5, 2026
- **Question Raised:** What do the distributions, correlations, and feature characteristics look like on the training partition (`X_train`), and how do they inform preprocessing without data snooping?
- **Key Empirical Discoveries on Train (116,466 rows):**
  1. **Protocol Specificity:** R2L and U2R attacks are strictly confined to the **TCP** protocol (100% of R2L and 98% of U2R are TCP). ICMP connections are split between Normal, DoS (`smurf`), and Probe.
  2. **Severe Skewness:** `src_bytes` spans from 0 to 693,375,640 (median: 147.0) with an extreme skewness of **339.89**. `urgent` (217.35), `num_compromised` (215.10), and `dst_bytes` (84.04) also exhibit heavy tails. This justifies applying `np.log1p` before scaling for linear models (Logistic Regression).
  3. **High Multicollinearity (13 Pairs with $|r| > 0.95$):**
     - Perfect redundancies in SYN error rates: `srv_serror_rate` $\leftrightarrow$ `dst_host_srv_serror_rate` ($r = 0.9983$), `serror_rate` $\leftrightarrow$ `dst_host_serror_rate` ($r = 0.9967$).
     - Host compromise twins: `num_compromised` $\leftrightarrow$ `num_root` ($r = 0.9955$).
     - REJ error rates: `rerror_rate` $\leftrightarrow$ `srv_rerror_rate` ($r = 0.9913$).
     - *Decision:* Keep all correlated features for tree models (trees split on thresholds internally), but use permutation importance rather than MDI to avoid splitting credit.
  4. **Zero-Inflation & Host Content Discriminators:**
     - Content features (`urgent`, `su_attempted`, `num_shells`, `root_shell`, `num_failed_logins`) are >99.9% zeros across the general population.
     - However, non-zero values are almost exclusively concentrated in **R2L and U2R** (e.g. `hot` is non-zero in 43.1% of R2L and 57.1% of U2R; `root_shell` is non-zero in 11.9% of U2R).
  5. **Feature-to-Family Discriminative Separation:**
     - **DoS and Probe** are distinguished by *traffic-window features* (`count`, `srv_count`, `serror_rate`).
     - **R2L and U2R** are distinguished by *host content features* (`hot`, `num_root`, `num_file_creations`, `num_failed_logins`).
  6. **Feature Column Partitions Added to `src/config.py`:**
     - `CONSTANT_COLS = ["num_outbound_cmds", "is_host_login"]` (2 cols)
     - `CATEGORICAL_COLS = ["protocol_type", "service", "flag"]` (3 cols)
     - `BINARY_COLS = ["is_guest_login", "land", "logged_in", "root_shell"]` (4 cols)
     - `NUMERIC_COLS` = 32 remaining continuous/count features.
     - `HEAVY_TAILED_COLS` = 16 numeric features with skewness $> 5.0$.
     - Proved full coverage: `CONSTANT + CATEGORICAL + BINARY + NUMERIC == 41 features`.

---

### Entry 6: Leakage-Free Preprocessing & Row-Wise Feature Engineering (Phase 7)
- **Date:** October 6, 2026
- **Question Raised:** How do we package feature engineering, categorical encoding, and numeric scaling so they re-fit strictly inside each CV fold without information leakage?
- **Implementation & Architecture:**
  1. **Row-Wise Feature Engineering (`src/features.py`):**
     - `bytes_ratio`: $\log(1 + \text{src\_bytes}) - \log(1 + \text{dst\_bytes})$ (directional flow ratio without zero-division risk).
     - `zero_payload`: Binary indicator for $(\text{src\_bytes} = 0 \land \text{dst\_bytes} = 0)$ capturing scanning/flood probes.
     - `content_activity`: Host-level suspicious indicator count summing payload anomalies (`hot`, `num_failed_logins`, `num_compromised`, `num_root`, etc.).
     - `privilege_flag`: Binary indicator for privilege escalation indicators ($\text{root\_shell} > 0 \lor \text{su\_attempted} > 0 \lor \text{num\_root} > 0$).
  2. **Pipeline Preprocessor (`src/preprocessing.py`):**
     - Categorical features (`protocol_type`, `service`, `flag`) $\rightarrow$ `OneHotEncoder(handle_unknown='ignore', sparse_output=False)` producing 80 encoded columns on train.
     - Binary features (`BINARY_COLS` + engineered binary flags) $\rightarrow$ passthrough.
     - When `scale=False` (tree models): all remaining numerical features pass through untouched (115 total columns without engineering, 119 with engineering).
     - When `scale=True` (linear models): heavy-tailed features get `log1p` + `StandardScaler`; remaining numerics get `StandardScaler`. Added `feature_names_out="one-to-one"` to ensure seamless pipeline introspection.
  3. **Verification & Assertions Passed:**
     - **Row-Independence:** Transforming a single row in isolation yields identical numerical values to transforming that row within a batch (proving zero cross-row statistical leakage).
     - **Unseen Categories:** Input records with previously unseen services transform without errors.
     - **Immutability:** `add_features()` returns a copy and does not mutate input DataFrames.
     - **Pipeline Integration:** `build_pipeline(DummyClassifier())` fits and predicts smoothly across all four combinations of `scale` $\in \{\text{True}, \text{False}\}$ and `engineered` $\in \{\text{True}, \text{False}\}$.

---

### Entry 7: Evaluation Harness Architecture & The Dummy Sanity Floor (Phase 8)
- **Date:** October 6, 2026
- **Question Raised:** How do we construct an unshakeable, leak-proof cross-validation harness that accurately measures multiclass performance, tracks real-world operational security constraints (FPR $\le 0.5\%$), benchmarks inference latency, and establishes an empirical performance floor?
- **Implementation & Architectural Decisions:**
  1. **Strict Train-Only 5-Fold Stratified Cross-Validation (`src/evaluation.py`):**
     - Configured `get_cv(n_splits=5, seed=42)` using `StratifiedKFold(shuffle=True)`.
     - Verified fold disjointness ($V_i \cap T_i = \emptyset$), strict index partition completeness ($\sum |V_i| = 116,466$), and deterministic reproducibility across runs.
  2. **Multi-Perspective Metrics Engine (`multiclass_metrics` & `binary_view`):**
     - **Multiclass View:** Computes overall Accuracy, Macro-F1 (primary metric), Weighted-F1, Balanced Accuracy, and per-class Precision, Recall, and F1 across all 5 families (`Normal`, `DoS`, `Probe`, `R2L`, `U2R`) with `zero_division=0`.
     - **Operational Binary View:** Projects predictions to binary intrusion detection:
       $$\text{FPR} = \frac{\text{Normal classified as Attack}}{\text{Total Actual Normal}}$$
       $$\text{FNR} = \frac{\text{Attacks classified as Normal}}{\text{Total Actual Attacks}}$$
       This directly ties into our core operational IDS requirement: an enterprise intrusion detection system must maintain $\text{FPR} \le 0.5\%$ to prevent alert fatigue from overwhelming security operations centers (SOC).
  3. **Timing & Out-of-Fold (OOF) Tracking (`evaluate_cv`):**
     - Manual CV loop with `sklearn.base.clone(pipeline)` to ensure zero state carryover between folds.
     - Times training (`fit_time`) and latency (`predict_time_per_1k` in ms per 1,000 queries) per fold.
     - Accumulates exact Out-of-Fold predictions ($N = 116,466$) for downstream threshold calibration and error analysis.
  4. **The Dummy Classifier Floor (M0):**
     - Built `M0_dummy` using `DummyClassifier(strategy='most_frequent')` wrapped in `build_pipeline(scale=False, engineered=False)`.
     - Predicts strictly the majority class (`Normal`) for all samples.
- **Empirical Baseline Results (5-Fold CV on 116,466 training samples):**
  - **Accuracy:** $0.6033$ (exactly equals the prevalence of `Normal` in train: $70,264 / 116,466$).
  - **Macro-F1:** $0.1505$ (Normal F1 is $0.7526$; all 4 attack families have F1 of $0.0000$; macro average $= 0.7526 / 5$).
  - **Weighted-F1:** $0.4540$.
  - **Balanced Accuracy:** $0.2000$ (recall is $1.0000$ for Normal and $0.0000$ for all 4 attacks; mean recall $= 1/5$).
  - **Binary FPR:** $0.0000$ (0 false alarms because it never flags any connection as an attack).
  - **Binary FNR:** $1.0000$ (misses 100% of all intrusions: 0/43,657 DoS, 0/1,704 Probe, 0/799 R2L, 0/42 U2R).
  - **Inference Latency:** $\approx 0.0011$ ms per 1,000 connections.
- **Key Takeaways & Significance for Report & Video:**
  - **The "0% False Alarm" Fallacy:** M0 achieves the theoretical ideal of zero false alarms ($\text{FPR} = 0\%$), yet it is completely useless as an IDS because it allows 100% of attacks to penetrate undetected ($\text{FNR} = 100\%$).
  - **Accuracy as a Deceptive Metric:** M0 appears to have $>60\%$ accuracy despite having zero detection capability, reinforcing why Macro-F1, per-class recall, and paired FPR/FNR are mandatory.
  - Any valid machine learning candidate (M1–M4) must substantially beat Macro-F1 $> 0.1505$ and FNR $\ll 1.0000$ while maintaining $\text{FPR} \le 0.0050$.
- **Artifacts Generated:** Saved fold metrics to `reports/metrics/cv_results_M0_dummy.csv`.

---

### Entry 8: Logistic Regression Linear Baseline & The Linear Alert Fatigue Barrier (Phase 9)
- **Date:** October 7, 2026
- **Question Raised:** How effectively can a linear model separate network attack classes from normal traffic under balanced class weighting, and does a linear decision boundary satisfy the enterprise false alarm constraint ($\text{FPR} \le 0.5\%$)?
- **Model Architecture & Preprocessing (`M1_logreg`):**
  - **Estimator:** Multinomial `LogisticRegression(solver='lbfgs', max_iter=3000, class_weight='balanced', random_state=42)`.
  - **Preprocessing:** Pipeline with `scale=True` (StandardScaler on all numeric features, log1p + StandardScaler on heavy-tailed columns) and `OneHotEncoder(handle_unknown='ignore')` yielding 115 input features.
  - **Class Weighting:** Inversely proportional to class frequencies ($w_c = N / (K \cdot N_c)$): Normal ($0.33$), DoS ($0.53$), Probe ($13.67$), R2L ($29.15$), U2R ($554.60$).
- **Key Empirical Discoveries & Results (5-Fold CV on 116,466 training samples):**
  1. **Convergence Sensitivity & Necessity of Scaling:**
     - Fitting without feature scaling (`scale=False`) triggers `ConvergenceWarning: lbfgs failed to converge` even after hundreds of iterations, driven by extreme feature variance (e.g., `src_bytes` with skewness $>300$ and values up to $6.9 \times 10^8$).
     - With `scale=True`, L-BFGS converges smoothly across all 5 folds with zero convergence warnings.
  2. **Performance Summary:**
     - **Accuracy:** $0.9882 \pm 0.0009$ ($98.82\%$).
     - **Macro-F1:** $0.7702 \pm 0.0043$ (Range: $0.7666$ to $0.7767$). A massive leap over M0 Dummy ($0.1505$).
     - **Binary FPR:** **$0.0181 \pm 0.0015$ ($1.81\%$)**. **Violates the operational limit ($\le 0.50\%$) by 3.6x!**
     - **Binary FNR:** $0.0013 \pm 0.0002$ ($0.13\%$; captures $>99.8\%$ of attacks).
     - **Per-Class Breakdown:**
       - `Normal`: Recall $98.19\%$, F1 $0.9904$
       - `DoS`: Recall $99.86\%$, F1 $0.9988$
       - `Probe`: Recall $98.88\%$, F1 $0.9099$
       - `R2L`: Recall $98.00\%$, F1 $0.6557$ (Precision: $49.31\%$)
       - `U2R`: Recall $78.89\%$, F1 $0.2962$ (Precision: $18.36\%$)
     - **Fit Latency:** $\approx 50.4$s per fold; inference latency $\approx 0.0019$ ms per 1,000 packets.
  3. **The Core Theoretical Finding for Section III & IV of the Final Report:**
     - **The Linear Decision Boundary Barrier:** Under balanced class weights, logistic regression bends its hyperplane to capture rare attacks (achieving high recall: $98.0\%$ R2L, $78.9\%$ U2R). However, because linear hyperplanes cannot model non-linear boundaries between packet attributes (e.g. valid web requests vs. stealthy HTTP probes), it over-flags benign traffic as intrusive.
     - **Operational Impact:** An FPR of $1.81\%$ means that out of 1,000,000 normal transactions per day, **~18,100 false alarms** are generated daily, overwhelming SOC analysts and causing alert fatigue.
     - This provides clear empirical justification for transitioning to non-linear tree-based architectures (Decision Tree M2, Random Forest M3, LightGBM M4).
  4. **Interpretability & Top Coefficient Drivers:**
     - `DoS`: Driven by `flag_S0` (+4.76), `service_ecr_i` (+4.61), `protocol_type_icmp` (+4.26) — classic ICMP floods and half-open SYN connections.
     - `Normal`: Driven by `service_http` (+4.08), `is_guest_login` (+3.90).
     - `R2L`: Driven by `service_imap4` (+6.64), `protocol_type_tcp` (+3.92).
     - `U2R`: Driven by `service_telnet` (+9.41), `logged_in` (+4.34) — interactive terminal sessions leading to unauthorized root transitions.
- **Artifacts Generated:** Saved fold metrics to `reports/metrics/cv_results_M1_logreg.csv`.




