# Discussion Summary — ML Training Pipeline

## Table of Contents

1. [Pipeline Overview](#1-pipeline-overview)
2. [The 3-Gate Engine](#2-the-3-gate-engine)
3. [Gate 1: Promise — Deep Dive](#3-gate-1-promise--deep-dive)
4. [22-Dimensional Feature Vector](#4-22-dimensional-feature-vector)
5. [Positive and Negative Sample Generation](#5-positive-and-negative-sample-generation)
6. [Label Smoothing](#6-label-smoothing)
7. [ML Terminology Used](#7-ml-terminology-used)
8. [Production Pipeline (DVC + MLflow + Prefect)](#8-production-pipeline-dvc--mlflow--prefect)

---

## 1. Pipeline Overview

The training pipeline converts a book ("Notable Horoscopes" by B.V. Raman) into ML training data. It has 5 steps:

```
Step 1: Download OCR     → raw text from Archive.org
Step 2: Parse Horoscopes → structured JSON (25 charts, 36 events)
Step 3: Validate Data    → quality gate (blocks bad data)
Step 4: Generate Features → 22-dim vectors (108 samples)
Step 5: Build Training Set → numpy arrays for XGBoost
```

**Data flow:**
```
OCR Text → 25 Charts → 36 Events → 108 Samples → X(108,22) + y(108,)
                                     ↑
                        36 positive + 72 negative
```

**Key files:**
- `scripts/training/01_download_ocr.py` — downloads book OCR text
- `scripts/training/02_parse_horoscopes.py` — regex parsing of horoscope blocks
- `scripts/training/03_validate_data.py` — quality gate (coordinates, dates)
- `scripts/training/04_generate_features.py` — runs 3-gate engine, creates feature vectors
- `scripts/training/05_build_training_set.py` — converts to numpy, applies label smoothing
- `scripts/training/pipeline_flow.py` — Prefect orchestration (wraps all 5 steps)
- `scripts/training/run_pipeline.py` — simple fallback runner (no Prefect needed)

---

## 2. The 3-Gate Engine

The core prediction system is based on Vedic astrology (Jyotish). A life event is considered "promised" only if it passes through 3 sequential gates:

```
Gate 1: PROMISE → "Can it happen?"    (birth chart — static, lifelong)
Gate 2: DASHA   → "Is the timing right (long-term)?"  (planetary periods — years)
Gate 3: TRANSIT → "Is the timing right (short-term)?"  (current sky — months/weeks)
```

**Then:**
```
Gate 1 + Gate 2 + Gate 3
    → compute_convergence()    → single convergence score
    → compute_quality_flags()  → data quality indicators
    → build_feature_vector()   → 22-dimensional vector for XGBoost
```

**Analogy:**
1. **Promise** = "Is the seed planted?" (birth chart)
2. **Dasha** = "Is it the right season?" (planetary period)
3. **Transit** = "Is it raining today?" (current sky)

All three must align for an event to manifest — that's the core Jyotish principle.

**Key files:**
- `src/jyotish_ai/prediction/gate1_promise.py`
- `src/jyotish_ai/prediction/gate2_dasha.py`
- `src/jyotish_ai/prediction/gate3_transit.py`
- `src/jyotish_ai/prediction/convergence.py`
- `src/jyotish_ai/prediction/quality_flags.py`
- `src/jyotish_ai/prediction/feature_builder.py`

---

## 3. Gate 1: Promise — Deep Dive

Gate 1 answers: **"Is this event written in the birth chart?"**

If the birth chart doesn't show potential for an event, the pipeline short-circuits (returns INSUFFICIENT). No point checking timing if the event isn't even promised.

### Scoring Formula

```
Promise Score = 0.35 × Lord Dignity
             + 0.15 × Occupant Score
             + 0.20 × Navamsha Confirmation
             + 0.30 × SAV Score
```

**Threshold:** Score must be >= 0.3 to pass the gate.

### Sub-Score 1: House Lord Dignity (weight: 0.35)

Each event type maps to a house:

| Event | House | What it represents |
|-------|-------|--------------------|
| Marriage | 7th | Partnerships |
| Career | 10th | Profession, status |
| Child | 5th | Children, creativity |
| Property | 4th | Home, real estate |
| Health | 6th | Illness |

How strong is the lord of that house?

| Planet's Dignity | Score |
|-----------------|-------|
| Exalted | 1.0 |
| Moolatrikona | 0.85 |
| Own sign | 0.75 |
| Friendly sign | 0.5 |
| Neutral | 0.25 |
| Enemy sign | 0.125 |
| Debilitated | 0.0 |

**Example — Nehru's Marriage:**
- Ascendant = Aries, so 7th house = Libra, Lord = Venus
- If Venus is exalted (in Pisces) -> dignity = 1.0
- If Venus is debilitated (in Virgo) -> dignity = 0.0

### Sub-Score 2: Occupant Analysis (weight: 0.15)

Who is sitting in the event house?

- Start at 0.5 (neutral baseline)
- Each **benefic** (Jupiter, Venus, Moon, Mercury): **+0.15**
- Each **malefic** (Sun, Mars, Saturn, Rahu, Ketu): **-0.10**
- Empty house: stays at 0.5

**Example:**
- 7th house has Jupiter + Mars -> 0.5 + 0.15 - 0.10 = **0.55**
- 7th house has Saturn + Rahu -> 0.5 - 0.10 - 0.10 = **0.30**

### Sub-Score 3: Navamsha Confirmation (weight: 0.20)

The Navamsha (D-9) is a divisional chart — a "second opinion" on the birth chart.

| Condition | Score |
|-----------|-------|
| Event lord in **own sign** in navamsha | 1.0 |
| Event lord in **kendra/trikona** (houses 1,4,5,7,9,10) | 0.8 |
| Otherwise | 0.3 |

### Sub-Score 4: SAV — Sarva Ashtakavarga (weight: 0.30)

Ashtakavarga is a point-based system. SAV = total votes across all planets for a sign.

- **Range:** 18-37 bindus per sign
- **Normalization:** `(raw - 18) / 19`
- **Classical rule:** SAV >= 28 is favorable

**Example:** Libra has SAV = 30 -> (30-18)/19 = **0.63**

### Full Worked Example — Marriage Check

```
Person: Ascendant = Aries

7th house = Libra -> Lord = Venus

Sub-score 1: Venus is in Pisces (exalted)     -> 1.00
Sub-score 2: Jupiter in 7th house              -> 0.65
Sub-score 3: Venus in own sign in navamsha     -> 1.00
Sub-score 4: Libra SAV = 30 bindus             -> 0.63

Promise = 0.35 x 1.00 + 0.15 x 0.65 + 0.20 x 1.00 + 0.30 x 0.63
        = 0.35 + 0.097 + 0.20 + 0.189
        = 0.836

Score 0.84 >= 0.3 threshold -> GATE PASSED
-> Proceed to Gate 2 (Dasha)
```

---

## 4. 22-Dimensional Feature Vector

A **feature vector** is a list of numbers that describes something to a machine. Machines can't read text or understand astrology — they only understand numbers.

**Real-world analogy:**
```
Person: "Rahul, 28 years old, 5'10", 72 kg, earns 50K"
Feature vector: [28, 5.83, 72, 50000]
```

### Our 22 Features — Complete Layout

Each sample answers 22 questions, each scored 0.0 (worst) to 1.0 (best):

#### Features 0-4: Gate 1 — Promise (birth chart)

| # | Feature | What it measures |
|---|---------|-----------------|
| 0 | lord_dignity | How strong is the event house lord? |
| 1 | occupant_score | Benefics vs malefics in the event house |
| 2 | navamsha_score | Does the D-9 chart confirm the lord's strength? |
| 3 | sav_normalized | Ashtakavarga bindu count for the event sign |
| 4 | gate1.score | Overall promise score (weighted combo of 0-3) |

#### Features 5-8: Gate 2 — Dasha (long-term timing)

| # | Feature | What it measures |
|---|---------|-----------------|
| 5 | md_score | Mahadasha (major period) lord's connection to event |
| 6 | ad_score | Antardasha (sub-period) lord's connection to event |
| 7 | gate2.score | Overall dasha score |
| 8 | connection_count | How many dasha-event connections exist? (count/8) |

#### Features 9-11: Gate 3 — Transit (short-term timing)

| # | Feature | What it measures |
|---|---------|-----------------|
| 9 | gate3.score | Overall transit score |
| 10 | active_months_ratio | Fraction of transit window with active triggers |
| 11 | peak_bav_score | Peak Bhinna Ashtakavarga score during transit |

#### Feature 12: Convergence

| # | Feature | What it measures |
|---|---------|-----------------|
| 12 | convergence | How well do all 3 gates agree? (0-3 normalized to 0-1) |

#### Features 13-17: Quality Flags (data reliability)

| # | Feature | What it measures |
|---|---------|-----------------|
| 13 | birth_time_tier | Tier 1=1.0 (exact), Tier 2=0.5 (approximate), Tier 3=0.0 (unknown) |
| 14 | lagna_mode | Using Moon chart? (1.0=Chandra, 0.0=regular) |
| 15 | dasha_boundary | Event near a dasha period change? (1.0=yes, risky) |
| 16 | dasha_ambiguous | Is the dasha period unclear? (1.0=yes) |
| 17 | is_retrospective | Looking at a past event? (1.0=yes, always true for training) |

#### Features 18-21: Demographics (placeholder for future)

| # | Feature | Current Value |
|---|---------|--------------|
| 18 | Gender | 0.5 (placeholder) |
| 19 | Age | 0.5 (placeholder) |
| 20 | Education | 0.5 (placeholder) |
| 21 | Income | 0.5 (placeholder) |

### Example — Nehru Marriage (Positive Sample)

```
[0.50, 0.65, 0.80, 0.63, 0.62,   <- Gate 1 (Promise)
 0.45, 0.90, 0.68, 0.38,          <- Gate 2 (Dasha)
 0.71, 0.33, 0.58,                <- Gate 3 (Transit)
 0.67,                             <- Convergence
 0.50, 0.00, 0.00, 0.00, 1.00,   <- Quality flags
 0.50, 0.50, 0.50, 0.50]          <- Demographics (placeholder)

Label: 0.85 (positive, approximate birth time)
```

### Example — Nehru Marriage 1911 (Negative Sample — time shifted)

```
[0.50, 0.65, 0.80, 0.63, 0.62,   <- Gate 1: SAME (birth chart doesn't change!)
 0.20, 0.30, 0.25, 0.13,          <- Gate 2: LOW (wrong dasha period)
 0.22, 0.08, 0.19,                <- Gate 3: LOW (wrong transits)
 0.36,                             <- Convergence: LOW (gates don't agree)
 0.50, 0.00, 0.00, 0.00, 1.00,   <- Quality flags: SAME
 0.50, 0.50, 0.50, 0.50]          <- Demographics: SAME

Label: 0.0 (negative)
```

**Key insight:** Features 0-4 (promise) stay the same because the birth chart doesn't change. Features 5-11 (timing) change dramatically because the planetary periods and transits are different in 1911 vs 1916. This is exactly what XGBoost learns — timing matters!

### College Admission Analogy

```
Student Application (Feature Vector):
[GPA, SAT_Score, Essay, Recommendation, Interview, ...]

Label: 1 (admitted) or 0 (rejected)

After 1000 applications, model learns:
"High GPA + High SAT + Good Essay = Admitted"

Our pipeline does the same, but with planetary positions:
"Strong Promise + Right Dasha + Supporting Transits = Event Happened"
```

**Key file:** `src/jyotish_ai/prediction/feature_builder.py`

---

## 5. Positive and Negative Sample Generation

### The Problem

The book only has real events (things that happened). But a model needs to also learn what **doesn't** match. This is called **Negative Sampling**.

### Our Strategy: 1 Positive + 2 Negatives per Event

For each real event, we create 3 training samples:

```
Real Event: "Nehru married on Feb 8, 1916"

Sample 1 — POSITIVE (real event):
  Person: Nehru | Event: Marriage | Date: 1916-02-08 | Label: 0.85

Sample 2 — TIME-SHIFTED NEGATIVE (hard negative):
  Person: Nehru | Event: Marriage | Date: 1911-02-08 | Label: 0.0
  (Same person, same event type, but 5 years earlier — didn't happen)

Sample 3 — CROSS-EVENT NEGATIVE (easier negative):
  Person: Nehru | Event: Career | Date: 1916-02-08 | Label: 0.0
  (Same person, same date, but different event type — wrong category)
```

### Full Dataset Example

| Person | Event | Date | Type | Label |
|--------|-------|------|------|-------|
| Nehru | Marriage | 1916-02-08 | Positive | 0.85 |
| Nehru | Marriage | 1911-02-08 | Time-shifted negative | 0.0 |
| Nehru | Career | 1916-02-08 | Cross-event negative | 0.0 |
| Nehru | Career | 1947-08-15 | Positive | 0.85 |
| Nehru | Career | 1942-08-15 | Time-shifted negative | 0.0 |
| Nehru | Marriage | 1947-08-15 | Cross-event negative | 0.0 |
| Tilak | Career | 1880-01-01 | Positive | 0.65 |
| Tilak | Career | 1875-01-01 | Time-shifted negative | 0.0 |
| Tilak | Marriage | 1880-01-01 | Cross-event negative | 0.0 |

**Result:** 36 real events across 25 charts become 108 training samples (36 positive + 72 negative).

### Why Two Types of Negatives?

| Type | ML Term | What it teaches | Difficulty |
|------|---------|----------------|------------|
| Time-shifted (-5 years) | **Hard Negative** | Timing matters — same chart, wrong time | Hard to distinguish |
| Cross-event (different type) | **Easier Negative** | Event type matters — same time, wrong event | Easier to distinguish |

**Why mix?** Pure hard negatives make training unstable. Pure easy negatives don't teach much. The mix gives both stability and discrimination power.

### ML Terminology

- **Negative Sampling** — creating synthetic "wrong" examples
- **Contrastive Learning** — model learns by comparing positive vs negative
- **Hard Negatives** — negatives that are very similar to positives (time-shifted)
- **Data Augmentation** — broader category of generating synthetic training data
- **Positive-to-Negative Ratio** — here 1:2 (36 positive, 72 negative)

**Key file:** `scripts/training/04_generate_features.py` (lines 145-193)

---

## 6. Label Smoothing

### What is Label Smoothing?

Instead of using hard labels (0 or 1), use softer values that reflect uncertainty:

| Label | Value | When Used |
|-------|-------|-----------|
| LABEL_POSITIVE_EXACT | 0.85 | Birth time is precisely known |
| LABEL_POSITIVE_APPROXIMATE | 0.65 | Birth time is approximate/uncertain |
| LABEL_NEGATIVE | 0.0 | Synthetic negative samples |

### Why Not Just Use 1.0 and 0.0?

Real-world data has uncertainty. OCR-parsed birth times may be approximate. A birth time off by 30 minutes changes the ascendant, which changes all house positions.

- **Without smoothing:** Model learns "this is 100% correct" even for noisy data -> overfitting
- **With smoothing:** Model learns "this is probably correct" -> better generalization

### How It Works in Code

```python
# In 05_build_training_set.py (lines 72-79)
if sample["label"] == 1 and sample["sample_type"] == "positive":
    if sample["confidence"] == "approximate":
        y = 0.65   # LABEL_POSITIVE_APPROXIMATE
    else:
        y = 0.85   # LABEL_POSITIVE_EXACT
else:
    y = 0.0         # LABEL_NEGATIVE
```

**Key file:** `scripts/training/05_build_training_set.py` (lines 32-34, 72-79)

---

## 7. ML Terminology Used

| Term | Definition | Our Pipeline Example |
|------|-----------|---------------------|
| **Feature Vector** | List of numbers describing one sample | 22 numbers per event |
| **Feature Engineering** | Converting raw data to numerical features | Chart data -> 22-dim vector |
| **Negative Sampling** | Creating synthetic wrong examples | Time-shifted + cross-event negatives |
| **Contrastive Learning** | Learning by comparing positive vs negative | Real events vs fake events |
| **Hard Negatives** | Negatives very similar to positives | Same person, -5 years |
| **Label Smoothing** | Soft labels reflecting uncertainty | 0.85 / 0.65 instead of 1.0 |
| **Overfitting** | Model memorizes training data, fails on new data | Why we use label smoothing |
| **XGBoost** | Gradient-boosted decision tree ensemble | Our model of choice |
| **Training Set** | Data the model learns from | 108 samples, X=(108,22) |
| **Ground Truth** | The correct/known answer | Real events from the book |
| **Epoch** | One complete pass through training data | XGBoost handles internally |
| **Hyperparameter** | Settings chosen before training | Learning rate, tree depth |
| **Ensemble** | Combining multiple models | XGBoost = many decision trees |
| **Stratified Split** | Maintaining class proportions in splits | Phase 5 (deferred) |

---

## 8. Production Pipeline (DVC + MLflow + Prefect)

### Problem

The original pipeline had issues:
- **64% data quality failure** — 32/50 records had wrong coordinates (OCR parsing bugs)
- **No data versioning** — no way to reproduce previous data
- **No experiment tracking** — no record of what happened in each run
- **No orchestration** — `subprocess.run()` with no retries or quality gates

### Solution — 3 Tools, Clear Separation

| Tool | Role | What it tracks |
|------|------|---------------|
| **DVC** | Data versioning only | Raw/processed data files (.txt, .json, .npz) |
| **MLflow** | Experiment tracking | Metrics, parameters, model artifacts |
| **Prefect** | Pipeline orchestration | Task execution, retries, quality gates |

**Key principle:** No overlap between tools. DVC does NOT run the pipeline. MLflow does NOT track data files. Prefect is the sole executor.

### Implementation Status

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | Done | Data quality fixes — regex, label smoothing, quality gate |
| Phase 2 | Done | DVC initialized, 4 data files tracked |
| Phase 3 | Done | MLflow tracking added to steps 04 and 05 |
| Phase 4 | Done | Prefect flow created with 5 tasks |
| Phase 5 | Deferred | Production hardening — train/val/test split, config file |

### Data Quality Fixes Applied

1. **Enhanced coordinate regex** — handles 10+ OCR variations (degree symbols, typos, time-based longitude)
2. **Label smoothing bug** — `confidence` field now propagated from step 04 to step 05
3. **Quality gate** — blocks pipeline on fallback coordinates or parse rate < 80%
4. **Gandhi double-degree fix** — `"21 °37°"` -> `"21°37'"` pre-cleaning regex

### Running the Pipeline

```bash
# Option 1: Prefect (recommended — retries, logging, quality gates)
python scripts/training/pipeline_flow.py

# Option 2: Simple runner (fallback — no Prefect dependency)
python scripts/training/run_pipeline.py
```

**Key files:**
- `docs/PLAN_PRODUCTION_PIPELINE.md` — full implementation plan with Zen review findings
- `scripts/training/pipeline_flow.py` — Prefect orchestration
- `scripts/training/run_pipeline.py` — simple fallback runner
