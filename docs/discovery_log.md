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
    - Test row contamination: **72,640 out of 98,805 test rows (73.52%)** appeared word-for-word in the training set!
    - Raw Test Accuracy: **0.9997 (99.97%)**
    - Raw Test Macro-F1: **0.9083**
    - Honest evaluation on the non-leaked test subset (only the 26,165 non-leaked rows):
      - Honest Accuracy: **0.9988**
      - Honest Macro-F1: **0.9063**
      - Proves that apparent near-perfection on the raw set was heavily inflated by row memorization of duplicate DoS packets rather than generalized learning.
  - **CLEAN (Deduplicated) Data:**
    - Test row contamination: **0 rows (0.00% overlap)**.
    - Clean Test Accuracy: **0.9991**
    - Clean Test Macro-F1: **0.9085**.
- **Key Takeaway for Report & Video:**
  - Central empirical proof for Section II: **"If a model looks 99.96% perfect, you should be deeply suspicious."** High raw accuracy was driven by memorizing repeated `smurf` (280k) and `neptune` (55k) flood packets.

---

### Entry 4: Stratified 80/20 Train/Test Split & Leakage Assertions (Phase 5)
- **Date:** October 5, 2026
- **Question Raised:** How do we partition the data so rare classes are representative and test data remains completely uncontaminated?
- **Design Decisions:**
  - Stratified 80/20 split based on the 5-family target:
    - **Train Set (80%):** 116,466 rows (Normal: 70,264; DoS: 43,657; Probe: 1,704; R2L: 799; U2R: 42)
    - **Test Set (20%):** 29,117 rows (Normal: 17,567; DoS: 10,914; Probe: 426; R2L: 200; U2R: 10)
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
     - SYN error redundancies: `srv_serror_rate` $\leftrightarrow$ `dst_host_srv_serror_rate` ($r = 0.9983$), `serror_rate` $\leftrightarrow$ `dst_host_serror_rate` ($r = 0.9967$).
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
  2. **Pipeline Preprocessor & Column Width Alignment (`src/preprocessing.py`):**
     - Categorical features (`protocol_type`, `service`, `flag`) $\rightarrow$ `OneHotEncoder(handle_unknown='ignore', sparse_output=False)`.
     - *Why 115 vs. 116 columns:* In the raw dataset, 66 services exist ($3 + 66 + 11 = 80$ one-hot categories $\rightarrow$ 116 total features). In the training partition `X_train`, exactly 65 services appear ($3 + 65 + 11 = 79$ one-hot categories $\rightarrow$ 115 total features without engineering, and 119 with the 4 engineered features).
     - Binary features (`BINARY_COLS` + engineered binary flags) $\rightarrow$ passthrough.
     - When `scale=False` (tree models): all remaining numerical features pass through untouched (115 total columns without engineering, 119 with engineering).
     - When `scale=True` (linear models): heavy-tailed features get `log1p` + `StandardScaler`; remaining numerics get `StandardScaler`. Added `feature_names_out="one-to-one"` to ensure seamless pipeline introspection.
  3. **Verification & Assertions Passed:**
     - **Row-Independence:** Transforming a single row in isolation yields identical numerical values to transforming that row within a batch (proving zero cross-row statistical leakage).
     - **Unseen Categories:** Input records with previously unseen services transform without errors (`handle_unknown='ignore'`).
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

### Entry 8: Logistic Regression Baseline (M1) & The Alert-Fatigue Barrier (Phase 9)
- **Date:** October 12, 2026
- **Question Raised:** Can a multinomial linear model with one-hot encoding, log1p transformation, standard scaling, and balanced class weighting serve as an effective baseline for intrusion detection, and what does its false positive rate reveal about operational alert fatigue?
- **Model Architecture & Preprocessing (`M1_logreg`):**
  - **Estimator:** `LogisticRegression(solver='lbfgs', class_weight='balanced', max_iter=3000, random_state=42)`.
  - **Preprocessing:** Pipeline with `scale=True, engineered=False` (`OneHotEncoder` for categoricals, `log1p` + `StandardScaler` for heavy-tailed numerics, `StandardScaler` for remaining numerics).
- **Key Empirical Discoveries & Results (5-Fold CV on 116,466 training samples):**
  1. **Performance Gains Over Floor:**
     - **Accuracy:** $0.9882 \pm 0.0007$ ($98.82\%$).
     - **Macro-F1:** $0.7702 \pm 0.0043$ ($+61.97$ points over Dummy M0).
     - **Binary FNR:** $0.00130 \pm 0.00034$ ($0.13\%$), capturing $>99.87\%$ of all intrusions.
  2. **The Alert-Fatigue Barrier Violation:**
     - **Binary FPR:** **$0.01810 \pm 0.00030$ ($1.810\%$)**!
     - In an enterprise network processing 1,000,000 connections/day, this generates **~18,100 false alarms every day**, exceeding our operational ceiling ($\le 0.50\% \approx 5,000$ alarms/day) by $3.6\times$.
     - An SOC analyst team would be completely overwhelmed by alert fatigue.
  3. **Per-Family Recall:**
     - `Normal`: $98.19\%$ (F1: $0.9904$)
     - `DoS`: $99.86\%$ (F1: $0.9992$)
     - `Probe`: $98.88\%$ (F1: $0.8872$)
     - `R2L`: $98.00\%$ (F1: $0.6711$)
     - `U2R`: $78.89\%$ (F1: $0.3031$)
- **Initial Hypothesis & Re-evaluation Annotation:**
  - *(Important Annotation: We initially hypothesized that linear boundaries fundamentally cannot separate Normal traffic from attacks without producing high false alarms. As proven later in Entry 13 / Finding 36, this hypothesis was incorrect: unweighted Logistic Regression achieved an FPR of 0.144%, well under the 0.5% limit. The primary driver of the 1.81% false positive rate was the balanced class weighting pushing the decision hyperplane deep into Normal traffic space to catch minority points).*
- **Artifacts Generated:**
  - Fold metrics: `reports/metrics/cv_results_M1_logreg.csv`
  - OOF predictions: `reports/metrics/oof_M1_logreg.npz`

---

### Entry 9: Decision Tree Baseline (M2), Non-Linear Threshold Boundaries & The Overfitting Dilemma (Phase 10)
- **Date:** October 12, 2026
- **Question Raised:** Can non-linear axis-aligned splits solve the alert fatigue problem ($\text{FPR} \le 0.5\%$) while lifting Macro-F1, and what happens to model generalization when individual trees grow without depth constraints?
- **Model Architecture & Preprocessing (`M2_tree`):**
  - **Estimator:** `DecisionTreeClassifier(class_weight='balanced', min_samples_leaf=2, random_state=42, max_depth=None)`.
  - **Preprocessing:** Pipeline with `scale=False, engineered=False` (trees are invariant to monotonic transformations; omitting scaling cuts execution time while preserving raw interpretable split thresholds).
- **Key Empirical Discoveries & Results (5-Fold CV on 116,466 training samples):**
  1. **Performance Surge & Alert Fatigue Resolution:**
     - **Macro-F1:** Jumps from $0.7702$ (Logistic Regression) to **$0.9122 \pm 0.0158$** ($+14.2$ percentage points!).
     - **Binary FPR:** Plummets from $1.81\%$ down to **$0.0016 \pm 0.0003$ ($0.16\%$)**!
     - **Operational Compliance:** $0.16\%$ comfortably clears the $\le 0.50\%$ enterprise false alarm ceiling. In a 1,000,000 requests/day environment, daily false alarms drop from ~18,100 down to ~1,600 (a **91.2% reduction in false alert fatigue**).
     - **Binary FNR:** $0.0015 \pm 0.0004$ ($0.15\%$).
     - **Accuracy:** $0.9983 \pm 0.0001$ ($99.83\%$).
     - **Fit Latency:** Rapid training at **$1.21$s per fold** (vs. ~50.1s for Logistic Regression).
  2. **Per-Class Performance:**
     - `Normal`: Recall $99.84\%$, F1 $0.9987$
     - `DoS`: Recall $99.97\%$, F1 $0.9997$
     - `Probe`: Recall $98.59\%$, F1 $0.9822$
     - `R2L`: Recall $94.99\%$, F1 $0.9348$ (up from $0.6557$ in M1)
     - `U2R`: Recall $69.17\%$, F1 $0.6456$ (more than double M1's $0.2962$)
  3. **Feature Importance (MDI) & Split Mechanisms:**
     - Top feature: `dst_host_srv_count` accounts for **$29.99\%$** of total Gini impurity reduction.
     - Followed by `src_bytes` ($20.01\%$), `dst_host_serror_rate` ($15.35\%$), and `dst_bytes` ($11.03\%$).
     - These top 4 features explain over **$76\%$ of total discriminative splits**.
     - *(Caveat on MDI Bias)*: Mean Decrease in Impurity (Gini importance) has a well-documented bias toward continuous and high-cardinality features like `dst_host_srv_count`, inflating their apparent ranking relative to binary or low-cardinality indicators. Permutation importance or ensemble feature sampling provides a less biased assessment.
  4. **The Overfitting & Depth Validation Curve Discovery (Figure `p10_validation_curve_depth.png`):**
     - Tested `max_depth` $\in [2, 3, 4, 6, 8, 10, 12, 16, 20, \text{None}]$ across 50 CV fits.
     - **Shallow Depths (2–6):** Suffer severe underfitting (Macro-F1 $0.4086 \rightarrow 0.6933$).
     - **Intermediate Depths (8–16):** Strong generalization growth (Macro-F1 reaches $0.9146$ at depth 16).
     - **Deep / Unconstrained Trees (20 vs. None):**
       - Unconstrained tree reaches **depth 23 with 224 leaves**.
       - Training Macro-F1 increases from $0.9804 \rightarrow 0.9847$, while CV Macro-F1 shifts slightly from $0.9146$ (depth 16) to $0.9122$ (None).
       - This drop of $\Delta = 0.0024$ is well within fold standard deviation ($\sigma \approx 0.0158$), indicating mild leaf memorization (e.g. isolating 2-sample U2R leaves) rather than catastrophic failure.
  5. **Core Justification for Phase 11 (Random Forest M3):**
     - Single unpruned decision trees have high variance and memorize rare-class leaf noise (e.g., isolating 2-sample U2R leaves).
     - This provides direct theoretical and empirical justification for ensemble bagging in **Phase 11 (Random Forest M3)**: averaging across hundreds of decorrelated trees reduces variance without sacrificing the non-linear threshold advantages.
- **Artifacts Generated:**
  - Fold metrics: `reports/metrics/cv_results_M2_tree.csv`
  - Figure: `reports/figures/p10_validation_curve_depth.png`

---

### Entry 10: Random Forest Bagging Ensemble (M3), OOB Consistency & Sub-0.05% Alert Fatigue Suppression (Phase 11)
- **Date:** October 12, 2026
- **Question Raised:** Can bootstrap aggregation (bagging) with random feature subspaces ($\sqrt{p}$) resolve single-tree variance and depth memorization, reduce enterprise false alarm rates below $0.05\%$, and provide trustworthy out-of-bag validation?
- **Model Architecture & Preprocessing (`M3_rf`):**
  - **Estimator:** `RandomForestClassifier(n_estimators=300, class_weight='balanced_subsample', max_features='sqrt', min_samples_leaf=2, oob_score=True, n_jobs=-1, random_state=42)`.
  - **Preprocessing:** Pipeline with `scale=False, engineered=False` (tree ensembles are invariant to monotonic transformations).
  - **Ensemble Upgrades:**
    - `n_estimators=300`: Ample ensemble size to achieve empirical convergence on bootstrap variance reduction.
    - `class_weight='balanced_subsample'`: Re-computes class weighting on each bootstrap draw ($\mathcal{D}^{*b}$) rather than on the aggregate training set, preventing rare classes like U2R from being overwhelmed in individual trees.
    - `oob_score=True`: Evaluates predictions on out-of-bag samples without separate validation partitioning.
- **Key Empirical Discoveries & Results (5-Fold CV on 116,466 training samples):**
  1. **Performance Surge Across All Metrics:**
     - **Accuracy:** $0.9993 \pm 0.0001$ ($99.93\%$).
     - **Macro-F1:** Rises to **$0.9498 \pm 0.0157$** ($+3.76$ points over Decision Tree M2's $0.9122$, and $+17.96$ points over Logistic Regression M1's $0.7702$).
     - **Binary FPR:** Compresses to an astounding **$0.00036 \pm 0.00024$ ($0.036\%$)**!
       - In an enterprise network processing 1,000,000 connections/day, daily false alarms drop from ~18,100 (Logistic Regression) and ~1,640 (Decision Tree) down to **only ~360 alarms per day**.
       - This is **less than $1/13\text{th}$ of our operational target ceiling ($\le 0.5\%$)**, effectively extinguishing alert fatigue.
     - **Binary FNR:** Drops to **$0.00106 \pm 0.00036$ ($0.11\%$)**, capturing $>99.89\%$ of all attacks.
  2. **Rare-Class Stabilization:**
     - `Normal`: Recall $99.96\%$, F1 $0.9995$
     - `DoS`: Recall $99.98\%$, F1 $0.9999$
     - `Probe`: Recall $99.35\%$, F1 $0.9944$
     - `R2L`: Recall $96.24\%$, F1 **$0.9721$** (Precision: $98.2\%$)
     - `U2R`: Recall $78.89\%$, F1 **$0.7830$** (Precision: $77.8\%$; up from $0.6456$ in Decision Tree and $0.2962$ in Logistic Regression).
  3. **Out-of-Bag (OOB) vs. Cross-Validation Consistency:**
     - **OOB Accuracy:** $0.9994$ (matches 5-fold CV accuracy $0.9993$).
     - **OOB Macro-F1:** **$0.9503$** (matches 5-fold CV Macro-F1 $0.9498$ within $0.05\%$).
     - This empirically confirms that out-of-bag validation acts as an unbiased internal estimator, verifying the integrity of the 5-fold cross-validation harness.
  4. **Smooth Feature Subspace Importances (MDI):**
     - In Decision Tree M2, `dst_host_srv_count` heavily monopolized the top split ($29.99\%$).
     - In Random Forest M3, feature subspace sampling ($m = \sqrt{115} \approx 10$) decorrelates the trees, distributing importance smoothly:
       - `dst_host_srv_count`: $8.67\%$
       - `src_bytes`: $8.02\%$
       - `dst_bytes`: $5.88\%$
       - `count`: $4.36\%$
       - `dst_host_diff_srv_rate`: $4.08\%$
       - `logged_in`: $4.06\%$
       - `service_http`: $3.92\%$
       - `dst_host_serror_rate`: $3.75\%$
  5. **Tree-Count Validation Curve (Figure `p11_rf_n_estimators.png`):**
     - Tested $B \in [25, 50, 100, 200, 300]$ trees.
     - As $B$ increases, CV Macro-F1 rises from $0.9452$ ($B=25$) to $0.9542$ ($B=100$), and hovers between $0.950$ and $0.954$ through $B=300$. These fluctuations ($0.950\text{--}0.954$) reflect fold noise ($\sigma \approx 0.0157$) rather than a true plateau or decay.
     - Unlike single unpruned trees, increasing the number of bagging trees does not induce catastrophic generalization error, consistent with Breiman's Law of Large Numbers for Random Forests.
  6. **Inference Latency:**
     - Batch inference throughput: $47.5$ ms per 1,000 connections (evaluated in batch mode, not single-record pipeline latency), corresponding to $>21,000$ records/sec in batch processing mode.
- **Artifacts Generated:**
  - Fold metrics: `reports/metrics/cv_results_M3_rf.csv`
  - OOF predictions & probabilities: `reports/metrics/oof_M3_rf.npz`
  - Figure: `reports/figures/p11_rf_n_estimators.png`

---

### Entry 11: LightGBM Gradient Boosting (M4), Rare-Class Leaf Sensitivity, and Overfitting Dynamics (Phase 12)
- **Date:** October 12, 2026
- **Question Raised:** Can sequential gradient boosting with histogram binning and leaf-wise tree growth (LightGBM) outperform bootstrap aggregation (Random Forest) in enterprise tabular intrusion detection, particularly in detecting ultra-minority classes (`U2R`, `R2L`), minimizing training and inference latency, and maintaining an enterprise false positive rate $\le 0.05\%$?
- **Model Architecture & Preprocessing (`M4_lgbm`):**
  - **Estimator:** `LGBMClassifier(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=10, subsample=0.8, subsample_freq=1, colsample_bytree=0.8, class_weight='balanced', deterministic=True, force_row_wise=True, n_jobs=-1, random_state=42, verbose=-1)`.
  - **Preprocessing:** Pipeline with `scale=False, engineered=False` (LightGBM natively bins continuous values into 256 discrete histograms, rendering monotonic scaling irrelevant).
  - **Hyperparameter Rationale & Architectural Design:**
    - `num_leaves=31` (leaf-wise / best-first tree growth): Optimizes the global loss function directly by splitting the leaf with maximum loss reduction rather than forcing symmetric level-wise growth.
    - `learning_rate=0.05` & `n_estimators=300`: Moderate shrinkage rate coupled with 300 boosting stages ensures smooth gradient convergence without premature overshooting.
    - `min_child_samples=10`: Candidate adjustment for extreme class imbalance to explore leaf formation on rare attack clusters. However, empirical sensitivity testing (see below) demonstrates no detectable effect across tested values, and this parameter is carried into tuning.
    - `subsample=0.8` (`subsample_freq=1`) & `colsample_bytree=0.8`: Injects stochastic bagging and feature subspace sampling per tree, preventing early greedy splits from degenerating on dominant features (`dst_host_srv_count`, `src_bytes`).
    - `class_weight='balanced'`: Cost-sensitive reweighting scaling gradient and Hessian updates inversely to class prevalence.
- **Key Empirical Discoveries & Results (5-Fold CV on 116,466 training samples):**
  1. **Top-Performing Baseline Among Evaluated Models:**
     - **Accuracy:** **$0.9995 \pm 0.0002$** ($99.95\%$, superior to M3 RF's $0.9993$).
     - **Macro-F1:** Rises to **$0.9563 \pm 0.0249$** (Highest among baseline models: $+0.65$ points over Random Forest M3's $0.9498$, $+4.41$ points over Decision Tree M2's $0.9122$, and $+18.61$ points over Logistic Regression M1's $0.7702$).
     - **Binary FPR:** Compresses further to **$0.00030 \pm 0.00018$ ($0.030\%$)**!
       - In an enterprise network processing 1,000,000 connections/day, daily false alarms drop from ~360 (Random Forest) down to **only ~300 per day** ($\approx 1/17\text{th}$ of our pre-registered alert-fatigue barrier $\le 0.5\%$).
     - **Binary FNR:** Halved relative to Random Forest, plummeting to **$0.00054 \pm 0.00023$ ($0.054\%$)** (misses only $\sim 5$ attacks per 10,000 attack events, vs. $\sim 11$ for RF).
  2. **Rare-Class Sensitivity Gains:**
     - `Normal`: Recall $99.97\%$, F1 $0.9997$
     - `DoS`: Recall $99.99\%$, F1 $0.9999$
     - `Probe`: Recall $99.47\%$, F1 $0.9953$
     - `R2L`: Recall **$98.37\%$**, F1 **$0.9843$** (vs. $96.24\%$ recall and $0.9721$ F1 in Random Forest).
     - `U2R`: Recall **$81.67\%$**, F1 **$0.8024$** (vs. $78.89\%$ recall and $0.7830$ F1 in Random Forest; first model to surpass $0.80$ F1 on U2R!).
  3. **`min_child_samples` Sensitivity Analysis:**
     - Evaluated across $mcs \in [20, 10, 5]$:
       - $mcs = 20$: Macro-F1 $= 0.9628$, U2R recall $= 86.11\%$, R2L recall $= 98.50\%$, FPR $= 0.00027$.
       - $mcs = 10$ (M4 default): Macro-F1 $= 0.9563$, U2R recall $= 81.67\%$, R2L recall $= 98.37\%$, FPR $= 0.00030$.
       - $mcs = 5$: Macro-F1 $= 0.9666$, U2R recall $= 86.11\%$, R2L recall $= 98.50\%$, FPR $= 0.00028$.
     - *Empirical Finding*: The response is non-monotonic ($mcs=10$ scored lowest among the three) and the gaps ($0.003\text{--}0.010$) are well within the fold standard deviation ($\sigma = 0.0249$). There is **no detectable effect, within noise**. We therefore carry this parameter into Phase 16 hyperparameter tuning rather than treating $10$ as an essential modification.
  4. **Boosting Iterations & Overfitting Dynamics (Figure `p12_lgbm_iterations.png`):**
     - Probed across $k \in [50, 100, 200, 400, 800]$ boosting iterations.
     - Train Macro-F1 escalates rapidly from $0.9584$ ($k=50$) to $1.0000$ ($k \ge 200$), indicating full training set memorization.
     - However, validation Macro-F1 monotonically rises and stabilizes: $0.9375$ ($k=50$) $\rightarrow 0.9433$ ($k=100$) $\rightarrow 0.9592$ ($k=200$) $\rightarrow 0.9593$ ($k=400$) $\rightarrow 0.9611$ ($k=800$).
     - Unlike unpruned decision trees which experience severe test degradation, gradient boosting with shrinkage ($\eta=0.05$) and stochastic row/feature subsampling resists validation collapse even as training loss approaches zero.
  5. **Computational & Operational Efficiency:**
     - Comparing summed fit time across identical cross-validation folds, LightGBM is approximately **$1.4\times$ faster** to fit than Random Forest M3 due to 8-bit histogram discretization and leaf-wise splitting.
- **Artifacts Generated:**
  - Fold metrics: `reports/metrics/cv_results_M4_lgbm.csv`
  - OOF predictions & probabilities: `reports/metrics/oof_M4_lgbm.npz`
  - Figure: `reports/figures/p12_lgbm_iterations.png`

---

### Entry 12: Cross-Model CV Evaluation, Pre-Registered Model Selection Rule & Primary Deployment Candidate (Phase 13)
- **Date:** October 13, 2026
- **Question Raised:** When evaluating all five model paradigms (M0 Dummy, M1 Logistic Regression, M2 Decision Tree, M3 Random Forest, M4 LightGBM) across identical 5-fold cross-validation splits, which model satisfies the pre-registered operational false alarm rate constraint ($\le 0.5\%$), delivers superior macro-F1 and rare-class sensitivity, and wins according to our pre-registered model selection protocol?
- **Evaluation Architecture & Methodology:**
  - **Harness:** Unified evaluation using `summarize_cv` and `paired_diff` in `src/evaluation.py` across identical 5 folds on 116,466 training samples.
  - **Pre-Registered Selection Protocol (Locked at `2026-10-13 00:05`):**
    1. **FPR Gate (Operational Alert-Fatigue Barrier):** Discard any model whose mean CV false positive rate exceeds $0.5\%$ ($0.0050$).
    2. **Primary Ranking:** Rank remaining compliant models by mean CV Macro-F1.
    3. **Tie-Break Criterion:** Acknowledge that cross-validation folds share training data and are not independent (Nadeau & Bengio, 2003). If the gap between two models is within one pooled fold standard deviation ($|\Delta| < \sigma_{\text{pooled}}$), treat the performance difference as a statistical tie and break it strictly in pre-registered hierarchical order:
       - *(a)* Higher combined rare-class recall ($\text{Recall}_{\text{R2L}} + \text{Recall}_{\text{U2R}}$);
       - *(b)* Lower binary FPR;
       - *(c)* Faster compute (fit time + inference latency);
       - *(d)* Simpler model complexity.
- **Key Empirical Discoveries & Results:**
  1. **FPR Gate Evaluation:**
     - `M0_dummy`: $\text{FPR} = 0.00000$ $\rightarrow$ **PASS** (trivial baseline; 100% false negative rate).
     - `M1_logreg`: $\text{FPR} = 0.01810$ ($1.810\%$) $\rightarrow$ **FAIL** (exceeds $0.50\%$ threshold by $3.6\times$; ~18,100 false alarms/day; disqualified from enterprise deployment).
     - `M2_tree`: $\text{FPR} = 0.00164$ ($0.164\%$) $\rightarrow$ **PASS** (~1,640 false alarms/day).
     - `M3_rf`: $\text{FPR} = 0.00036$ ($0.036\%$) $\rightarrow$ **PASS** (~360 false alarms/day).
     - `M4_lgbm`: $\text{FPR} = 0.00030$ ($0.030\%$) $\rightarrow$ **PASS** (~300 false alarms/day).
  2. **Macro-F1 Ranking Among Compliant Models:**
     1. **`M4_lgbm` (LightGBM):** Macro-F1 $= \mathbf{0.9563 \pm 0.0249}$ (Accuracy $0.9995$, FPR $0.030\%$, FNR $0.054\%$).
     2. **`M3_rf` (Random Forest):** Macro-F1 $= 0.9498 \pm 0.0157$ (Accuracy $0.9993$, FPR $0.036\%$, FNR $0.106\%$).
     3. **`M2_tree` (Decision Tree):** Macro-F1 $= 0.9122 \pm 0.0158$ (Accuracy $0.9983$, FPR $0.164\%$, FNR $0.151\%$).
     4. **`M0_dummy` (Dummy):** Macro-F1 $= 0.1505 \pm 0.0000$ (Accuracy $0.6033$, FPR $0.000\%$, FNR $100.0\%$).
  3. **M3 vs. M4 Head-to-Head & Tie-Break Analysis (Pre-Freeze Models):**
     - Absolute Macro-F1 difference: $|\Delta| = 0.0065$ ($0.65$ percentage points).
     - Pooled fold standard deviation: $\sigma_{\text{pooled}} = 0.0203$.
     - Since $|\Delta| < \sigma_{\text{pooled}}$, M3 and M4 are declared a **TIE** under Step 3 of the pre-registered protocol.
     - **Tie-Break Criteria Evaluation on Pre-Freeze Baselines:**
       - **(a) Combined Rare-Class Recall:**
         - `M4_lgbm`: $\text{Recall}_{\text{R2L}} (98.37\%) + \text{Recall}_{\text{U2R}} (81.67\%) = 180.04\%$
         - `M3_rf`: $\text{Recall}_{\text{R2L}} (96.24\%) + \text{Recall}_{\text{U2R}} (78.89\%) = 175.13\%$
         - $\rightarrow$ M4 leads narrowly: in raw count across the pooled dataset, this represents a difference of just 1 U2R instance ($34$ vs. $33$ out of $42$) and 10 R2L instances ($785$ vs. $775$ out of $799$). Characterizing this as "decisive" is an overclaim; the performance gap is very narrow.
       - **(b) Binary FPR:**
         - Pre-freeze CV favored M4 ($0.030\%$ vs. $0.036\%$). However, after freezing features and evaluating pooled out-of-fold predictions in Entry 14, M3 yielded 17 false alarms while M4 yielded 19 false alarms, indicating tie-break (b) does not persistently favor M4 post-freeze.
       - **(c) Compute Efficiency:**
         - Summed fit time: M4 is $\approx 1.4\times$ faster to fit across folds than M3.
  4. **Provisional Deployment Leader:**
     - **`M4_lgbm` (LightGBM)** is designated the **provisional leader** on pre-freeze baselines. Because the margins are narrow (1 U2R row, 10 R2L rows), post-freeze false alarms slightly favor M3 (17 vs. 19), and hyperparameter tuning remains to be completed, the final architecture selection will be rerun on frozen, tuned models in Phase 17 using 5×3 repeated cross-validation before any irrevocable deployment commitment.
- **Artifacts Generated:**
  - Metrics comparison table: `reports/metrics/comparison_cv.csv`
  - Figures:
    - `reports/figures/p13_macro_f1_box.png` (Per-fold Macro-F1 boxplot across 5 folds)
    - `reports/figures/p13_per_class_recall.png` (Per-class recall comparison across all 5 families)
    - `reports/figures/p13_fpr_fnr.png` (Operational FPR vs. FNR with 0.5% threshold)
    - `reports/figures/p13_fit_time.png` (Cross-validation training time comparison)
    - `reports/figures/p13_predict_time.png` (Inference latency per 1k samples)

---

### Entry 13: Controlled Ablations (Class Weights & Engineered Features) and Frozen Model Settings (Phase 14)
- **Date:** October 13, 2026
- **Question Raised:** What is the isolated causal effect of cost-sensitive class weighting (`class_weight='balanced'`) and row-wise feature engineering (`engineered=True`) across all four classifiers, and does the evidence justify freezing these settings for all downstream phases?

#### Finding 36 (CORRECTS Entry 8): What Actually Drives Logistic Regression's False Positive Rate & Cost-Sensitive Ablation Diagnostic (Experiment A)
- **What & Comparative Results:**
  - `M1_logreg`:
    - Weight ON: Macro-F1 $= 0.7702$, FPR $= 0.01810$ ($1.810\%$), R2L recall $= 98.00\%$, U2R recall $= 78.89\%$.
    - Weight OFF: Macro-F1 $= 0.8826$, FPR $= 0.00144$ ($0.144\%$), R2L recall $= 87.48\%$, U2R recall $= 47.78\%$.
    - U2R recall drops by $31.11$ percentage points when weights are removed, while precision rises from $18.36\%$ to $69.62\%$.
  - `M2_tree` (Decision Tree Unweighted):
    - Weight ON $\rightarrow$ OFF: Macro-F1 drops from $0.9122 \rightarrow 0.8797$; FPR drops from $0.164\% \rightarrow 0.067\%$.
    - Rare-class recall: R2L recall changes from $94.99\% \rightarrow 94.11\%$; U2R recall drops from $69.17\% \rightarrow 38.06\%$ ($-31.11$ points).
  - `M3_rf` (Random Forest Unweighted):
    - Weight ON $\rightarrow$ OFF: Macro-F1 drops from $0.9498 \rightarrow 0.9098$; FPR drops from $0.036\% \rightarrow 0.013\%$.
    - Rare-class recall: R2L recall changes from $96.24\% \rightarrow 93.36\%$; U2R recall drops from $78.89\% \rightarrow 45.00\%$ ($-33.89$ points).
  - `M4_lgbm` (LightGBM Unweighted Diagnostic):
    - 5-Fold CV metrics: Macro-F1 collapsed to **$0.3673$**, FPR rose to $7.345\%$, R2L recall collapsed to $15.95\%$, U2R recall collapsed to $0.00\%$.
    - *Diagnostic Audit on Fold 0 Run*:
      - `params_diff(pipe_on, pipe_off)`: Evaluated estimator diffs — only `clf__class_weight` differed (`'balanced'` vs. `None`). Pipeline structure, transformers, and column ordering were completely identical.
      - Fitted tree count: `pipe[-1].booster_.num_trees() == 1020` (all 300 boosting stages fitted without early termination).
      - Warnings during fit/predict: `0`.
      - Fold 0 Per-Class F1 Breakdown:
        - `f1_Normal`: $0.9410$ (recall: $96.02\%$, precision: $92.26\%$)
        - `f1_DoS`: $0.8907$ (recall: $80.78\%$, precision: $99.24\%$)
        - `f1_Probe`: $0.0027$ (recall: $0.59\%$, precision: $0.18\%$)
        - `f1_R2L`: $0.0000$ (recall: $0.00\%$)
        - `f1_U2R`: $0.0000$ (recall: $0.00\%$)
        - Sum of per-class F1: $0.9410 + 0.8907 + 0.0027 + 0 + 0 = 1.8344 \implies \text{Macro-F1} = 1.8344 / 5 = 0.3669$.
      - Fold 0 Confusion Matrix:
        ```
                     pred_Normal  pred_DoS  pred_Probe  pred_R2L  pred_U2R
        true_Normal        13494        19         248       292         0
        true_DoS             662      7054         891       115        10
        true_Probe           303        35           2         0         0
        true_R2L             160         0           0         0         0
        true_U2R               9         0           0         0         0
        ```
      - *Root Cause Analysis*: Without balanced sample weights, LightGBM's default multiclass cross-entropy loss and leaf-wise splitting allowed massive leakage across classes: 662 DoS rows leaked into Normal, 891 DoS rows were misclassified as Probe, and 292 Normal rows were misclassified as R2L (driving false alarms up to 7.35%). Both Normal and DoS F1 scores degraded substantially (down from $0.999+$ to $0.941$ and $0.891$), explaining why the sum of F1 scores collapsed to ~1.84.
- **Why It Matters & Scientific Stance:**
  - Entry 8 originally conjectured that linear boundaries fundamentally cannot separate Normal traffic from attacks without high FPR. The empirical ablation disproves this: unweighted Logistic Regression achieved an FPR of $0.144\%$, comfortably clearing the $\le 0.50\%$ alert-fatigue barrier. The $1.81\%$ FPR was primarily driven by balanced class weighting forcing the decision boundary deep into Normal traffic space.
  - The decision to keep weights ON across all models remains well-founded: unweighted training severely degrades minority attack recall across every single model family (LR U2R recall fell 31.1 points, Tree fell 31.1 points, RF fell 33.9 points).
  - However, we refrain from claiming that class weighting is "strictly indispensable for gradient boosting" in general until this behavior is tested across alternative learning rates, loss formulations, and objective functions during Phase 16 tuning.

#### Finding 37: Engineered-Features Ablation Decision (Experiment B)
- **What:**
  - Pre-registered adoption rule (stamped `2026-10-13 12:15`): Adopt `USE_ENGINEERED = True` only if BOTH hold:
    1. The mean Macro-F1 gain across M1–M4 is positive ($> 0$).
    2. No single model's Macro-F1 drops by more than its own fold standard deviation.
  - Empirical 5-fold cross-validation results:
    - `M1_logreg`: Macro-F1 off $= 0.7702$, on $= 0.7744$ ($\Delta = +0.0042$, fold SD $= 0.0043$; drop $>$ SD: False; paired wins: 4/5)
    - `M2_tree`: Macro-F1 off $= 0.9122$, on $= 0.9182$ ($\Delta = +0.0060$, fold SD $= 0.0158$; drop $>$ SD: False; paired wins: 3/5)
    - `M3_rf`: Macro-F1 off $= 0.9498$, on $= 0.9574$ ($\Delta = +0.0076$, fold SD $= 0.0157$; drop $>$ SD: False; paired wins: 5/5)
    - `M4_lgbm`: Macro-F1 off $= 0.9563$, on $= 0.9602$ ($\Delta = +0.0038$, fold SD $= 0.0249$; drop $>$ SD: False; paired wins: 4/5)
  - Mean Macro-F1 gain across M1–M4: **$+0.0054$**.
  - Any model dropped $>$ fold SD: **False** (all 4 models achieved positive mean gains).
  - Decision: **`USE_ENGINEERED = True` is officially ADOPTED**.
- **Why It Matters & Empirical Assessment:**
  - Every individual model gain ($+0.0038$ to $+0.0076$) is smaller than its corresponding fold standard deviation ($\sigma \approx 0.004$ to $0.025$). Across the models, these gains represent **no measurable benefit beyond fold noise**.
  - Saying that the features "enrich representations" is an overclaim given these marginal increments.
  - The 4 engineered features (`bytes_ratio`, `zero_payload`, `content_activity`, `privilege_flag` — note that `log_src_bytes` is a transformer inside `ColumnTransformer`, not an engineered feature) are adopted strictly because:
    1. The pre-registered formal adoption rule was satisfied;
    2. Computational overhead is nil;
    3. Row-wise computation has mathematically proven zero information leakage.

#### Finding 38: Frozen Global Settings
- **What:**
  - `USE_CLASS_WEIGHT = True` (protects rare-class recall across U2R and R2L).
  - `USE_ENGINEERED = True` (adopted via pre-registered positive empirical gains across all models).
- **Why It Matters:**
  - All four baseline models (M1–M4) were re-evaluated and re-saved under these frozen settings.
  - These exact settings are locked in `src/config.py` for all subsequent phases (tuning, repeated cross-validation, threshold calibration, and test evaluation), guaranteeing absolute consistency and preventing configuration drift.
- **Artifacts Generated:**
  - Class weight ablation metrics: `reports/metrics/ablation_class_weight.csv`
  - Feature engineering ablation metrics: `reports/metrics/ablation_engineered.csv`
  - Updated baseline fold results and out-of-fold predictions: `cv_results_{model}.csv` and `oof_{model}.npz` for M1–M4.

---

### Entry 14: Out-of-Fold Error Analysis, Rare-Class Breakdown, Wilson CIs & False Positive Anatomy (Phase 15)
- **Date:** October 13, 2026
- **Question Raised:** When examining pooled out-of-fold predictions on all 116,466 training samples, which specific rare attack subtypes (`U2R`: `buffer_overflow`, `loadmodule`, `rootkit`, `perl`; `R2L`: `warezclient`, `guess_passwd`, `warezmaster`, `imap`, `ftp_write`, `multihop`, `phf`, `spy`) are caught vs. missed, where do missed attacks go, and what network services drive false alarms on Normal traffic?
- **Methodology & Alignment Verification:**
  - **Positional Alignment Verified:** Proved `(meta_train.map(ATTACK_TO_FAMILY).values == y_train.values).all()`. Out-of-fold predictions strictly align $1:1$ with feature records and attack metadata labels.
  - **Wilson 95% Score Confidence Intervals:** Computed exact Wilson score intervals (`scipy.stats.binomtest`) to properly quantify binomial uncertainty on small attack populations ($n \le 44$).
- **Key Empirical Discoveries & Results:**
  1. **Pooled Out-of-Fold Confusion Matrix (Figure `p15_confusion_pooled.png`):**
     - `Normal` and `DoS` remain virtually perfect ($>99.8\%$ recall across all three tree models). For `Probe`, M3 and M4 achieve $>99.3\%$ recall ($99.35\%$ and $99.47\%$), while Decision Tree M2 achieves $98.59\%$ (tree Probe recall is not uniformly $>99.5\%$).
     - `R2L` ($N=799$ total): LightGBM M4 achieves **$98.25\%$** pooled recall ($785/799$ detected; only 14 misses). Random Forest M3 achieves $96.99\%$ ($775/799$).
     - `U2R` ($N=42$ total): LightGBM M4 achieves **$80.95\%$** pooled recall ($34/42$ detected; 8 misses). Random Forest M3 detects $33/42$ ($78.57\%$). Decision Tree M2 detects $29/42$ ($69.05\%$).
  2. **Per-Attack Subtype Breakdown & Wilson 95% CIs:**
     - **U2R Attacks:**
       - `buffer_overflow` ($n=23$): M4 catches $21/23$ ($91.3\%$, 95% CI: $[73.2\%, 97.6\%]$); M3 catches $22/23$ ($95.7\%$).
       - `loadmodule` ($n=8$): M4 catches $6/8$ ($75.0\%$, 95% CI: $[40.9\%, 92.9\%]$); M3 catches $5/8$ ($62.5\%$).
       - `rootkit` ($n=8$): M4 catches $4/8$ ($50.0\%$, 95% CI: $[21.5\%, 78.5\%]$); M3 catches $3/8$ ($37.5\%$). Rootkits evade detection by mimicking legitimate admin sessions.
       - `perl` ($n=3$): Both M3 and M4 achieve $3/3$ ($100.0\%$, 95% CI: $[43.9\%, 100.0\%]$).
     - **R2L Attacks:**
       - `warezclient` ($n=715$, majority R2L): M4 catches **$714/715$** ($99.86\%$, 95% CI: $[99.2\%, 99.98\%]$); M3 catches $709/715$ ($99.16\%$).
       - `guess_passwd` ($n=44$): Both M3 and M4 catch $43/44$ ($97.73\%$, 95% CI: $[88.2\%, 99.6\%]$).
       - `warezmaster` ($n=13$): Both catch $10/13$ ($76.9\%$, 95% CI: $[49.7\%, 91.8\%]$).
       - Rare R2L ($n \le 9$): `imap` ($7/9$ on M4), `multihop` ($4/6$ on M4), `ftp_write` ($3/7$ on M4), `phf` ($3/3$ on M4), `spy` ($1/2$ on M4).
  3. **Missed Destinations Analysis (Where Misses Go):**
     - For U2R:
       - M4 misses 8 rows: **$6$ went to Normal ($75\%$)**, $1$ to R2L, $1$ to Probe.
       - M3 misses 9 rows: **$8$ went to Normal ($89\%$)**, $1$ to Probe.
       - M2 misses 13 rows: **$8$ went to Normal ($62\%$)**, $4$ to R2L, $1$ to Probe.
     - For R2L:
       - M4 misses 14 rows: **$10$ went to Normal ($71\%$)**, $3$ to U2R, $1$ to DoS.
       - M3 misses 24 rows: **$19$ went to Normal ($79\%$)**, $4$ to U2R, $1$ to DoS.
     - **Core IDS Insight:** Missed intrusions almost universally blend into **Normal traffic** ($71\%\text{--}89\%$ of misses). Attackers do not trigger traffic-flood anomalies; they blend into baseline interactive user behavior.
  4. **Caught vs. Missed U2R Feature Profiles (LightGBM M4, $n=34$ caught vs. $n=8$ missed):**
     - Caught U2R sessions have elevated `hot` indicators (mean $1.65$ vs. $0.62$ in missed, and $0.05$ in Normal), `num_root` (mean $1.00$ vs. $0.00$ in missed), and larger payloads (`dst_bytes` mean $5,981$ vs. $1,278$).
     - Missed U2R sessions exhibit zero `num_root` and small byte transfers, avoiding anomalous payload triggers.
  5. **False Positive Anatomy (Normal Connections Flagged as Attack):**
     - Total false positives out of 70,264 Normal connections:
       - M3 RF: only **17 false alarms** ($0.0242\%$).
       - M4 LightGBM: only **19 false alarms** ($0.0270\%$).
     - **Top Services Contributing to False Positives:**
       - `telnet`: 6/19 ($31.6\%$) in M4; 5/17 ($29.4\%$) in M3.
       - `ftp_data`: 5/19 ($26.3\%$) in M4; 9/17 ($52.9\%$) in M3.
     - **TCP Flag Distribution & Baseline Context:**
       - `SF` (normal established connection) accounts for $\sim 74\%$ of all false positives ($14/19$ in M4; $12/17$ in M3).
       - *Baseline Prevalence Context*: In baseline Normal traffic, $66,384$ out of $70,264$ connections (**$94.48\%$**) have `flag == 'SF'`. Thus, the $74\%$ SF share among false alarms is actually **under-represented** relative to baseline Normal traffic. In contrast, non-SF flags (`REJ`, `RSTO`) make up only $5.52\%$ of Normal traffic but represent $\sim 26\%$ of false alarms, indicating that abnormal session terminations disproportionately trigger false alerts.
     - **Operational Context:** Administrative interactive logins (`telnet`) and bulk file transfers (`ftp_data`) closely resemble unauthorized privilege escalations and FTP abuse (`warezclient`), serving as the primary source of enterprise alert noise.
  6. **Tree Leaf Memorization Verified:**
     - Decision Tree M2 placed the 42 U2R instances into **9 separate leaves**, with 6 leaves holding only 2 to 3 samples total, validating that unconstrained CART isolates extreme minority points into bespoke memorization pockets.
- **Artifacts Generated:**
  - Figure: `reports/figures/p15_confusion_pooled.png`
  - Per-attack metric tables: `reports/metrics/p15_per_attack_{model}_{family}.csv` for all 4 models and both rare families.

---

### Entry 15: Equal-Budget Randomized Hyperparameter Tuning & Inner-CV Dynamics (Phase 16)
- **Date:** October 13, 2026
- **Question Raised:** Under frozen settings (`USE_CLASS_WEIGHT = True`, `USE_ENGINEERED = True`), can targeted randomized hyperparameter search (`RandomizedSearchCV` with 3-fold inner Stratified CV, scoring on Macro-F1 across all 5 families) improve generalization across the four candidate architectures, and what do the resulting parameter configurations reveal about model capacity and regularization?
- **Methodology & Search Spaces:**
  - **Harness:** `RandomizedSearchCV` using 3-fold stratified inner cross-validation (`StratifiedKFold(n_splits=3, shuffle=True, random_state=SEED + 1)`), evaluating Macro-F1 (`labels=FAMILIES, zero_division=0`).
  - **Search Spaces & Budgets:**
    - `M1_logreg`: `clf__C` $\in [0.01, 0.1, 1, 10]$ (budget: 4 candidates, exhaustive).
    - `M2_tree`: `clf__max_depth` $\in [None, 8, 12, 16, 24]$, `clf__min_samples_leaf` $\in [1, 2, 5, 10]$, `clf__criterion` $\in ['gini', 'entropy']$, `clf__ccp_alpha` $\in [0, 1e-5, 1e-4]$ (120 combinations, budget: 30 candidates).
    - `M3_rf`: `clf__max_features` $\in ['sqrt', 0.2, 0.4]$, `clf__min_samples_leaf` $\in [1, 2, 4]$, `clf__max_depth` $\in [None, 25]$ (18 combinations, budget: 18 candidates, exhaustive).
    - `M4_lgbm`: `clf__n_estimators` $\in [200, 400, 800]$, `clf__learning_rate` $\in [0.03, 0.05, 0.1]$, `clf__num_leaves` $\in [15, 31, 63]$, `clf__min_child_samples` $\in [5, 10, 20]$, `clf__colsample_bytree` $\in [0.6, 0.8, 1.0]$, `clf__reg_lambda` $\in [0, 1, 5]$ (729 combinations, budget: 20 candidates).
- **Key Empirical Discoveries & Results:**
  1. **Tuned vs. Default Inner 3-Fold Macro-F1 Comparison:**
     - `M1_logreg`: Default $= 0.7815 \pm 0.0282 \rightarrow$ Tuned $= \mathbf{0.8249} \pm 0.0230$ ($\Delta = \mathbf{+0.0434}$, $+4.34$ percentage points gain!).
       - Best configuration: `{'clf__C': 10}`.
       - Relaxing L2 shrinkage from default $C=1.0$ to $C=10$ allows the linear decision boundary to fit sharper separating hyperplanes for sparse rare-class indicators without incurring numerical instability.
     - `M2_tree`: Default $= 0.9240 \pm 0.0128 \rightarrow$ Tuned $= \mathbf{0.9407} \pm 0.0045$ ($\Delta = \mathbf{+0.0166}$, $+1.66$ percentage points gain).
       - Best configuration: `{'clf__min_samples_leaf': 1, 'clf__max_depth': 24, 'clf__criterion': 'entropy', 'clf__ccp_alpha': 0}`.
       - Information gain (`entropy`) combined with deep leaves ($depth=24$) isolates localized minority attack signatures (`U2R`, `R2L`) more cleanly than Gini impurity.
     - `M3_rf`: Default $= 0.9569 \pm 0.0070 \rightarrow$ Tuned $= \mathbf{0.9654} \pm 0.0061$ ($\Delta = \mathbf{+0.0085}$, $+0.85$ percentage points gain).
       - Best configuration: `{'clf__min_samples_leaf': 4, 'clf__max_features': 0.4, 'clf__max_depth': None}`.
       - Substantially widening the feature subspace from $\sqrt{p} \approx 11$ up to $0.4 \times 119 \approx 48$ features allows individual trees to inspect multiple correlated discriminators simultaneously, while `min_samples_leaf=4` prevents leaf-level noise memorization.
     - `M4_lgbm`: Default $= 0.9679 \pm 0.0104 \rightarrow$ Tuned $= \mathbf{0.9670} \pm 0.0110$ ($\Delta = -0.0009$).
       - Best configuration: `{'clf__reg_lambda': 0, 'clf__num_leaves': 63, 'clf__n_estimators': 800, 'clf__min_child_samples': 20, 'clf__learning_rate': 0.03, 'clf__colsample_bytree': 0.6}`.
       - The minute $-0.0009$ delta is well within fold standard deviation ($\sigma = 0.0104$) and reflects that default $n\_estimators=300$ was not evaluated in the grid. LightGBM's default settings were already operating near the empirical ceiling.
  2. **Model Selection Horizon for Phase 17:**
     - The gap between tuned Random Forest M3 ($0.9654$) and tuned LightGBM M4 ($0.9670$) is merely $0.0016$, well below fold variability ($\sigma \approx 0.011$).
     - The best configurations were exported to `models/best_params.json` and are strictly locked for the repeated outer cross-validation and definitive model selection protocol in Phase 17.
- **Artifacts Generated:**
  - Tuning results tables:
    - `reports/metrics/tuning_M1_logreg.csv` (4 candidates)
    - `reports/metrics/tuning_M2_tree.csv` (30 candidates)
    - `reports/metrics/tuning_M3_rf.csv` (18 candidates)
    - `reports/metrics/tuning_M4_lgbm.csv` (20 candidates)
  - Tuned vs. default summary: `reports/metrics/tuned_vs_default_inner.csv`
  - Exported parameters: `models/best_params.json`

---

### Entry 16: Repeated 5×3 Cross-Validation, Tuning Sign Test & Definitive Model Selection (Phase 17)
- **Date:** October 13, 2026
- **Question Raised:** Using 5×3 Repeated Stratified Cross-Validation (15 folds) on training data only, does hyperparameter tuning justify model replacement under the pre-registered 12-of-15 sign test, which model architecture survives the 0.5% FPR operational gate, and which candidate emerges as the champion under our pre-registered model selection protocol?

#### Finding 44: The Selection Decision
- **What:**
  - Evaluated on 5×3 repeated CV (15 folds on $N=116,466$):
    - `M0_dummy`: Macro-F1 $= 0.1505 \pm 0.0000$, FPR $= 0.0000$ (Passes FPR gate; 100% attack misses).
    - `M1_logreg` (tuned): Macro-F1 $= 0.8071 \pm 0.0155$, FPR $= 0.0141$ ($1.411\%$) $\rightarrow$ **DISCARDED by FPR gate** ($> 0.0050$, exceeding operational alert fatigue threshold by $2.8\times$).
    - `M2_tree` (default): Macro-F1 $= 0.9183 \pm 0.0183$, FPR $= 0.0012$ ($0.121\%$) (Passes FPR gate).
    - `M3_rf` (default): Macro-F1 $= 0.9535 \pm 0.0136$, FPR $= 0.000256$ ($0.0256\%$) (Passes FPR gate).
    - `M4_lgbm` (default): Macro-F1 $= \mathbf{0.9606 \pm 0.0155}$, FPR $= 0.000256$ ($0.0256\%$) (Passes FPR gate).
  - Top vs. Runner-Up: `M4_lgbm` ($0.9606$) vs. `M3_rf` ($0.9535$).
    - Macro-F1 gap: $\Delta = 0.0071$ ($0.71$ percentage points).
    - Pooled fold standard deviation: $\sigma_{\text{pooled}} = 0.0145$.
    - Since $|\Delta| < \sigma_{\text{pooled}}$, M3 and M4 are declared a **statistical tie** under Step 3 of the pre-registered selection rule.
  - **Tie-Break Evaluation:**
    - Criterion (a) Combined Rare-Class Recall ($\text{Recall}_{\text{R2L}} + \text{Recall}_{\text{U2R}}$):
      - `M4_lgbm`: $0.9821 + 0.8176 = \mathbf{1.7997}$ ($179.97\%$).
      - `M3_rf`: $0.9695 + 0.7787 = 1.7482$ ($174.82\%$).
      - **Winner:** **`M4_lgbm` (LightGBM)** wins on tie-break (a) by $+5.15$ percentage points!
    - Decided by: `tie-break (a) R2L+U2R recall`.
    - Runner-up: `M3_rf`.
    - Discarded by FPR gate: `['M1_logreg']`.
- **Why It Matters:** 15 folds across 3 repeats provide far steadier variance estimates than a single 5-fold split. The decision adhered strictly to the pre-registered protocol locked before seeing results.

#### Finding 45: Tie-Break Fragility & Empirical Honesty
- **What:**
  - The tie-break margin rests on a very small number of physical instances:
    - On U2R ($N=42$ per repeat): M4 detected $81.76\%$ ($\sim 34.3$ rows) vs. M3's $77.87\%$ ($\sim 32.7$ rows) $\rightarrow$ a margin of only **$\approx 1.6$ U2R connections** per repeat (out of 116,466 total traffic).
    - On R2L ($N=799$ per repeat): M4 detected $98.21\%$ ($\sim 784.7$ rows) vs. M3's $96.95\%$ ($\sim 774.6$ rows) $\rightarrow$ a margin of **$\approx 10.1$ R2L connections** per repeat.
    - On False Positive Rate: Both models produced an identical FPR of $0.0256\%$ (~18 false alarms out of 70,264 Normal connections per repeat), differing by less than $0.001$ false alarms per fold.
- **Why It Matters:** While `M4_lgbm` legitimately wins under our formal rules, intellectual honesty requires documenting that the separation between Random Forest and LightGBM is not an insurmountable chasm, but a narrow margin of $\sim 12$ rare intrusion packets in a dataset of over 116,000 instances.

#### Finding 46: Tuning Payoff & Parsimony (Sign Test Results)
- **What:**
  - Tuned replaced default for **only 1 model (`M1_logreg`)**: won 15/15 folds ($p = 0.0000$), lifting 15-fold Macro-F1 from $0.7740 \rightarrow 0.8071$ ($+3.31$ points).
  - Kept default for all tree architectures:
    - `M2_tree`: tuned won 9/15 folds ($p = 0.304$) $\rightarrow$ kept default.
    - `M3_rf`: tuned won 11/15 folds ($p = 0.059$) $\rightarrow$ missed the 12/15 threshold by 1 fold, kept default.
    - `M4_lgbm`: tuned won 9/15 folds ($p = 0.304$) $\rightarrow$ kept default.
  - Final selected model configurations: `M0_dummy`: default, `M1_logreg`: tuned, `M2_tree`: default, `M3_rf`: default, `M4_lgbm`: default.
- **Why It Matters:** Confirms the finding from Phase 16 that tree ensemble default settings were already operating close to Bayes optimal on this dataset. Enforcing the strict 12/15 sign-test threshold prevented adopting over-complex tuned configurations whose apparent gains were within fold noise.
- **Artifacts Generated:**
  - `reports/metrics/phase17_selection_summary.csv` (15-fold metrics summary)
  - `models/selection_decision.json` (formal pre-registered decision record)


