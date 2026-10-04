# Discovery Log — Network Guardian IDS Project

This log records our actual development journey, empirical observations, failures, wrong turns, and key decisions throughout the project.

---

## Log Entries Template

### Entry 1: Data Understanding & The Duplicate Row Discovery
- **Date:** 
- **Question Raised:** What does the raw KDD Cup 1999 10% dataset actually contain, and can we split it randomly as-is?
- **Observation / Finding:** 
  - 70.5% of rows (348,435 out of 494,021) are exact duplicates.
  - A random split on raw data causes 73.5% of test instances to appear verbatim in the training set, leading a default decision tree to artificially report 99.96% accuracy (memorization, not detection).
- **Action Taken:** Deduplicate before train/test splitting.
- **Impact on Results:** Dataset reduces to 145,586 unique instances; class distribution dramatically changes (e.g., `smurf` drops from 280,790 to 641 rows).

### Entry 2: Class Imbalance & Rarity of U2R
- **Date:** 
- **Question Raised:** How severe is class imbalance across the 5 families after deduplication?
- **Observation / Finding:** 
  - Normal: 87,832 rows
  - DoS: 54,572 rows
  - Probe: 2,131 rows
  - R2L: 999 rows
  - U2R: 52 rows (extreme rarity; test set holds only ~10 rows).
- **Action Taken:** Use stratified splitting, cross-validation for rare-class estimates, Wilson confidence intervals, and macro-F1 as primary metric.

### Entry 3: Feature Inspection & Constant Columns
- **Date:** 
- **Question Raised:** Are all 41 columns informative?
- **Observation / Finding:** `num_outbound_cmds` and `is_host_login` have zero variance (all values are 0).
- **Action Taken:** Drop both constant columns. Note near-constant columns (`land`, `urgent`, `su_attempted`) and retain them as attack signals.

### Entry 4: Baseline Models & Linear Model Behavior
- **Date:** 
- **Question Raised:** How does Logistic Regression perform compared to tree-based approaches?
- **Observation / Finding:** Logistic Regression achieves reasonable recall with class weighting, but suffers from a ~1.9% false-positive rate (~330 false alarms on 17,567 normal test connections), violating operational constraints.
- **Action Taken:** Establish Logistic Regression as linear baseline; evaluate tree-based ensembles for lower FPR.

### Entry 5: Model Selection & Pre-Registered Selection Rule
- **Date:** 
- **Question Raised:** Which candidate should be recommended for production?
- **Selection Rule:**
  1. Discard models with binary FPR > 0.5%.
  2. Rank by mean macro-F1 over repeated CV (5×3 = 15 folds).
  3. Require winning model to win at least 12/15 paired folds (sign test p ≈ 0.02).
  4. Tie-breaking: rare-class recall (R2L+U2R) -> lower FPR -> faster inference -> simpler model.
