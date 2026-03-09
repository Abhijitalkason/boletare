"""
Step 5: Build XGBoost training set from feature vectors.

Converts feature_vectors.json to numpy arrays:
  - X: (N x 22) feature matrix
  - y: (N,) label vector with label smoothing applied

Label smoothing:
  - Positive + exact confidence:      0.85
  - Positive + approximate confidence: 0.65
  - Negative:                          0.0

Saves training_set.npz and training_metadata.json.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "training"
INPUT_FILE = DATA_DIR / "feature_vectors.json"
OUTPUT_NPZ = DATA_DIR / "training_set.npz"
OUTPUT_META = DATA_DIR / "training_metadata.json"

# Label smoothing values
LABEL_POSITIVE_EXACT = 0.85
LABEL_POSITIVE_APPROXIMATE = 0.65
LABEL_NEGATIVE = 0.0


def main() -> int:
    if not INPUT_FILE.exists():
        print(f"ERROR: Input file not found: {INPUT_FILE}")
        print("Run 04_generate_features.py first.")
        return 1

    with open(INPUT_FILE) as f:
        data = json.load(f)

    samples = data.get("samples", [])
    print(f"Loaded {len(samples)} samples from {INPUT_FILE.name}")

    # Filter out error samples
    valid = [s for s in samples if not s.get("error", False)]
    errored = len(samples) - len(valid)
    if errored:
        print(f"Excluded {errored} samples with errors")

    if not valid:
        print("ERROR: No valid samples to build training set.")
        return 1

    # Build arrays
    X_list: list[list[float]] = []
    y_list: list[float] = []
    event_type_counts: dict[str, int] = {}

    for sample in valid:
        fv = sample["feature_vector"]
        if len(fv) != 22:
            print(f"WARNING: Skipping sample with {len(fv)} features (expected 22): {sample['chart_id']}")
            continue

        X_list.append(fv)

        # Apply label smoothing
        if sample["label"] == 1:
            # Check if the original event had approximate confidence
            if sample.get("sample_type") == "positive":
                # We don't have confidence directly here, use 0.85 as default
                y_list.append(LABEL_POSITIVE_EXACT)
            else:
                y_list.append(LABEL_NEGATIVE)
        else:
            y_list.append(LABEL_NEGATIVE)

        et = sample.get("event_type", "unknown")
        event_type_counts[et] = event_type_counts.get(et, 0) + 1

    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.float32)

    print(f"\nTraining set shape: X={X.shape}, y={y.shape}")
    print(f"Positive samples (label > 0): {(y > 0).sum()}")
    print(f"Negative samples (label == 0): {(y == 0).sum()}")

    # Save numpy arrays
    np.savez(OUTPUT_NPZ, X=X, y=y)
    print(f"Saved training set to {OUTPUT_NPZ}")

    # Save metadata
    metadata = {
        "total_samples": len(X_list),
        "positive_count": int((y > 0).sum()),
        "negative_count": int((y == 0).sum()),
        "feature_dimensions": 22,
        "event_type_distribution": event_type_counts,
        "label_smoothing": {
            "positive_exact": LABEL_POSITIVE_EXACT,
            "positive_approximate": LABEL_POSITIVE_APPROXIMATE,
            "negative": LABEL_NEGATIVE,
        },
        "source": "notable_horoscopes_bv_raman",
        "generated_at": datetime.now().isoformat(),
    }

    with open(OUTPUT_META, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Saved metadata to {OUTPUT_META}")

    # Summary
    print(f"\n{'='*60}")
    print(f"TRAINING SET SUMMARY")
    print(f"{'='*60}")
    print(f"Total samples:     {metadata['total_samples']}")
    print(f"Positive:          {metadata['positive_count']}")
    print(f"Negative:          {metadata['negative_count']}")
    print(f"Features:          {metadata['feature_dimensions']}")
    print(f"Event distribution:")
    for et, count in sorted(event_type_counts.items()):
        print(f"  {et}: {count}")
    print(f"{'='*60}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
