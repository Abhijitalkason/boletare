# ML Pipeline Review & Recommendations

**Date:** 2026-04-15
**Reviewer:** Claude Code + Zen Code Review
**Project:** Jyotish AI — Vedic Astrology Event Prediction Engine
**Status:** Model underperforms hand-coded baseline. Architectural pivot required.

---

## 1. Problem Statement

### What We're Trying to Do

The Jyotish AI system predicts the likelihood of major life events (marriage, career, child, property, health) for a given person based on their Vedic birth chart. The prediction engine has 4 layers:

```
Layer 1 (Compute)  → Birth chart from planetary positions (PySwissEph)
Layer 2 (Predict)  → 3-gate scoring: Promise + Dasha + Transit → Convergence score
Layer 3 (Narrate)  → Claude AI generates natural language explanation
Layer 4 (Deliver)  → API response to user
```

Layer 2 currently uses **hand-coded weights** to combine three gate scores into a final prediction:

```
convergence = (Gate1 + Gate2 + Gate3) / 3.0
```

The ML initiative aimed to **replace the hand-coded equal weights** with learned optimal weights using XGBoost, trained on historical horoscope data with documented life events.

### What Went Wrong

After significant investment in data collection, parsing, and pipeline development:

| Metric | XGBoost Model | Hand-Coded Baseline | Naive (always negative) |
|--------|--------------|--------------------|-----------------------|
| **Accuracy** | **36.4%** | **67.8%** | 66.7% |
| F1 Score | 0.505 | 0.107 | 0.0 |
| ROC-AUC | 0.513 | — | 0.5 |
| Precision | 0.34 | — | — |
| Recall | 0.98 | — | — |

**The XGBoost model is worse than simply using equal weights.** It's even worse than always predicting "no event" (66.7% naive accuracy). Adding more training data (108 → 363 samples) made performance *worse*, not better.

### Why This Matters

- Engineering time spent on OCR parsing, data collection, and pipeline development did not improve predictions
- The model cannot be deployed — it would degrade user experience compared to the existing hand-coded system
- The fundamental approach (tree-based ML on pre-computed scores) appears to be wrong for this problem structure

---

## 2. What Was Built

### Data Pipeline (6 Sources, 592 Charts, 252 Events)

```
Archive.org OCR Books
    │
    ├── 02_parse_horoscopes.py        → Notable Horoscopes (50 charts, 36 events)
    ├── 02b_parse_technique_books.py  → Santhanam + Raman v1/v2 (463 charts, 103 events)
    ├── 02c_parse_hpa.py              → Hindu Predictive Astrology (14 charts, 0 events)
    ├── 02e_parse_sanjay_rath.py      → Sanjay Rath: Crux (65 charts, 113 events)
    │
    ├── 03b_merge_datasets.py         → all_charts_merged.json (592 charts, 252 events)
    ├── 03_validate_data.py           → Quality gates + validation
    ├── 04_generate_features.py       → 22-dimensional feature vectors (363 samples)
    ├── 05_build_training_set.py      → training_set.npz
    ├── 06_train_model.py             → XGBoost 5-fold CV (regressor vs classifier)
    └── 07_evaluate_model.py          → Evaluation reports + SHAP analysis
```

### Feature Architecture (22 Dimensions)

```
Features 0-4:   Gate 1 sub-scores (promise evaluation)
  ├── g1_lord_dignity, g1_occupant_score, g1_navamsha_score
  ├── g1_sav_normalized
  └── g1_overall_score          ← weighted sum of features 0-3

Features 5-8:   Gate 2 sub-scores (dasha evaluation)
  ├── g2_mahadasha_score, g2_antardasha_score
  ├── g2_overall_score          ← weighted sum of features 5-6
  └── g2_connection_count

Features 9-11:  Gate 3 sub-scores (transit evaluation)
  ├── g3_overall_score          ← weighted sum of sub-components
  ├── g3_active_months_ratio
  └── g3_peak_bav_score

Feature 12:     convergence_normalized = (g1_overall + g2_overall + g3_overall) / 3.0

Features 13-17: Quality flags (birth_time_tier, lagna_mode, dasha_boundary, etc.)
Features 18-21: Demographics (all hardcoded to 0.5 — placeholder, dropped before training)
```

### Training Configuration

- **Model:** XGBoost (Classifier with binary:logistic, scale_pos_weight=2)
- **Samples:** 363 (121 positive, 242 negative)
- **Features used:** 18 (after dropping 4 placeholder features)
- **Cross-validation:** Stratified 5-Fold
- **Hyperparameters:** max_depth=3, n_estimators=100, learning_rate=0.1, early_stopping_rounds=10
- **Negative sampling:** 2 negatives per positive (time-shifted + cross-event)
- **Label smoothing:** positive_exact=0.85, positive_approximate=0.65, negative=0.0

---

## 3. Root Cause Analysis

### The review identified 7 issues (2 critical, 3 high, 1 medium, 1 low):

### CRITICAL #1: Feature Redundancy

The 18 active features are **not independent** — they are sub-components of just 3 gate scores plus their average.

```
Problem visualization:

  Feature 0 (g1_lord_dignity)     ──┐
  Feature 1 (g1_occupant_score)   ──┤
  Feature 2 (g1_navamsha_score)   ──┼── Feature 4 (g1_overall_score) ──┐
  Feature 3 (g1_sav_normalized)   ──┘                                  │
                                                                        │
  Feature 5 (g2_mahadasha_score)  ──┐                                  │
  Feature 6 (g2_antardasha_score) ──┼── Feature 7 (g2_overall_score) ──┼── Feature 12 (convergence)
  Feature 8 (g2_connection_count) ──┘                                  │
                                                                        │
  Feature 9 (g3_overall_score)    ──┐                                  │
  Feature 10 (g3_active_months)   ──┼── (implicit g3_total) ───────────┘
  Feature 11 (g3_peak_bav_score)  ──┘
```

**The model is being asked to learn optimal weights over pre-computed weighted sums.** This is like asking someone to improve a cake recipe by re-weighing the already-mixed batter — the ingredients are already combined.

XGBoost sees:
- 5 features that are components of g1_overall (which it also sees)
- 4 features that are components of g2_overall (which it also sees)
- 3 features that are components of g3_overall (which it also sees)
- 1 feature that is the average of g1, g2, g3 (which it also sees separately)

This multicollinearity confuses tree splits and prevents meaningful pattern discovery.

### CRITICAL #2: Flawed Negative Sampling

The cross-event negative sampling strategy assumes events are mutually exclusive:

```
Positive: Person X had a MARRIAGE on 14-May-1934     → label = 1
Negative: Person X had a HEALTH event on 14-May-1934  → label = 0  ← WRONG!
```

**This is false.** A person can have a health crisis, career change, and property purchase in the same year. The "cross-event negative" creates systematically incorrect labels because:

- The model learns "if marriage features are positive, health features should be negative on the same date"
- But the astrology engine computes independent gate scores per event type — they CAN both be positive
- This injects contradictory training signals

### HIGH #3: No Sample Weighting by Source Quality

All 363 samples are treated equally despite vastly different reliability:

| Source | Samples | Label Quality | Treated As |
|--------|---------|--------------|------------|
| Notable Horoscopes | 108 | High (biographical, exact dates) | Equal weight |
| Technique Books | ~140 | Low-Medium (approximate dates, theory-mixed) | Equal weight |
| Sanjay Rath | ~115 | Medium (some approximate, some strong) | Equal weight |

Adding 255 noisier samples without downweighting them **diluted the signal** from the original 108 high-quality samples. This directly explains why performance degraded from 108 → 363 samples.

### HIGH #4: Model Stops Learning After 2 Trees

The early stopping mechanism halted at **median_best_iteration=2** (out of 100 possible trees). This means:

- By the 3rd tree, the model is already overfitting
- The features don't contain enough discriminative information for tree-based learning
- A simpler model (linear, 3-parameter) would likely perform as well or better

### HIGH #5: 91% of Charts Skipped

Of 592 merged charts, **539 were skipped** during feature generation because `needs_manual_review=True`. This flag is set when:
- A chart has no events (most technique book charts), OR
- A chart has no valid coordinates (OCR parsing failure)

Only 53 charts (9%) actually produced the 363 training samples. The massive data collection effort (11 OCR files, 6 books) yielded very little usable training data.

### MEDIUM #6: No Source-Stratified Cross-Validation

The 5-fold CV stratifies by label (positive/negative) but not by data source. This means:
- Some folds may contain mostly Notable Horoscopes (high quality)
- Others may contain mostly technique book data (low quality)
- Fold-to-fold performance variance is driven by data quality, not model capability

### LOW #7: Placeholder Features

Features 18-21 (gender, age, education, income) are hardcoded to 0.5. They are correctly dropped before training but still occupy space in the pipeline, causing confusion about the true feature count (22 stated, 18 used).

---

## 4. Why XGBoost Is the Wrong Tool

### The Fundamental Mismatch

XGBoost excels at learning complex non-linear patterns from **independent, raw features** with **thousands of samples**. This problem has:

- **Dependent, pre-computed features** (sub-scores of 3 gates + their average)
- **363 samples** (far below the ~1,000-10,000 needed for 18 features)
- **A near-optimal baseline** (67.8%) that is already a simple linear combination

### What XGBoost Is Being Asked to Do

```
Hand-coded:  convergence = (G1 + G2 + G3) / 3   → 67.8% accuracy

XGBoost:     Learn f(g1_sub1, g1_sub2, g1_sub3, g1_sub4, g1_overall,
                      g2_sub1, g2_sub2, g2_overall, g2_count,
                      g3_overall, g3_months, g3_bav,
                      convergence, tier, lagna, boundary, ambiguous, retro)
             → 36.4% accuracy
```

XGBoost cannot improve on `(G1+G2+G3)/3` when it's also given G1, G2, G3, and all their sub-components as inputs. The redundancy creates contradictory split points in the trees, and with only 363 samples, there isn't enough data to resolve the contradiction.

### What the Right Tool Should Do

```
Learn:  convergence = w1*G1 + w2*G2 + w3*G3 + bias   → ???% accuracy

Where:
  - w1, w2, w3 are 3 learnable weights (not 18+ tree parameters)
  - The model has 3-4 parameters (not hundreds of tree splits)
  - Even 50 samples is sufficient for 3-parameter optimization
```

---

## 5. Recommended Alternatives

### Tier 1: Try Immediately (Combined effort: ~2 hours)

#### Option A — Scipy Direct Optimization
Learn optimal w1, w2, w3 by directly maximizing F1 score.

```python
from scipy.optimize import minimize

def objective(weights):
    w1, w2, w3 = weights
    scores = w1 * G1 + w2 * G2 + w3 * G3
    predictions = (scores >= threshold).astype(int)
    return -f1_score(y_true, predictions)

result = minimize(objective, x0=[1, 1, 1], method='Nelder-Mead')
```

- **Effort:** 30 minutes
- **Gives you:** The theoretical ceiling — best possible linear combination
- **Risk:** May overfit without cross-validation

#### Option B — Logistic Regression on 3 Features
Standard ML approach for learning a linear combination with regularization.

```python
from sklearn.linear_model import LogisticRegression

X = features[:, [4, 7, 10]]  # g1_overall, g2_overall, g3_overall only
model = LogisticRegression(class_weight='balanced')
model.fit(X, y_binary)

# Learned weights = your new optimal convergence formula
print(f"w1={model.coef_[0][0]:.3f}, w2={model.coef_[0][1]:.3f}, w3={model.coef_[0][2]:.3f}")
```

- **Effort:** 1 hour
- **Gives you:** Regularized optimal weights + calibrated probabilities
- **Risk:** Low — 3 parameters with 363 samples is very safe

#### Option C — Isotonic Regression (Score Calibration)
Keep equal weights, just calibrate the score-to-probability mapping.

```python
from sklearn.isotonic import IsotonicRegression

convergence_scores = (G1 + G2 + G3) / 3.0
calibrator = IsotonicRegression(out_of_bounds='clip')
calibrator.fit(convergence_scores, y_binary)
```

- **Effort:** 30 minutes
- **Gives you:** Better probability estimates from existing scores
- **Risk:** None — doesn't change the scoring function

### Tier 2: Try If Tier 1 Succeeds (~4 hours)

#### Option D — Bayesian Logistic Regression
Same as Option B but with uncertainty estimates on each weight.

```python
import pymc as pm

with pm.Model():
    w1 = pm.Normal('w1', mu=1, sigma=1)
    w2 = pm.Normal('w2', mu=1, sigma=1)
    w3 = pm.Normal('w3', mu=1, sigma=1)
    p = pm.math.sigmoid(w1*G1 + w2*G2 + w3*G3)
    y_obs = pm.Bernoulli('y', p=p, observed=y_binary)
    trace = pm.sample(2000)
```

- **Effort:** 3-4 hours
- **Gives you:** Confidence intervals on each gate's importance
- **Risk:** Requires PyMC dependency

### Tier 3: Only If Tier 1 Fails (Deeper Changes)

#### Option E — Improve the Gates Themselves
If optimal weights still don't beat 67.8%, the problem isn't weight calibration — it's that the gate scores themselves aren't discriminative enough. This means improving the astrology engine's core logic:

- Better Gate 1 (Promise): Refine house-lord dignity, occupant scoring, navamsha strength rules
- Better Gate 2 (Dasha): Improve mahadasha/antardasha relevance scoring
- Better Gate 3 (Transit): Better transit window detection, ashtakavarga calculations

This is domain-knowledge work, not ML work.

---

## 6. Decision Framework

```
Step 1: Run Logistic Regression on 3 features (g1, g2, g3)
        │
        ├── Beats 67.8%? ─── YES ──→ Ship LR model. Problem solved.
        │                            The equal weights were suboptimal.
        │                            Deploy: convergence = w1*G1 + w2*G2 + w3*G3
        │
        └── Still ≤ 67.8%? ─ YES ──→ Equal weights ARE optimal.
                                      │
                                      ├── Option 1: Accept 67.8% baseline for production
                                      │             Focus engineering on user experience
                                      │
                                      ├── Option 2: Improve gate quality (domain knowledge)
                                      │             Better astrology rules → better G1, G2, G3
                                      │
                                      └── Option 3: Collect organic user feedback data
                                                    Real confirmed outcomes → gold-standard labels
                                                    Revisit ML when dataset reaches ~1,000 confirmed events
```

---

## 7. Additional Fixes (Independent of Model Choice)

These should be applied regardless of which model alternative is chosen:

### Fix 1: Add Sample Weighting
```python
# In 05_build_training_set.py or 06_train_model.py
source_weights = {
    "notable_horoscopes": 1.0,        # High quality
    "sanjay_rath_crux": 0.7,          # Medium quality
    "judge_horoscope_santhanam": 0.4,  # Low-medium quality
    "judge_horoscope_v1_raman": 0.4,
    "judge_horoscope_v2_raman": 0.4,
}
```

### Fix 2: Replace Cross-Event Negatives
Instead of "same chart, same date, different event type" (flawed), use:
```python
# Random date from non-event periods
negative_date = birth_date + timedelta(days=random.randint(365, 365*50))
# Ensure it doesn't coincide with any known event
while any(abs((negative_date - known_event).days) < 365 for known_event in chart_events):
    negative_date = birth_date + timedelta(days=random.randint(365, 365*50))
```

### Fix 3: Source-Stratified Cross-Validation
```python
from sklearn.model_selection import StratifiedGroupKFold
# Groups = data source, stratify = label
cv = StratifiedGroupKFold(n_splits=5)
for train_idx, test_idx in cv.split(X, y, groups=source_labels):
    ...
```

---

## 8. Key Learnings

1. **More data is not always better.** Adding noisier data without quality controls degraded the model. Data quality matters more than quantity at small scales.

2. **Feature engineering should create independent signals.** Feeding a model both sub-scores AND their pre-computed weighted sums creates redundancy that hurts tree-based methods.

3. **Match model complexity to problem complexity.** A 3-parameter problem (learn 3 weights) doesn't need a model with hundreds of parameters (XGBoost trees). Simpler models outperform complex ones when the hypothesis space is simple.

4. **The hand-coded baseline is a strong benchmark.** The astrology engine's equal-weight convergence formula encodes significant domain expertise. ML should be expected to provide marginal improvements, not revolutionary ones.

5. **Validate with the cheapest experiment first.** The 1-day logistic regression test should have been run before the 4-week data expansion effort. It would have revealed the feature redundancy problem immediately.

---

## 9. Files Reference

### Pipeline Scripts
| File | Purpose |
|------|---------|
| `scripts/training/parse_utils.py` | Shared parsing utilities |
| `scripts/training/02_parse_horoscopes.py` | Notable Horoscopes parser (Cluster A) |
| `scripts/training/02b_parse_technique_books.py` | Technique books parser (Cluster B) |
| `scripts/training/02c_parse_hpa.py` | Hindu Predictive Astrology parser (Cluster C) |
| `scripts/training/02e_parse_sanjay_rath.py` | Sanjay Rath parser |
| `scripts/training/02d_parse_magazines.py` | Magazine parser stub (deferred) |
| `scripts/training/03_validate_data.py` | Data validation + quality gates |
| `scripts/training/03b_merge_datasets.py` | Multi-dataset merge |
| `scripts/training/04_generate_features.py` | 22-D feature vector generation |
| `scripts/training/05_build_training_set.py` | NumPy training arrays |
| `scripts/training/06_train_model.py` | XGBoost training + dual experiment |
| `scripts/training/07_evaluate_model.py` | Evaluation + SHAP + baseline comparison |
| `scripts/training/run_pipeline.py` | Master pipeline runner |

### Data Files
| File | Contents |
|------|----------|
| `data/training/all_charts_merged.json` | 592 charts, 252 events (merged from 6 sources) |
| `data/training/merge_manifest.json` | Source breakdown and statistics |
| `data/training/training_metadata.json` | 363 samples, event distribution |
| `data/training/feature_vectors.json` | 22-D feature vectors |
| `data/training/training_set.npz` | NumPy arrays for XGBoost |

### Model Artifacts
| File | Contents |
|------|----------|
| `models/xgboost_v1.json` | Trained XGBoost model (underperforming) |
| `models/evaluation_report.json` | Full metrics + baseline comparison |
| `models/classification_report.txt` | Precision/recall per class |
| `models/confusion_matrix.png` | TP=118, FP=228, TN=14, FN=3 |
| `models/feature_importance.png` | SHAP analysis |
| `models/roc_pr_curves.png` | ROC-AUC=0.513, PR-AUC=0.365 |

### Data Sources
| File | Contents |
|------|----------|
| `docs/TRAINING_DATA_SOURCES.md` | All 11 OCR sources with download details |
| `scripts/training/ocr_sources.py` | Source configuration for bulk downloads |
| `scripts/training/01b_download_all_ocr.py` | Bulk OCR downloader |
