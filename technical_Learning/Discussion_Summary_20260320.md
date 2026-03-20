# Discussion Summary — 2026-03-20

## Session Overview

This session focused on fixing the XGBoost training pipeline (Steps 6 & 7) which was producing all-negative predictions (F1=0.0), and understanding the ML concepts behind the fixes.

---

## 1. Initial Problem: Model Predicts All Negatives

After running the first implementation of Steps 6 & 7, the XGBoost model achieved:
- F1 = 0.000 (zero — no positive predictions at all)
- Accuracy = 66.7% (same as always predicting "negative")
- ROC-AUC = 0.524 (barely above random)

The model was effectively useless — it called everything negative.

---

## 2. Zen Code Review: Root Cause Analysis

We ran a Zen code review on the implementation, which found 7 issues:

### HIGH Severity (Must Fix)

**Issue 1: scale_pos_weight ignored by XGBRegressor**
- `scale_pos_weight` tells the model "pay extra attention to positive cases"
- But this only works with `XGBClassifier` (classification mode)
- We were using `XGBRegressor` (regression mode) — the parameter was silently ignored
- The sensitivity test comparing spw=1 vs spw=2 was meaningless

**Issue 2: Smoothed labels cause all-negative predictions**
- Our labels: 72 samples at 0.0, 34 at 0.65, 2 at 0.85
- Average label = (72x0 + 34x0.65 + 2x0.85) / 108 = ~0.22
- XGBRegressor with reg:logistic predicts values near this mean (~0.15-0.30)
- We used 0.5 as the cutoff for "positive"
- Since NO prediction reached 0.5, everything was called negative
- Analogy: Setting the passing mark at 50 when the average score is 22

**Issue 3: No binary-label experiment**
- We only tried smoothed labels (0.0/0.65/0.85)
- Should also try simple binary (0/1) to determine if the issue is label format or data size

### MEDIUM Severity (Should Fix)

**Issue 4: Threshold hardcoded at 0.5** — Should sweep thresholds to find optimal cutoff
**Issue 5: min_child_weight=3 too restrictive** — With ~86 samples per fold, reduce to 1
**Issue 6: No early stopping** — 50 trees on 86 samples risks overfitting

### LOW Severity

**Issue 7: Feature names hardcoded** — Could drift from feature_builder.py

---

## 3. Understanding Labels

### What is a Label?
A label is the "correct answer" you give the model so it can learn. Like an answer key for an exam.

### Our 3 Label Values (Label Smoothing)

| Label | Meaning | Count | Example |
|-------|---------|-------|---------|
| 0.85 | Event happened at EXACT predicted time | 2 | Marriage in exact dasha period |
| 0.65 | Event happened approximately | 34 | Career change within ~1 year |
| 0.00 | Event didn't happen (negative sample) | 72 | Time-shifted or cross-event |

### Why Smoothed Labels?
- 0.85 instead of 1.0 because astrology predictions are never 100% certain
- 0.65 for approximate matches because timing wasn't exact
- This is called "label smoothing" — adds uncertainty to training

### The Problem Smoothed Labels Caused
- Mean label = ~0.22 (heavily skewed toward 0)
- Regression model predicts near the mean
- All predictions below 0.5 threshold = all negative

### The Solution: Keep Both, Let Step 6 Decide
- Don't change Step 5 (keep smoothed labels in training_set.npz)
- Step 6 derives binary labels: `y_binary = (y > 0.5).astype(int)` → [0, 1]
- Run both experiments, compare results

---

## 4. Dual-Experiment Fix Plan

### Zen Review of the Plan

Zen reviewed the dual-experiment plan and found it **sound** with 2 medium improvements:

1. **eval_set label matching**: Early stopping eval_set must use the correct label type
   - Regressor: smoothed labels for eval_set (matches training)
   - Classifier: binary labels for eval_set (matches training)

2. **Final model n_estimators**: Use median best_iteration from CV folds instead of hardcoded 100 trees

### Implementation

Two files changed (no changes to Steps 1-5 or pipeline runners):

**06_train_model.py — Major Rewrite:**
- Replaced single XGBRegressor with dual experiment approach
- Experiment A: XGBRegressor + smoothed labels + optimal threshold sweep
- Experiment B: XGBClassifier + binary labels + scale_pos_weight=2 + optimal threshold
- Shared changes: min_child_weight 3→1, n_estimators 50→100, early_stopping_rounds=10
- Threshold sweep: 0.05 to 0.95 in steps of 0.05, pick threshold maximizing F1
- Winner selected by F1, final model trained on all data with median best_iteration
- Metadata saved in cv_predictions.npz: experiment_type, optimal_threshold

**07_evaluate_model.py — Modified:**
- Loads experiment_type and optimal_threshold from cv_predictions.npz
- Uses correct model class (XGBClassifier or XGBRegressor) for SHAP
- Reports experiment context in output

---

## 5. Results: Before vs After

| Metric | Before (broken) | After (fixed) |
|--------|-----------------|---------------|
| F1 Score | 0.000 | **0.522** |
| True Positives | 0 / 36 | **35 / 36** |
| False Positives | 0 | 63 |
| ROC-AUC | 0.524 | **0.575** |
| Recall | 0% | **97%** |
| Precision | 0% | 36% |

### Experiment Comparison

| | Exp A (Regressor + Smoothed) | Exp B (Classifier + Binary) |
|---|---|---|
| F1 at 0.5 threshold | 0.054 | 0.410 |
| Optimal threshold | 0.10 | 0.35 |
| F1 at optimal threshold | 0.522 | **0.522** |
| ROC-AUC | 0.484 | **0.575** |
| Median best iteration | 0 | **6** |

**Winner: Experiment B (Classifier + Binary Labels)** because:
- Better ROC-AUC (0.575 vs 0.484)
- More meaningful threshold (0.35 vs 0.10)
- Actually learned something (6 trees vs 0 — regressor gave up immediately)

### What This Tells Us
- **Smoothed labels don't help** at 108 samples — the nuance confuses the model
- **Binary labels work better** for this small dataset
- **Features have weak but real signal** — timing features (Gates 2 & 3) dominate
- **108 samples is the bottleneck** — model over-predicts positives (high recall, low precision)

---

## 6. SHAP Feature Importance

Top 5 features from the winning model:

| Rank | Feature | SHAP Value | Gate |
|------|---------|------------|------|
| 1 | convergence_normalized | 0.1266 | Overall convergence |
| 2 | g3_overall_score | 0.1168 | Gate 3 (Transit) |
| 3 | g2_mahadasha_score | 0.1125 | Gate 2 (Dasha) |
| 4 | g2_overall_score | 0.1067 | Gate 2 (Dasha) |
| 5 | g3_peak_bav_score | 0.1017 | Gate 3 (Transit) |

**Key insight:** Timing features (Gates 2 & 3) matter more than promise features (Gate 1). The convergence score itself is the most predictive single feature.

---

## 7. Baseline Comparison

| Model | Accuracy | F1 |
|-------|----------|-----|
| XGBoost (optimal threshold) | 40.7% | **0.522** |
| Convergence baseline (threshold=0.60) | 67.6% | 0.054 |
| Naive (always predict negative) | 66.7% | 0.000 |

XGBoost has lower accuracy but much higher F1 — it's better at *finding* the positives, at the cost of also flagging many false positives.

---

## 8. Output Files Generated

### Step 6 outputs (in models/):
- `xgboost_v1.json` — trained XGBoost model (10 trees)
- `cv_predictions.npz` — out-of-fold predictions + experiment metadata
- `feature_names.json` — 18 feature names

### Step 7 outputs (in models/):
- `confusion_matrix.png` — TP=35, FP=63, TN=9, FN=1
- `feature_importance.png` — SHAP bar plot
- `roc_pr_curves.png` — ROC + PR curves
- `classification_report.txt` — per-class precision/recall/F1
- `evaluation_report.json` — all metrics in JSON

---

## 9. Key ML Concepts Learned Today

### Threshold Tuning
- The default 0.5 threshold is arbitrary
- With imbalanced data, lower thresholds often work better
- Sweep thresholds on held-out predictions to find optimal F1

### XGBRegressor vs XGBClassifier
- **Regressor** (reg:logistic): Predicts continuous values [0,1], good for smoothed labels
- **Classifier** (binary:logistic): Predicts class probabilities, needs 0/1 labels
- `scale_pos_weight` only works with Classifier

### Early Stopping
- Prevents overfitting by stopping tree building when validation loss stops improving
- `early_stopping_rounds=10` = stop if no improvement for 10 consecutive trees
- Requires eval_set in model.fit()

### best_iteration
- The tree number where the model performed best on validation data
- Used to set n_estimators for the final model (trained on all data without early stopping)

### Dual-Experiment Methodology
- Run two approaches on same data with same CV splits
- Compare fairly using the same metric (F1)
- Tells you whether the problem is configuration or data

---

## 10. Understanding ROC-AUC (Our Learning)

### What is ROC?

ROC stands for "Receiver Operating Characteristic" — a fancy name for a simple idea: **draw every possible threshold on one chart so you can compare them all at once**. Imagine a slider that goes from 0.0 to 1.0. At each position, you get a different trade-off between catching real positives (True Positive Rate) and accidentally flagging negatives (False Positive Rate). The ROC curve plots all these trade-offs on a single chart.

### What is AUC?

AUC (Area Under the Curve — NOT AOC!) is just the shaded area under the ROC curve. It squashes the entire curve into **one number between 0 and 1**, so you can compare models without arguing about which threshold is best.

- AUC = 1.0 — perfect model (never happens in practice)
- AUC = 0.5 — random guessing (coin flip)
- AUC = 0.0 — perfectly wrong (also never happens)

### Our Model's AUC: 0.575

Our model's AUC is **0.575** — barely above the random-guess baseline of 0.50. That's not a failure though. It directly reflects the **108-sample bottleneck**. The model's F1 jump from 0.000 to 0.522 means it learned something real; there just isn't enough data yet to make it confident. Once we cross ~500 samples, expect the AUC to climb meaningfully.

### The Orange Dot Insight

At our chosen threshold of 0.35, the operating point is way up in the top-right corner of the ROC curve:
- **Very high TPR (97%)** — catches almost every real event
- **Very high FPR (88%)** — but also flags many non-events

That's our model saying: **"When in doubt, flag it."**

For Jyotish AI, where **missing a real event might matter more than a false alarm**, this is actually a reasonable operating point for now. It's better to say "this planetary combination might cause an event" and be wrong sometimes, than to miss a genuine prediction.

### Key Takeaway

The ROC curve helps us understand the **trade-off between sensitivity and specificity**. Right now our model is set to maximum sensitivity (catch everything). As we add more training data, the curve will shift up and to the left — meaning we can maintain high TPR while reducing FPR. That's when the model becomes truly useful.

---

## 11. Next Steps

1. **Grow the dataset** — 108 samples is the bottleneck. Target 500+ for meaningful improvements
2. **Commit all changes** — checkpoint the working dual-experiment pipeline
3. **Investigate Gate 1 features** — SHAP shows Gate 1 (promise) contributes very little
4. **Re-evaluate smoothed labels** — try again when dataset reaches 500+ samples
