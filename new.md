I looked at your project folder before designing anything. Your data file is the **KDD Cup 1999 "10%" subset**: 494,021 rows, 41 features and 23 labels. I also read your spec, the rubric and the documentation template. Then I ran a quick pilot on your actual file so the recommendations rest on evidence, not on each model's reputation.

The pilot numbers below are a preview, not your results. Your team has to reproduce them and report its own. The spec also requires you to disclose AI assistance, and that includes this design.

**Tags used below:** **[BP]** established best practice · **[DS]** something I checked in your file · **[ER]** my engineering recommendation · **[OPT]** optional experiment.

---

## Part A — What your data actually looks like

| Finding | Evidence from your file | What it means |
|---|---|---|
| **70.5% of rows are exact duplicates** [DS] | 348,435 of 494,021 rows; only 145,586 are unique | Remove duplicates **before** splitting. If you split the raw file at random, **73.5% of test rows also appear word-for-word in train**, and a plain decision tree scores **99.96% accuracy**. That score comes from memorising rows, not from detecting attacks. This is your strongest discovery-log entry and your answer to the guide question "if a model looks perfect, should you be suspicious?" |
| Removing duplicates changes the class balance [DS] | smurf drops from 280,790 to 641; neptune from 107,201 to 51,820. Afterwards: **Normal 87,832 · DoS 54,572 · Probe 2,131 · R2L 999 · U2R 52** | On the raw file, "always predict DoS" already gets 79% accuracy. Accuracy can't be your judge |
| U2R is extremely rare [DS] | 52 rows in total (buffer_overflow 30, rootkit 10, loadmodule 9, perl 3) | A 20% test set holds only about 10 U2R rows, so each one moves recall by 10 points. Rare-class numbers from a single split are noise; you need cross-validation (CV) |
| Constant columns [DS] | `num_outbound_cmds` and `is_host_login` are always 0 | Drop both. They carry no information |
| Near-constant columns [DS] | `land` has 20 ones, `urgent` 4 non-zero values, `su_attempted` 12 non-zero values and is coded 0/1/2 even though it's described as binary | Keep them (rare, but tied to attacks). Note the 0/1/2 coding in your data-quality notes |
| Strongly redundant pairs [DS] | 13 pairs with \|r\| > 0.95: the serror_rate group (about 0.996), the rerror_rate group, and num_compromised with num_root (0.994) | Harmless for tree models. They only muddy Logistic Regression's coefficients. Show the correlation heatmap, but don't drop them (see Part E) |
| Extreme skew [DS] | `src_bytes` median 147, maximum 693,375,640 | Apply log1p for the linear model only. **Don't remove outliers**, because large byte counts are often the attack itself |
| Categorical columns [DS] | protocol_type has 3 values, service 66, flag 11 | One-hot encoding gives about 116 input columns, which is easy to handle |
| Missing values and label conflicts [DS] | 0 NaN; 1 feature vector appears with two different labels | Drop the conflicting rows |
| R2L and U2R are TCP content attacks [DS] | All 999 R2L rows and 49 of 52 U2R rows are TCP | Content features (`hot`, `num_failed_logins`, `root_shell`, …) separate R2L/U2R. Traffic-window features (`count`, `serror_rate`, …) separate DoS/Probe |

## Part B — Pilot results (deduplicated data, default settings, same split for every model)

| Model | Test macro-F1 | 5-fold CV macro-F1 (mean ± SD) | CV R2L recall | CV U2R recall | Binary false-positive rate | Fit time |
|---|---|---|---|---|---|---|
| Logistic Regression (balanced) | 0.771 | — | — | — | **1.88%** | 45 s |
| Decision Tree | 0.916 | 0.912 ± 0.014 | 0.94 | 0.71 | 0.13% | 1 s |
| Random Forest | 0.960 | 0.935 ± 0.014 | 0.95 | 0.62 | **0.01%** | 8 s |
| **LightGBM** | 0.968 | **0.953 ± 0.022** | **0.98** | **0.81** | 0.04% | 8 s |
| XGBoost | 0.975 | 0.945 ± 0.019 | 0.98 | 0.72 | 0.02% | 18 s |
| sklearn HistGradientBoosting | — | 0.954 ± 0.022 | 0.98 | 0.79 | 0.03% | — |
| Isolation Forest (trained on Normal only) | binary only | — | 0.23 | 0.50 | **10.4%** | — |

What the pilot shows:

- **Every tree model is near-perfect on Normal, DoS and Probe.** All the differences between models are in R2L and U2R. So macro-F1 and rare-class recall have to decide the comparison, not accuracy.
- **Logistic Regression catches attacks but raises too many false alarms.** A 1.9% false-positive rate meant about 330 false alarms on 17,567 normal test connections. That makes it a useful baseline lesson, not a usable IDS.
- **Boosting beats Random Forest, which beats a single Decision Tree, on the rare classes.** LightGBM, XGBoost and HistGradientBoosting are statistically indistinguishable from each other.
- **Isolation Forest fails the brief.** It flags 1 in 10 normal connections and misses 77% of R2L. It also can't name an attack family at all.

---

## Part C — Answers to your eight questions

**1. Which models to implement.** Four core models from three different families:

- Logistic Regression (linear)
- Decision Tree (single tree)
- Random Forest (bagging ensemble)
- LightGBM (boosting ensemble)

Add a Dummy classifier as a sanity floor and Isolation Forest as an optional side experiment. Details are in Final §1.

**2. Isolation Forest: leave it out of the main comparison, but run it as an optional side experiment.** It's unsupervised and only answers "normal or not". The task requires predicting the attack family, so it can't count as one of your three classification approaches. It's still worth running once to answer a fair question: could we detect attacks without labels, for example novel ones? The pilot says poorly (10% false-positive rate, 23% R2L recall). That's an honest negative result for your discovery log and limitations section.

**3. XGBoost or LightGBM: gradient boosting fits this project, but pick one of the two.** Both are the same family of algorithm. Including both adds a fourth tuning job without adding a different approach, and the pilot can't separate them. **Choose LightGBM** because:

- It's faster on Colab's 2-core CPU.
- It accepts `class_weight='balanced'` and string labels directly. XGBoost needs label-encoded targets and manual `sample_weight` for multiclass weighting.
- It's preinstalled in Colab.

Fallback: if your instructor wants scikit-learn only, `HistGradientBoostingClassifier` is the same idea and scored the same in the pilot (0.954).

**4. Random Forest as the baseline: no.** RF is a strong contender, not a baseline. If you call it the baseline, the bar is so high that nothing looks like an improvement, and you lose the story of "simple model, then better model". Your baselines are Dummy, Logistic Regression and the Decision Tree.

**5. Simpler models: yes, both Logistic Regression and the Decision Tree.**

- **Logistic Regression** shows that encoding and scaling matter, and that a linear boundary costs you false alarms.
- **Decision Tree** produces readable rules for the video and is the clearest way to demonstrate overfitting (validation curve over `max_depth`).
- Naive Bayes, KNN and SVM are rejected; reasons are in Part D.

**6. Problem formulation: one multiclass model.** Derive the binary Normal-vs-Attack view from its probabilities: P(attack) = 1 − P(Normal).

- The required output is the family, so multiclass is mandatory.
- The pilot's multiclass models already reach a 0.01–0.04% binary false-positive rate and about 0.05% false-negative rate.
- A two-stage pipeline (binary detector, then family classifier) compounds errors: an attack missed in stage 1 never reaches stage 2. It also doubles the tuning and explanation work, for no measured benefit. **[ER]**

**7. Training both binary and multiclass models: report both views, but train one model.** Every metric for the binary view comes from the multiclass model's predictions. [OPT] If you want to prove the point, train one binary LightGBM and show that the derived binary metrics are just as good.

**8. Final production/prototype candidate: chosen by a selection rule you write down before you run the final comparison** (Part F). The pilot predicts **LightGBM**, with **Random Forest** as runner-up. If tuned LightGBM doesn't consistently beat RF on the paired CV folds, recommend RF: it's simpler and has the lowest false-positive rate. Either outcome is defensible as long as the evidence decides it.

---

## Part D — Full model assessment

| Model | Categorical features | Class imbalance | Train / predict cost | Interpretability | Overfitting risk | Fit for IDS | Verdict |
|---|---|---|---|---|---|---|---|
| Dummy (most frequent) | n/a | n/a | trivial | total | none | none | **Keep as sanity floor** (macro-F1 about 0.15) |
| Logistic Regression | needs one-hot | `class_weight` | moderate / fast | high (coefficients) | low | too many false alarms (pilot) | **Keep: linear baseline** |
| Decision Tree | one-hot fine | `class_weight` | very fast / fast | high (rules, tree plot) | **high** | weak on rare classes | **Keep: interpretable baseline + overfitting demo** |
| Random Forest | one-hot fine | `balanced_subsample` | moderate / moderate | medium (permutation importance) | low–medium | lowest false-positive rate in pilot | **Keep: bagging contender** |
| LightGBM | one-hot fine | `class_weight` | fast / fast | medium | medium (controlled by tuning) | best rare-class recall in pilot | **Keep: boosting contender** |
| XGBoost | one-hot | needs sample weights | slower | medium | medium | ties LightGBM | **Reject:** same family, no new evidence |
| Isolation Forest | needs encoding + scaling | not applicable (unsupervised) | fast | low | — | binary only, 10% false positives | **Optional side experiment only** |
| SVM (RBF kernel) | one-hot + scaling | `class_weight` | training scales roughly with n² (116k rows is slow) | low | medium | no clear gain | **Reject:** cost |
| KNN | scaling-sensitive with one-hot | poor | must compare each prediction against all training rows | low | medium | too slow at prediction time | **Reject** |
| Naive Bayes | — | priors only | trivial | medium | — | its independence assumption breaks on features correlated at r > 0.99 | **Reject** |
| MLP / neural network | one-hot + scaling | sklearn's MLP has no `class_weight` | slow, sensitive to tuning | low | medium–high | no expected gain on tabular data | **Optional at most; deep learning not recommended** |

**Why not deep learning [BP]:** on medium-sized tabular data, gradient-boosted trees still match or beat neural networks (Grinsztajn et al., 2022). Your pilot boosting model already sits at the limit set by U2R noise. A neural network would add tuning work and reduce explainability with no technical justification.

**Why not SMOTE [ER]:**

- SMOTE interpolates between rows. On one-hot columns that creates fractional categories that can't exist (you'd need SMOTENC instead).
- It would invent synthetic U2R rows from only about 42 training rows that span 4 different attack types.
- Class weights get the same rebalancing effect with no synthetic data and no leakage risk.
- So you don't need imbalanced-learn. You can show the effect of weights with one ablation (E3 in Part G).

---

## Part E — Data preparation decisions

| Step | Decision | Justification |
|---|---|---|
| Load | `header=None`, column names from `kddcup.names.txt`, strip the trailing `.` from labels | [DS] The file has no header and labels look like `normal.` |
| Label mapping | attack name → family; keep the attack name in a **separate metadata frame, never in X** | Keeping the attack name as a feature would leak the answer. Holding it as metadata lets you say *which* attacks get missed, e.g. "rootkit misread as Normal" |
| Validation | assert 41 features, expected dtypes, no NaN/inf, every label mapped | [BP] Fail loudly. There's no missing data now, but the check protects the prediction pipeline later |
| Duplicates | `drop_duplicates()` on features + label **before** splitting; drop the one conflicting-label vector | [BP] (Tavallaee et al., 2009) plus [DS] the 73.5% overlap shown above |
| Constant columns | drop `num_outbound_cmds` and `is_host_login` | Zero variance in your file |
| Binary symbolic columns (`land`, `logged_in`, `is_guest_login`) | keep as numeric 0/1 | They're already binary; one-hot adds nothing |
| Categorical columns | `OneHotEncoder(handle_unknown='ignore')` for all models | [BP] Low cardinality (66 values at most). Ordinal codes would impose a false order on the linear model. Target encoding adds leakage risk for no gain. `ignore` handles a new service value at prediction time |
| Scaling | Logistic Regression: `log1p` then `StandardScaler`. Trees: none | Trees split on thresholds and ignore scale. LR's solver needs comparable feature magnitudes, and log1p tames the 693M-byte values |
| Outliers | keep | They are attack signal (e.g. `back`, `warezmaster` byte volumes) |
| Correlated features | keep all; show the heatmap; explain importance with **permutation importance**, not the trees' built-in impurity importance | Prediction doesn't suffer. Impurity importance is biased toward continuous columns and splits credit between correlated twins |
| Feature selection | none, apart from the constant columns | 116 columns is small, and tree models select features internally. [OPT] A top-k permutation-importance ablation |
| Class imbalance | class weights on every model; tune "balanced" vs none | Explained in Part D |
| Split | stratified 80/20, `random_state=42`, giving about 116,468 train and 29,117 test rows | [BP] Stratifying keeps about 10 U2R and 200 R2L rows in test. There are no timestamps, so a time-based split isn't possible; list that as a limitation |
| Model selection | 5-fold `StratifiedKFold` on **train only**; the test set is touched exactly once | [BP] |
| Preventing leakage | all preprocessing inside one sklearn `Pipeline` passed to CV and the search | [BP] Scalers and encoders are re-fit inside every fold |

**Remaining leakage and realism risks** (put these in the limitations section):

- **Near-duplicates survive.** Many neptune rows differ only in their counter values, so even deduplicated test scores are somewhat optimistic.
- **Traffic-window features are legitimate but simulation-bound.** `count`, `srv_count`, `serror_rate` and the other rates summarise the previous 2 seconds or 100 connections. They'd be available at prediction time, but they are what make DoS and Probe trivially separable in this 1998 simulated network.
- **The dataset itself is dated and artificial** (McHugh, 2000).
- **The test set has no unseen attack types.** The official KDD "corrected" test file does, so real-world performance would be lower.

## Part F — Feature engineering

Keep it small. The pilot shows tree models are already at their ceiling, so engineered features mainly help Logistic Regression and perhaps R2L/U2R. **Keep a feature only if it improves CV macro-F1 in the ablation (E4); otherwise drop it and log that in the discovery log.** Every feature below is computed from one row only, uses no target and no cross-row statistics, so **none can leak**. Implement them as a transformer inside the Pipeline so prediction applies them automatically.

| Feature | Formula | What it captures | Most likely helps |
|---|---|---|---|
| `log_src_bytes`, `log_dst_bytes`, `log_duration` | `np.log1p(x)` | Turns the extreme byte/time skew into a usable scale (a transform, not new information) | Logistic Regression |
| `bytes_ratio` | `log1p(src_bytes) − log1p(dst_bytes)` | Direction of data flow: uploads (warezmaster) and large requests (back) look different from normal downloads | LR, R2L |
| `zero_payload` | `(src_bytes == 0) & (dst_bytes == 0)` | Connections with no data, typical of SYN floods (neptune) and scans (portsweep, satan) | LR, DoS/Probe |
| `content_activity` | `hot + num_failed_logins + num_compromised + num_root + num_file_creations + num_shells + num_access_files` | Total host-level suspicious activity in the session | LR/DT, R2L/U2R |
| `privilege_flag` | `(root_shell > 0) \| (su_attempted > 0) \| (num_root > 0)` | Any sign of privilege escalation | DT/LR, U2R |

Rejected: aggregate error rates (the serror/rerror columns are already about 0.99 correlated), polynomial or interaction terms (trees learn interactions themselves), and anything computed across rows (leakage risk).

## Part G — Evaluation framework

**Primary metric: macro-F1.** It weights all five families equally, so U2R counts as much as Normal, and it penalises both missed attacks and false alarms. **[BP]**

**Two hard constraints from the binary view.** Normal is "negative"; any attack family is "positive".

- Binary false-positive rate (Normal flagged as an attack) **≤ 0.5%**. Translate it in the report: at thousands of connections per minute, 0.5% still means dozens of false alarms per minute. That's the base-rate problem (Axelsson, 2000).
- Report the binary false-negative rate (attack predicted as Normal) prominently.

**Secondary metrics:**

- Per-class precision, recall and F1, plus the classification report
- Balanced accuracy (which equals macro recall)
- Normalised confusion matrix
- One-vs-rest PR-AUC per class. For imbalanced data this is more honest than ROC-AUC (Saito & Rehmsmeier, 2015)
- Macro ROC-AUC, reported with the caveat that huge true-negative counts inflate it
- Weighted F1 and accuracy, reported only to show how misleading they are here
- Training time, and prediction time per 1,000 rows (median of 3 runs, same `n_jobs` for every model)

**Error analysis, ranked by real cost:**

| Error type | Example | Cost |
|---|---|---|
| Attack predicted as Normal (false negative) | U2R or R2L missed | **Worst.** An attacker gets in or escalates privileges |
| Normal predicted as an attack (false positive) | alert fatigue | High in volume: analysts start ignoring alerts |
| Attack assigned to the wrong family | Probe labelled DoS | Moderate. An alert still fires, but the response is wrong |

Break errors down by original attack name using the metadata frame.

**Handling the rare classes:**

- Base U2R/R2L conclusions on **out-of-fold predictions from CV on train** (`cross_val_predict`), which gives a pooled confusion matrix over all ~42 training U2R rows.
- Report test-set rare-class recall as "k out of n" with a Wilson 95% confidence interval. For example, 9/10 U2R recall has a CI of about 0.60–0.98. Saying this out loud is exactly the critical interpretation the rubric rewards.

**Selection rule — write it into notebook 03 *before* running the final comparison:**

1. Discard any model whose CV binary false-positive rate exceeds 0.5%.
2. Rank the rest by mean macro-F1 over repeated CV (5 folds × 3 repeats = 15 folds, the same folds for every model).
3. Model A is *consistently better* than B only if it wins at least 12 of the 15 paired folds (sign test p ≈ 0.02; a heuristic, because folds aren't fully independent).
4. If no model is consistently better, prefer in this order: higher combined R2L+U2R recall, lower false-positive rate, faster prediction, simpler model.

**Overfitting analysis:**

- Compare train, CV and test macro-F1 for every model. Tree ensembles reaching train F1 = 1.0 is expected; what matters is the gap and how stable the CV scores are.
- Plot the Decision Tree validation curve over `max_depth`.
- Plot the LightGBM validation curve over `n_estimators`.
- Plot a learning curve for the final model. If CV is still rising at full data, rare classes are limited by data, not by the model.
- Report Random Forest's out-of-bag (OOB) score.

## Part H — Hyperparameter tuning

Use `RandomizedSearchCV` on the full Pipeline, scoring `f1_macro`, with 3-fold stratified CV on train and `random_state=42`. Give Random Forest and LightGBM **the same budget (20 candidates each)** so neither gets an unfair advantage.

| Model | Starting point | Search space | Parameters that matter most, and why |
|---|---|---|---|
| Logistic Regression | `C=1`, lbfgs, `max_iter=3000`, balanced | `C` ∈ {0.01, 0.1, 1, 10}; `class_weight` ∈ {balanced, None} (8 configurations) | `C` sets regularisation strength; the class weights drive the false-alarm trade-off |
| Decision Tree | balanced, `min_samples_leaf=2` | `max_depth` ∈ {None, 8, 12, 16, 24}; `min_samples_leaf` ∈ {1, 2, 5, 10}; `criterion` ∈ {gini, entropy}; `ccp_alpha` ∈ {0, 1e-5, 1e-4}; `class_weight` ∈ {balanced, None} (30 sampled) | Depth and leaf size control overfitting; too large a leaf size erases U2R |
| Random Forest | 300 trees, `balanced_subsample`, `oob_score=True` | `max_features` ∈ {sqrt, 0.2, 0.4}; `min_samples_leaf` ∈ {1, 2, 4}; `max_depth` ∈ {None, 25}; `class_weight` ∈ {balanced_subsample, None} (20 sampled) | `max_features` controls how different the trees are; don't tune the tree count (more trees only cost time) |
| LightGBM | 300 trees, `learning_rate=0.05`, `num_leaves=31`, balanced, `deterministic=True`, `force_row_wise=True` | `n_estimators` ∈ {200, 400, 800}; `learning_rate` ∈ {0.03, 0.05, 0.1}; `num_leaves` ∈ {15, 31, 63}; `min_child_samples` ∈ {5, 10, 20}; `subsample` = 0.8 with `subsample_freq=1`; `colsample_bytree` ∈ {0.6, 0.8, 1.0}; `reg_lambda` ∈ {0, 1, 5}; `class_weight` ∈ {balanced, None} (20 sampled) | `min_child_samples` is critical, because the default of 20 can stop U2R from getting its own leaves. Learning rate × number of trees sets model capacity. Full "balanced" weighting gives U2R a weight of about 550, which may raise false positives, hence tuning it |

Add a `QUICK_MODE` flag in your config (`n_iter=4`) for development runs, then switch it off for the final run. Expect roughly 20–30 minutes for notebook 03 on Colab.

---

# FINAL RECOMMENDED PROJECT DESIGN

## 1. Final models

| # | Model | Role |
|---|---|---|
| M0 | `DummyClassifier(strategy="most_frequent")` | Sanity floor. Proves accuracy is misleading. Not counted as an approach |
| **M1** | **Logistic Regression** (multinomial, balanced) | Linear baseline; shows why preparation matters and what false alarms cost |
| **M2** | **Decision Tree** | Interpretable baseline; readable rules; demonstrates overfitting |
| **M3** | **Random Forest** | Bagging ensemble; robust, low-false-alarm contender and fallback recommendation |
| **M4** | **LightGBM** | Boosting ensemble; **expected final candidate**, confirmed or rejected by the selection rule |
| X1 [OPT] | Isolation Forest, trained on Normal only | Side experiment: could anomaly detection work without labels? Not a contender |

## 2. Final architecture

```
════════════════════ OFFLINE: notebooks 01–04 ════════════════════
kddcup.csv ─► Load + schema validation (41 features, dtypes, no NaN/inf, labels mapped)
           ─► Map label → family   (attack name moved to metadata, never a feature)
           ─► Clean: drop duplicates · drop conflicting-label rows · drop 2 constant columns
           ─► Stratified 80/20 split (seed 42) ──────────────► TEST SET (locked)
                         │
                   TRAIN (≈116k rows)
                         │
     ┌─ sklearn Pipeline (re-fit inside every CV fold) ──────────────┐
     │ FeatureEngineer (row-wise, no leakage)                         │
     │ ColumnTransformer                                              │
     │   ├─ protocol_type / service / flag → OneHot(ignore unknown)   │
     │   └─ numeric → LR: log1p + StandardScaler | trees: as-is       │
     │ Classifier (class-weighted): M1 | M2 | M3 | M4                 │
     └────────────────────────────────────────────────────────────────┘
                         │
   Default CV ─► Ablations ─► RandomizedSearchCV ─► Repeated CV 5×3 (same folds)
                         │
   Selection rule (CV evidence only) ─► Re-fit winner on all of TRAIN
                         │
   Single TEST evaluation (all 4 models reported) ─► Error + overfitting analysis
                         │
   Out-of-fold probabilities ─► choose IDS thresholds
                         │
   Save: final_pipeline.joblib + model_card.json
═══════════════════ ONLINE: src/predict.py ═══════════════════════
Connection record (41 raw fields)
 ─► schema check ─► final_pipeline.predict_proba
 ─► category = most likely family · confidence = its probability · p_attack = 1 − P(Normal)
 ─► decision policy:  p_attack ≥ t_alert           → ALERT (family = most likely attack family)
                      t_review ≤ p_attack < t_alert → REVIEW
                      otherwise                     → ALLOW
 ─► JSON output
```

Example output:

```json
{"predicted_category": "R2L", "confidence": 0.94, "p_attack": 0.97,
 "probabilities": {"Normal": 0.03, "DoS": 0.00, "Probe": 0.01, "R2L": 0.94, "U2R": 0.02},
 "ids_decision": "ALERT", "priority": "HIGH"}
```

- **Thresholds:** start with `t_alert = 0.5`. Choose `t_review` from the out-of-fold threshold curve so the REVIEW queue holds at most about 1% of Normal traffic. Never tune thresholds on the test set.
- **Priority** is a fixed policy table, not machine learning: U2R and R2L = HIGH, DoS = MEDIUM, Probe = LOW.
- **"Confidence" is a score, not a calibrated probability.** Class weighting distorts probabilities, so say this in your limitations. [OPT] Show a reliability diagram.

## 3. Final data pipeline (exact order)

1. Load the CSV with column names → strip `.` from labels.
2. Validate: shape, dtypes, NaN/inf, unmapped labels (assertions).
3. Map labels to the 5 families → move the attack name to `meta`.
4. Remove exact duplicates → remove the conflicting-label rows → record counts before and after.
5. Drop `num_outbound_cmds` and `is_host_login`.
6. Stratified 80/20 split, seed 42 → save `train_idx.npy` and `test_idx.npy`.
7. Assert: no overlapping indices, no identical rows across train/test, no label or attack-name column in X.
8. Inside the Pipeline: `FeatureEngineer` → `ColumnTransformer` (one-hot; log1p+scaling for LR only) → classifier.

## 4. Final evaluation plan

- **Primary:** CV macro-F1 (mean ± SD), with the binary false-positive rate ≤ 0.5% as a hard constraint.
- **Secondary:** per-class precision/recall/F1, balanced accuracy, binary false-negative rate and attack detection rate, one-vs-rest PR-AUC per class, macro ROC-AUC, accuracy (shown as misleading), training time, prediction time per 1,000 rows.
- **Validation:** 3-fold CV for tuning → 5×3 repeated stratified CV for the final comparison → one test-set evaluation.
- **Required plots:**
  1. Class distribution, raw vs deduplicated (log scale)
  2. Duplicate counts per attack type
  3. Protocol × family heatmap
  4. Top-15 services by family
  5. log(src_bytes) box plots by family
  6. Correlation heatmap
  7. CV macro-F1 box plot per model
  8. Per-class recall grouped bars
  9. Normalised confusion matrix for each of the 4 models
  10. Binary false-positive vs false-negative bars
  11. PR curves for the final model
  12. Train/CV/test gap bars
  13. Decision Tree depth validation curve
  14. Final-model learning curve
  15. Permutation importance (top 15)
  16. Training/prediction time bars
  17. Threshold vs false-positive rate / detection rate curve
  18. [OPT] Isolation Forest score histogram by family

## 5. Final experiment plan

| ID | Experiment | Output |
|---|---|---|
| E0 | Leakage demo: raw random split vs deduplicated (Decision Tree) | the "99.96% is fake" finding |
| E1 | Dummy baseline | floor score (macro-F1 about 0.15) |
| E2 | M1–M4 with default settings, same 5-fold CV | first comparison table |
| E3 | Imbalance ablation: class weights on vs off (all models) | evidence for using class weights |
| E4 | Feature-engineering ablation: with vs without (LR, LightGBM) | keep or drop each engineered feature |
| E5 | Tuning: RandomizedSearchCV with equal budgets | best parameters, `cv_results` CSVs |
| E6 | Final comparison: tuned M1–M4, 5×3 repeated CV, paired folds | selection-rule evidence |
| E7 | Re-fit the winner on train → one test evaluation of all 4 models | final results table |
| E8 | Error analysis (out-of-fold + test; by attack name) and overfitting analysis | sections V.2 and V.3 |
| E9 | IDS thresholds from out-of-fold probabilities, plus a prediction demo (one row per family) | prototype output |
| X1 [OPT] | Isolation Forest, trained on Normal only | discovery log and limitations material |

## 6. Final folder structure

```
network-guardian/
├── README.md              # purpose, how to run (Colab + local), headline results, AI-use disclosure
├── requirements.txt       # pinned versions
├── data/
│   ├── raw/               # kddcup.csv(.gz), kddcup.names.txt, training_attack_types.txt — never edited
│   └── processed/         # train_idx.npy, test_idx.npy, dedup_summary.csv
├── notebooks/             # 01–05, run in order
├── src/                   # reusable code imported by the notebooks
├── models/                # saved pipelines + model card
├── reports/
│   ├── metrics/           # CSV/JSON results that feed the documentation tables
│   └── figures/           # numbered PNGs (fig01_class_distribution.png …)
└── docs/
    ├── discovery_log.md   # dated running log, updated every session
    └── final_documentation.pdf
```

A separate `tests/` folder isn't needed. Put assertion checks in `src/validate.py` and run them at the top of each notebook. That gives the same safety without pytest.

## 7. Final notebook structure

| Notebook | Contents | Writes |
|---|---|---|
| `01_data_understanding` | load, schema, class distribution, duplicates, constant/rare columns, skew, correlations, protocol/service analysis | figures 1–6, `dedup_summary.csv` |
| `02_data_preparation` | label mapping, cleaning, split, leakage demo (E0), feature-engineering definitions, pipeline construction and checks | split indices |
| `03_model_development` | E1–E6: baselines, ablations, tuning, repeated CV, **selection rule declared up front** | tuned models, CV CSVs |
| `04_evaluation_and_recommendation` | E7–E9: test evaluation, confusion matrices, error/overfitting analysis, thresholds, model metadata table, prediction demo, recommendation | final model, test metrics, figures 7–17 |
| `05_optional_anomaly_detection` | X1 (Isolation Forest) | figure 18 |

Every notebook opens with the same setup cell: set the path, set the seed, print library versions, and print the data file's SHA-256 hash. Each must pass "Restart & Run All" on a fresh Colab runtime. If your instructor expects a single notebook, the five can be merged in order.

## 8. Final Python modules (`src/`)

| File | Responsibility |
|---|---|
| `config.py` | `SEED=42`, paths, column lists, label→family map, constant columns, CV settings, `QUICK_MODE` |
| `data.py` | `load_raw()`, `map_families()`, `clean()` (deduplicate, conflicts, constant columns), `make_split()` |
| `validate.py` | schema and leakage assertions |
| `features.py` | `add_features(df)` plus an sklearn `FunctionTransformer` wrapper |
| `preprocessing.py` | `build_preprocessor(scale: bool)` |
| `models.py` | `get_models()` (pipelines for M0–M4) and `get_search_spaces()` |
| `evaluation.py` | multiclass + binary metrics, Wilson CI, timing, paired-fold comparison, `build_metadata_table()` |
| `plots.py` | every figure, consistent style, saved with figure numbers |
| `predict.py` | `load_model()`, `predict_connection(record) → dict` (decision policy) |

Keep the key decisions visible in the notebooks themselves, such as the pipeline definition and the selection rule. Every member must be able to explain each line, so don't hide the reasoning inside modules.

## 9. Final model artifacts

| File | Contents |
|---|---|
| `models/{logreg,dtree,rf,lgbm}.joblib` | each tuned **full Pipeline**: feature engineering + encoders + scaler + model in one file, so training and prediction can't drift apart |
| `models/final_pipeline.joblib` | the selected model, re-fit on all of train |
| `models/model_card.json` | class order, raw input schema and allowed categories, engineered features, the post-encoding feature names (`get_feature_names_out()`), parameters, thresholds, seed, library versions, data hash, headline metrics |
| `reports/metrics/` | `cv_results_<model>.csv`, `comparison_cv.csv` (per fold), `test_metrics.json`, `classification_report_<model>.csv`, `confusion_<model>.csv`, `timing.csv`, `model_metadata.csv`, `run_info.json` |
| `data/processed/` | split indices (tiny files, and the split is exactly reproducible) |

## 10. Documentation alignment

| Documentation section | Comes from |
|---|---|
| I. Introduction | README; the families as defined in the spec |
| II.1 Data understanding | notebook 01, `dedup_summary.csv`, figures 1–6 |
| II.2 Feature description | config column lists + the `kddcup.names` descriptions (role: input/target/dropped) |
| II.3 Data preparation | notebook 02 + ablations E3/E4 (the effect of each decision on results) |
| III.1–III.4 Model sections (add **III.4** for the fourth model) | notebook 03: description, configuration = best parameters, training = CV procedure, results = per-model report |
| IV. Model metadata | `model_metadata.csv`, whose rows match the template exactly (name, algorithm, target, number of features, training/test sizes, parameters, random state, metrics, training/prediction time, main result) |
| V.1 Comparative results | `comparison_cv.csv` + `test_metrics.json` |
| V.2 Error analysis | E8: error-cost table, confusion matrices, misses by attack name |
| V.3 Overfitting analysis | train/CV/test gaps, validation and learning curves, OOB score |
| V.4 Recommendation | selection-rule output + limitations (Part E risks, small U2R sample, no unseen attacks, uncalibrated confidence) |
| VI. Results and visualizations | `reports/figures/`, with numbered figures, captions and interpretations |
| VII. Discovery log | `docs/discovery_log.md`. Entries you will probably hit: the fake 99.96%, the smurf collapse, constant columns, Logistic Regression's false alarms, U2R noise, Isolation Forest's failure. Record them only when **you** actually find them |
| VIII. Executive summary | its 6 questions map to: problem → Part A findings → the 4 models + selection rule → recommendation → limitations/next steps → the duplicate-leakage surprise |
| IX. Reflection | each member, individually |
| X. References | below, plus library documentation and an AI-use disclosure |

## 11. Final technology stack

Python 3 (Colab default), **pandas, NumPy, scikit-learn, LightGBM, Matplotlib, Seaborn, joblib** (installed with scikit-learn). SciPy comes with scikit-learn and covers the sign test and Wilson CI.

Not needed: XGBoost, imbalanced-learn, TensorFlow/PyTorch, MLflow, YAML configuration.

Pin the exact versions with `pip freeze | grep -iE "pandas|numpy|scikit|lightgbm|matplotlib|seaborn"` on Colab.

## 12. Implementation roadmap

1. **Setup:** repo, folders, `config.py`, requirements, seed, data hash; start `discovery_log.md` on day one.
2. **Understand the data:** notebook 01 complete, with figures.
3. **Correctness:** cleaning, split, leakage demo, `validate.py` assertions all passing. *Don't model until these pass.*
4. **Baselines:** Dummy + M1–M4 with default settings in one CV loop (E1–E2).
5. **Ablations:** class weights and engineered features (E3–E4); freeze the feature set.
6. **Tuning:** equal-budget searches (E5); write the selection rule in a markdown cell.
7. **Final comparison:** 5×3 repeated CV (E6) → apply the rule → re-fit → test once (E7).
8. **Analysis:** errors, overfitting, thresholds, prediction demo (E8–E9).
9. **Optional:** Isolation Forest (X1).
10. **Freeze:** fresh Colab runtime → Restart & Run All → confirm the numbers match the saved metrics.
11. **Documentation:** fill the template from `reports/`, then the executive summary, reflections and references.
12. **Video** (5–8 minutes): every member on camera and speaking.

### Core references

- Tavallaee, M. et al. (2009). A detailed analysis of the KDD CUP 99 data set. *IEEE CISDA.*
- McHugh, J. (2000). Testing intrusion detection systems. *ACM TISSEC.*
- Axelsson, S. (2000). The base-rate fallacy and the difficulty of intrusion detection. *ACM TISSEC.*
- Sommer, R. & Paxson, V. (2010). Outside the closed world: On using machine learning for network intrusion detection. *IEEE S&P.*
- Breiman, L. (2001). Random forests. *Machine Learning.*
- Ke, G. et al. (2017). LightGBM. *NeurIPS.*
- Liu, F. T. et al. (2008). Isolation forest. *ICDM.*
- Saito, T. & Rehmsmeier, M. (2015). The precision-recall plot is more informative than the ROC plot on imbalanced datasets. *PLoS ONE.*
- Chawla, N. et al. (2002). SMOTE. *JAIR.*
- Grinsztajn, L. et al. (2022). Why do tree-based models still outperform deep learning on tabular data? *NeurIPS.*
- Pedregosa, F. et al. (2011). Scikit-learn. *JMLR.*
- KDD Cup 1999 Data, UCI Machine Learning Repository.

If you'd like, I can turn this into a shareable design doc for your group, or scaffold the repo and `src/` files in your project folder.

Sources: [Project_Specs.md](computer:///home/nightingale/My_Projects/is_project/Project_Specs.md), [Document.md](computer:///home/nightingale/My_Projects/is_project/Document.md), [kddcup.csv](computer:///home/nightingale/My_Projects/is_project/archive/kddcup.data/kddcup.csv)