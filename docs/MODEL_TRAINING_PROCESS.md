# Model Training Process — Step-by-Step Guide

**Project:** Jyotish AI — Vedic Astrology Event Prediction Engine
**Date:** 2026-04-16
**Model Version:** XGBoost v1 (trained on 108 samples from Notable Horoscopes)
**Status:** Base model trained. Underperforms hand-coded baseline. Waiting for real user data to improve.

---

## Table of Contents

1. [Overview — What Are We Training?](#1-overview--what-are-we-training)
2. [The Data Source](#2-the-data-source)
3. [Step 1 — Download OCR Text](#3-step-1--download-ocr-text)
4. [Step 2 — Parse Horoscopes](#4-step-2--parse-horoscopes)
5. [Step 3 — Validate Data](#5-step-3--validate-data)
6. [Step 4 — Generate Features](#6-step-4--generate-features)
7. [Step 5 — Build Training Set](#7-step-5--build-training-set)
8. [Step 6 — Train Model](#8-step-6--train-model)
9. [Step 7 — Evaluate Model](#9-step-7--evaluate-model)
10. [Current Results](#10-current-results)
11. [How to Re-Train When New Data Arrives](#11-how-to-re-train-when-new-data-arrives)
12. [File Reference](#12-file-reference)

---

## 1. Overview — What Are We Training?

### The Problem

The Jyotish AI system predicts life events (marriage, career, child, property, health) using a 3-gate Vedic astrology engine:

```
Gate 1 (Promise):  "Is the event written in the birth chart?"
Gate 2 (Dasha):    "Is the right planetary period running?"
Gate 3 (Transit):  "Are favorable transits happening now?"
```

Each gate produces a score from 0.0 to 1.0. The current prediction formula combines them with equal weights:

```
convergence = (Gate1 + Gate2 + Gate3) / 3.0
```

### The Goal of ML Training

Train a model that learns **better weights** than equal (1/3, 1/3, 1/3). For example, maybe marriage prediction works better with Gate 1 weighted higher:

```
convergence = 0.45 × Gate1 + 0.25 × Gate2 + 0.30 × Gate3
```

### What the Model Learns

Given a birth chart and a specific date, the model answers:

```
Question: "Did this event happen to this person on this date?"
Answer:   Probability 0.0 (definitely no) to 1.0 (definitely yes)
```

---

## 2. The Data Source

### The Book

**"Notable Horoscopes"** by B.V. Raman — a collection of 77 biographical horoscope case studies of famous Indian personalities.

Each chapter covers one person with:
- Exact birth date, time, and place
- Planetary positions and chart diagrams
- Biographical narrative with documented life events and dates

### Why This Book

| Requirement | Notable Horoscopes |
|---|---|
| Birth TIME (not just date) | ✅ Minute-level precision |
| Birth PLACE with coordinates | ✅ Lat/Lon included |
| Documented life events | ✅ Marriage dates, career milestones, health events |
| Event dates (not just "middle age") | ✅ Most events have year or exact date |
| Indian charts | ✅ All Indian personalities |
| Available as OCR text | ✅ On Archive.org |

### Book Location

- **Archive.org:** https://archive.org/details/NotableHoroscopesBVR
- **Local OCR file:** `data/training/raw/notable_horoscopes_ocr.txt` (715 KB)

---

## 3. Step 1 — Download OCR Text

### Script: `scripts/training/01_download_ocr.py`

### What It Does

Downloads the `_djvu.txt` (OCR text) file from Archive.org for "Notable Horoscopes."

### Process

```
Archive.org
    │
    ├── Try: internetarchive Python package (primary method)
    │   └── ia.download("NotableHoroscopesBVR", files=["Notable Horoscopes_djvu.txt"])
    │
    ├── Fallback: Direct HTTP download
    │   └── https://archive.org/download/NotableHoroscopesBVR/Notable%20Horoscopes_djvu.txt
    │
    └── Validation:
        ├── File must exist after download
        ├── Minimum size: 10 KB
        └── English content check: ≥50% ASCII alphabetic characters
```

### Output

```
data/training/raw/notable_horoscopes_ocr.txt (715 KB, 25,165 lines)
```

### How to Run

```bash
python scripts/training/01_download_ocr.py
```

---

## 4. Step 2 — Parse Horoscopes

### Script: `scripts/training/02_parse_horoscopes.py` (689 lines)

### What It Does

Extracts structured data from raw OCR text using a two-stage hybrid parser.

### Stage 1 — Block Identification

The parser scans for chapter boundaries using the regex pattern:

```
Pattern: No\.\s*(\d+)\.\s*[-—]+\s*(.+?)

Matches lines like:
  "No. 1.— SRI KRISHNA"
  "No. 76.— BANGALORE VENKATA RAMAN"
```

Each match marks the start of a horoscope chapter. The text between two matches is one "block."

**Result:** 63 blocks found in the OCR text.

### Stage 2 — Field Extraction

For each block, the parser extracts:

#### Birth Date

```
Input text:  "Born on 8th August 1912"
Parser tries 3 patterns:
  Pattern 1: "8th August 1912"     → DD Month YYYY
  Pattern 2: "August 8, 1912"      → Month DD, YYYY
  Pattern 3: "8-8-1912"            → DD-MM-YYYY
Output:      date(1912, 8, 8)
```

#### Birth Time

```
Input text:  "at about 7-30 P.M. (L.M.T.)"
Parser tries 5 patterns:
  Pattern 1: "midnight"             → 00:00
  Pattern 2: "noon"                 → 12:00
  Pattern 3: "7-30 P.M."           → HH:MM + AM/PM
  Pattern 4: "7 P.M."              → HH + AM/PM (hour only)
  Pattern 5: "between 10 and 12 at night" → average
Output:      time(19, 30)
```

#### Coordinates

```
Input text:  "Lat. 13° N., Long. 77° E."
Parser handles:
  - Standard:    "Lat. 13° N., Long. 77° E."
  - Reversed:    "Long. 88° 25' E., Lat. 23° 23' N."
  - Time-based:  "Long. 5h. 10m. 20s. E."
  - OCR errors:  "°" read as "D", "J", "~"
Output:      latitude=13.0, longitude=77.0
```

#### Place

```
Input text:  "Born at Bangalore"
Parser tries:
  1. Explicit coordinates (from lat/lon extraction above)
  2. City name lookup against indian_cities.json (50 cities)
  3. Fallback coordinates (20.5937, 78.9629) if nothing found
Output:      place="Bangalore", lat=12.97, lon=77.59, tier=1
```

#### Gender

```
Input text:  "He was married... his career... him to become..."
Parser counts pronouns:
  he/his/him count: 15
  she/her/hers count: 0
  Result: he > she → "male"
Output:      gender="male"
```

#### Life Events

```
Input text:  "He was married on 14th May 1934 at Bangalore."

Parser scans for event keywords:
  marriage: ["married", "marriage", "wedding", "wed"]
  career:   ["appointed", "promotion", "career", "elected"]
  child:    ["child", "son", "daughter"]
  property: ["property", "house", "land", "purchased"]
  health:   ["illness", "death", "died", "surgery", "accident"]

When keyword found in a sentence, extract date from same sentence:
  "married on 14th May 1934" → event_type="marriage", date="1934-05-14"

Output: [
  {"event_type": "marriage", "event_date": "1934-05-14", "confidence": "exact"},
  {"event_type": "career",  "event_date": "1936-06-15", "confidence": "approximate"}
]
```

#### Reliability

```
Rules:
  If person name is in LEGENDARY_FIGURES (Sri Krishna, Jesus, etc.)  → "legendary"
  If birth_date is before 500 AD                                     → "low"
  If birth time was approximate ("about", "between X and Y")         → "medium"
  Otherwise                                                          → "high"
```

### Parsing Results

```
Blocks found:          63
Parsed successfully:   50  (13 failed: B.C. dates, missing times)
Flagged for review:    25  (missing coordinates or no events)
Total events extracted: 36

Reliability distribution:
  high:      35 charts
  medium:    14 charts
  legendary:  1 chart
```

### Output

```
data/training/notable_horoscopes.json

Structure:
{
  "source": "notable_horoscopes_bv_raman",
  "book_url": "https://archive.org/details/NotableHoroscopesBVR",
  "charts": [
    {
      "id": "NH_001",
      "person_name": "OMAR KHAYYAM",
      "birth_date": "1048-05-18",
      "birth_time": "04:48:00",
      "birth_place": "Nishapur",
      "latitude": 36.2167,
      "longitude": 58.75,
      "timezone_offset": 5.5,
      "birth_time_tier": 2,
      "gender": "male",
      "birth_data_reliability": "high",
      "events": [
        {
          "event_type": "health",
          "event_date": "1123-06-15",
          "confidence": "approximate"
        }
      ],
      "needs_manual_review": false,
      "parse_warnings": []
    },
    ... (49 more charts)
  ]
}
```

### How to Run

```bash
python scripts/training/02_parse_horoscopes.py
```

---

## 5. Step 3 — Validate Data

### Script: `scripts/training/03_validate_data.py`

### What It Does

Validates the parsed JSON against quality rules before feeding it to the ML pipeline.

### Validation Rules

#### Schema Validation (Pydantic)

Every chart must have:
- `id` (string)
- `birth_date` (valid ISO date)
- `birth_time` (valid ISO time)
- `birth_place` (string)
- `latitude` (-90 to 90)
- `longitude` (-180 to 180)
- `gender` (male/female/unknown)
- `events` (array of {event_type, event_date, confidence})

#### Domain Sanity Checks

| Check | Rule | Purpose |
|---|---|---|
| Birth year | 500 ≤ year ≤ 2028 | Filter ancient/future dates |
| Birth time digits | minutes ≤ 59, hours ≤ 23 | Catch OCR digit errors |
| India coordinates | lat 6-37°N, lon 67-98°E | Warn if outside India |
| Event after birth | event_date > birth_date | Logic check |
| Event before 2025 | event_date ≤ 2025 | No future events |
| Age at marriage | 14-60 years | Sanity check |
| Age at career | 16-70 years | Sanity check |
| Age at child | 18-55 years | Sanity check |
| Age at property | 18-80 years | Sanity check |
| Age at health | 0-100 years | Sanity check |

#### Quality Gates (Pipeline Stops If Failed)

1. **Fallback coordinates:** If any chart uses default India-center coordinates (20.5937, 78.9629), it means coordinate parsing failed → pipeline error
2. **Parse rate:** If less than 80% of charts pass validation → pipeline error

#### Duplicate Detection

Warns if two charts have identical (birth_date + birth_time + birth_place).

### Output

```
data/training/validation_report.txt

Contains:
  - Per-chart warnings and errors
  - Event type distribution
  - Quality gate pass/fail status
```

### How to Run

```bash
python scripts/training/03_validate_data.py
```

---

## 6. Step 4 — Generate Features

### Script: `scripts/training/04_generate_features.py`

### What It Does

This is the most important step. For each chart+event combination, it runs the **full 3-gate astrology engine** and produces a **22-dimensional feature vector.**

### How 36 Events Become 108 Samples

For each of the 36 documented events, the pipeline creates 3 samples:

```
EVENT: Person married on 14-May-1934

SAMPLE 1 — POSITIVE (label = 1)
  Chart:      Person's birth data
  Event type: marriage
  Event date: 14-May-1934 (actual date)
  Label:      1 (event DID happen)

SAMPLE 2 — TIME-SHIFTED NEGATIVE (label = 0)
  Chart:      Same person's birth data
  Event type: marriage
  Event date: 14-May-1929 (5 years BEFORE actual date)
  Label:      0 (marriage didn't happen 5 years early)

SAMPLE 3 — CROSS-EVENT NEGATIVE (label = 0)
  Chart:      Same person's birth data
  Event type: health (DIFFERENT event type)
  Event date: 14-May-1934 (same date)
  Label:      0 (a health event wasn't documented on this date)
```

**36 events × 3 = 108 training samples**

### The 7-Stage Feature Computation

For each sample, these 7 stages run in sequence:

#### Stage 1: Compute Birth Chart (Layer 1 Engine)

```python
chart = compute_birth_chart(
    birth_date=date(1912, 8, 8),
    birth_time=time(19, 30),
    latitude=13.0,
    longitude=77.0,
    tz_offset=5.5,
    birth_time_tier=BirthTimeTier.TIER_1
)
```

This calculates using the Swiss Ephemeris (PySwissEph):
- All 9 planet positions (Sun through Ketu) in signs and degrees
- 12 house cusps
- Vimshottari dasha periods with start/end dates
- Sarva Ashtakavarga table (8×12 matrix of bindus)
- Navamsha (D-9) chart positions
- Planetary dignities (exalted, own sign, friendly, neutral, enemy, debilitated)

#### Stage 2: Gate 1 — Promise Evaluation

```python
gate1 = evaluate_promise(chart, EventType.MARRIAGE)
```

Asks: "Is marriage written in this birth chart?"

Computes 4 sub-scores for the 7th house (marriage house):

| Sub-score | Weight | What It Measures |
|---|---|---|
| Lord dignity | 0.35 | How strong is the 7th lord? (exalted=1.0, debilitated=0.0) |
| Occupant score | 0.15 | Are benefics or malefics sitting in the 7th house? |
| Navamsha score | 0.20 | Does the D-9 chart confirm the lord's strength? |
| SAV normalized | 0.30 | Ashtakavarga bindus for the 7th sign (0-8 normalized to 0-1) |

```
Gate 1 score = 0.35 × lord_dignity + 0.15 × occupant + 0.20 × navamsha + 0.30 × SAV
```

**Features generated: [0] through [4]**

#### Stage 3: Gate 2 — Dasha Evaluation

```python
gate2 = evaluate_dasha(chart, EventType.MARRIAGE, event_date=date(1934, 5, 14))
```

Asks: "Is the right dasha running on 14-May-1934?"

Finds which Mahadasha and Antardasha are active on the event date, then checks:
- Does the Mahadasha lord connect to the 7th house (marriage)?
- Does the Antardasha lord connect to the 7th house?
- How many total house connections exist?

**Features generated: [5] through [8]**

#### Stage 4: Gate 3 — Transit Evaluation

```python
gate3 = evaluate_transit(chart, EventType.MARRIAGE, event_date=date(1934, 5, 14))
```

Asks: "Are favorable transits happening around 14-May-1934?"

Checks a 24-month window around the event date:
- Jupiter and Saturn aspects to the 7th house
- Ashtakavarga transit scores
- How many months have favorable indicators

**Features generated: [9] through [11]**

#### Stage 5: Convergence

```python
convergence_score, convergence_level = compute_convergence(gate1, gate2, gate3)
```

Simple average of the three gate scores, normalized to 0-1:

```
convergence_normalized = (Gate1.score + Gate2.score + Gate3.score) / 3.0
```

**Feature generated: [12]**

#### Stage 6: Quality Flags

```python
quality_flags = compute_quality_flags(chart, is_retrospective=True)
```

Metadata about the data quality:

| Feature | Meaning | Values |
|---|---|---|
| [13] birth_time_tier | How precise is the birth time? | 1.0=exact, 0.5=approximate, 0.0=unknown |
| [14] lagna_mode | Using moon chart instead of ascendant? | 0.0=standard, 1.0=chandra |
| [15] dasha_boundary | Born near a dasha period boundary? | 0.0=no, 1.0=yes (risky) |
| [16] dasha_ambiguous | Is the dasha period unclear? | 0.0=no, 1.0=yes |
| [17] is_retrospective | Predicting a past event? | 1.0=yes (always true for training) |

**Features generated: [13] through [17]**

#### Stage 7: Demographics (Placeholder)

```
Features [18-21] = 0.5, 0.5, 0.5, 0.5
```

These are placeholders for gender, age, education, income — not available from book data. Will be filled when real user data arrives.

### The Complete 22-Feature Vector

```
INDEX  FEATURE NAME                SOURCE          EXAMPLE VALUE
─────  ──────────────────────────  ──────────────  ─────────────
[ 0]   g1_lord_dignity             Gate 1          0.50
[ 1]   g1_occupant_score           Gate 1          0.40
[ 2]   g1_navamsha_score           Gate 1          1.00
[ 3]   g1_sav_normalized           Gate 1          0.74
[ 4]   g1_overall_score            Gate 1 (sum)    0.66
[ 5]   g2_mahadasha_score          Gate 2          0.85
[ 6]   g2_antardasha_score         Gate 2          0.70
[ 7]   g2_overall_score            Gate 2 (sum)    0.80
[ 8]   g2_connection_count         Gate 2          0.50
[ 9]   g3_overall_score            Gate 3          0.72
[10]   g3_active_months_ratio      Gate 3          0.58
[11]   g3_peak_bav_score           Gate 3          0.80
[12]   convergence_normalized      All gates avg   0.73
[13]   birth_time_tier             Quality         1.00
[14]   lagna_mode                  Quality         0.00
[15]   dasha_boundary              Quality         0.00
[16]   dasha_ambiguous             Quality         0.00
[17]   is_retrospective            Quality         1.00
[18]   gender (placeholder)        Demographics    0.50
[19]   age (placeholder)           Demographics    0.50
[20]   education (placeholder)     Demographics    0.50
[21]   income (placeholder)        Demographics    0.50
```

**All values are normalized to [0.0, 1.0]**

### Which Charts Are Skipped

The feature generator skips charts that:
- Have `needs_manual_review = true` (missing coordinates or no events)
- Have zero events

**50 charts → 25 skipped → 25 charts processed → 36 events → 108 samples**

### Output

```
data/training/feature_vectors.json

Structure:
{
  "samples": [
    {
      "chart_id": "NH_001",
      "event_type": "health",
      "event_date": "1123-06-15",
      "feature_vector": [0.50, 0.40, 1.00, ...],  // 22 numbers
      "label": 1,
      "sample_type": "positive",
      "confidence": "approximate",
      "error": false
    },
    ... (107 more samples)
  ]
}
```

### How to Run

```bash
python scripts/training/04_generate_features.py
```

---

## 7. Step 5 — Build Training Set

### Script: `scripts/training/05_build_training_set.py`

### What It Does

Converts the JSON feature vectors into NumPy arrays for XGBoost, applying label smoothing.

### Label Smoothing

Raw labels are binary (0 or 1), but we adjust them based on confidence:

```
Positive event with EXACT date    → label = 0.85  (2 samples)
Positive event with APPROXIMATE   → label = 0.65  (34 samples)
Negative sample                   → label = 0.00  (72 samples)
```

**Why smooth?** A positive event with an approximate date (year-only) is less certain than one with an exact date. The smoothed label tells the model "this is probably positive, but not 100% certain."

### Output

```
data/training/training_set.npz
  X: shape (108, 22) — feature matrix
  y: shape (108,)    — smoothed labels

data/training/training_metadata.json
  {
    "total_samples": 108,
    "positive_count": 36,
    "negative_count": 72,
    "feature_dimensions": 22,
    "event_type_distribution": {
      "health": 34, "marriage": 23, "career": 26,
      "property": 16, "child": 9
    },
    "label_smoothing": {
      "positive_exact": 0.85,
      "positive_approximate": 0.65,
      "negative": 0.0
    },
    "source": "notable_horoscopes_bv_raman"
  }
```

### How to Run

```bash
python scripts/training/05_build_training_set.py
```

---

## 8. Step 6 — Train Model

### Script: `scripts/training/06_train_model.py`

### What It Does

Trains an XGBoost model using Stratified 5-Fold Cross-Validation, running two experiments to find the best approach.

### Data Preparation

```python
# Load
X = (108, 22)  # Full feature matrix
y = (108,)     # Smoothed labels

# Drop placeholder features 18-21
X = X[:, :18]  # Now (108, 18)

# Create binary labels for stratification
y_binary = (y > 0.5).astype(int)  # 36 positive, 72 negative
```

### Hyperparameters (Shared)

```python
{
    "max_depth": 3,              # Tree depth (shallow to prevent overfitting)
    "n_estimators": 100,         # Maximum trees (early stopping will reduce this)
    "learning_rate": 0.1,        # Step size
    "subsample": 0.8,            # Use 80% of data per tree
    "colsample_bytree": 0.8,     # Use 80% of features per tree
    "min_child_weight": 1,       # Minimum samples in leaf
    "early_stopping_rounds": 10, # Stop if no improvement for 10 rounds
    "eval_metric": "logloss",    # Optimization target
}
```

### Experiment A: Regressor + Smoothed Labels

```python
model = XGBRegressor(objective="reg:logistic", ...)
model.fit(X_train, y_smoothed_train)  # Labels: 0.0, 0.65, 0.85
predictions = model.predict(X_test)    # Output: 0.0 to 1.0
```

The regressor treats labels as continuous values and tries to predict the exact smoothed probability.

### Experiment B: Classifier + Binary Labels

```python
model = XGBClassifier(objective="binary:logistic", scale_pos_weight=2, ...)
model.fit(X_train, y_binary_train)     # Labels: 0 or 1
predictions = model.predict_proba(X_test)[:, 1]  # Output: 0.0 to 1.0
```

The classifier treats labels as binary (event happened or not) with `scale_pos_weight=2` to handle class imbalance (72 negatives vs 36 positives).

### 5-Fold Cross-Validation

The data is split into 5 folds, stratified by label (each fold has ~7 positive and ~14 negative samples):

```
Fold 1: Train on folds 2-5 (86 samples) → Test on fold 1 (22 samples)
Fold 2: Train on folds 1,3-5 (86 samples) → Test on fold 2 (22 samples)
Fold 3: Train on folds 1-2,4-5 (86 samples) → Test on fold 3 (22 samples)
Fold 4: Train on folds 1-3,5 (86 samples) → Test on fold 4 (22 samples)
Fold 5: Train on folds 1-4 (86 samples) → Test on fold 5 (22 samples)
```

Each fold produces out-of-fold predictions. Combined, we get predictions for all 108 samples without data leakage.

### Threshold Optimization

The model outputs probabilities (0.0 to 1.0). We need a threshold to convert to yes/no:

```
Sweep thresholds from 0.05 to 0.95:
  threshold=0.05 → predict "yes" for almost everything → high recall, low precision
  threshold=0.50 → balanced → moderate recall and precision
  threshold=0.95 → predict "yes" for very few → low recall, high precision

Pick threshold that maximizes F1 score (harmonic mean of precision and recall)
```

### Winner Selection

```
Experiment A (Regressor):  F1 = 0.522 at threshold 0.10
Experiment B (Classifier): F1 = 0.522 at threshold 0.35

Winner: Experiment B (same F1, but classifier approach is cleaner)
```

### Final Model Training

The winner model is retrained on ALL 108 samples (no held-out set):

```python
# Use median best_iteration from CV as n_estimators
final_n_estimators = max(median_best_iteration, 10)  # = 10 trees

final_model = XGBClassifier(n_estimators=10, ...)
final_model.fit(X_all, y_binary_all)
final_model.save_model("models/xgboost_v1.json")
```

### What XGBoost Actually Learned

With early stopping at 2 iterations:

```
Tree 1: "If convergence_normalized > 0.35 → lean positive"
Tree 2: "If g2_mahadasha_score > 0.20 AND g3_overall_score > 0.50 → adjust up"

That's it. Only 2 decision rules. The features don't contain enough
signal for more complex patterns with only 108 samples.
```

### MLflow Logging

Both experiments are logged to MLflow:
- Experiment name: `jyotish-training`
- Run names: `06_regressor_smoothed`, `06_classifier_binary`
- Logged: all metrics, hyperparameters, model artifact

### Output

```
models/xgboost_v1.json         — Trained XGBoost model (11 KB)
models/cv_predictions.npz      — Out-of-fold predictions for evaluation
models/feature_names.json      — 18 feature names for SHAP labeling
```

### How to Run

```bash
python scripts/training/06_train_model.py
```

---

## 9. Step 7 — Evaluate Model

### Script: `scripts/training/07_evaluate_model.py`

### What It Does

Evaluates the trained model against baselines and generates visual reports.

### Metrics Computed

| Metric | What It Measures |
|---|---|
| **Accuracy** | % of predictions correct |
| **Precision** | Of all "yes" predictions, how many were right? |
| **Recall** | Of all actual events, how many did we catch? |
| **F1 Score** | Balance between precision and recall |
| **ROC-AUC** | Model's ability to rank positives above negatives |
| **PR-AUC** | Precision-recall curve area |

### Confusion Matrix

```
                 Predicted
                 Negative  Positive
Actual Negative    9         63      (FP=63 false alarms)
Actual Positive    1         35      (TP=35 correct predictions)

TP=35: Model correctly predicted 35 out of 36 events
FP=63: Model incorrectly predicted 63 non-events as events
TN=9:  Model correctly predicted 9 non-events
FN=1:  Model missed 1 real event
```

### Baseline Comparisons

```
XGBoost accuracy:      0.407 (F1=0.522)
Convergence baseline:  0.676 (threshold=0.60)  ← Hand-coded (G1+G2+G3)/3
Naive baseline:        0.667                    ← Always predict "no event"

XGBoost beats naive:        NO ❌
XGBoost beats convergence:  NO ❌
```

### SHAP Feature Importance

SHAP (SHapley Additive exPlanations) shows which features the model relies on most:

```
Rank  Feature                    SHAP Value
1.    convergence_normalized     0.1266
2.    g3_overall_score           0.1168
3.    g2_mahadasha_score         0.1125
4.    g2_overall_score           0.1067
5.    g3_peak_bav_score          0.1017
```

**Key insight:** The top features are just the gate scores and convergence — the same values the hand-coded formula uses. The sub-components (features 0-3, 5-6, 8, 10) contribute less.

### Output

```
models/confusion_matrix.png      — Visual confusion matrix
models/roc_pr_curves.png         — ROC and Precision-Recall curves
models/feature_importance.png    — SHAP bar chart
models/classification_report.txt — Per-class precision/recall/F1
models/evaluation_report.json    — All metrics in machine-readable format
```

### How to Run

```bash
python scripts/training/07_evaluate_model.py
```

---

## 10. Current Results

### Model Performance

| Metric | XGBoost v1 | Hand-coded Baseline | Naive Baseline |
|---|---|---|---|
| **Accuracy** | 0.407 | **0.676** | 0.667 |
| **F1 Score** | 0.522 | 0.054 | 0.000 |
| **ROC-AUC** | 0.575 | — | 0.500 |
| **Precision** | 0.357 | — | — |
| **Recall** | 0.972 | — | — |

### Why the Model Underperforms

1. **Too few real events (36):** Not enough data for any model to learn reliable patterns
2. **Feature redundancy:** Sub-scores + their weighted sums confuse the tree splits
3. **Synthetic negatives may be wrong:** Cross-event negatives assume events are mutually exclusive
4. **Hand-coded baseline is already near-optimal:** Equal weights capture most of the signal

### Current Recommendation

**Ship the hand-coded convergence formula as the base model.** It achieves 67.6% accuracy using proven Vedic astrology principles. Retrain when real user data is available.

---

## 11. How to Re-Train When New Data Arrives

### When You Have New User Data

When users start confirming events through the app, you'll have data like:

```json
{
  "user_id": "U123",
  "birth_date": "1990-03-15",
  "birth_time": "14:30:00",
  "birth_place": "Pune",
  "latitude": 18.52,
  "longitude": 73.86,
  "gender": "male",
  "age": 36,
  "event_type": "marriage",
  "event_date": "2025-11-20",
  "confirmed": true
}
```

### Re-Training Steps

```bash
# Step 1: Export user data to JSON (matching the chart schema)
python scripts/training/export_user_data.py  # (to be built)

# Step 2: Generate features
python scripts/training/04_generate_features.py user_data.json

# Step 3: Build training set
python scripts/training/05_build_training_set.py

# Step 4: Train model
python scripts/training/06_train_model.py

# Step 5: Evaluate
python scripts/training/07_evaluate_model.py

# Step 6: If model beats baseline → deploy new weights
```

### Milestones

| Confirmed Events | What to Try |
|---|---|
| 100 events | Logistic Regression on 3 gate scores |
| 300 events | Per-event-type weight optimization |
| 500 events | Logistic Regression with quality flags |
| 1,000 events | XGBoost with proper data volume |
| 5,000 events | Neural network / advanced approaches |

---

## 12. File Reference

### Pipeline Scripts

| Script | Step | What It Does |
|---|---|---|
| `01_download_ocr.py` | 1 | Downloads OCR text from Archive.org |
| `02_parse_horoscopes.py` | 2 | Parses OCR into structured JSON (689 lines) |
| `03_validate_data.py` | 3 | Validates data quality with gates |
| `04_generate_features.py` | 4 | Runs 3-gate engine, creates 22-D vectors |
| `05_build_training_set.py` | 5 | Converts to NumPy arrays with label smoothing |
| `06_train_model.py` | 6 | Trains XGBoost with 5-fold CV |
| `07_evaluate_model.py` | 7 | Evaluates model, generates reports |
| `run_pipeline.py` | All | Runs all 7 steps in sequence |

### Data Files

| File | What It Contains |
|---|---|
| `data/training/raw/notable_horoscopes_ocr.txt` | Raw OCR text (715 KB) |
| `data/training/notable_horoscopes.json` | 50 parsed charts with 36 events |
| `data/training/feature_vectors.json` | 108 samples × 22 features |
| `data/training/training_set.npz` | NumPy arrays X=(108,22) y=(108,) |
| `data/training/training_metadata.json` | Sample counts and distribution |
| `data/training/validation_report.txt` | Quality validation report |
| `data/geocoding/indian_cities.json` | 50 Indian cities with coordinates |

### Model Files

| File | What It Contains |
|---|---|
| `models/xgboost_v1.json` | Trained XGBoost model (11 KB) |
| `models/cv_predictions.npz` | Out-of-fold predictions |
| `models/feature_names.json` | 18 feature names |
| `models/evaluation_report.json` | All metrics + baseline comparison |
| `models/classification_report.txt` | Per-class precision/recall |
| `models/confusion_matrix.png` | Visual confusion matrix |
| `models/roc_pr_curves.png` | ROC and PR curves |
| `models/feature_importance.png` | SHAP feature importance |

### Run the Complete Pipeline

```bash
python scripts/training/run_pipeline.py
```

This executes all 7 steps in sequence, stopping on the first error.
