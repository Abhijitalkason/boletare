"""
Master runner: chains all 7 training pipeline steps with progress logging.

Stops on first error.

Usage:
    python scripts/training/run_pipeline.py
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent

STEPS = [
    ("01_download_ocr.py", "Download OCR text from Archive.org"),
    ("02_parse_horoscopes.py", "Parse Notable Horoscopes into structured JSON"),
    ("02b_parse_technique_books.py", "Parse technique books (Santhanam + Raman v1/v2)"),
    ("02c_parse_hpa.py", "Parse Hindu Predictive Astrology"),
    ("02e_parse_sanjay_rath.py", "Parse Sanjay Rath — Crux of Vedic Astrology"),
    ("03b_merge_datasets.py", "Merge all datasets with provenance"),
    ("03_validate_data.py", "Validate merged data quality"),
    ("04_generate_features.py", "Generate 22-dim feature vectors"),
    ("05_build_training_set.py", "Build XGBoost training set"),
    ("06_train_model.py", "Train XGBoost model with 5-fold CV"),
    ("07_evaluate_model.py", "Evaluate model and generate reports"),
]


def main() -> int:
    print("=" * 60)
    print("TRAINING DATA PIPELINE")
    print("=" * 60)
    print(f"Steps: {len(STEPS)}")
    print()

    total_start = time.time()

    for i, (script, description) in enumerate(STEPS, 1):
        script_path = SCRIPTS_DIR / script
        if not script_path.exists():
            print(f"ERROR: Script not found: {script_path}")
            return 1

        print(f"[{i}/{len(STEPS)}] {description}")
        print(f"     Running: {script}")
        print("-" * 60)

        step_start = time.time()
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(SCRIPTS_DIR.parent.parent),
        )
        step_elapsed = time.time() - step_start

        if result.returncode != 0:
            print(f"\nERROR: Step {i} ({script}) failed with exit code {result.returncode}")
            print("Pipeline stopped.")
            return 1

        print(f"     Completed in {step_elapsed:.1f}s")
        print()

    total_elapsed = time.time() - total_start
    print("=" * 60)
    print(f"PIPELINE COMPLETE ({total_elapsed:.1f}s)")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
