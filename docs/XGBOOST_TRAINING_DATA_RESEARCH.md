# Phase 3 — XGBoost Training Data Research & Recommendations

## Context
Research findings on training data sources for the Phase 3 XGBoost calibration model. The system currently uses hand-coded convergence weights (Phase 1) with a 22-dimensional feature vector ready (Phase 2). Phase 3 will train an XGBoost model to replace the hand-coded weights with learned calibration.

## Current System State
- **Phase 1 (implemented):** Hand-coded weights (w1=1.0, w2=1.0, w3=1.0), fixed thresholds (high=2.5, medium=1.5, low=0.5)
- **Phase 2 (implemented):** 22-dimensional feature vector builder (`src/jyotish_ai/prediction/feature_builder.py`)
- **Phase 3 (NOT implemented):** XGBoost calibration — training, storage, inference

## System Architecture (Layers & Phases)

### Layers (Architectural — all implemented)

| Layer | Name | Modules | What it does |
|-------|------|---------|-------------|
| Layer 1 | Compute (Engine) | `engine/ephemeris`, `houses`, `dignity`, `dasha`, `ashtakavarga`, `navamsha`, `boundary`, `chart_computer`, `yogas`, `doshas`, `transit` | Computes birth charts using Swiss Ephemeris |
| Layer 2 | Predict | `prediction/gate1_promise`, `gate2_dasha`, `gate3_transit`, `convergence`, `quality_flags`, `feature_builder` | Three-gate scoring + convergence + feature vectors |
| Layer 3 | Narrate | `narration/claude_narrator`, `mock_narrator` | AI narration via Claude API |
| Layer 4 | Deliver | `delivery/api_delivery`, `whatsapp` | API response or WhatsApp delivery |
| Layer 5 | Engage | `engagement/scheduler`, `weekly_transit` | Weekly transit insights |

### Phases (Evolutionary — prediction engine maturity)

| Phase | Name | Status | What it covers |
|-------|------|--------|---------------|
| Phase 1 | Hand-coded rules | Implemented | Static weights, fixed thresholds, placeholder demographics |
| Phase 2 | Feature engineering | Implemented | 22-dim normalized feature vector ready for ML |
| Phase 3 | XGBoost calibration | NOT implemented | ML model replaces hand-coded weights |

### 22-Dimensional Feature Vector Layout

```
Features 0-4:   Gate 1 sub-scores (lord_dignity, occupant, navamsha, sav, gate1_score)
Features 5-8:   Gate 2 sub-scores (md_score, ad_score, gate2_score, connection_count)
Features 9-11:  Gate 3 sub-scores (gate3_score, active_months_ratio, peak_bav)
Feature 12:     Convergence score (normalized 0-3 → 0-1)
Features 13-17: Quality flags (tier, lagna_mode, boundary, ambiguous, retrospective)
Features 18-21: Demographics (gender, age, education, income) — placeholder 0.5
```

---

## Part 1: Why External Data is Needed

### The Cold-Start Problem
- The system has an `events` table for users to report real life events (marriage, career, etc.)
- The `EventService` records these with label smoothing based on reporting delay
- But at launch, there are zero user-reported events to train on
- Waiting for organic user data would take months/years

### Why Not Astro-Databank (ADB)?
- ADB is the world's largest verified astrology database (~60,000+ charts)
- Birth times are Rodden-rated (AA = birth certificate, A = memory)
- **Problem: ~80% non-Indian data** — Western charts with Western cultural patterns
- Vedic Jyotish uses different rules, dashas, cultural event patterns than Western astrology
- Training on Western data would introduce systematic bias for an Indian astrology system

### What's Needed
- Indian-specific birth data with verified birth times
- Documented life events with approximate dates
- Coverage across all 5 event types: marriage, career, child, property, health

---

## Part 2: Existing Data Infrastructure (Already Built)

The codebase already has the infrastructure for training data:

### Events Table — Ground Truth Labels
**File:** `src/jyotish_ai/persistence/models.py` (lines 249-282)
- Users report real events via `/api/v1/events` endpoint
- Fields: `event_type`, `event_date`, `is_retrospective`, `label_smoothed`
- Label smoothing: events reported closer to occurrence get higher confidence (1.0 = same day, decays over time)

### Predictions Table — Feature Vectors
**File:** `src/jyotish_ai/persistence/models.py` (lines 189-242)
- Every prediction stores the 22-dimensional `feature_vector_json`
- Also stores all gate scores, convergence score, quality flags

### Users Table — Demographics
**File:** `src/jyotish_ai/persistence/models.py` (lines 45-118)
- Gender, age, education, income bracket, marital status
- Would fill features 18-21 (currently hardcoded to 0.5)

### The Intended Training Loop (Not Yet Built)
```
1. User onboards → birth data stored
2. User reports past events → "I got married on 2020-03-15" (ground truth)
3. System runs retrospective prediction for that date → generates feature vector
4. Pair: (feature_vector, did_event_happen=1, label_smoothed=0.85)
5. Collect many such pairs across users
6. Train XGBoost: features → calibrated probability
```

---

## Part 3: Indian Data Sources for XGBoost Training

### Tier 1 — Highest Chart Volume (Best for Training)

| Book | Author | ~Charts | Events | Data Quality |
|---|---|---|---|---|
| Notable Horoscopes | B.V. Raman | ~77 | Marriage, career, children, health, death | Very high — verified birth times |
| Three Hundred Important Combinations | B.V. Raman | ~150 illustrations | Yogas mapped to real life outcomes | High — from actual horoscopes |
| Hindu Predictive Astrology | B.V. Raman | ~30-40 | Mixed events | High |
| Karma and Rebirth in Hindu Astrology | K.N. Rao | Many (illustrative) | Life events, karma patterns | High |

**B.V. Raman combined: ~250-270 charts**

### Tier 2 — Event-Specific Books

| Book | Author | Focus | Why Useful |
|---|---|---|---|
| Astrology and Timing of Marriage | K.N. Rao | Marriage | Dedicated marriage event charts — directly maps to `EventType.MARRIAGE` |
| Planets and Children | K.N. Rao | Childbirth | Dedicated child event charts — maps to `EventType.CHILD` |
| Ups and Downs in Careers | K.N. Rao | Career | Dedicated career event charts — maps to `EventType.CAREER` |
| The Art of Prediction in Astrology | Gayatri Devi Vasudev | All events | Documented predictions with outcomes |
| Advanced Principles of Prediction | Gayatri Devi Vasudev | All events | Case studies with charts |

**K.N. Rao's event-specific books are goldmines** — each book focuses on ONE event type, which directly maps to the system's 5 prediction categories.

### Tier 3 — Technique-Specific (Feature Engineering Insights)

| Book | Author | Value |
|---|---|---|
| Predicting Through Navamsa and Nadi | C.S. Patel | Could improve Gate 1 navamsha features |
| Crux of Vedic Astrology — Timing of Events | Sanjay Rath | Could improve Gate 2 dasha features |
| Predicting Through Jaimini's Chara Dasha | K.N. Rao | Alternative dasha system — potential new features |
| Analytical Approach to Vedic Astrology | Dr. K.S. Charak | Specifically designed with documented case studies |

### Tier 4 — Journals & Archives (Bulk Data)

| Source | ~Charts | Notes |
|---|---|---|
| The Astrological Magazine (1936-2008) | ~500+ | Founded by B.V. Raman, 70 years of monthly case studies |
| Modern Astrology Magazine (2009-present) | ~100+ | Successor publication, edited by Gayatri Devi Vasudev |
| Journal of Astrology (K.N. Rao) | ~200+ | K.N. Rao's own journal with research articles |
| Saptarishis Astrology magazine | ~200+ | Modern Indian astrology research publication |

### K.N. Rao's Private Collection
- **50,000+ horoscopes** with 10 important life events each
- Perhaps the largest individual collection any astrologer has
- If 1% accessible → 500 charts, 5,000 labeled events — sufficient for XGBoost
- Contact via: Journal of Astrology / Bharatiya Vidya Bhavan astrology school

### Other Indian Sources
- **Indian public figures** — Politicians, cricketers, Bollywood stars whose birth data is published and life events well-documented. Wikipedia/Wikidata filtered for Indian nationals could yield ~2,000-5,000 entries (birth times need verification)
- **Crowd-sourced from Jyotish practitioners** — Partner with 5-10 practicing astrologers who have hundreds of client charts with known outcomes. Anonymize data. Most authentic training data possible.

---

## Part 4: Estimated Total Data Yield

| Source | Charts | Events |
|---|---|---|
| B.V. Raman books | ~270 | ~400+ |
| K.N. Rao event-specific books | ~200 | ~300+ |
| Gayatri Devi Vasudev books | ~100 | ~150+ |
| C.S. Patel / Sanjay Rath | ~80 | ~100+ |
| Journal archives | ~300 | ~500+ |
| **Total** | **~950** | **~1,450+** |

---

## Part 5: Key Training Challenges

### 1. Negative Sampling
Books only document events that DID happen. XGBoost needs both positive and negative labels.

**Strategies:**
| Strategy | How |
|----------|-----|
| Time-window negatives | If person married in 2015, their 2010 chart is a negative sample for marriage |
| Cross-event negatives | If someone had a career event but NOT marriage in same period → negative for marriage |
| Age-based negatives | No marriage prediction before age 16, no retirement before 40 |
| ADB absence | If a source documents a person extensively but lists no marriage → negative for marriage |

### 2. Temporal Alignment
The feature vector depends on `query_date` (affects Gate 2 dasha and Gate 3 transit scores). For book data:
- Use the actual event date as query_date for positive samples
- Use a different date (e.g., 5 years before event) for negative samples
- This ensures the dasha/transit features reflect the correct time period

### 3. Selection Bias
"Notable Horoscopes" features exceptional lives (prime ministers, celebrities). The model would be biased toward predicting dramatic outcomes for ordinary users.
- **Mitigation:** Weight ordinary charts higher, or use stratified sampling
- K.N. Rao's practitioner-based collection would have more ordinary people

### 4. Class Imbalance
Marriage and career events will dominate. Property and health events are rarer in books.
- **Mitigation:** SMOTE (Synthetic Minority Oversampling), class weights in XGBoost, or stratified k-fold

### 5. Data Scarcity
~950 charts is modest for ML. Minimum viable dataset considerations:
- XGBoost can work with hundreds of samples (better than deep learning for small data)
- Use 5-fold cross-validation to maximize training data usage
- Consider per-event-type models if data is too sparse for a unified model

### 6. Demographics Gap
Features 18-21 (gender, age, education, income) are placeholder `0.5` in feature_builder.py.
- Book charts rarely include education/income data
- Gender and approximate age can be inferred
- Consider dropping these features initially or keeping them as `0.5`

---

## Part 6: Zen AI Review & Recommendations

### Zen's Assessment of Structured Data Extraction
Zen confirmed that **structured data extraction (birth data + events into JSON) is the correct approach** for XGBoost training. Key points from Zen's review:

> "XGBoost is a gradient boosting library designed for structured, tabular data. Its input consists of numerical features and it predicts a target variable. Your 22-dimensional feature vector is precisely the kind of input XGBoost expects. The author's interpretive text does not serve as direct input for training an XGBoost model."

### Zen's Three Value Categories for Book Content

| Purpose | What to extract | Benefit |
|---|---|---|
| **XGBoost Training** | Birth data + event dates (structured JSON) | Direct ML training signal |
| **Feature Engineering** | Study interpretive text for predictive patterns not yet in 22 features | May inspire new Gate 1/2/3 features |
| **Narration Improvement** | Author's interpretive style, terminology, reasoning patterns | Could improve Claude API narration prompts (Layer 3) |

### Zen's Identified Risks

1. **Data Scarcity** — ~300-500 samples from books is the minimum. XGBoost handles small data better than deep learning but generalization is a concern.
2. **Selection Bias** — Notable horoscopes feature exceptional lives, not average users.
3. **Event Definition Inconsistency** — "Period of prosperity" vs "started business on YYYY-MM-DD". Inconsistent labeling introduces noise.
4. **Ground Truth Verification** — Historical text interpretations are not always objectively verifiable facts.
5. **Feature Sufficiency** — 22 features may not capture all Vedic astrology interaction effects. XGBoost learns interactions well but needs good base features.
6. **Interpretability** — XGBoost predictions should align with accepted Jyotish principles. SHAP (SHapley Additive exPlanations) values recommended for model interpretability.

### Our Critical Analysis of Zen's Review

**Where Zen is correct (~75% of review):**
- Structured extraction sufficient for XGBoost — Correct
- Book text valuable for narration (Layer 3) — Correct
- Selection bias concern — Correct
- Data scarcity as #1 risk — Correct

**Where Zen overstated:**
- "Text could inspire new features" — Partially true but overstated. The 22 features already cover major Jyotish factors. Better approach: analyze where gates produce wrong predictions on known events, then investigate what's missing (data-driven feature discovery > text reading).
- "22 features may not be enough" — Debatable for Phase 3 v1. Many production XGBoost models work with 10-50 features. Issue is sample count, not feature count.
- SHAP for interpretability — Correct but premature before having a working model.

**What Zen missed entirely:**
1. **Negative sampling strategy** — Critical for XGBoost. Books only give positives.
2. **Temporal alignment problem** — Which query_date for feature vector generation matters greatly for Gate 2/3 scores.
3. **Cross-validation strategy** — With ~300-500 samples, k-fold is essential. No mention from Zen.
4. **Class imbalance** — Some event types will have far more examples than others.

---

## Part 7: Recommended Data Collection Strategy

```
Week 1-2:   B.V. Raman books (Notable Horoscopes + Three Hundred Important
            Combinations + Hindu Predictive Astrology) → ~270 high-quality charts

Week 2-3:   K.N. Rao event-specific books (Marriage, Children, Careers)
            → ~200 targeted charts with event-specific labels

Week 3-4:   Gayatri Devi Vasudev books + journal archives
            → ~400 additional charts

Ongoing:    K.N. Rao partnership / Jyotish practitioner data /
            user retrospective events → scale to thousands
```

---

## Part 8: Data Extraction Format

For each chart extracted from books, create a structured JSON entry:

```json
{
  "source": "notable_horoscopes_bv_raman",
  "charts": [
    {
      "id": "NH_001",
      "birth_date": "1889-04-20",
      "birth_time": "18:30:00",
      "birth_place": "Braunau am Inn, Austria",
      "latitude": 48.26,
      "longitude": 13.04,
      "timezone_offset": 1.0,
      "birth_time_tier": 1,
      "gender": "male",
      "events": [
        {"event_type": "career", "event_date": "1933-01-30"},
        {"event_type": "marriage", "event_date": "1945-04-29"},
        {"event_type": "health", "event_date": "1945-04-30"}
      ]
    }
  ]
}
```

**Important:** Only factual data points (birth data + event dates) are extracted — not the author's interpretive analysis. The engine recomputes all astrological analysis from birth data via Layer 1 and Layer 2.

---

## Part 9: Phase 3 Implementation Pipeline (High-Level)

When ready to implement, the pipeline would be:

```
Step 1: Data Collection
        Extract structured chart data from books into JSON files
        Store in: data/training/

Step 2: Feature Generation
        For each chart + event pair:
        - Run Layer 1 (chart_computer) to compute birth chart
        - Run Layer 2 (3-gate scoring) with event_date as query_date
        - Call build_feature_vector() → 22-float vector
        - Label: 1 (positive) or 0 (negative via sampling strategy)

Step 3: Training Dataset Assembly
        - Combine all (feature_vector, label) pairs
        - Apply label smoothing for retrospective events
        - Generate negative samples (time-window + cross-event)
        - Split: 80% train, 20% validation (stratified by event type)

Step 4: Model Training
        - Train XGBoost classifier per event type (or unified)
        - Hyperparameter tuning via 5-fold cross-validation
        - Evaluate: AUC-ROC, precision, recall, calibration curve

Step 5: Model Storage
        - Save trained model as .json or .pkl
        - Store in: models/ directory
        - Version with metadata (training date, data sources, metrics)

Step 6: Inference Integration
        - Replace hand-coded convergence in orchestrator Step 5
        - Load model at startup
        - feature_vector → model.predict_proba() → calibrated confidence
        - Map probability to ConfidenceLevel (high/medium/low/insufficient)

Step 7: Monitoring
        - Track prediction accuracy as user events come in
        - Periodic retraining with new user data
        - SHAP values for interpretability checks
```

---

## Part 10: Key Decisions Pending

| Decision | Options | Impact |
|---|---|---|
| Unified vs per-event model | One model for all 5 events vs 5 separate models | Per-event allows event-specific features but needs more data per type |
| Negative sampling ratio | 1:1, 1:2, 1:3 (positive:negative) | Higher ratio = more conservative predictions |
| Demographics features | Keep as 0.5, drop, or infer from books | Affects feature vector dimensions |
| Model format | .pkl (pickle) vs .json (XGBoost native) | .json is portable, .pkl is faster |
| Retraining schedule | On-demand vs periodic (weekly/monthly) | Depends on data inflow rate |

---

*Research Date: March 5, 2026*
*Status: Research complete. Implementation pending.*
