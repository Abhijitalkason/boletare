# Plan: Train the XGBoost Model — Training Data Extraction Pipeline

## Context

We need training data for the Phase 3 XGBoost calibration model. Currently, the Jyotish AI prediction engine uses hand-coded convergence weights (`score = w1*G1 + w2*G2 + w3*G3`) with fixed thresholds. Phase 3 replaces this with an XGBoost model that learns optimal weights from real horoscope data.

The book "Notable Horoscopes" by B.V. Raman is available on Archive.org with clean English OCR text (77 structured horoscopes). We'll build an automated pipeline to download the OCR text, parse horoscope examples into structured JSON, validate the data, and generate 22-dimensional feature vectors using the existing engine. This creates the first training dataset for XGBoost.

**Book URL:** `https://archive.org/details/NotableHoroscopesBVR`
**Archive.org ID:** `NotableHoroscopesBVR`

**Note:** "Hindu Predictive Astrology" (Archive.org ID: `jmbQ_hindu-predictive-astrology-b.-v.-raman`) was originally planned but its OCR produced Devanagari instead of English. "Notable Horoscopes" has 77 charts (vs ~30-40), 100% English OCR, and one structured chapter per horoscope — making it the superior data source.

---

## New Directory Structure

```
boletare/
  data/
    training/
      raw/                                 # Downloaded OCR text
        notable_horoscopes_ocr.txt
      notable_horoscopes.json              # Parsed structured chart data
      feature_vectors.json                 # Generated feature vectors + labels
      training_set.npz                     # Final numpy arrays for XGBoost
      training_metadata.json               # Sample counts, distribution stats
    geocoding/
      indian_cities.json                   # Static lat/lon lookup (~50 cities)
  scripts/
    training/
      01_download_ocr.py                   # Download OCR text from Archive.org
      02_parse_horoscopes.py               # Parse OCR -> structured JSON (hybrid: block detection + field extraction)
      03_validate_data.py                  # Validate extracted data quality
      04_generate_features.py              # Run engine -> 22-dim feature vectors
      05_build_training_set.py             # Assemble XGBoost training matrix
      run_pipeline.py                      # Master runner for all 5 steps
      test_parser.py                       # Unit tests for parsing patterns
  models/                                  # Will receive trained .json models (future)
```

---

## Development Order (Zen-recommended iterative approach)

```
Step 1: 01_download_ocr.py              (trivial, foundational)
Step 2: 03_validate_data.py             (build Pydantic schema FIRST — defines the contract)
Step 3: 02_parse_horoscopes.py          (develop against validator, iterate)
        + test_parser.py                (unit tests for regex patterns)
        (iterate between parse -> validate -> fix patterns -> repeat)
Step 4: 04_generate_features.py         (once validated data exists)
Step 5: 05_build_training_set.py        (final step)
Step 6: run_pipeline.py                 (chains all steps)
```

---

## Script-by-Script Plan

### Script 1: `01_download_ocr.py`

**Purpose:** Download full OCR text from Archive.org

- Use `internetarchive` package to get item metadata
- Download the `_djvu.txt` file (full OCR text)
- Fallback: direct HTTP download via `https://archive.org/download/{id}/{id}_djvu.txt`
- Save to `data/training/raw/hpa_ocr_full.txt`
- Verify file is not empty (>10KB)

---

### Script 2: `02_parse_horoscopes.py` (Zen: highest risk — use hybrid approach)

**Purpose:** Extract structured birth data + life events from OCR text

#### Two-stage hybrid parsing (from Zen review):

**Stage 1 — Block Identification:**
- Scan full OCR text for horoscope block boundaries
- Use markers like `"Chart No."`, `"Horoscope No."`, page breaks, section headings
- Extract each block as an isolated text chunk
- This limits regex scope — patterns only run within a single block, reducing false matches

**Stage 2 — Field Extraction within blocks:**
- Apply targeted regex patterns ONLY within each identified block:
  - Birth dates: `"born on 8th August 1912"`, `"Date of Birth: 8-8-1912"`, etc.
  - Birth times: `"7-35 p.m."`, `"Time of Birth: 7:35 PM"`, etc.
  - Places: `"Place: Bangalore"`, `"born at Bangalore"`, `"Lat. 13 N., Long. 77' 35' E"`
  - Events: marriage/career/child/property/health keywords with dates

#### Special handling:
- **LMT to IST conversion:** `correction_minutes = (82.5 - longitude) * 4.0`
- **Gender inference** from pronouns ("he/his" vs "she/her")
- **Event type mapping:** "married" -> MARRIAGE, "appointed" -> CAREER, etc.
- **`needs_manual_review` flag** for ambiguous entries

#### Error logging (from Zen review):
- Log EVERY block: parsed successfully or failed
- For failures: log the specific reason (date format mismatch, missing time, unknown place, etc.)
- Log line numbers and raw text excerpt for each block
- Summary at end: X blocks found, Y parsed successfully, Z flagged for review

#### Geocoding:
Static lookup ONLY from `data/geocoding/indian_cities.json` (~50 major Indian cities with aliases like "Bombay" -> "Mumbai"). No API calls — unknown places flagged for manual input with `needs_manual_review: true`.

#### Imprecise location policy (from Zen review):
If book says "a village in Mysore district", use the district capital coordinates and set `birth_time_tier: 2` to reflect reduced accuracy.

#### Output: `data/training/hindu_predictive_astrology.json`

```json
{
  "source": "hindu_predictive_astrology_bv_raman",
  "charts": [{
    "id": "HPA_001",
    "birth_date": "1912-08-08",
    "birth_time": "19:35:00",
    "birth_place": "Bangalore, India",
    "latitude": 12.9716, "longitude": 77.5946,
    "timezone_offset": 5.5,
    "birth_time_tier": 1,
    "gender": "male",
    "events": [{"event_type": "marriage", "event_date": "1938-09-15", "confidence": "exact"}],
    "raw_text_excerpt": "First 200 chars...",
    "needs_manual_review": false,
    "parse_warnings": []
  }]
}
```

---

### Script 2b: `test_parser.py` (from Zen review — develop alongside Script 2)

**Purpose:** Unit tests for parsing regex patterns

- Create a small set of manually curated text samples from the book representing:
  - **Easy case:** clean "Chart No. X" with clear date/time/place
  - **Hard case:** narrative format with dates embedded in sentences
  - **Ambiguous case:** missing time, approximate dates ("around 1938")
  - **Incomplete case:** place without coordinates
- Test each regex pattern individually
- Test the full block -> extraction pipeline
- Run with `pytest` — ensures patterns don't regress as we iterate

---

### Script 3: `03_validate_data.py` (build FIRST — defines the contract)

**Purpose:** Quality-check extracted JSON using Pydantic schema

#### Pydantic models (build these first — Script 2 must produce data matching these):

```python
class EventEntry(BaseModel):
    event_type: str   # Must be in EventType values
    event_date: date
    confidence: str = "exact"  # "exact" or "approximate"

class ChartEntry(BaseModel):
    id: str
    birth_date: date
    birth_time: time
    birth_place: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    timezone_offset: float
    birth_time_tier: int = Field(ge=1, le=3)
    gender: str
    events: list[EventEntry]
    raw_text_excerpt: str = ""
    needs_manual_review: bool = False
    parse_warnings: list[str] = []
```

#### Validations:
- Schema validation via Pydantic models above
- Date sanity: birth 1850-2000, events after birth, events before 2025
- Age sanity: marriage 14-60, career 16-70, child 18-55
- Coordinate sanity: lat 6-37, lon 68-98 (India range), warn for non-Indian
- Duplicate detection (same birth_date + birth_time + place)
- Event type distribution report
- OCR digit sanity: flag times with minutes > 59, hours > 23

#### Output:
Validation report to stdout + `data/training/validation_report.txt`

---

### Script 4: `04_generate_features.py`

**Purpose:** Run each chart+event through the existing 3-gate engine to produce feature vectors

#### Reuses existing code (no modifications needed):
- `engine/chart_computer.py` -> `compute_birth_chart()`
- `prediction/gate1_promise.py` -> `evaluate_promise()`
- `prediction/gate2_dasha.py` -> `evaluate_dasha()`
- `prediction/gate3_transit.py` -> `evaluate_transit()`
- `prediction/convergence.py` -> `compute_convergence()`
- `prediction/quality_flags.py` -> `compute_quality_flags()`
- `prediction/feature_builder.py` -> `build_feature_vector()`

#### Negative sample generation (2 per positive):
1. **Time-shifted:** Same chart, `event_date - 5 years` (different dasha/transit running)
2. **Cross-event:** Same chart+date, pick a different event type from the 5 defined EventTypes that is NOT documented for this person on this date

#### Cross-event negative clarification (from Zen review):
Only use event types from the fixed `EventType` enum (MARRIAGE, CAREER, CHILD, PROPERTY, HEALTH). "Not documented" means the book does not mention this event type for this person at this date. Acknowledge that absence of documentation does not mean the event didn't happen — this is an acceptable approximation for PoC.

#### Error handling:
- If `compute_birth_chart()` fails (e.g., date outside ephemeris range), log error and skip
- If any gate evaluation throws, catch, log, mark sample as `"error": true`
- Print summary: X samples generated, Y errors, Z skipped

#### Output: `data/training/feature_vectors.json`
Each sample contains: `chart_id`, `event_type`, `feature_vector` (22 floats), `label` (1/0), `sample_type`

---

### Script 5: `05_build_training_set.py`

**Purpose:** Convert to numpy arrays for XGBoost

- Load feature_vectors.json, exclude samples with `"error": true`
- Build X (N x 22) and y (N,) arrays
- Apply label smoothing: 0.85 for exact dates, 0.65 for approximate dates, 0.0 for negatives
- Save as `data/training/training_set.npz`
- Save `data/training/training_metadata.json` with:
  - Total samples, positive/negative counts
  - Event type distribution
  - Source book info
  - Generation timestamp

---

### Runner: `run_pipeline.py`

Chains all 5 scripts with progress logging and stop-on-error.

---

## Dependencies to Add

In `pyproject.toml`, new optional group:

```toml
training = [
    "internetarchive>=4.0.0",
]
```

Note: `geopy` removed — using static lookup only for determinism per Zen feedback. Unknown places flagged for manual input.

---

## Critical Files Referenced (existing, NOT modified)

| File | Function | Used By |
|---|---|---|
| `src/jyotish_ai/engine/chart_computer.py` | `compute_birth_chart()` | Script 04 |
| `src/jyotish_ai/prediction/feature_builder.py` | `build_feature_vector()` | Script 04 |
| `src/jyotish_ai/prediction/gate1_promise.py` | `evaluate_promise()` | Script 04 |
| `src/jyotish_ai/prediction/gate2_dasha.py` | `evaluate_dasha()` | Script 04 |
| `src/jyotish_ai/prediction/gate3_transit.py` | `evaluate_transit()` | Script 04 |
| `src/jyotish_ai/prediction/convergence.py` | `compute_convergence()` | Script 04 |
| `src/jyotish_ai/prediction/quality_flags.py` | `compute_quality_flags()` | Script 04 |
| `src/jyotish_ai/domain/types.py` | `EventType`, `BirthTimeTier` enums | Scripts 02-04 |

---

## Estimated Data Yield

- 77 charts from "Notable Horoscopes"
- ~100-150 positive event samples (multiple events per chart)
- ~200-300 negative samples (2x ratio)
- **Total: ~350-500 training rows**

This is a PoC starting point. The same pipeline can be rerun on other books to scale up.

---

## Known Risks & Mitigations (from Zen reviews)

| Risk | Mitigation |
|---|---|
| Regex parsing brittle for varied formats | Hybrid approach: block detection first, then targeted extraction within blocks. Unit tests. Manual review of flagged entries. |
| OCR digit errors in dates/times | Validate minutes <= 59, hours <= 23, dates within expected ranges. Compare subset against original book pages. |
| Small dataset (~150-240 rows) for 22 features | Aggressive XGBoost regularization (L1/L2, max_depth=3-4). This is PoC — pipeline reusable for more books. |
| Selection bias (textbook examples) | Acknowledged. PoC validates pipeline, not production model. More diverse data needed later. |
| "Not documented" does not mean "did not happen" for negatives | Acceptable approximation for PoC. Clearly documented assumption. |
| Imprecise locations ("village in Mysore district") | Use district capital coordinates, downgrade birth_time_tier to 2. |
| LMT vs IST historical complexity | Formula correct for pre-1947 LMT. Verify a few examples against known charts. |

---

## Verification

1. Run `01_download_ocr.py` -> verify `hpa_ocr_full.txt` exists and is >10KB
2. Run `pytest scripts/training/test_parser.py` -> all parsing unit tests pass
3. Run `02_parse_horoscopes.py` -> verify JSON has at least 10 chart entries
4. Run `03_validate_data.py` -> verify no critical errors, review flagged entries
5. Run `04_generate_features.py` -> verify each sample has 22-float feature vector
6. Run `05_build_training_set.py` -> verify `training_set.npz` loads correctly with `np.load()`
7. Run `run_pipeline.py` end-to-end -> verify all steps complete without errors
