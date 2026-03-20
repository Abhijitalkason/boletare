# ML Concepts — Quick Reference

## 1. Negative Sampling

**What:** Creating synthetic "wrong" examples to train a model alongside real "correct" examples.

**Why:** Most real-world data only has positive examples (things that happened). The model needs to also learn what *doesn't* match to make useful predictions.

**Example from our pipeline:**
- Nehru's marriage in 1916 → **positive sample** (real event)
- Nehru's marriage shifted to 1911 → **negative sample** (didn't happen at this time)
- Nehru's career_change in 1916 → **negative sample** (wrong event type)

### Types of Negatives

| Type | Description | Difficulty |
|------|-------------|------------|
| **Hard Negatives** | Very similar to positives — differ in only one subtle aspect | Hard for model to distinguish |
| **Easy Negatives** | Clearly different from positives — differ in multiple aspects | Easy for model to distinguish |
| **Random Negatives** | Randomly sampled from the dataset | Variable difficulty |

### Our Strategy: Mixed Negatives (1:2 ratio)

For each real event, we generate 2 negatives:

```
Real Event (Positive)
  |
  +-- Time-Shifted Negative (HARD)
  |     Same person, same event type, time shifted -5 years
  |     Forces model to learn precise planetary timing
  |
  +-- Cross-Event Negative (EASIER)
        Same person, same time, different event type
        Forces model to distinguish event types
```

**Result:** 36 real events → 36 positives + 72 negatives = 108 training samples

---

## 2. Label Smoothing

**What:** Instead of using hard labels (0 or 1), use softer values (0.65 or 0.85) for positives.

**Why:** Real-world data has uncertainty. OCR-parsed birth times may be approximate. Label smoothing prevents the model from becoming overconfident on noisy data.

**Our values:**
| Label | Value | When Used |
|-------|-------|-----------|
| `LABEL_POSITIVE_EXACT` | 0.85 | Birth time is precisely known |
| `LABEL_POSITIVE_APPROXIMATE` | 0.65 | Birth time is approximate/uncertain |
| `LABEL_NEGATIVE` | 0.0 | Synthetic negative samples |

**Without smoothing:** Model learns "this is 100% correct" even for approximate data → overfitting.
**With smoothing:** Model learns "this is probably correct" → better generalization.

---

## 3. Feature Engineering

**What:** Converting raw data into numerical vectors the model can process.

**Our pipeline:** Each event becomes a 22-dimensional feature vector containing:
- Planetary positions (longitude in zodiac)
- House positions
- Planetary aspects (angular relationships)

```
Raw: "Nehru born 14 Nov 1889, 23:11, Allahabad"
  → Astronomical calculation (Swiss Ephemeris)
  → [284.5, 132.7, 45.2, ..., 178.3]  (22 numbers)
```

---

## 4. Contrastive Learning

**What:** A training paradigm where the model learns by comparing similar and dissimilar pairs.

**How it works:**
1. Show model a positive example (real event + correct planetary positions)
2. Show model a negative example (fake event + different planetary positions)
3. Model learns: "what makes the positive different from the negative?"

**Analogy:** Learning to identify a friend's face — you don't just memorize their face, you also learn how it differs from other faces.

**Our use:** Each training batch contains both positive (real events) and negative (synthetic non-events). XGBoost learns which planetary patterns correlate with real events vs. non-events.

---

## 5. Train / Validation / Test Split

**What:** Dividing data into three non-overlapping sets.

| Set | Purpose | Typical Size |
|-----|---------|-------------|
| **Training** | Model learns from this | 70% |
| **Validation** | Tune hyperparameters, prevent overfitting | 15% |
| **Test** | Final unbiased evaluation | 15% |

**Rule:** Never let the model see test data during training. Test set = exam the model hasn't studied for.

**Our pipeline (current):** Single training set. Train/val/test split is Phase 5 (deferred until dataset grows).

---

## 6. XGBoost

**What:** Extreme Gradient Boosting — an ensemble of decision trees trained sequentially, where each tree corrects the errors of the previous one.

**Why XGBoost for this project:**
- Works well with small datasets (108 samples)
- Handles tabular/numerical features naturally (our 22-dim vectors)
- Fast training and inference
- Built-in feature importance — tells us which planetary positions matter most

---

## 7. Data Versioning (DVC)

**What:** Git for data. Tracks large data files without storing them in git.

**How:**
```
git tracks:  training_set.npz.dvc  (small metadata file — hash + size)
DVC tracks:  training_set.npz      (actual data — could be GBs)
```

**Why:** Data changes over time (new charts added, parsing bugs fixed). DVC lets you reproduce any previous version of the data.

---

## 8. Experiment Tracking (MLflow)

**What:** Logging parameters, metrics, and artifacts for every pipeline run.

**What we track:**
- **Parameters:** label smoothing values, feature dimensions
- **Metrics:** sample counts, positive/negative ratio, charts processed
- **Artifacts:** training metadata JSON

**Why:** When you run the pipeline 50 times with different settings, MLflow tells you which run produced the best results.

---

## 9. Key ML Terms Glossary

| Term | Definition |
|------|-----------|
| **Overfitting** | Model memorizes training data but fails on new data |
| **Underfitting** | Model is too simple to capture patterns |
| **Epoch** | One complete pass through the training data |
| **Hyperparameter** | Settings you choose before training (learning rate, tree depth) |
| **Feature Vector** | Numerical representation of one data sample |
| **Ground Truth** | The correct/known answer for a training sample |
| **Batch** | Subset of training data processed together |
| **Loss Function** | Measures how wrong the model's predictions are |
| **Gradient Descent** | Algorithm that adjusts model weights to minimize loss |
| **Ensemble** | Combining multiple models for better predictions (XGBoost does this) |
| **Stratified Split** | Splitting data while maintaining class proportions in each set |
