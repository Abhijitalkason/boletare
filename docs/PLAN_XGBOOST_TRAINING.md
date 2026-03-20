# Plan: XGBoost Model Training & Evaluation (Step 6 & 7)

## Context

The training data pipeline (Steps 1-5) is complete. The prediction engine is 100% rule-based (3-gate convergence scoring with hardcoded thresholds). The feature_builder.py was designed from day 1 "for XGBoost calibration (Phase 3)" — the architecture is ready for ML integration.

**Current state:**
- **108 samples** (36 positive, 72 negative) in `data/training/training_set.npz`
- **22-dim feature vectors** — but features 18-21 are constant 0.5 placeholders → train on 18 features
- **Labels:** 34 approximate-positive (0.65) + 2 exact-positive (0.85) + 72 negative (0.0)
- **Rule-based baseline:** `compute_convergence()` maps weighted gate sum to ConfidenceLevel via thresholds (HIGH>=2.5, MEDIUM>=1.5, LOW>=0.5)
- **MLflow experiment:** `"jyotish-training"` (already used by steps 04, 05)

**Goals:**
1. Validate that the 18 features contain real predictive signal
2. SHAP feature importance — which gates/features matter most?
3. Baseline comparison — does XGBoost beat rule-based convergence scoring?
4. Establish metrics before growing the dataset

---

## Zen Review Findings (applied)

| # | Severity | Issue | Resolution |
|---|----------|-------|-----------|
| 1 | HIGH | Don't binarize smoothed labels | Feed 0.85/0.65/0.0 directly — XGBoost `binary:logistic` handles [0,1] |
| 2 | HIGH | Drop constant features 18-21 | Train on 18 features (indices 0-17) |
| 3 | HIGH | Add scikit-learn to deps | `scikit-learn>=1.4` |
| 4 | MED | `scale_pos_weight=2` may overcompensate with smoothed labels | **Train both ways** — with and without, compare CV metrics, pick better |
| 5 | MED | Step 6 saves CV predictions to disk | `models/cv_predictions.npz` for Step 7 |
| 6 | MED | Add PR-AUC | More informative than ROC-AUC for imbalanced data |
| 7 | MED | scikit-learn + matplotlib go in `ml` dep group, not `training` | Place alongside xgboost and shap |
| 8 | MED | `models/` directory needs `.gitignore` | Add `models/` to project `.gitignore` |
| 9 | LOW | Add `random_state=42` to StratifiedKFold | Reproducibility |

---

## Step 6: Train XGBoost Model

**Create:** `scripts/training/06_train_model.py`

### Input
- `data/training/training_set.npz` → X (108, 22), y (108,)

### Processing

1. **Load data:** `np.load("training_set.npz")` → X, y
2. **Drop features 18-21:** `X = X[:, :18]` → shape becomes (108, 18)
3. **Keep smoothed labels as-is** — no binarization (XGBoost handles continuous [0,1])
4. **Create binary labels for stratification only:** `y_binary = (y > 0.5).astype(int)`
5. **Stratified 5-Fold CV** (`StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`):
   - Each fold: train on ~86 samples, predict on ~22 samples
   - Collect out-of-fold predictions (probabilities) for all 108 samples
   - Compute per-fold metrics: accuracy, precision, recall, F1, ROC-AUC, PR-AUC
6. **Train final model on all 108 samples** (for SHAP + production saving)
7. **Save outputs:**
   - `models/xgboost_v1.json` — XGBoost model (native JSON format)
   - `models/cv_predictions.npz` — y_true, y_pred_binary, y_pred_proba (for Step 7)
   - `models/feature_names.json` — 18 feature names for SHAP labeling
8. **Log to MLflow:** params, CV metrics (mean +/- std), model artifact

### XGBoost Hyperparameters

```python
params = {
    "objective": "binary:logistic",
    "eval_metric": "logloss",
    "max_depth": 3,              # shallow — prevent overfitting on 108 samples
    "n_estimators": 50,          # few trees
    "learning_rate": 0.1,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "min_child_weight": 3,       # prevent splits on tiny groups
    "random_state": 42,
}
```

### scale_pos_weight Sensitivity Test

Zen flagged that `scale_pos_weight=2` may overcompensate with smoothed labels (0.65/0.85 are already softer than 1.0). The script will:
1. Run CV with `scale_pos_weight=1` (default, no adjustment)
2. Run CV with `scale_pos_weight=2` (imbalance compensation)
3. Compare F1 scores, pick the better configuration
4. Log both to MLflow for transparency

### Feature Names (for SHAP labels)

```python
FEATURE_NAMES = [
    "g1_lord_dignity",        # 0
    "g1_occupant_score",      # 1
    "g1_navamsha_score",      # 2
    "g1_sav_normalized",      # 3
    "g1_overall_score",       # 4
    "g2_mahadasha_score",     # 5
    "g2_antardasha_score",    # 6
    "g2_overall_score",       # 7
    "g2_connection_count",    # 8
    "g3_overall_score",       # 9
    "g3_active_months_ratio", # 10
    "g3_peak_bav_score",      # 11
    "convergence_normalized", # 12
    "birth_time_tier",        # 13
    "lagna_mode",             # 14
    "dasha_boundary",         # 15
    "dasha_ambiguous",        # 16
    "is_retrospective",       # 17
]
```

### Output Files

```
models/xgboost_v1.json      — saved model
models/cv_predictions.npz   — out-of-fold predictions (y_true, y_pred, y_prob)
models/feature_names.json   — 18 feature names
```

---

## Step 7: Evaluate Model

**Create:** `scripts/training/07_evaluate_model.py`

### Input
- `models/cv_predictions.npz` — from Step 6
- `models/xgboost_v1.json` — final model (for SHAP)
- `data/training/training_set.npz` — features (for SHAP + baseline)
- `models/feature_names.json` — feature labels

### Processing

#### A. Confusion Matrix
- Use CV predictions (binary: threshold 0.5 on probabilities)
- Plot heatmap with TP/FP/TN/FN counts
- Save: `models/confusion_matrix.png`

#### B. Classification Report
- Precision, recall, F1-score per class
- Save: `models/classification_report.txt`

#### C. ROC Curve + PR Curve
- ROC-AUC: overall discrimination
- PR-AUC: better for 1:2 imbalanced data
- Plot both curves on single figure
- Save: `models/roc_pr_curves.png`

#### D. SHAP Feature Importance
- Load final model (trained on all data)
- `shap.TreeExplainer(model)` → SHAP values for all 108 samples
- Bar plot: mean |SHAP value| per feature, labeled with feature names
- Save: `models/feature_importance.png`

#### E. Rule-Based Baseline Comparison
- **Naive baseline:** always predict "negative" = 66.7% accuracy (72/108)
- **Convergence baseline:** use feature 12 (convergence_normalized) with threshold sweep
  - Try thresholds 0.1 to 0.9, find best accuracy
- **XGBoost accuracy** from CV
- Report: "XGBoost: X% vs Convergence: Y% vs Naive: 66.7%"
- Save: `models/evaluation_report.json`

### Output Files

```
models/confusion_matrix.png       — confusion matrix heatmap
models/feature_importance.png     — SHAP bar plot
models/roc_pr_curves.png          — ROC + PR curves
models/classification_report.txt  — per-class precision/recall/F1
models/evaluation_report.json     — all metrics + baseline comparison
```

### MLflow Logging
- Metrics: TP, FP, TN, FN, ROC-AUC, PR-AUC, baseline accuracies
- Artifacts: all 4 plots + 2 reports

---

## Pipeline Integration

### Modify: `scripts/training/pipeline_flow.py`

Add two new Prefect tasks following existing pattern:

```python
@task
def train_model(training_set_path: Path) -> Path:
    mod = importlib.import_module("06_train_model")
    result = mod.main()
    if result != 0:
        raise RuntimeError("06_train_model failed")
    return mod.OUTPUT_MODEL

@task
def evaluate_model(model_path: Path) -> Path:
    mod = importlib.import_module("07_evaluate_model")
    result = mod.main()
    if result != 0:
        raise RuntimeError("07_evaluate_model failed")
    return mod.OUTPUT_REPORT

@flow(name="training-pipeline", log_prints=True)
def training_pipeline():
    ocr = download_ocr()
    parsed = parse_horoscopes(ocr)
    validated = validate_data(parsed)
    features = generate_features(validated)
    training_set = build_training_set(features)
    model = train_model(training_set)       # NEW
    evaluate_model(model)                    # NEW
```

### Modify: `scripts/training/run_pipeline.py`

Add to STEPS list:

```python
STEPS = [
    ("01_download_ocr.py", "Download OCR text from Archive.org"),
    ("02_parse_horoscopes.py", "Parse horoscopes into structured JSON"),
    ("03_validate_data.py", "Validate extracted data quality"),
    ("04_generate_features.py", "Generate 22-dim feature vectors"),
    ("05_build_training_set.py", "Build XGBoost training set"),
    ("06_train_model.py", "Train XGBoost model with 5-fold CV"),        # NEW
    ("07_evaluate_model.py", "Evaluate model and generate reports"),     # NEW
]
```

---

## Dependencies

### Add to `pyproject.toml` `[project.optional-dependencies.ml]` group:

```toml
ml = [
    "xgboost>=2.0.0",       # already present
    "shap>=0.45.0",          # already present
    "scikit-learn>=1.4",     # NEW — CV, metrics, confusion matrix
    "matplotlib>=3.8",       # NEW — plots
]
```

**Install:** `pip install xgboost scikit-learn shap matplotlib`

---

## Files Summary

| Action | File | What Changes |
|--------|------|-------------|
| Create | `scripts/training/06_train_model.py` | XGBoost training: load data, drop features 18-21, 5-fold CV, save model + CV predictions |
| Create | `scripts/training/07_evaluate_model.py` | Evaluation: confusion matrix, SHAP, ROC/PR curves, baseline comparison |
| Modify | `scripts/training/pipeline_flow.py` | Add `train_model` and `evaluate_model` Prefect tasks to flow |
| Modify | `scripts/training/run_pipeline.py` | Add steps 06 and 07 to STEPS list |
| Modify | `pyproject.toml` | Add `scikit-learn>=1.4`, `matplotlib>=3.8` to `ml` optional deps |
| Modify | `.gitignore` | Add `models/` to ignore model artifacts and plots |

---

## What to Expect

**Realistic expectations with 108 samples:**
- Accuracy: 65-80% (high variance between folds)
- Key question: does XGBoost beat naive baseline (66.7%)?
  - **YES** → features have real predictive signal, grow dataset for better results
  - **NO** → features need rework before adding more data
- SHAP will reveal: are Gate 2 (timing) features more important than Gate 1 (promise)?
- Quality flags (13-17) may or may not contribute — SHAP will tell us

---

## Future: Production Integration (NOT in this plan)

After Step 7 confirms the model works, the integration point is clear:

**File:** `src/jyotish_ai/services/orchestrator.py` (lines 123-130)

```python
# Current: threshold-based
convergence_score, confidence_level = compute_convergence(gate1, gate2, gate3)

# Future: XGBoost-based (behind feature flag)
if settings.use_xgboost_confidence:
    confidence_level = predict_from_xgboost(feature_vector)
```

This is Phase 3 work — only after we're confident in the model.

---

## Verification

```bash
# 1. Install dependencies
pip install xgboost scikit-learn shap matplotlib

# 2. Run training
python scripts/training/06_train_model.py
# Expected: "Model saved to models/xgboost_v1.json"
# Expected: "CV Accuracy: 0.XX +/- 0.XX"

# 3. Run evaluation
python scripts/training/07_evaluate_model.py
# Expected: 5 output files in models/

# 4. Check outputs
ls models/
cat models/classification_report.txt
cat models/evaluation_report.json

# 5. View plots
open models/confusion_matrix.png
open models/feature_importance.png
open models/roc_pr_curves.png

# 6. MLflow dashboard
mlflow ui
# Open http://localhost:5000 → see training + evaluation runs
```

---

## Execution Order

```
Install deps → Step 6 (train) → Step 7 (evaluate) → Review results → Decide next steps
```
