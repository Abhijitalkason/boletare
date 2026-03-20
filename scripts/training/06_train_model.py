"""
Step 6: Train XGBoost model with Stratified 5-Fold Cross-Validation.

Runs TWO experiments to find the best approach:
  - Experiment A: XGBRegressor + smoothed labels (0.0/0.65/0.85) + optimal threshold
  - Experiment B: XGBClassifier + binary labels (0/1) + scale_pos_weight=2

Picks the winner by F1 score at optimal threshold.

Outputs:
  - models/xgboost_v1.json       — winning model (trained on all data)
  - models/cv_predictions.npz    — out-of-fold predictions + metadata for Step 7
  - models/feature_names.json    — 18 feature names for SHAP labeling
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import mlflow
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold
from xgboost import XGBClassifier, XGBRegressor

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "training"
MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "models"
INPUT_FILE = DATA_DIR / "training_set.npz"
OUTPUT_MODEL = MODEL_DIR / "xgboost_v1.json"
OUTPUT_CV = MODEL_DIR / "cv_predictions.npz"
OUTPUT_FEATURES = MODEL_DIR / "feature_names.json"

FEATURE_NAMES = [
    "g1_lord_dignity",
    "g1_occupant_score",
    "g1_navamsha_score",
    "g1_sav_normalized",
    "g1_overall_score",
    "g2_mahadasha_score",
    "g2_antardasha_score",
    "g2_overall_score",
    "g2_connection_count",
    "g3_overall_score",
    "g3_active_months_ratio",
    "g3_peak_bav_score",
    "convergence_normalized",
    "birth_time_tier",
    "lagna_mode",
    "dasha_boundary",
    "dasha_ambiguous",
    "is_retrospective",
]

# Shared hyperparameters (both experiments)
SHARED_PARAMS = {
    "max_depth": 3,
    "n_estimators": 100,
    "learning_rate": 0.1,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "min_child_weight": 1,
    "random_state": 42,
    "eval_metric": "logloss",
    "early_stopping_rounds": 10,
}

# Experiment A: Regressor with smoothed labels
REGRESSOR_PARAMS = {
    **SHARED_PARAMS,
    "objective": "reg:logistic",
}

# Experiment B: Classifier with binary labels
CLASSIFIER_PARAMS = {
    **SHARED_PARAMS,
    "objective": "binary:logistic",
    "scale_pos_weight": 2,
}


def find_optimal_threshold(y_true_binary: np.ndarray, y_prob: np.ndarray) -> tuple[float, float]:
    """Sweep thresholds 0.05-0.95, return (threshold, F1) that maximizes F1."""
    best_threshold = 0.5
    best_f1 = 0.0
    for t in np.arange(0.05, 0.96, 0.05):
        pred = (y_prob >= t).astype(int)
        f1 = f1_score(y_true_binary, pred, zero_division=0)
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = float(t)
    return best_threshold, best_f1


def run_cv(
    X: np.ndarray,
    y_train_labels: np.ndarray,
    y_eval_binary: np.ndarray,
    experiment_name: str,
    model_class: type,
    params: dict,
) -> dict:
    """Run Stratified 5-Fold CV and return metrics + OOF predictions."""
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    is_classifier = model_class == XGBClassifier

    oof_proba = np.zeros(len(y_train_labels))
    fold_metrics: list[dict] = []
    best_iterations: list[int] = []

    for fold_idx, (train_idx, test_idx) in enumerate(skf.split(X, y_eval_binary), 1):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train = y_train_labels[train_idx]
        y_eval_test = y_train_labels[test_idx]  # eval_set matches training label type
        y_test_bin = y_eval_binary[test_idx]

        model = model_class(**params)
        model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_eval_test)],
            verbose=False,
        )

        best_iter = model.best_iteration if hasattr(model, "best_iteration") else params.get("n_estimators", 100)
        best_iterations.append(best_iter)

        if is_classifier:
            proba = model.predict_proba(X_test)[:, 1]
        else:
            proba = model.predict(X_test)

        oof_proba[test_idx] = proba

        # Per-fold metrics at default 0.5 threshold (for logging)
        pred_05 = (proba >= 0.5).astype(int)
        fold_metrics.append({
            "fold": fold_idx,
            "best_iteration": best_iter,
            "accuracy": accuracy_score(y_test_bin, pred_05),
            "precision": precision_score(y_test_bin, pred_05, zero_division=0),
            "recall": recall_score(y_test_bin, pred_05, zero_division=0),
            "f1": f1_score(y_test_bin, pred_05, zero_division=0),
            "roc_auc": roc_auc_score(y_test_bin, proba) if len(set(y_test_bin)) > 1 else 0.0,
        })

    # Find optimal threshold on ALL OOF predictions
    optimal_threshold, optimal_f1 = find_optimal_threshold(y_eval_binary, oof_proba)
    oof_pred = (oof_proba >= optimal_threshold).astype(int)

    # Aggregate metrics at optimal threshold
    agg = {
        "accuracy_optimal": float(accuracy_score(y_eval_binary, oof_pred)),
        "precision_optimal": float(precision_score(y_eval_binary, oof_pred, zero_division=0)),
        "recall_optimal": float(recall_score(y_eval_binary, oof_pred, zero_division=0)),
        "f1_optimal": float(optimal_f1),
        "roc_auc": float(roc_auc_score(y_eval_binary, oof_proba)),
        "optimal_threshold": float(optimal_threshold),
        "median_best_iteration": int(np.median(best_iterations)),
    }

    # Also compute metrics at default 0.5 threshold for comparison
    oof_pred_05 = (oof_proba >= 0.5).astype(int)
    agg["f1_at_05"] = float(f1_score(y_eval_binary, oof_pred_05, zero_division=0))
    agg["accuracy_at_05"] = float(accuracy_score(y_eval_binary, oof_pred_05))

    return {
        "experiment_name": experiment_name,
        "aggregate": agg,
        "fold_metrics": fold_metrics,
        "best_iterations": best_iterations,
        "oof_proba": oof_proba,
        "oof_pred": oof_pred,
    }


def main() -> int:
    if not INPUT_FILE.exists():
        print(f"ERROR: Input file not found: {INPUT_FILE}")
        print("Run 05_build_training_set.py first.")
        return 1

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # Load data
    npz = np.load(INPUT_FILE)
    X_full, y = npz["X"], npz["y"]
    print(f"Loaded training set: X={X_full.shape}, y={y.shape}")

    # Drop placeholder features 18-21
    X = X_full[:, :18]
    print(f"Dropped features 18-21 (placeholders) -> X={X.shape}")

    # Binary labels for stratification and evaluation
    y_binary = (y > 0.5).astype(int)
    print(f"Positive: {y_binary.sum()}, Negative: {(1 - y_binary).sum()}")
    print(f"Smoothed label distribution: {dict(zip(*np.unique(y, return_counts=True)))}")

    # === EXPERIMENT A: Regressor + Smoothed Labels ===
    print(f"\n{'='*60}")
    print("EXPERIMENT A: Regressor + Smoothed Labels")
    print(f"{'='*60}")

    result_a = run_cv(
        X, y_train_labels=y, y_eval_binary=y_binary,
        experiment_name="regressor_smoothed",
        model_class=XGBRegressor, params=REGRESSOR_PARAMS,
    )
    agg_a = result_a["aggregate"]
    print(f"  F1 at 0.5 threshold:     {agg_a['f1_at_05']:.3f}")
    print(f"  Optimal threshold:       {agg_a['optimal_threshold']:.2f}")
    print(f"  F1 at optimal threshold: {agg_a['f1_optimal']:.3f}")
    print(f"  ROC-AUC:                 {agg_a['roc_auc']:.3f}")
    print(f"  Median best iteration:   {agg_a['median_best_iteration']}")

    # === EXPERIMENT B: Classifier + Binary Labels ===
    print(f"\n{'='*60}")
    print("EXPERIMENT B: Classifier + Binary Labels")
    print(f"{'='*60}")

    result_b = run_cv(
        X, y_train_labels=y_binary, y_eval_binary=y_binary,
        experiment_name="classifier_binary",
        model_class=XGBClassifier, params=CLASSIFIER_PARAMS,
    )
    agg_b = result_b["aggregate"]
    print(f"  F1 at 0.5 threshold:     {agg_b['f1_at_05']:.3f}")
    print(f"  Optimal threshold:       {agg_b['optimal_threshold']:.2f}")
    print(f"  F1 at optimal threshold: {agg_b['f1_optimal']:.3f}")
    print(f"  ROC-AUC:                 {agg_b['roc_auc']:.3f}")
    print(f"  Median best iteration:   {agg_b['median_best_iteration']}")

    # === PICK WINNER ===
    print(f"\n{'='*60}")
    print("COMPARISON")
    print(f"{'='*60}")

    if agg_a["f1_optimal"] >= agg_b["f1_optimal"]:
        winner = result_a
        winner_class = XGBRegressor
        winner_params = REGRESSOR_PARAMS
        winner_labels = y
        experiment_type = "regressor"
    else:
        winner = result_b
        winner_class = XGBClassifier
        winner_params = CLASSIFIER_PARAMS
        winner_labels = y_binary
        experiment_type = "classifier"

    print(f"  Exp A (Regressor):  F1={agg_a['f1_optimal']:.3f} (threshold={agg_a['optimal_threshold']:.2f})")
    print(f"  Exp B (Classifier): F1={agg_b['f1_optimal']:.3f} (threshold={agg_b['optimal_threshold']:.2f})")
    print(f"  WINNER: {winner['experiment_name']} (F1={winner['aggregate']['f1_optimal']:.3f})")

    # === TRAIN FINAL MODEL ON ALL DATA ===
    print(f"\n{'='*60}")
    print("TRAINING FINAL MODEL ON ALL DATA")
    print(f"{'='*60}")

    # Use median best_iteration from CV as n_estimators (Zen fix #2)
    median_iters = winner["aggregate"]["median_best_iteration"]
    final_n_estimators = max(median_iters, 10)  # minimum 10 trees
    final_params = {
        k: v for k, v in winner_params.items()
        if k != "early_stopping_rounds"
    }
    final_params["n_estimators"] = final_n_estimators
    print(f"  Using n_estimators={final_n_estimators} (median from CV)")

    final_model = winner_class(**final_params)
    final_model.fit(X, winner_labels, verbose=False)

    # Save model
    final_model.save_model(str(OUTPUT_MODEL))
    print(f"  Model saved to {OUTPUT_MODEL}")

    # Save CV predictions with metadata
    optimal_threshold = winner["aggregate"]["optimal_threshold"]
    np.savez(
        OUTPUT_CV,
        y_true=y_binary,
        y_pred=winner["oof_pred"],
        y_prob=winner["oof_proba"],
        y_smoothed=y,
        optimal_threshold=np.array([optimal_threshold]),
        experiment_type=np.array([experiment_type]),
    )
    print(f"  CV predictions saved to {OUTPUT_CV}")

    # Save feature names
    with open(OUTPUT_FEATURES, "w") as f:
        json.dump(FEATURE_NAMES, f, indent=2)
    print(f"  Feature names saved to {OUTPUT_FEATURES}")

    # === LOG TO MLFLOW ===
    mlflow.set_experiment("jyotish-training")

    for result in [result_a, result_b]:
        run_name = f"06_{result['experiment_name']}"
        is_winner = result["experiment_name"] == winner["experiment_name"]
        with mlflow.start_run(run_name=run_name):
            mlflow.log_params({
                "experiment_type": result["experiment_name"],
                "n_features": 18,
                "n_samples": len(y),
                "cv_folds": 5,
                "is_winner": is_winner,
            })
            for metric_name, value in result["aggregate"].items():
                mlflow.log_metric(metric_name, value)
            if is_winner:
                mlflow.log_artifact(str(OUTPUT_MODEL))

    # === SUMMARY ===
    agg = winner["aggregate"]
    print(f"\n{'='*60}")
    print("TRAINING SUMMARY")
    print(f"{'='*60}")
    print(f"  Winner:           {winner['experiment_name']}")
    print(f"  Optimal threshold:{agg['optimal_threshold']:.2f}")
    print(f"  F1 (optimal):     {agg['f1_optimal']:.3f}")
    print(f"  Accuracy:         {agg['accuracy_optimal']:.3f}")
    print(f"  ROC-AUC:          {agg['roc_auc']:.3f}")
    print(f"  Final n_trees:    {final_n_estimators}")
    print(f"  Model:            {OUTPUT_MODEL}")
    print(f"{'='*60}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
