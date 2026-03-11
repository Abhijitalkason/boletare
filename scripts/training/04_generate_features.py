"""
Step 4: Generate 22-dimensional feature vectors from parsed chart data.

Runs each chart+event through the existing 3-gate engine:
  compute_birth_chart -> evaluate_promise -> evaluate_dasha -> evaluate_transit
  -> compute_convergence -> compute_quality_flags -> build_feature_vector

Generates negative samples (2 per positive):
  1. Time-shifted: same chart, event_date - 5 years
  2. Cross-event: same chart+date, different EventType
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import date, time, timedelta
from pathlib import Path
from random import choice, seed

import mlflow

# Add project src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from jyotish_ai.domain.types import BirthTimeTier, EventType
from jyotish_ai.engine.chart_computer import compute_birth_chart
from jyotish_ai.prediction.gate1_promise import evaluate_promise
from jyotish_ai.prediction.gate2_dasha import evaluate_dasha
from jyotish_ai.prediction.gate3_transit import evaluate_transit
from jyotish_ai.prediction.convergence import compute_convergence
from jyotish_ai.prediction.quality_flags import compute_quality_flags
from jyotish_ai.prediction.feature_builder import build_feature_vector

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "training"
INPUT_FILE = DATA_DIR / "notable_horoscopes.json"
OUTPUT_FILE = DATA_DIR / "feature_vectors.json"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

ALL_EVENT_TYPES = [EventType.MARRIAGE, EventType.CAREER, EventType.CHILD, EventType.PROPERTY, EventType.HEALTH]

EVENT_TYPE_MAP = {
    "marriage": EventType.MARRIAGE,
    "career": EventType.CAREER,
    "child": EventType.CHILD,
    "property": EventType.PROPERTY,
    "health": EventType.HEALTH,
}

TIER_MAP = {
    1: BirthTimeTier.TIER_1,
    2: BirthTimeTier.TIER_2,
    3: BirthTimeTier.TIER_3,
}


def generate_sample(
    chart_id: str,
    birth_date_str: str,
    birth_time_str: str,
    latitude: float,
    longitude: float,
    tz_offset: float,
    birth_time_tier: int,
    event_type_str: str,
    event_date_str: str,
    label: int,
    sample_type: str,
    confidence: str = "exact",
    is_retrospective: bool = True,
) -> dict | None:
    """Generate a single feature vector sample.

    Returns dict with chart_id, event_type, feature_vector, label, sample_type.
    Returns None if computation fails.
    """
    try:
        bd = date.fromisoformat(birth_date_str)
        bt_parts = birth_time_str.split(":")
        bt = time(int(bt_parts[0]), int(bt_parts[1]))
        ed = date.fromisoformat(event_date_str)
        et = EVENT_TYPE_MAP.get(event_type_str.lower())
        tier = TIER_MAP.get(birth_time_tier, BirthTimeTier.TIER_2)

        if et is None:
            logger.warning("Unknown event type: %s", event_type_str)
            return None

        # Step 1: Compute birth chart
        chart = compute_birth_chart(
            birth_date=bd,
            birth_time=bt,
            latitude=latitude,
            longitude=longitude,
            tz_offset=tz_offset,
            birth_time_tier=tier,
        )

        # Step 2: Gate 1 — Promise
        gate1 = evaluate_promise(chart, et)

        # Step 3: Gate 2 — Dasha
        gate2 = evaluate_dasha(chart, et, ed)

        # Step 4: Gate 3 — Transit
        gate3 = evaluate_transit(chart, et, ed)

        # Step 5: Convergence
        conv_score, conv_level = compute_convergence(gate1, gate2, gate3)

        # Step 6: Quality flags
        qf = compute_quality_flags(chart, is_retrospective=is_retrospective)

        # Step 7: Feature vector
        fv = build_feature_vector(gate1, gate2, gate3, conv_score, qf)

        return {
            "chart_id": chart_id,
            "event_type": event_type_str,
            "event_date": event_date_str,
            "feature_vector": fv,
            "label": label,
            "sample_type": sample_type,
            "confidence": confidence,
            "error": False,
        }

    except Exception as e:
        logger.error("Error generating sample for %s/%s/%s: %s", chart_id, event_type_str, event_date_str, e)
        return {
            "chart_id": chart_id,
            "event_type": event_type_str,
            "event_date": event_date_str,
            "feature_vector": [],
            "label": label,
            "sample_type": sample_type,
            "error": True,
            "error_message": str(e),
        }


def generate_negative_time_shifted(chart: dict, event: dict) -> dict | None:
    """Generate time-shifted negative: same chart, event_date - 5 years."""
    try:
        ed = date.fromisoformat(event["event_date"])
        shifted = ed.replace(year=ed.year - 5)
        # Ensure shifted date is after birth
        bd = date.fromisoformat(chart["birth_date"])
        if shifted <= bd:
            shifted = bd + timedelta(days=365)  # 1 year after birth as fallback
    except ValueError:
        return None

    return generate_sample(
        chart_id=chart["id"],
        birth_date_str=chart["birth_date"],
        birth_time_str=chart["birth_time"],
        latitude=chart["latitude"],
        longitude=chart["longitude"],
        tz_offset=chart["timezone_offset"],
        birth_time_tier=chart["birth_time_tier"],
        event_type_str=event["event_type"],
        event_date_str=shifted.isoformat(),
        label=0,
        sample_type="time_shifted_negative",
    )


def generate_negative_cross_event(chart: dict, event: dict) -> dict | None:
    """Generate cross-event negative: same chart+date, different EventType."""
    current_type = event["event_type"].lower()
    other_types = [t for t in EVENT_TYPE_MAP if t != current_type]
    if not other_types:
        return None

    other_type = choice(other_types)

    return generate_sample(
        chart_id=chart["id"],
        birth_date_str=chart["birth_date"],
        birth_time_str=chart["birth_time"],
        latitude=chart["latitude"],
        longitude=chart["longitude"],
        tz_offset=chart["timezone_offset"],
        birth_time_tier=chart["birth_time_tier"],
        event_type_str=other_type,
        event_date_str=event["event_date"],
        label=0,
        sample_type="cross_event_negative",
    )


def main() -> int:
    if not INPUT_FILE.exists():
        print(f"ERROR: Input file not found: {INPUT_FILE}")
        print("Run 02_parse_horoscopes.py first.")
        return 1

    seed(42)  # Reproducibility for negative sampling

    with open(INPUT_FILE) as f:
        data = json.load(f)

    charts = data.get("charts", [])
    print(f"Loaded {len(charts)} charts from {INPUT_FILE.name}")

    samples: list[dict] = []
    errors = 0
    skipped = 0

    for chart in charts:
        if chart.get("needs_manual_review", False):
            logger.info("Skipping %s (needs manual review)", chart["id"])
            skipped += 1
            continue

        if not chart.get("events"):
            logger.info("Skipping %s (no events)", chart["id"])
            skipped += 1
            continue

        for event in chart["events"]:
            # Positive sample
            pos = generate_sample(
                chart_id=chart["id"],
                birth_date_str=chart["birth_date"],
                birth_time_str=chart["birth_time"],
                latitude=chart["latitude"],
                longitude=chart["longitude"],
                tz_offset=chart["timezone_offset"],
                birth_time_tier=chart["birth_time_tier"],
                event_type_str=event["event_type"],
                event_date_str=event["event_date"],
                label=1,
                sample_type="positive",
                confidence=event.get("confidence", "exact"),
            )
            if pos:
                samples.append(pos)
                if pos.get("error"):
                    errors += 1

            # Negative 1: time-shifted
            neg1 = generate_negative_time_shifted(chart, event)
            if neg1:
                samples.append(neg1)
                if neg1.get("error"):
                    errors += 1

            # Negative 2: cross-event
            neg2 = generate_negative_cross_event(chart, event)
            if neg2:
                samples.append(neg2)
                if neg2.get("error"):
                    errors += 1

    # Summary
    positive = sum(1 for s in samples if s["label"] == 1 and not s.get("error"))
    negative = sum(1 for s in samples if s["label"] == 0 and not s.get("error"))
    print(f"\n{'='*60}")
    print(f"FEATURE GENERATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total samples:    {len(samples)}")
    print(f"Positive:         {positive}")
    print(f"Negative:         {negative}")
    print(f"Errors:           {errors}")
    print(f"Charts skipped:   {skipped}")
    print(f"{'='*60}")

    # Log metrics to MLflow
    mlflow.set_experiment("jyotish-training")
    with mlflow.start_run(run_name="04_generate_features"):
        mlflow.log_metric("charts_processed", len(charts) - skipped)
        mlflow.log_metric("charts_skipped", skipped)
        mlflow.log_metric("error_count", errors)
        mlflow.log_metric("features_generated", len(samples))
        mlflow.log_metric("positive_samples", positive)
        mlflow.log_metric("negative_samples", negative)

    # Write output
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump({"samples": samples}, f, indent=2)

    print(f"\nOutput saved to {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
