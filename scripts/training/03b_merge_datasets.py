"""
Step 3b: Merge all parsed datasets into a single file for feature generation.

Scans data/training/ for JSON files matching the chart schema pattern
(has "source" and "charts" keys). Merges them with provenance metadata.

Output:
  - data/training/all_charts_merged.json  — combined chart data
  - data/training/merge_manifest.json     — source files, counts, stats
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "training"
OUTPUT_FILE = DATA_DIR / "all_charts_merged.json"
MANIFEST_FILE = DATA_DIR / "merge_manifest.json"

# Files to skip (not chart data)
SKIP_FILES = {"training_metadata.json", "merge_manifest.json", "all_charts_merged.json"}


def find_chart_files() -> list[Path]:
    """Find all JSON files in data/training/ that contain chart data."""
    chart_files = []
    for f in sorted(DATA_DIR.glob("*.json")):
        if f.name in SKIP_FILES:
            continue
        try:
            with open(f) as fh:
                data = json.load(fh)
            if isinstance(data, dict) and "source" in data and "charts" in data:
                if isinstance(data["charts"], list):
                    chart_files.append(f)
        except (json.JSONDecodeError, KeyError):
            continue
    return chart_files


def main() -> int:
    chart_files = find_chart_files()

    if not chart_files:
        print("ERROR: No chart data files found in", DATA_DIR)
        return 1

    print(f"Found {len(chart_files)} chart data files:\n")

    all_charts: list[dict] = []
    manifest_entries: list[dict] = []
    seen_ids: set[str] = set()

    for f in chart_files:
        with open(f) as fh:
            data = json.load(fh)

        source = data["source"]
        charts = data["charts"]

        # Count stats
        total = len(charts)
        with_events = sum(1 for c in charts if c.get("events"))
        total_events = sum(len(c.get("events", [])) for c in charts)
        needs_review = sum(1 for c in charts if c.get("needs_manual_review"))

        # Check for ID collisions
        collisions = 0
        for chart in charts:
            chart_id = chart["id"]
            if chart_id in seen_ids:
                collisions += 1
                # Re-prefix with source to avoid collision
                chart["id"] = f"{source[:3]}_{chart_id}"
            seen_ids.add(chart["id"])
            # Tag with source for provenance
            chart["_source_file"] = f.name

        all_charts.extend(charts)

        print(f"  {f.name:45s} charts={total:>4}  with_events={with_events:>4}  events={total_events:>4}  review={needs_review:>4}")
        if collisions:
            print(f"    WARNING: {collisions} ID collisions re-prefixed")

        manifest_entries.append({
            "file": f.name,
            "source": source,
            "charts": total,
            "charts_with_events": with_events,
            "total_events": total_events,
            "needs_review": needs_review,
            "id_collisions": collisions,
        })

    # Event type distribution across all sources
    event_dist: dict[str, int] = {}
    for chart in all_charts:
        for event in chart.get("events", []):
            etype = event.get("event_type", "unknown")
            event_dist[etype] = event_dist.get(etype, 0) + 1

    # Write merged output
    merged = {
        "source": "multi_source_merged",
        "merged_at": datetime.now().isoformat(),
        "source_count": len(chart_files),
        "charts": all_charts,
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(merged, f, indent=2)

    # Write manifest
    manifest = {
        "merged_at": datetime.now().isoformat(),
        "total_charts": len(all_charts),
        "total_events": sum(len(c.get("events", [])) for c in all_charts),
        "charts_with_events": sum(1 for c in all_charts if c.get("events")),
        "event_distribution": event_dist,
        "sources": manifest_entries,
    }

    with open(MANIFEST_FILE, "w") as f:
        json.dump(manifest, f, indent=2)

    # Summary
    total_events = sum(len(c.get("events", [])) for c in all_charts)
    charts_with_events = sum(1 for c in all_charts if c.get("events"))

    print(f"\n{'='*60}")
    print(f"MERGE SUMMARY")
    print(f"{'='*60}")
    print(f"  Sources merged:      {len(chart_files)}")
    print(f"  Total charts:        {len(all_charts)}")
    print(f"  Charts with events:  {charts_with_events}")
    print(f"  Total events:        {total_events}")
    print(f"  Event distribution:  {event_dist}")
    print(f"\n  Estimated training samples (1 pos + 2 neg per event): ~{total_events * 3}")
    print(f"\n  Output: {OUTPUT_FILE}")
    print(f"  Manifest: {MANIFEST_FILE}")
    print(f"{'='*60}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
