# XGBoost & ML Guide for Jyotish AI — A Beginner's Guide

*This document explains how Machine Learning and XGBoost work, using our own Jyotish AI system as examples throughout. No prior ML knowledge required.*

---

## Table of Contents

1. [What is Machine Learning?](#1-what-is-machine-learning)
2. [The Jyotish Analogy — Why ML?](#2-the-jyotish-analogy--why-ml)
3. [What is a Feature?](#3-what-is-a-feature)
4. [Our 22 Features Explained](#4-our-22-features-explained)
5. [How the System Works TODAY (Phase 1)](#5-how-the-system-works-today-phase-1)
6. [What is XGBoost?](#6-what-is-xgboost)
7. [How Phase 3 Will Change Things](#7-how-phase-3-will-change-things)
8. [How Training Works — Step by Step](#8-how-training-works--step-by-step)
9. [How Prediction Works After Training](#9-how-prediction-works-after-training)
10. [Key ML Concepts You Need to Know](#10-key-ml-concepts-you-need-to-know)
11. [Complete Before vs After Flow](#11-complete-before-vs-after-flow)
12. [Glossary](#12-glossary)

---

## 1. What is Machine Learning?

Machine Learning (ML) is teaching a computer to **learn patterns from examples** instead of writing rules by hand.

### A Simple Analogy

Imagine you're a student learning Jyotish from a guru:

- **Traditional programming** = The guru gives you a rulebook: "If 7th lord is exalted AND Venus is strong, predict marriage." You follow the rules exactly.
- **Machine Learning** = The guru shows you 1,000 horoscopes and says "this person got married, this one didn't." You study them and figure out the patterns yourself.

The key difference:
- In traditional programming, **humans write the rules**
- In machine learning, **the computer discovers the rules** from data

### Why is ML Useful?

A human astrologer might know 50 rules for predicting marriage. But there could be subtle patterns they miss — like a combination of weak 7th lord + strong Venus + specific dasha + certain transit that works 73% of the time. ML can discover these hidden patterns from data.

---

## 2. The Jyotish Analogy — Why ML?

### What We Have Today (Phase 1 — Hand-coded Rules)

Right now, our system works like a student following a rulebook:

```
Score = 1.0 × Gate1 + 1.0 × Gate2 + 1.0 × Gate3

If Score >= 2.5 → HIGH confidence
If Score >= 1.5 → MEDIUM confidence
If Score >= 0.5 → LOW confidence
If Score <  0.5 → NEGATIVE
```

**The problem:** Who decided that the weights should be 1.0, 1.0, 1.0? Who decided 2.5 is the right threshold for HIGH? These are educated guesses based on expert guidance. They might not be optimal.

### What ML Will Do (Phase 3 — Learned Rules)

Instead of us guessing the weights and thresholds, we'll:
1. Show the computer hundreds of real horoscopes with known outcomes
2. Let it figure out the **best weights and thresholds** automatically
3. It might discover that Gate 2 (dasha) matters more than Gate 1 (promise) for marriage, but Gate 1 matters more for career

**Think of it like this:**
- Phase 1 = A first-year Jyotish student following textbook rules
- Phase 3 = An experienced astrologer who has seen 1,000 charts and developed intuition

---

## 3. What is a Feature?

A **feature** is a single measurable piece of information that describes something.

### Real-World Example

If you were describing a person to help someone find them in a crowd:

```
Feature 1: Height = 5.8 feet
Feature 2: Weight = 70 kg
Feature 3: Age = 30
Feature 4: Wearing glasses = Yes (1) or No (0)
```

Each feature is a **number** that captures one aspect of the person.

### Jyotish Example

If you were describing a horoscope to predict marriage:

```
Feature 1: 7th lord dignity score = 0.8 (strong)
Feature 2: Venus strength = 0.6 (moderate)
Feature 3: Dasha lord connection to 7th house = 0.9 (strong)
Feature 4: Jupiter transiting 7th house = 1.0 (yes)
```

### Why Numbers?

Computers can't understand "Venus is strong" or "the 7th lord is exalted." They only understand numbers. So we convert every astrological concept into a number between 0.0 (weakest) and 1.0 (strongest). This is called **normalization**.

### What is a Feature Vector?

A **feature vector** is simply a list of all features together. Our system creates a list of 22 numbers for every prediction:

```
[0.8, 0.6, 0.3, 0.7, 0.65, 0.9, 0.4, 0.7, 0.5, 0.8, 0.3, 0.6, 0.55, 1.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.5, 0.5, 0.5]
 ↑                              ↑                        ↑              ↑                        ↑
 Gate 1 scores                   Gate 2 scores             Gate 3 scores  Quality flags             Demographics
```

This is like a "fingerprint" of the horoscope — it captures everything important as numbers.

---

## 4. Our 22 Features Explained

Here's what each of the 22 numbers in our feature vector means:

### Gate 1 Features (0-4) — "Does the birth chart promise this event?"

| # | Feature | What it Measures | Example |
|---|---------|-----------------|---------|
| 0 | Lord Dignity | How strong is the house lord? Exalted=1.0, Debilitated=0.0 | 7th lord Jupiter exalted → 1.0 |
| 1 | Occupant Score | Are there benefic planets in the house? | Venus in 7th house → 0.8 |
| 2 | Navamsha Score | Does the D-9 chart support the event? | 7th lord strong in navamsha → 0.7 |
| 3 | SAV (Ashtakavarga) | How many benefic points does the house have? | 7th house has 30/48 points → 0.625 |
| 4 | Gate 1 Overall | Combined promise score | Average of above → 0.65 |

**In simple terms:** "Looking at the birth chart alone, does this person's horoscope support marriage?"

### Gate 2 Features (5-8) — "Is the right dasha running?"

| # | Feature | What it Measures | Example |
|---|---------|-----------------|---------|
| 5 | MD Score | Is the Mahadasha lord connected to the event? | Venus Mahadasha (natural 7th significator) → 0.9 |
| 6 | AD Score | Is the Antardasha lord connected? | Jupiter Antardasha (7th lord) → 0.8 |
| 7 | Gate 2 Overall | Combined dasha score | 0.85 |
| 8 | Connection Count | How many dasha-house connections exist? | 5 out of 8 possible → 0.625 |

**In simple terms:** "Is the current time period (dasha) activating the marriage-related planets?"

### Gate 3 Features (9-11) — "Are the transits favorable?"

| # | Feature | What it Measures | Example |
|---|---------|-----------------|---------|
| 9 | Gate 3 Overall | Transit window strength | Jupiter + Saturn both aspecting 7th → 0.8 |
| 10 | Active Months Ratio | What % of the next 24 months have favorable transits? | 8 out of 24 months → 0.33 |
| 11 | Peak BAV Score | Best ashtakavarga transit score in the window | Peak month has strong SAV → 0.7 |

**In simple terms:** "Are Jupiter and Saturn currently supporting this event through transit?"

### Feature 12 — Convergence Score

| # | Feature | What it Measures |
|---|---------|-----------------|
| 12 | Convergence | Combined score of all 3 gates (0-3 range, normalized to 0-1) |

**In simple terms:** "Overall, how strongly do all three factors (promise + dasha + transit) agree?"

### Quality Flags (13-17) — "How reliable is this prediction?"

| # | Feature | What it Measures | Values |
|---|---------|-----------------|--------|
| 13 | Birth Time Tier | How accurate is the birth time? | 1.0 = hospital certificate, 0.5 = family memory, 0.0 = rough guess |
| 14 | Lagna Mode | Which ascendant was used? | 0.0 = standard lagna, 1.0 = chandra lagna |
| 15 | Boundary Sensitive | Is the person born near a sign boundary? | 0.0 = No, 1.0 = Yes (less reliable) |
| 16 | Dasha Ambiguous | Is the dasha period boundary unclear? | 0.0 = No, 1.0 = Yes |
| 17 | Retrospective | Are we predicting a past event? | 0.0 = Future prediction, 1.0 = Past event |

**In simple terms:** "Should we trust this prediction more or less based on data quality?"

### Demographics (18-21) — "Who is this person?"

| # | Feature | What it Measures | Current Value |
|---|---------|-----------------|---------------|
| 18 | Gender | Male or Female | 0.5 (placeholder) |
| 19 | Age | How old is the person | 0.5 (placeholder) |
| 20 | Education | Education level | 0.5 (placeholder) |
| 21 | Income | Income bracket | 0.5 (placeholder) |

**Currently all set to 0.5** because we don't have real demographic data yet. These exist because cultural factors affect when events happen (e.g., marriage age varies by education level).

---

## 5. How the System Works TODAY (Phase 1)

### The Current Pipeline

```
Birth Data (date, time, place)
        │
        ▼
┌─────────────────────┐
│   LAYER 1: ENGINE    │   Computes the birth chart
│   (chart_computer)   │   Planets, houses, dashas,
│                      │   ashtakavarga, navamsha
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│   LAYER 2: PREDICT   │
│                      │
│  Gate 1 (Promise)────┼──→ score: 0.0 to 1.0
│  Gate 2 (Dasha)──────┼──→ score: 0.0 to 1.0
│  Gate 3 (Transit)────┼──→ score: 0.0 to 1.0
│                      │
│  ┌─────────────────┐ │
│  │  CONVERGENCE    │ │   ← THIS IS WHAT XGBOOST WILL REPLACE
│  │                 │ │
│  │  Score = 1.0×G1 │ │   Hand-coded weights (1.0, 1.0, 1.0)
│  │       + 1.0×G2  │ │   Hand-coded thresholds (2.5, 1.5, 0.5)
│  │       + 1.0×G3  │ │
│  │                 │ │
│  │  if >= 2.5: HIGH│ │
│  │  if >= 1.5: MED │ │
│  │  if >= 0.5: LOW │ │
│  │  else: NEGATIVE │ │
│  └─────────────────┘ │
│                      │
│  Feature Vector ─────┼──→ [22 numbers] (built but NOT used for scoring)
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  LAYER 3: NARRATE    │   Claude AI writes the prediction text
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  LAYER 4: DELIVER    │   Sends via API or WhatsApp
└─────────────────────┘
```

### The Problem with Hand-Coded Weights

```python
# Current code (convergence.py):
score = w1 * gate1.score + w2 * gate2.score + w3 * gate3.score

# w1 = 1.0, w2 = 1.0, w3 = 1.0 (all equal)
```

**Questions we can't answer today:**
- Should Gate 2 (dasha) matter MORE than Gate 1 (promise) for marriage? Maybe w2 should be 1.5?
- Is 2.5 really the right threshold for HIGH confidence? Maybe it should be 2.3?
- Should the quality flags (birth time tier, boundary sensitivity) reduce the confidence?
- Does age or gender affect when events happen?

**We are guessing.** ML lets the data tell us the answers.

---

## 6. What is XGBoost?

### The Name

**XGBoost** = e**X**treme **G**radient **Boost**ing

Don't worry about the fancy name. Let's understand it piece by piece.

### Step 1: What is a Decision Tree?

A decision tree is like a flowchart of yes/no questions:

```
                    Is Gate1 score > 0.6?
                   /                    \
                 YES                     NO
                 /                        \
        Is Gate2 score > 0.7?         PREDICT: No marriage
       /                    \
     YES                     NO
     /                        \
Is transit active?        PREDICT: Low chance
   /            \
  YES            NO
  /               \
PREDICT:        PREDICT:
High chance     Medium chance
```

This is exactly how a Jyotish astrologer thinks:
1. First check if the birth chart promises marriage (Gate 1)
2. If yes, check if the right dasha is running (Gate 2)
3. If yes, check if transits support it (Gate 3)

**A decision tree automates this thinking using data.**

### Step 2: What is "Boosting"?

One tree might make mistakes. So XGBoost builds **many trees** (typically 100-500), where each new tree tries to fix the mistakes of the previous ones.

```
Tree 1: Makes prediction → gets some wrong
                                    ↓
Tree 2: Focuses on the ones Tree 1 got WRONG → fixes some
                                    ↓
Tree 3: Focuses on the ones Tree 1+2 got WRONG → fixes more
                                    ↓
... (repeat 100-500 times) ...
                                    ↓
Final: Combine ALL trees → much better prediction
```

**Analogy:** Imagine 100 astrologers looking at the same chart:
- Astrologer 1 focuses on house lords
- Astrologer 2 focuses on what Astrologer 1 missed (dasha patterns)
- Astrologer 3 focuses on what both missed (transit timing)
- Together, they're much more accurate than any single astrologer

### Step 3: What is "Gradient"?

"Gradient" is the mathematical method XGBoost uses to figure out which mistakes to focus on next. Think of it like walking downhill:
- You're on a mountain (many errors)
- Each step (each tree) takes you downhill (fewer errors)
- Eventually you reach the bottom (best possible accuracy)

You don't need to understand the math. Just know that it's the technique that makes XGBoost find the best predictions efficiently.

### Why XGBoost and Not Something Else?

| Method | Good At | Bad At | For Us? |
|--------|---------|--------|---------|
| **XGBoost** | Small datasets (100-10,000 rows), tabular/numeric data, fast training | Images, text | **Perfect fit** — we have ~1,000 charts with 22 numeric features |
| Deep Learning (Neural Networks) | Images, text, very large datasets (100,000+) | Small datasets, hard to interpret | Too complex, needs too much data |
| Linear Regression | Very simple patterns | Complex interactions between features | Too simple — astrology has complex rules |
| Random Forest | General purpose, easy to use | Slightly less accurate than XGBoost | Good alternative, but XGBoost is better |

**XGBoost is the gold standard for structured/tabular data with small-to-medium datasets.** That's exactly what we have.

---

## 7. How Phase 3 Will Change Things

### Before (Phase 1) — Hand-coded

```
22 Features ──→ [HAND-CODED FORMULA] ──→ Score ──→ HIGH/MEDIUM/LOW
                     │
                     │  score = 1.0×G1 + 1.0×G2 + 1.0×G3
                     │  if score >= 2.5: HIGH
                     │  (humans wrote these rules)
```

### After (Phase 3) — XGBoost

```
22 Features ──→ [TRAINED XGBOOST MODEL] ──→ Probability ──→ HIGH/MEDIUM/LOW
                     │
                     │  model learned from 1,000+ real examples
                     │  automatically discovered:
                     │  - which features matter most
                     │  - how they interact
                     │  - optimal thresholds
```

### What Exactly Changes in the Code?

**Current code** (`convergence.py` line 41):
```python
score = w1 * gate1.score + w2 * gate2.score + w3 * gate3.score
```

**Phase 3 code** (conceptual):
```python
feature_vector = build_feature_vector(gate1, gate2, gate3, ...)
probability = xgboost_model.predict_proba(feature_vector)
# probability = 0.82 means "82% chance this event will happen"
```

### What XGBoost Discovers That We Can't

XGBoost might learn things like:

```
Discovery 1: For MARRIAGE predictions, Gate 2 (dasha) is 1.7x more
             important than Gate 1 (promise)

Discovery 2: When birth_time_tier = 0.0 (rough guess), the prediction
             should be 30% less confident

Discovery 3: If Gate 1 > 0.7 AND Gate 2 > 0.6 AND Gate 3 > 0.5,
             confidence should be HIGH (not just when sum >= 2.5)

Discovery 4: The navamsha score (feature 2) matters much more for
             marriage than for career predictions
```

These are **non-linear interactions** — things a simple weighted sum can't capture, but XGBoost can.

---

## 8. How Training Works — Step by Step

Training is the process of showing examples to XGBoost so it can learn patterns.

### Step 1: Prepare the Training Data

We extract data from books (B.V. Raman, K.N. Rao, etc.):

```
Person A: Born 1950-03-15, 06:30, Bangalore
          Events: married 1975-06-10, career_change 1980-01-15

Person B: Born 1962-11-22, 14:00, Delhi
          Events: married 1985-03-20, child 1988-07-01

Person C: Born 1970-08-05, 09:15, Mumbai
          Events: career_change 1995-04-10
          (No marriage documented → useful for negative samples)
```

### Step 2: Generate Feature Vectors

For each person + event combination, run our existing engine:

```
Person A + "marriage on 1975-06-10":
  → Layer 1 computes birth chart
  → Gate 1 evaluates 7th house promise → 0.75
  → Gate 2 evaluates dasha on 1975-06-10 → 0.82
  → Gate 3 evaluates transits on 1975-06-10 → 0.68
  → Feature vector: [0.8, 0.6, 0.7, 0.65, 0.75, 0.9, 0.8, 0.82, 0.5, 0.68, 0.4, 0.55, 0.75, 1.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.5, 0.5, 0.5]
  → Label: 1 (marriage DID happen)
```

### Step 3: Create Negative Samples

We also need examples where events did NOT happen:

```
Person A + "marriage on 1965-06-10" (10 years BEFORE actual marriage):
  → Same birth chart
  → Gate 2 evaluates dasha on 1965 → 0.3 (different dasha running)
  → Gate 3 evaluates transits on 1965 → 0.2 (no favorable transit)
  → Feature vector: [0.8, 0.6, 0.7, 0.65, 0.75, 0.2, 0.3, 0.3, 0.1, 0.2, 0.1, 0.3, 0.35, 1.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.5, 0.5, 0.5]
  → Label: 0 (marriage did NOT happen in 1965)
```

### Step 4: Build the Training Table

After processing all charts, we get a table like this:

```
| Feature 0 | Feature 1 | ... | Feature 21 | Label |
|-----------|-----------|-----|------------|-------|
|    0.80   |    0.60   | ... |    0.50    |   1   |  ← Person A, marriage happened
|    0.80   |    0.60   | ... |    0.50    |   0   |  ← Person A, marriage NOT yet (1965)
|    0.65   |    0.70   | ... |    0.50    |   1   |  ← Person B, marriage happened
|    0.65   |    0.70   | ... |    0.50    |   0   |  ← Person B, career NOT happened
|    0.55   |    0.40   | ... |    0.50    |   1   |  ← Person C, career happened
|    0.55   |    0.40   | ... |    0.50    |   0   |  ← Person C, marriage NOT happened
| ...       |    ...    | ... |    ...     |  ...  |
```

With ~950 charts and negative sampling, we'd have **~3,000-5,000 rows** in this table.

### Step 5: Train XGBoost

```python
import xgboost as xgb

# Load training data
X = all_feature_vectors  # shape: (3000, 22) → 3000 rows, 22 columns
y = all_labels           # shape: (3000,)    → 1 or 0 for each row

# Train the model
model = xgb.XGBClassifier(
    n_estimators=200,      # Build 200 decision trees
    max_depth=4,           # Each tree can ask up to 4 questions deep
    learning_rate=0.1,     # Learn slowly (more stable)
)
model.fit(X, y)

# Save the model
model.save_model("models/marriage_model.json")
```

**What happens inside `model.fit()`:**
1. Tree 1 looks at all 3,000 examples, finds the best yes/no questions to separate marriages from non-marriages
2. Tree 2 focuses on the 500 examples Tree 1 got wrong
3. Tree 3 focuses on the 200 examples Trees 1+2 got wrong
4. ... repeat 200 times ...
5. Final model: 200 trees that together predict marriage probability very accurately

### Step 6: Evaluate the Model

After training, we check how good the model is:

```
Tested on 600 examples (20% of data, held out):

                    Predicted YES    Predicted NO
Actual YES              240              30        ← 89% caught (recall)
Actual NO                40             290        ← 88% correct (precision)

Overall Accuracy: 88%
```

This tells us: "When the model says HIGH confidence, it's right 88% of the time."

---

## 9. How Prediction Works After Training

Once the model is trained and saved, here's how a real prediction works:

```
┌──────────────────────────────────────────────────────────────┐
│                    USER REQUEST                               │
│  "Will Rahul get married? Born: 1995-03-15, 08:30, Pune"     │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 1: LAYER 1 — COMPUTE BIRTH CHART                       │
│  → Planets, houses, dashas, ashtakavarga, navamsha            │
│  (Same as today — no change)                                  │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 2: LAYER 2 — RUN THREE GATES                           │
│  → Gate 1 (Promise): 0.72                                     │
│  → Gate 2 (Dasha):   0.85                                     │
│  → Gate 3 (Transit): 0.61                                     │
│  (Same as today — no change)                                  │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 3: BUILD FEATURE VECTOR                                 │
│  → [0.8, 0.6, 0.7, 0.65, 0.72, 0.9, 0.8, 0.85, ...]        │
│  → 22 numbers, each between 0.0 and 1.0                      │
│  (Same as today — no change)                                  │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 4: XGBOOST PREDICTION  ← ← ← THIS IS NEW              │
│                                                               │
│  OLD WAY:  score = 1.0×0.72 + 1.0×0.85 + 1.0×0.61 = 2.18    │
│            → MEDIUM (because 2.18 < 2.5)                      │
│                                                               │
│  NEW WAY:  probability = model.predict_proba([features])      │
│            → 0.78 (78% chance of marriage)                     │
│            → HIGH (because model learned that this specific    │
│              combination of strong dasha + decent promise      │
│              + moderate transit = high confidence)             │
│                                                               │
│  The model sees patterns the simple formula misses!           │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 5-6: NARRATE + DELIVER                                  │
│  (Same as today — no change)                                  │
└──────────────────────────────────────────────────────────────┘
```

### Key Insight

**Only Step 4 changes.** Everything before (chart computation, gate scoring, feature building) and everything after (narration, delivery) stays exactly the same. XGBoost is a **drop-in replacement** for the hand-coded convergence formula.

---

## 10. Key ML Concepts You Need to Know

### 10.1 Training Data vs Test Data

```
All Data (1,000 charts)
     │
     ├── 80% → Training Data (800 charts)
     │         XGBoost learns from these
     │
     └── 20% → Test Data (200 charts)
               We check accuracy on these
               XGBoost NEVER sees these during training
```

**Why split?** If you test a student using the same questions they studied, you can't tell if they actually understand or just memorized. Same with ML — we test on data the model never saw.

### 10.2 Overfitting — The #1 Danger

**Overfitting** = the model memorizes the training data instead of learning general patterns.

**Jyotish analogy:** Imagine an astrologer who has only seen 10 charts. He notices that all 3 people who got married had Moon in Taurus. He concludes: "Moon in Taurus = marriage!" But this was just a coincidence in his small sample. With 1,000 charts, this pattern would disappear.

**Signs of overfitting:**
- 99% accuracy on training data, but 60% on test data
- Model makes very specific rules that only apply to the training examples

**How to prevent it:**
- Use enough training data (300+ examples minimum)
- Don't make trees too deep (`max_depth=4` instead of `max_depth=20`)
- Use cross-validation (see below)

### 10.3 Cross-Validation

With only ~1,000 charts, we can't afford to waste 20% on testing. **Cross-validation** lets us use ALL data for both training and testing:

```
5-Fold Cross-Validation:

Round 1: Train on folds 2,3,4,5 → Test on fold 1 → Accuracy: 85%
Round 2: Train on folds 1,3,4,5 → Test on fold 2 → Accuracy: 87%
Round 3: Train on folds 1,2,4,5 → Test on fold 3 → Accuracy: 83%
Round 4: Train on folds 1,2,3,5 → Test on fold 4 → Accuracy: 86%
Round 5: Train on folds 1,2,3,4 → Test on fold 5 → Accuracy: 84%

Average Accuracy: 85%
```

Every chart gets used for training 4 times and testing once. No data is wasted.

### 10.4 Negative Sampling

Our books only tell us about events that **happened**. But the model also needs to learn what "no event" looks like.

```
POSITIVE sample: Person married in 2015
  → Feature vector computed at query_date=2015 → Label = 1

NEGATIVE sample: Same person, but we ask "married in 2005?"
  → Feature vector computed at query_date=2005 → Label = 0
  (Different dasha was running, different transits)
```

**Why it matters:** Without negative samples, the model would predict "YES" for everything.

**Common ratio:** 1 positive : 2 negatives. So for 1,000 positive examples, we generate 2,000 negative examples.

### 10.5 Label Smoothing

Not all labels are equally reliable:

```
"I got married on 2020-03-15"     → Label confidence: 1.0 (recent, exact date)
"I got married around 1985"       → Label confidence: 0.7 (approximate)
"I think I changed jobs in 1978"  → Label confidence: 0.5 (vague memory)
```

Our system already has this built in (`EventService._compute_label_smoothing`). Instead of hard 0/1 labels, we use soft labels (0.0 to 1.0) that reflect how sure we are about the event date.

### 10.6 Class Imbalance

If we have 500 marriage examples but only 50 health examples, the model will be great at predicting marriage but terrible at health.

**Solutions:**
- **Class weights:** Tell XGBoost "each health example is worth 10× more than each marriage example"
- **SMOTE:** Generate synthetic health examples by combining similar real ones
- **Separate models:** Train one model per event type (marriage model, career model, etc.)

### 10.7 Feature Importance

After training, XGBoost can tell us which features matter most:

```
Feature Importance (example):

Gate 2 overall (dasha)    ████████████████████ 18%
Gate 1 overall (promise)  ███████████████      14%
MD score                  ██████████████       13%
Gate 3 overall (transit)  ████████████         11%
AD score                  ██████████           9%
Lord dignity              █████████            8%
Navamsha score            ████████             7%
Birth time tier           ██████               5%
SAV normalized            █████                4%
Active months ratio       ████                 3%
...                       ...                  ...
```

This tells us: "Dasha (Gate 2) matters most for predictions, followed by promise (Gate 1)."

### 10.8 SHAP Values — Understanding Individual Predictions

SHAP (SHapley Additive exPlanations) tells us WHY a specific prediction was made:

```
Prediction: "Rahul has 78% chance of marriage"

WHY?
  Gate 2 (dasha) score = 0.85     pushed prediction UP by +15%
  Gate 1 (promise) score = 0.72   pushed prediction UP by +10%
  Gate 3 (transit) score = 0.61   pushed prediction UP by +5%
  Birth time tier = 0.5           pushed prediction DOWN by -3%
  Navamsha score = 0.3            pushed prediction DOWN by -2%
  ...

  Base rate (average prediction):  53%
  + All contributions:             +25%
  = Final prediction:              78%
```

This is important for **trust** — when a user asks "why did you predict HIGH?", we can explain exactly which astrological factors contributed.

### 10.9 Hyperparameters

Hyperparameters are **settings** you choose before training. The model doesn't learn these — you set them:

| Hyperparameter | What it Controls | Our Likely Value |
|---------------|-----------------|-----------------|
| `n_estimators` | How many trees to build | 100-300 |
| `max_depth` | How many questions each tree can ask | 3-5 |
| `learning_rate` | How fast to learn (slower = more stable) | 0.05-0.1 |
| `min_child_weight` | Minimum examples needed to make a split | 5-10 |
| `subsample` | What % of data each tree sees | 0.7-0.9 |

**Finding the best values:** We try different combinations and see which gives the best cross-validation accuracy. This is called **hyperparameter tuning**.

---

## 11. Complete Before vs After Flow

### BEFORE (Phase 1 — Current System)

```
Birth Data
    │
    ▼
Layer 1: Compute Chart ──→ planets, houses, dashas
    │
    ▼
Layer 2: Three Gates
    │
    ├─ Gate 1 (Promise)  ──→ score (0-1)
    ├─ Gate 2 (Dasha)    ──→ score (0-1)
    └─ Gate 3 (Transit)  ──→ score (0-1)
    │
    ▼
HAND-CODED FORMULA:
    score = 1.0 × G1 + 1.0 × G2 + 1.0 × G3
    │
    ▼
FIXED THRESHOLDS:
    >= 2.5 → HIGH
    >= 1.5 → MEDIUM
    >= 0.5 → LOW
    <  0.5 → NEGATIVE
    │
    ▼
Feature Vector built (22 numbers) ──→ stored in DB but NOT USED for scoring
    │
    ▼
Layer 3: Claude narrates ──→ "Based on your chart..."
    │
    ▼
Layer 4: Deliver via API/WhatsApp
```

### AFTER (Phase 3 — With XGBoost)

```
Birth Data
    │
    ▼
Layer 1: Compute Chart ──→ planets, houses, dashas    [NO CHANGE]
    │
    ▼
Layer 2: Three Gates                                   [NO CHANGE]
    │
    ├─ Gate 1 (Promise)  ──→ score (0-1)
    ├─ Gate 2 (Dasha)    ──→ score (0-1)
    └─ Gate 3 (Transit)  ──→ score (0-1)
    │
    ▼
Feature Vector built (22 numbers)                      [NO CHANGE]
    │
    ▼
XGBOOST MODEL:                                        [NEW — REPLACES FORMULA]
    probability = model.predict_proba(feature_vector)
    │
    ├─ probability = 0.85 → HIGH     (model learned this threshold)
    ├─ probability = 0.60 → MEDIUM   (from real data)
    ├─ probability = 0.35 → LOW
    └─ probability = 0.15 → NEGATIVE
    │
    ▼
Layer 3: Claude narrates ──→ "Based on your chart..."  [NO CHANGE]
    │
    ▼
Layer 4: Deliver via API/WhatsApp                      [NO CHANGE]
```

### What's Different?

| Aspect | Phase 1 (Today) | Phase 3 (XGBoost) |
|--------|-----------------|-------------------|
| How confidence is calculated | `1.0×G1 + 1.0×G2 + 1.0×G3` | Model uses all 22 features, learned weights |
| Weights | Fixed by humans (1.0, 1.0, 1.0) | Learned from 1,000+ real examples |
| Thresholds | Fixed (2.5, 1.5, 0.5) | Learned from data |
| Can learn interactions | No — just adds scores | Yes — can learn "if G1 high AND G2 high, then extra boost" |
| Uses quality flags | No — they're ignored | Yes — birth time tier affects confidence |
| Uses demographics | No — placeholder 0.5 | Can use real values if available |
| Adapts over time | No — fixed forever | Yes — retrain with new data |
| Output | Score (0-3) | Probability (0%-100%) |

---

## 12. Glossary

| Term | Simple Meaning |
|------|---------------|
| **Feature** | A single number describing one aspect of the data (e.g., "lord dignity = 0.8") |
| **Feature Vector** | A list of all features together (our 22 numbers) |
| **Label** | The answer we're trying to predict (1 = event happened, 0 = didn't happen) |
| **Training** | Showing the model many examples so it can learn patterns |
| **Inference** | Using the trained model to make predictions on new data |
| **Model** | The trained "brain" — a file containing all the learned patterns |
| **Decision Tree** | A flowchart of yes/no questions that leads to a prediction |
| **Boosting** | Building many trees where each fixes the mistakes of the previous ones |
| **Overfitting** | Model memorizes training data instead of learning general patterns |
| **Cross-Validation** | Rotating which data is used for training vs testing to maximize data usage |
| **Negative Sampling** | Creating examples of "event did NOT happen" for balanced training |
| **Label Smoothing** | Using soft labels (0.7 instead of 1.0) when the event date is uncertain |
| **Class Imbalance** | Having too many examples of one type (500 marriages) vs another (50 health events) |
| **Hyperparameters** | Settings you choose before training (number of trees, depth, learning rate) |
| **Feature Importance** | Which features matter most for predictions (ranked list) |
| **SHAP Values** | Explanation of why a specific prediction was made (which features pushed it up/down) |
| **Normalization** | Converting values to a standard range (0.0 to 1.0) so they're comparable |
| **Epoch** | One complete pass through all training data (XGBoost uses "rounds" instead) |
| **Precision** | When model says YES, how often is it correct? |
| **Recall** | Of all actual YES cases, how many did the model find? |
| **AUC-ROC** | Overall measure of model quality (1.0 = perfect, 0.5 = random guessing) |
| **Gradient** | Mathematical technique for finding the best direction to reduce errors |
| **Calibration** | Ensuring that "80% confidence" actually means right 80% of the time |

---

*This document is part of the Jyotish AI project documentation.*
*See also: `XGBOOST_TRAINING_DATA_RESEARCH.md` for training data sources and collection strategy.*
