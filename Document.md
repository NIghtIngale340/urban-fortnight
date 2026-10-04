**PROJECT**

INTRODUCTION TO INTELLIGENT SYSTEMS

(CCINSYSL)

Submitted by:

**Last name, First name M.i**

**Last name, First name M.i**

**Last name, First name M.i**

**Last name, First name M.i**

**Last name, First name M.i**

Submitted to:

**NAME OF YOUR PROFESSOR**

Professor

**OCTOBER 2026**

# **Table of Contents**

[**I. INTRODUCTION [4](#introduction)**](#introduction)

[**II. DATA UNDERSTANDING AND PREPARATION [4](#data-understanding-and-preparation)**](#data-understanding-and-preparation)

[**II.1 Data Understanding [4](#ii.1-data-understanding)**](#ii.1-data-understanding)

[**II.2 Feature Description [5](#ii.2-feature-description)**](#ii.2-feature-description)

[**II.3 Data Preparation [5](#ii.3-data-preparation)**](#ii.3-data-preparation)

[**III. MACHINE LEARNING MODEL DEVELOPMENT [5](#machine-learning-model-development)**](#machine-learning-model-development)

[**III.1 Model (Name of the Model) [6](#iii.1-model-name-of-the-model)**](#iii.1-model-name-of-the-model)

[**III.1.1 Model Description [6](#iii.1.1-model-description)**](#iii.1.1-model-description)

[**III.1.2 Model Configuration [6](#iii.1.2-model-configuration)**](#iii.1.2-model-configuration)

[**III.1.3 Training Procedure [6](#iii.1.3-training-procedure)**](#iii.1.3-training-procedure)

[**III.1.4 Model Results [6](#iii.1.4-model-results)**](#iii.1.4-model-results)

[**III.2 Model (Name of the Model) [6](#iii.2-model-name-of-the-model)**](#iii.2-model-name-of-the-model)

[**III.2.1 Model Description [6](#iii.2.1-model-description)**](#iii.2.1-model-description)

[**III.2.2 Model Configuration [6](#iii.2.2-model-configuration)**](#iii.2.2-model-configuration)

[**III.2.3 Training Procedure [7](#iii.2.3-training-procedure)**](#iii.2.3-training-procedure)

[**III.2.4 Model Results [7](#iii.2.4-model-results)**](#iii.2.4-model-results)

[**III.3 Model (Name of the Model) [7](#iii.3-model-name-of-the-model)**](#iii.3-model-name-of-the-model)

[**III.3.1 Model Description [7](#iii.3.1-model-description)**](#iii.3.1-model-description)

[**III.3.2 Model Configuration [7](#iii.3.2-model-configuration)**](#iii.3.2-model-configuration)

[**III.3.3 Training Procedure [7](#iii.3.3-training-procedure)**](#iii.3.3-training-procedure)

[**III.3.4 Model Results [7](#iii.3.4-model-results)**](#iii.3.4-model-results)

[**IV. MODEL METADATA [8](#model-metadata)**](#model-metadata)

[**V. MODEL COMPARISON AND EVALUATION [9](#model-comparison-and-evaluation)**](#model-comparison-and-evaluation)

[**V.1 Comparative Results [9](#v.1-comparative-results)**](#v.1-comparative-results)

[**V.2 Error Analysis [9](#v.2-error-analysis)**](#v.2-error-analysis)

[**V.3 Overfitting Analysis [9](#v.3-overfitting-analysis)**](#v.3-overfitting-analysis)

[**V.4 Model Recommendation [10](#v.4-model-recommendation)**](#v.4-model-recommendation)

[**VI. RESULTS AND VISUALIZATIONS [10](#results-and-visualizations)**](#results-and-visualizations)

[**VII. DISCOVERY LOG [10](#discovery-log)**](#discovery-log)

[**VIII. EXECUTIVE SUMMARY [11](#executive-summary)**](#executive-summary)

[**IX. REFLECTION [11](#reflection)**](#reflection)

[**Name Of Student 1 [12](#name-of-student-1)**](#name-of-student-1)

[**Name Of Student 2 [12](#name-of-student-2)**](#name-of-student-2)

[**Name Of Student 3 [12](#name-of-student-3)**](#name-of-student-3)

[**Name Of Student 4 [12](#name-of-student-4)**](#name-of-student-4)

[**Name Of Student 5 [12](#name-of-student-5)**](#name-of-student-5)

[**X. REFERENCES [12](#references)**](#references)

# INTRODUCTION

*Provide a brief description and purpose of the developed Network Guardian machine-learning-based Intrusion Detection System (IDS).*

*Discuss the problem of identifying normal network connections and detecting network intrusions using machine learning.*

*Briefly discuss the four attack families considered in the project:*

- *DoS (Denial of Service)*

- *R2L (Remote to Local)*

- *U2R (User to Root)*

- *Probe*

*Explain the overall purpose of developing and comparing machine learning classification approaches for network intrusion detection.*

# DATA UNDERSTANDING AND PREPARATION

This section documents our comprehensive exploration, quality inspection, and data preparation procedures performed on the provided KDD Cup 1999 dataset.

## II.1 Data Understanding

### Overview and Initial Examination
The provided dataset is the KDD Cup 1999 10% subset (`kddcup.csv`), accompanied by the feature definition file `kddcup.names.txt` and attack category taxonomy `training_attack_types.txt`. 

Initial examination revealed the following key structural attributes:
- **Total Records:** 494,021 connection records.
- **Total Columns:** 42 columns, comprising 41 input features and 1 connection label.
- **Header:** The raw CSV file contains no header row. Column headers were parsed from `kddcup.names.txt`.
- **Missing / Invalid Values:** Exactly 0 missing values (NaN/null) and 0 infinite values across all 494,021 rows.
- **Label Formatting:** All raw labels terminate with a trailing period (e.g., `normal.`, `neptune.`, `smurf.`), which must be normalized before matching.

### Feature Types
The 41 input features span three functional groups:
1. **Basic Connection Features:** Characteristics extracted from TCP/IP connection headers (e.g., `duration`, `protocol_type`, `service`, `flag`, `src_bytes`, `dst_bytes`, `land`, `wrong_fragment`, `urgent`).
2. **Content Features:** Domain-specific domain knowledge payload features inspecting suspicious payload behavior within the connection (e.g., `hot`, `num_failed_logins`, `logged_in`, `num_compromised`, `root_shell`, `su_attempted`, `num_root`, `num_file_creations`, `num_shells`, `num_access_files`).
3. **Traffic Window Features:** Statistical summaries computed over a 2-second time window or past 100 connections (e.g., `count`, `srv_count`, `serror_rate`, `rerror_rate`, `same_srv_rate`, `dst_host_count`, etc.).

Of the 41 input features, 3 are symbolic categoricals (`protocol_type` with 3 values, `service` with 66 values, and `flag` with 11 values), while the remaining 38 are numerical (continuous rates, byte counters, or binary indicator flags).

### Discovery of Extreme Duplicate Redundancy
A critical empirical finding made during Phase 1 inspection is that **348,435 out of 494,021 rows (70.53%) are exact duplicates across all features and labels**:
- Only **145,586 unique connection vectors** exist in the entire dataset.
- Redundancy is concentrated in denial-of-service flood traffic: `smurf` contains 280,149 duplicate rows (a 99.77% duplication rate), `neptune` contains 55,381 duplicates, and `normal` contains 9,447 duplicates.
- Conversely, rare attack types contain zero duplicates (`buffer_overflow`: 30 instances, `rootkit`: 10 instances, `loadmodule`: 9 instances, `perl`: 3 instances).

| Attack Type | Original Raw Count | Duplicate Copies Removed | Clean Unique Count | Duplication Rate |
|:---|---:|---:|---:|---:|
| `smurf` | 280,790 | 280,149 | 641 | 99.77% |
| `neptune` | 107,201 | 55,381 | 51,820 | 51.66% |
| `normal` | 97,278 | 9,447 | 87,831 | 9.71% |
| `back` | 2,203 | 1,235 | 968 | 56.06% |
| `satan` | 1,589 | 683 | 906 | 42.98% |
| `portsweep` | 1,040 | 625 | 415 | 60.10% |
| `ipsweep` | 1,247 | 596 | 651 | 47.80% |
| `warezclient` | 1,020 | 127 | 893 | 12.45% |
| Rare attacks (U2R: `buffer_overflow`, `rootkit`, `loadmodule`, `perl`) | 52 | 0 | 52 | 0.00% |

## II.2 Feature Description

The 41 input features are systematically categorized below:

| Feature Name | Data Type | Group | Description | Role |
|:---|:---|:---|:---|:---|
| `duration` | Numerical (continuous) | Basic | Length of connection in seconds | Input |
| `protocol_type` | Categorical (symbolic) | Basic | Transport protocol (`tcp`, `udp`, `icmp`) | Input |
| `service` | Categorical (symbolic) | Basic | Network service on destination (`http`, `ftp`, `smtp`, etc.) | Input |
| `flag` | Categorical (symbolic) | Basic | Normal or error status flag (`SF`, `S0`, `REJ`, etc.) | Input |
| `src_bytes` | Numerical (continuous) | Basic | Bytes sent from source to destination | Input |
| `dst_bytes` | Numerical (continuous) | Basic | Bytes sent from destination to source | Input |
| `land` | Numerical (binary flag) | Basic | 1 if connection is from/to same host/port; 0 otherwise | Input |
| `wrong_fragment` | Numerical (continuous) | Basic | Number of wrong fragments | Input |
| `urgent` | Numerical (continuous) | Basic | Number of urgent packets | Input |
| `hot` | Numerical (continuous) | Content | Number of "hot" indicators (e.g. entering system dirs) | Input |
| `num_failed_logins` | Numerical (continuous) | Content | Number of failed login attempts | Input |
| `logged_in` | Numerical (binary flag) | Content | 1 if successfully logged in; 0 otherwise | Input |
| `num_compromised` | Numerical (continuous) | Content | Number of compromised conditions | Input |
| `root_shell` | Numerical (binary flag) | Content | 1 if root shell is obtained; 0 otherwise | Input |
| `su_attempted` | Numerical (discrete) | Content | 1 if `su root` attempted; 0 otherwise (values: 0, 1, 2) | Input |
| `num_root` | Numerical (continuous) | Content | Number of "root" accesses | Input |
| `num_file_creations` | Numerical (continuous) | Content | Number of file creation operations | Input |
| `num_shells` | Numerical (continuous) | Content | Number of shell prompts | Input |
| `num_access_files` | Numerical (continuous) | Content | Number of operations on access control files | Input |
| `num_outbound_cmds` | Numerical (continuous) | Content | Number of outbound commands in ftp session (Constant: 0) | Dropped |
| `is_host_login` | Numerical (binary flag) | Content | 1 if login belongs to host admin (Constant: 0) | Dropped |
| `is_guest_login` | Numerical (binary flag) | Content | 1 if login is a guest login; 0 otherwise | Input |
| `count` | Numerical (continuous) | Traffic Window | Connections to same host as current in past 2s | Input |
| `srv_count` | Numerical (continuous) | Traffic Window | Connections to same service as current in past 2s | Input |
| `serror_rate` | Numerical (continuous) | Traffic Window | % of connections with SYN errors | Input |
| `srv_serror_rate` | Numerical (continuous) | Traffic Window | % of connections with SYN errors (service) | Input |
| `rerror_rate` | Numerical (continuous) | Traffic Window | % of connections with REJ errors | Input |
| `srv_rerror_rate` | Numerical (continuous) | Traffic Window | % of connections with REJ errors (service) | Input |
| `same_srv_rate` | Numerical (continuous) | Traffic Window | % of connections to same service | Input |
| `diff_srv_rate` | Numerical (continuous) | Traffic Window | % of connections to different services | Input |
| `srv_diff_host_rate` | Numerical (continuous) | Traffic Window | % of connections to different hosts (service) | Input |
| `dst_host_count` | Numerical (continuous) | Host Window | Count of connections to destination host (past 100) | Input |
| `dst_host_srv_count` | Numerical (continuous) | Host Window | Count of connections to destination service (past 100) | Input |
| `dst_host_same_srv_rate` | Numerical (continuous) | Host Window | % to same service (destination host) | Input |
| `dst_host_diff_srv_rate` | Numerical (continuous) | Host Window | % to different services (destination host) | Input |
| `dst_host_same_src_port_rate` | Numerical (continuous) | Host Window | % from same source port (destination host) | Input |
| `dst_host_srv_diff_host_rate` | Numerical (continuous) | Host Window | % to different hosts (destination service) | Input |
| `dst_host_serror_rate` | Numerical (continuous) | Host Window | % with SYN errors (destination host) | Input |
| `dst_host_srv_serror_rate` | Numerical (continuous) | Host Window | % with SYN errors (destination service) | Input |
| `dst_host_rerror_rate` | Numerical (continuous) | Host Window | % with REJ errors (destination host) | Input |
| `dst_host_srv_rerror_rate` | Numerical (continuous) | Host Window | % with REJ errors (destination service) | Input |
| `family` | Categorical (5 classes) | Target | Normal, DoS, Probe, R2L, U2R | Target |

## II.3 Data Preparation

### 1. Label Mapping and Metadata Isolation
Raw labels were stripped of trailing periods and mapped into 5 major families according to `training_attack_types.txt`:
- **Normal:** Ordinary non-malicious connections.
- **DoS (Denial of Service):** Floods aimed at overwhelming services (`smurf`, `neptune`, `back`, `teardrop`, `pod`, `land`).
- **Probe:** Surveillance and port/host scanning (`satan`, `ipsweep`, `portsweep`, `nmap`).
- **R2L (Remote to Local):** Unauthorized remote access without an account (`warezclient`, `guess_passwd`, `warezmaster`, `imap`, `ftp_write`, `multihop`, `phf`, `spy`).
- **U2R (User to Root):** Local non-privileged users attempting privilege escalation (`buffer_overflow`, `rootkit`, `loadmodule`, `perl`).

Crucially, the raw attack name was extracted into a separate metadata series `meta_attack` and completely excluded from the feature matrix $X$ to prevent target leakage.

### 2. Conflict Resolution and Deduplication Order
To prevent data distortion, label mapping was performed *before* duplicate removal:
1. **Exact Duplicates:** 348,435 rows with identical feature vectors and identical family labels were dropped, keeping the first occurrence.
2. **Conflicting Labels:** Exactly 2 rows possessed identical feature vectors but conflicting family assignments; both were dropped as ambiguous noise.
3. **Same-Family Sub-Attack Variants:** Exactly 1 row shared an identical feature vector and family but differing raw attack names; the first instance was retained because the macro-family target was unambiguous.
4. **Dropped Constant Columns:** Confirmed that `num_outbound_cmds` and `is_host_login` contain zero variance (`nunique() == 1`, all values 0); both were dropped.
- **Final Cleaned Dataset:** Exactly **145,583 connection rows**.

### 3. The 99.96% Fake Leakage Proof
To validate why deduplication is mandatory, we implemented an experiment in `notebooks/data_preparation.ipynb` comparing a naive random 80/20 train/test split on raw data versus the cleaned data:
- **Raw Split (Leaked):** **72,652 out of 98,805 test rows (73.53%) appeared identically in the training set**. A default Decision Tree achieved a fraudulent **99.96% accuracy** and 0.9333 Macro-F1. When scored solely on non-leaked rows, performance dropped sharply, proving the high score was a byproduct of rote row memorization.
- **Clean Split (Safe):** Test row contamination was reduced to **0 rows (0.00%)**.

### 4. Stratified 80/20 Train/Test Partitioning
The cleaned dataset (145,583 rows) was partitioned using `StratifiedShuffleSplit` on the 5-family target (`random_state=42`):
- **Training Set (80%):** 116,466 rows (Normal: 70,265; DoS: 43,657; Probe: 1,704; R2L: 799; U2R: 42).
- **Test Set (20%):** 29,117 rows (Normal: 17,566; DoS: 10,914; Probe: 426; R2L: 200; U2R: 10).

The test indices were permanently saved to `data/processed/test_idx.npy` and locked. In `src/data.py`, dedicated accessors `load_train()` and `load_test()` enforce that all exploratory data analysis, feature engineering, and model cross-validation (Phases 6–12) strictly access `load_train()`. The test set will be loaded exactly once during final model evaluation.


# MACHINE LEARNING MODEL DEVELOPMENT

*Document the machine learning models developed for the Network Guardian system.*

*The project requires the development and comparison of at least three different classification approaches.*

*For each model, provide:*

## III.1 Model (Name of the Model)

*Identify the classification algorithm used.*

### **III.1.1 Model Description**

*Provide a brief description of the model and explain how it is used for the intrusion detection problem.*

### **III.1.2 Model Configuration**

*Document the important parameters and settings used when developing the model.*

### **III.1.3 Training Procedure**

*Describe how the model was trained using the prepared dataset.*

### **III.1.4 Model Results**

*Present the important results generated by the model.*

*Include appropriate tables, graphs, screenshots, or notebook outputs.*

## III.2 Model (Name of the Model)

*Identify the classification algorithm used.*

### **III.2.1 Model Description**

*Provide a brief description of the model and explain how it is used for the intrusion detection problem.*

### **III.2.2 Model Configuration**

*Document the important parameters and settings used when developing the model.*

### **III.2.3 Training Procedure**

*Describe how the model was trained using the prepared dataset.*

### **III.2.4 Model Results**

*Present the important results generated by the model.*

*Include appropriate tables, graphs, screenshots, or notebook outputs.*

## III.3 Model (Name of the Model)

*Identify the classification algorithm used.*

### **III.3.1 Model Description**

*Provide a brief description of the model and explain how it is used for the intrusion detection problem.*

### **III.3.2 Model Configuration**

*Document the important parameters and settings used when developing the model.*

### **III.3.3 Training Procedure**

*Describe how the model was trained using the prepared dataset.*

### **III.3.4 Model Results**

*Present the important results generated by the model.*

*Include appropriate tables, graphs, screenshots, or notebook outputs.*

# MODEL METADATA

*Provide the metadata of the machine learning models developed and compared in the project.*

*The Model Metadata should document the characteristics and configuration of each model.*

*Include the following:*

| ***Metadata***               | ***Model 1*** | ***Model 2*** | ***Model 3*** |
|------------------------------|---------------|---------------|---------------|
| **Model Name**               |               |               |               |
| **Algorithm / Approach**     |               |               |               |
| **Target Variable**          |               |               |               |
| **Number of Input Features** |               |               |               |
| **Features Used**            |               |               |               |
| **Training Data Size**       |               |               |               |
| **Testing Data Size**        |               |               |               |
| **Important Parameters**     |               |               |               |
| **Random State**             |               |               |               |
| **Evaluation Measures**      |               |               |               |
| **Training Time**            |               |               |               |
| **Prediction Time**          |               |               |               |
| **Main Result**              |               |               |               |

*Additional model-specific information may be included where appropriate.*

*The purpose of this section is to provide a clear technical summary of the models so that the differences between the approaches can be easily understood.*

# MODEL COMPARISON AND EVALUATION

*Present the evaluation and comparison of the machine learning models.*

*Discuss the evaluation measures used to determine how well each model performs.*

*Depending on the measures used, this section may include:*

- *Accuracy*

- *Precision*

- *Recall*

- *F1-Score*

- *Confusion Matrix*

- *Classification Report*

- *Training Time*

- *Prediction Time*

## V.1 Comparative Results

*Provide a comparison table summarizing the performance of the models.*

## V.2 Error Analysis

*Discuss the errors produced by the models.*

*Explain the significance of false positives and false negatives in the context of an Intrusion Detection System.*

## V.3 Overfitting Analysis

*Discuss whether there are indications of overfitting and explain how this was investigated.*

## V.4 Model Recommendation

*Identify the model recommended by the team for the Network Guardian prototype.*

*The recommendation must be supported by the evaluation results and should acknowledge the limitations of the project.*

# RESULTS AND VISUALIZATIONS

*Present the major results and visualizations generated throughout the project.*

*Include appropriate visualizations such as:*

- *Class distribution*

- *Feature distributions*

- *Feature comparisons*

- *Confusion matrices*

- *Model performance comparisons*

- *Other relevant visualizations*

*Each figure should include:*

- *Figure number*

- *Descriptive title*

- *Visualization*

- *Brief description*

- *Interpretation of the result*

# DISCOVERY LOG

This log records our actual development journey, empirical observations, failures, wrong turns, and key decisions throughout the project.

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

### Entry 4: Stratified 80/20 Train/Test Split & Leakage Assertions (Phase 5)
- **Date:** October 5, 2026
- **Question Raised:** How do we partition the data so rare classes are representative and test data remains completely uncontaminated?
- **Design Decisions:**
  - Stratified 80/20 split based on the 5-family target:
    - **Train Set (80%):** 116,466 rows (Normal: 70,265; DoS: 43,657; Probe: 1,704; R2L: 799; U2R: 42)
    - **Test Set (20%):** 29,117 rows (Normal: 17,566; DoS: 10,914; Probe: 426; R2L: 200; U2R: 10)
  - Saved split indices to disk (`data/processed/train_idx.npy`, `data/processed/test_idx.npy`) and recorded metadata in `data/processed/split_meta.json`.
  - Locked the test set: created `load_train()` and `load_test()` in `src/data.py` so subsequent modeling and EDA phases strictly access `load_train()`. The test set will be loaded exactly once during final model evaluation.
- **Integrity & Fault Injection Tests (`src/validate.py`):**
  - Verified index disjointness (`intersection == 0`).
  - Verified exact row union (`union == 145,583`).
  - Proved zero feature vector leakage (`row_overlap(X_train, X_test) == 0`).
  - Verified that fault injection tests (injecting intentional overlap or missing indices) raise `AssertionError` and pass break tests.


# EXECUTIVE SUMMARY

*Provide a concise executive summary written for a reader who has not reviewed the complete notebook.*

*Answer the following questions:*

1.  *What problem did we set out to solve, and why does it matter?*

2.  *What did we discover about the data that shaped our decisions?*

3.  *Which approaches did we compare, and how did we judge them?*

4.  *What do we recommend, and what evidence supports it?*

5.  *What are the limitations of our work, and what would we do next?*

6.  *What was our biggest mistake or surprise, and what did we learn from it?*

*The Executive Summary should use plain language and summarize the most important findings of the project.*

# REFLECTION

*Each team member must provide an individual reflection discussing their experience in developing the Network Guardian project.*

*The reflection should discuss:*

1.  *What did you learn about machine learning and intrusion detection?*

2.  *What did you learn from exploring and preparing the dataset?*

3.  *What did you learn from comparing different classification approaches?*

4.  *What challenges did you encounter?*

5.  *How did you respond to mistakes or unexpected results?*

6.  *What did you learn about evaluating machine learning models beyond accuracy?*

7.  *How can machine learning be applied to real-world cybersecurity problems?*

8.  *What would you improve if you were given additional time?*

## 

## Name Of Student 1

Discuss thoroughly your actual learning, experience, and contribution to the project.

## Name Of Student 2

Discuss thoroughly your actual learning, experience, and contribution to the project.

## Name Of Student 3

Discuss thoroughly your actual learning, experience, and contribution to the project.

## Name Of Student 4

Discuss thoroughly your actual learning, experience, and contribution to the project.

## Name Of Student 5

Discuss thoroughly your actual learning, experience, and contribution to the project.

# REFERENCES

Provide all references used throughout the project.

References may include:

- Machine learning documentation

- Python library documentation

- Research papers

- Tutorials

- Books

- Websites

- Other academic or technical resources

All external sources must be properly cited.

Any AI tools used during the project must also be disclosed according to the project requirements.
