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

