"""
Prefect pipeline flow for the training data pipeline.

Wraps the 5 training steps as Prefect tasks with:
- Return-value chaining (Prefect 3.x)
- Retries on download step
- Quality gate enforcement in validation step

Usage:
    python scripts/training/pipeline_flow.py

The existing run_pipeline.py is kept as a simple fallback (no Prefect dependency).
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

from prefect import flow, task

# Add scripts/training to path for importlib to find step modules
sys.path.insert(0, str(Path(__file__).resolve().parent))
# Add project src to path for engine imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))


@task(retries=2, retry_delay_seconds=10)
def download_ocr() -> Path:
    """Step 1: Download OCR text from Archive.org."""
    mod = importlib.import_module("01_download_ocr")
    result = mod.main()
    if result != 0:
        raise RuntimeError("01_download_ocr failed")
    return mod.OUTPUT_FILE


@task
def parse_horoscopes(ocr_path: Path) -> Path:
    """Step 2: Parse horoscope blocks into structured JSON."""
    mod = importlib.import_module("02_parse_horoscopes")
    result = mod.main()
    if result != 0:
        raise RuntimeError("02_parse_horoscopes failed")
    return mod.OUTPUT_FILE


@task
def validate_data(json_path: Path) -> Path:
    """Step 3: Validate data quality. QUALITY GATE: raises on failure."""
    mod = importlib.import_module("03_validate_data")
    result = mod.main()
    if result != 0:
        raise RuntimeError("03_validate_data quality gate failed")
    return mod.INPUT_FILE


@task
def generate_features(json_path: Path) -> Path:
    """Step 4: Generate feature vectors from parsed chart data."""
    mod = importlib.import_module("04_generate_features")
    result = mod.main()
    if result != 0:
        raise RuntimeError("04_generate_features failed")
    return mod.OUTPUT_FILE


@task
def build_training_set(features_path: Path) -> Path:
    """Step 5: Build XGBoost training set from feature vectors."""
    mod = importlib.import_module("05_build_training_set")
    result = mod.main()
    if result != 0:
        raise RuntimeError("05_build_training_set failed")
    return mod.OUTPUT_NPZ


@flow(name="training-pipeline", log_prints=True)
def training_pipeline():
    """End-to-end training data pipeline."""
    ocr = download_ocr()
    parsed = parse_horoscopes(ocr)
    validated = validate_data(parsed)
    features = generate_features(validated)
    build_training_set(features)


if __name__ == "__main__":
    training_pipeline()
