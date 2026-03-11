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

## Implementation Status

| Phase | Status | Description |
|-------|--------|-------------|
| **Phase 1** | **Done** | Data quality fixes — regex, label smoothing, quality gate |
| **Phase 2** | **Done** | DVC initialized, 4 data files tracked |
| **Phase 3** | **Done** | MLflow tracking added to steps 04 and 05 |
| **Phase 4** | **Done** | Prefect flow created with 5 tasks |
| **Phase 5** | **Deferred** | Production hardening — implement when dataset grows |

## Files Changed — Complete List

| Action | File | Phase | Status | What Changed |
|--------|------|-------|--------|--------------|
| Modify | `scripts/training/02_parse_horoscopes.py` | 1A | Done | Replaced single regex with 3 patterns (standard, reversed, time-based) + `_extract_latlon()`, `_clean_coord_number()`, `_OCR_ARTIFACT` helpers |
| Modify | `scripts/training/04_generate_features.py` | 1B, 3B | Done | Added `confidence` parameter to `generate_sample()` (line 72) + MLflow metrics logging (lines 273-281) |
| Modify | `scripts/training/05_build_training_set.py` | 1B, 3A | Done | Label smoothing uses `confidence` field: exact=0.85, approximate=0.65 (lines 72-78) + MLflow params/metrics/artifact logging (lines 116-132) |
| Modify | `scripts/training/03_validate_data.py` | 1C | Done | Quality gate: blocks on fallback coordinates (20.5937, 78.9629) + parse rate < 80% (lines 241-260) |
| Modify | `.gitignore` | 2B | Done | Added DVC cache + MLflow directory exclusions |
| Modify | `pyproject.toml` | 2B, 3C, 4B | Done | Added `dvc>=3.50.0`, `mlflow>=2.15.0`, `prefect>=3.0.0` to training dependencies |
| Create | `scripts/training/pipeline_flow.py` | 4A | Done | Prefect 3.x flow with 5 @task functions, return-value chaining, retries on download, quality gate enforcement |
| Create | `data/training/raw/notable_horoscopes_ocr.txt.dvc` | 2A | Done | DVC tracking metadata for raw OCR file |
| Create | `data/training/notable_horoscopes.json.dvc` | 2A | Done | DVC tracking metadata for parsed horoscopes |
| Create | `data/training/feature_vectors.json.dvc` | 2A | Done | DVC tracking metadata for feature vectors |
| Create | `data/training/training_set.npz.dvc` | 2A | Done | DVC tracking metadata for training set |
| Create | `data/training/.gitignore` | 2A | Done | DVC auto-generated — excludes DVC-tracked data files from git |
| Create | `data/training/raw/.gitignore` | 2A | Done | DVC auto-generated — excludes DVC-tracked raw files from git |
| Create | `.dvc/config` | 2A | Done | DVC configuration |
| Create | `.dvc/.gitignore` | 2A | Done | DVC internal gitignore |
| Create | `.dvcignore` | 2A | Done | DVC ignore patterns |
| Create | `configs/pipeline_config.yaml` | 5C | Deferred | Environment configuration — not needed for PoC |

## Execution Order

Phase 1 → 2 → 3 → 4 → 5 (sequential, each builds on previous)

---

## Zen Post-Implementation Review (Review #2)

After Phases 1–4 were implemented, Zen reviewed the actual code changes. Six issues were reported. Analysis and resolution below.

### Issues Reviewed

| # | Severity | Issue | Verdict | Resolution |
|---|----------|-------|---------|------------|
| 1 | HIGH | `pipeline_flow.py` — `importlib.import_module('01_download_ocr')` fails unless CWD is `scripts/training/` because that directory is not on `sys.path` | **Real bug** | Add `sys.path.insert(0, str(Path(__file__).resolve().parent))` to `pipeline_flow.py` so importlib can find the step scripts |
| 2 | HIGH | `pipeline_flow.py` — importlib caches modules; re-running flow in same process won't re-execute | **False positive** | Each `python pipeline_flow.py` invocation is a fresh process. Module cache resets per process. Prefect Server also spawns fresh processes per flow run. No fix needed. |
| 3 | HIGH | DVC auto-generated `.gitignore` files in `data/training/` and `data/training/raw/` are untracked — need to be committed to git | **Real — trivial** | Run `git add data/training/.gitignore data/training/raw/.gitignore`. These files tell git to ignore DVC-tracked data files. Without committing them, other developers' git won't exclude the data files. |
| 4 | MED | MLflow creates separate runs in `04_generate_features.py` and `05_build_training_set.py` — metrics spread across runs | **Acceptable for PoC** | Each step logs different metrics (feature generation vs. training set build). Separate runs are appropriate. Can consolidate into a parent run later if needed. |
| 5 | MED | `04_generate_features.py` logs MLflow metrics before writing the output file — if file write fails, MLflow shows success | **Acceptable** | If file write fails, the script returns non-zero exit code and Prefect catches it as a task failure. MLflow run metadata is still useful for debugging. Minor ordering preference, not a bug. |
| 6 | MED | No `configs/pipeline_config.yaml` created — MLflow experiment name `"jyotish-training"` is hardcoded in two files | **Expected** | This is Phase 5C (deferred). Hardcoded experiment name is fine for PoC. Config file will be created when dataset grows and environment configuration becomes necessary. |

### Fixes Applied

**Fix A — sys.path for script imports in pipeline_flow.py:**
```python
# Before (only src/ was on path):
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

# After (both src/ AND scripts/training/ on path):
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))
```

**Fix B — Commit DVC .gitignore files:**
```bash
git add data/training/.gitignore data/training/raw/.gitignore
```

### Summary

- **2 fixes applied** (sys.path bug + DVC gitignore commit)
- **1 false positive dismissed** (importlib caching)
- **3 medium issues accepted** (separate MLflow runs, logging order, deferred config)
