# Production-Ready Training Pipeline Plan

## MLflow + DVC + Prefect + Data Quality Fix

### Context

The training pipeline extracts horoscope data from OCR text, generates feature vectors, and builds XGBoost training sets. Current issues:

- **64% data quality failure** — 32/50 records have wrong coordinates due to OCR regex parsing bugs
- **No data versioning** — data files are untracked; no way to reproduce previous runs
- **No experiment tracking** — metrics, parameters, and artifacts are not logged Ref link - https://medium.com/@sachinsoni600517/a-practical-guide-to-experiment-tracking-in-mlops-14777cfc3724
- **No orchestration** — pipeline uses `subprocess.run()` with no retries, no quality gates
- **Label smoothing bug** — `LABEL_POSITIVE_APPROXIMATE` (0.65) is defined but never used

### Tooling Decisions

| Tool | Role | Why |
|------|------|-----|
| **DVC** | Data versioning only | Tracks raw/processed data files. NOT used for pipeline execution (avoids competing DAGs with Prefect). |
| **MLflow** | Experiment tracking | Logs metrics, parameters, model artifacts. Does NOT track data files (DVC does that). |
| **Prefect** | Pipeline orchestration | Sole pipeline executor. Prefect 3.x with return-value chaining, retries, quality gates. |

### Zen Review Findings (incorporated)

| # | Severity | Issue | Resolution |
|---|----------|-------|------------|
| 1 | HIGH | Repair script redundant — fix regex + re-run pipeline instead | Removed separate repair script. Fix regex in `02_parse_horoscopes.py` and re-run. |
| 2 | HIGH | Label smoothing fix incomplete — `04_generate_features.py` doesn't propagate `confidence` field | Both `04_generate_features.py` AND `05_build_training_set.py` need changes. |
| 3 | HIGH | DVC pipeline DAG + Prefect flow DAG = two competing pipeline definitions | DVC for data versioning only. Prefect is sole pipeline executor. |
| 4 | MED | DVC + MLflow both tracking artifacts — overlap | Clear separation: DVC = data files, MLflow = metrics + model artifacts. |
| 5 | MED | Prefect `wait_for=` syntax outdated for Prefect 3.x | Use Prefect 3.x native return-value chaining. |
| 6 | MED | No environment configuration specified | Added `configs/pipeline_config.yaml`. |

---

## Phase 1: Fix Data Quality

> Everything else depends on this. Do first.

### 1A. Enhanced Coordinate Regex

**File:** `scripts/training/02_parse_horoscopes.py` (line 157-162)

The current `LATLON_PATTERN` regex fails on 10+ OCR text variations:

| OCR Variation | Example | Fix |
|---------------|---------|-----|
| `D`, `~`, `J` as degree symbol | `Lat. 13D 0' N` | Treat as `°` |
| `Lat,` / `Let.` / `Lang.` typos | `Let. 13° 0' N` | Accept typos |
| Spaces in numbers | `1 3° 0' N` | Strip internal spaces |
| Time-based longitude | `5h. 10m. 20s. E` | Convert: h×15 + m×0.25 + s×0.004 |
| Missing apostrophes | `Lat. 13° 0 N` | Make `'` optional |
| Double degree symbols | `13°° 0' N` | Deduplicate |
| `0°3CT` OCR artifact | `Long. 0°3CT E` | Map to `0°30'` |

After fixing, re-run the full pipeline (steps 01-05) to regenerate all data.

### 1B. Fix Label Smoothing Bug

**File 1:** `scripts/training/04_generate_features.py`
- Propagate `confidence` field (`"exact"` or `"approximate"`) from event data into each feature vector sample

**File 2:** `scripts/training/05_build_training_set.py` (line 72-80)
- Use propagated `confidence` field:
  - `"exact"` → `LABEL_POSITIVE_EXACT` (0.85)
  - `"approximate"` → `LABEL_POSITIVE_APPROXIMATE` (0.65)

### 1C. Quality Gate in Validator

**File:** `scripts/training/03_validate_data.py` (line 241)
- Fail pipeline if parse rate < 80%
- Fail if fallback coordinates (20.5937, 78.9629) detected in any record
- Currently only warns — must block on these failures

**Verify:** Re-run full pipeline → all 50 records parse correctly. Validator → 0 errors.

---

## Phase 2: DVC (Data Versioning)

> DVC handles data versioning and lineage only. No `dvc repro` — Prefect is the pipeline executor.

### Setup

```bash
pip install dvc
dvc init
dvc add data/training/raw/notable_horoscopes_ocr.txt
dvc add data/training/notable_horoscopes.json
dvc add data/training/feature_vectors.json
dvc add data/training/training_set.npz
```

### Config Changes

- `.gitignore` — add DVC-tracked data files + `.dvc/` cache
- `pyproject.toml` — add `dvc` to dependencies

**Verify:** `dvc status` shows tracked files. `git diff` shows `.dvc` metadata files.

---

## Phase 3: MLflow (Experiment Tracking)

> MLflow tracks metrics, parameters, and model artifacts. DVC tracks data files. No overlap.

### Training Step (`05_build_training_set.py`)

- **Params:** label smoothing values, feature dimensions, split ratios
- **Metrics:** sample counts, positive/negative ratio, event type distribution
- **Artifacts:** `training_metadata.json` (NOT `.npz` — DVC tracks that)

### Feature Generation (`04_generate_features.py`)

- **Metrics:** total charts processed, skipped, error count, features generated

### Config

- `pyproject.toml` — add `mlflow` dependency
- Default: local `mlruns/` directory (no remote server for PoC)

**Verify:** `mlflow ui` → see experiment runs with metrics in browser.

---

## Phase 4: Prefect (Pipeline Orchestration)

> Prefect is the sole pipeline runner. Uses Prefect 3.x API with return-value chaining.

### Prefect Flow (`scripts/training/pipeline_flow.py`)

```python
from prefect import flow, task
from pathlib import Path

@task(retries=2, retry_delay_seconds=10)
def download_ocr() -> Path:
    # calls 01_download_ocr logic
    ...

@task
def parse_horoscopes(ocr_path: Path) -> Path:
    # calls 02_parse_horoscopes logic
    ...

@task
def validate_data(json_path: Path) -> Path:
    # calls 03_validate_data logic
    # QUALITY GATE: raise if parse_rate < 80%
    ...

@task
def generate_features(json_path: Path) -> Path:
    # calls 04_generate_features logic
    ...

@task
def build_training_set(features_path: Path) -> Path:
    # calls 05_build_training_set logic
    ...

@flow(name="training-pipeline", log_prints=True)
def training_pipeline():
    ocr = download_ocr()
    parsed = parse_horoscopes(ocr)
    validated = validate_data(parsed)
    features = generate_features(validated)
    build_training_set(features)

if __name__ == "__main__":
    training_pipeline()
```

The existing `run_pipeline.py` is kept as a simple fallback (no Prefect dependency needed).

**Verify:** `python scripts/training/pipeline_flow.py` → all tasks green in Prefect UI.

---

## Phase 5: Production Hardening

### 5A. Train/Val/Test Split

**File:** `scripts/training/05_build_training_set.py`
- Stratified 70/15/15 split by event type
- Output: `training_set.npz`, `validation_set.npz`, `test_set.npz`
- DVC track all three split files

### 5B. Data Quality Metrics

- Log parse success rate, coordinate extraction rate to MLflow per pipeline run
- Log data drift metrics (distribution changes between runs)

### 5C. Environment Configuration

**File:** `configs/pipeline_config.yaml`

```yaml
mlflow:
  tracking_uri: "mlruns/"            # local for PoC, switch to remote later
  experiment_name: "jyotish-training"

dvc:
  remote: "local"                    # switch to S3/GCS later
  remote_path: "/tmp/dvc-store"      # local cache for PoC

prefect:
  log_prints: true
  retries: 2
```

---

## Files Summary

| Action | File | Phase |
|--------|------|-------|
| Modify | `scripts/training/02_parse_horoscopes.py` | 1A |
| Modify | `scripts/training/04_generate_features.py` | 1B, 3B |
| Modify | `scripts/training/05_build_training_set.py` | 1B, 3A, 5A |
| Modify | `scripts/training/03_validate_data.py` | 1C |
| Modify | `.gitignore` | 2B |
| Modify | `pyproject.toml` | 2B, 3C, 4B |
| Create | `scripts/training/pipeline_flow.py` | 4A |
| Create | `configs/pipeline_config.yaml` | 5C |

## Execution Order

Phase 1 → 2 → 3 → 4 → 5 (sequential, each builds on previous)
