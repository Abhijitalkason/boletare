# Production Pipeline — Discussion Summary

A reference document capturing the end-to-end discussion, decisions, tool comparisons, and Q&A that led to the production pipeline plan.

---

## 1. Starting Point: Data Quality Investigation

### Discovery
While reviewing the training data (`data/training/notable_horoscopes.json`), we found that **NATHURAM VINAYAK GODSE** had completely wrong coordinates (latitude/longitude pointed to India's geographic center instead of his actual birthplace).

### Root Cause Analysis
- Investigated all 50 records in the dataset
- Found **32 out of 50 records (64%)** had wrong coordinates
- All 32 broken records had fallback coordinates `(20.5937, 78.9629)` — India's geographic center
- Root cause: The `LATLON_PATTERN` regex in `02_parse_horoscopes.py` (line 157-162) was too narrow
- The OCR text contained **10+ coordinate format variations** the regex couldn't handle

### OCR Variations Cataloged
| Variation | Example | Why Regex Failed |
|-----------|---------|-----------------|
| `D` as degree symbol | `Lat. 13D 0' N` | Regex only matched `°` |
| `J` as degree symbol | `Lat. 25J 19' N` | Same |
| `~` as degree symbol | `Lat. 22~ 30' N` | Same |
| `Lat,` (comma not period) | `Lat, 18°31' N` | Regex required `Lat.` |
| `Let.` (typo) | `Let. 36° 13' N` | Regex required `Lat` |
| `Lang.` (typo) | `Lang. 0° 5' W` | Regex required `Long` |
| Reversed order | `Long. 88° E., Lat. 23° N.` | Regex expected Lat first |
| Time-based longitude | `5h. 10m. 20s. E.` | Completely different format |
| Spaces in numbers | `1 3° 0' N` | Regex expected continuous digits |
| OCR artifacts | `0°3CT E.` | Random character substitution |
| Curly quotes | `N„` instead of `N.,` | Unicode punctuation |

### Additional Bugs Found
1. **Label smoothing bug**: `LABEL_POSITIVE_APPROXIMATE` (0.65) was defined in `05_build_training_set.py` but **never used** — all positive samples got 0.85 regardless of confidence
2. **Validation doesn't block**: `03_validate_data.py` only warned on coordinate issues, didn't fail the pipeline

---

## 2. Question: How Do Experts Build Production ML Pipelines?

### Key Principles Discussed
- **Data versioning** — Track every version of your training data (like git for data)
- **Experiment tracking** — Log every training run's parameters, metrics, and artifacts
- **Pipeline orchestration** — Automated, retry-capable, observable pipeline execution
- **Quality gates** — Automated checks that block bad data from reaching training
- **Reproducibility** — Any previous run can be exactly reproduced

### Production Pipeline Architecture
```
Data Source → ETL/Parsing → Validation (quality gate) → Feature Engineering
→ Training Set → Model Training → Evaluation → Model Registry → Deployment
```

Each step is:
- Version-controlled (code in git, data in DVC)
- Tracked (metrics in MLflow)
- Orchestrated (Prefect manages execution)
- Gated (validation blocks bad data)

---

## 3. Tool Comparison & Selection

### Question: Which tools should we use?

We evaluated multiple tools across three categories:

### Data Versioning

| Tool | Pros | Cons | Verdict |
|------|------|------|---------|
| **DVC** | Git-like for data, pipeline DAG, lightweight | Learning curve | Selected |
| **Delta Lake** | ACID transactions, time-travel | Overkill for files, needs Spark | Too heavy |
| **git-lfs** | Simple, built into git | No pipeline support, no diffing | Too basic |

### Experiment Tracking

| Tool | Pros | Cons | Verdict |
|------|------|------|---------|
| **MLflow** | Open-source, model registry, broad ecosystem | UI basic | Selected |
| **Weights & Biases (W&B)** | Beautiful UI, team collaboration, sweeps | Cloud-hosted, paid for teams | Good but not needed for PoC |
| **Neptune.ai** | Good for collaboration | SaaS dependency, cost | Overkill |

### Pipeline Orchestration

| Tool | Pros | Cons | Verdict |
|------|------|------|---------|
| **Prefect** | Python-native, easy decorators, good UI | Newer ecosystem | Selected |
| **Airflow** | Industry standard, massive ecosystem | Heavy, complex setup, DAG files | Over-engineered for this |
| **Dagster** | Type-safe, good testing | Smaller community | Good alternative |

### Why Not W&B?

User asked specifically about Weights & Biases. The answer:
- W&B is excellent for **team collaboration** and **hyperparameter sweeps**
- For a PoC with a small team, MLflow provides the same core functionality (experiment tracking) without cloud dependency
- MLflow is fully open-source and runs locally — no account needed
- W&B can be added later if team collaboration becomes important

### Final Decision
**MLflow + DVC + Prefect** — confirmed by user.

---

## 4. Tool Separation of Concerns

A key design decision to avoid overlap:

| Tool | Tracks | Does NOT Track |
|------|--------|---------------|
| **DVC** | Raw data files, processed data files (.json, .npz) | Metrics, parameters, models |
| **MLflow** | Metrics, parameters, model artifacts, metadata JSON | Data files (DVC does that) |
| **Prefect** | Pipeline execution, retries, task status | Data or metrics (DVC/MLflow do that) |

**Critical decision:** DVC is used for **data versioning only** — NOT for pipeline execution (`dvc repro` is not used). Prefect is the **sole pipeline executor**. This avoids having two competing pipeline DAGs.

---

## 5. Zen Review Findings

The plan was reviewed by Zen (AI code reviewer). Six issues found:

| # | Severity | Issue | Resolution |
|---|----------|-------|------------|
| 1 | HIGH | Repair script (06_repair_coordinates.py) redundant | Removed. Just fix regex and re-run pipeline. |
| 2 | HIGH | Label smoothing fix incomplete — 04_generate_features.py doesn't propagate confidence | Fixed both 04 AND 05 scripts. |
| 3 | HIGH | DVC pipeline DAG + Prefect flow = competing definitions | DVC for versioning only, Prefect is sole executor. |
| 4 | MED | DVC + MLflow both tracking artifacts | Clear separation defined (see table above). |
| 5 | MED | Prefect `wait_for=` syntax outdated for 3.x | Use return-value chaining instead. |
| 6 | MED | No environment configuration | Added `configs/pipeline_config.yaml`. |

---

## 6. XGBoost — Where Does It Fit?

### Question: Where is XGBoost in this plan?

XGBoost is **not** in the production pipeline plan. The plan covers the **training data pipeline** — getting data ready for XGBoost.

### The Full Picture
```
Phase A (this plan):  OCR → Parse → Validate → Features → Training Set (.npz)
Phase B (next plan):  Training Set → XGBoost Train → Model (.json) → Deploy
```

Phase B would:
1. Load `training_set.npz` (produced by Phase A)
2. Train XGBoost with regularization (small dataset: ~350-500 samples, 22 features)
3. Evaluate with cross-validation
4. Save model to `models/xgboost_calibration.json`
5. Replace hard-coded weights in `convergence.py` with XGBoost predictions
6. Log training metrics to MLflow

---

## 7. Production Hardening — Do We Need It?

### Question: Do we really need Phase 5 (Production Hardening)?

For PoC — **no**. Reasoning:
- **Train/val/test split**: With ~350-500 samples, splits are too thin. Cross-validation during XGBoost training is sufficient.
- **Data quality metrics in MLflow**: Already covered by Phase 3 logging + Phase 1C quality gate.
- **Environment config**: Defaults (local mlruns/, local DVC) work fine for PoC.

**Decision:** Keep Phase 5 in the plan but implement later when dataset grows.

---

## 8. Code Changes Made (Phase 1)

### 1A. Enhanced Coordinate Regex
**File:** `scripts/training/02_parse_horoscopes.py`
- Replaced single `LATLON_PATTERN` with 3 patterns: standard, reversed, time-based
- Added `_extract_latlon()` function that tries all 3 patterns
- Added `_clean_coord_number()` for OCR space-in-number cleanup
- Added `_OCR_ARTIFACT` pattern for "3CT" → "30'" cleanup
- Handles: D/J/~ as degree, Let/Lang typos, reversed Long-Lat order, time-format longitude, curly quotes

### 1B. Label Smoothing Bug Fix
**File 1:** `scripts/training/04_generate_features.py`
- Added `confidence` parameter to `generate_sample()` function
- Propagates `confidence` field from event data into feature vector output JSON

**File 2:** `scripts/training/05_build_training_set.py`
- Now uses `confidence` field: `"exact"` → 0.85, `"approximate"` → 0.65

### 1C. Quality Gate
**File:** `scripts/training/03_validate_data.py`
- Added fallback coordinate detection (20.5937, 78.9629)
- Added parse rate threshold (< 80% = fail)
- Pipeline now **blocks** on these issues instead of just warning

### Config Updates
**File:** `pyproject.toml` — Added `dvc`, `mlflow`, `prefect` to training dependencies
**File:** `.gitignore` — Added DVC-tracked files, MLflow directories

---

## 9. Documents Created

| Document | Purpose |
|----------|---------|
| `docs/SOLUTION_OVERVIEW.md` | High-level architecture of the Jyotish AI system |
| `docs/PLAN_TRAIN_XGBOOST_MODEL.md` | Original training data pipeline design (5 scripts) |
| `docs/XGBOOST_ML_GUIDE.md` | XGBoost learning guide |
| `docs/XGBOOST_TRAINING_DATA_RESEARCH.md` | Training data research |
| `docs/PLAN_PRODUCTION_PIPELINE.md` | Production pipeline plan (MLflow + DVC + Prefect) |
| `docs/PRODUCTION_PIPELINE_DISCUSSION_SUMMARY.md` | This document |

---

## 10. Remaining Work

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 (Data Quality) | Done | Regex fix, label smoothing fix, quality gate |
| Phase 2 (DVC) | Pending | Install DVC, init, track data files |
| Phase 3 (MLflow) | Pending | Install MLflow, add tracking to scripts 04 & 05 |
| Phase 4 (Prefect) | Pending | Install Prefect, create `pipeline_flow.py` |
| Phase 5 (Hardening) | Deferred | Train/val/test split, env config (do when dataset grows) |
| XGBoost Training | Future | Separate plan needed after pipeline produces clean data |
