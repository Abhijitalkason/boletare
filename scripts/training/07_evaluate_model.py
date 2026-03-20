"""
Step 7: Evaluate trained XGBoost model.

Loads the winning model and CV predictions from Step 6 (including
experiment type and optimal threshold metadata).

Generates:
  - Confusion matrix plot
  - Classification report
  - ROC + Precision-Recall curves
  - SHAP feature importance plot
  - Rule-based baseline comparison
  - Evaluation report JSON
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import mlflow
import numpy as np
import shap
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)
from xgboost import XGBClassifier, XGBRegressor

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "training"
MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "models"
INPUT_CV = MODEL_DIR / "cv_predictions.npz"
INPUT_MODEL = MODEL_DIR / "xgboost_v1.json"
INPUT_TRAINING = DATA_DIR / "training_set.npz"
INPUT_FEATURES = MODEL_DIR / "feature_names.json"

OUTPUT_CONFUSION = MODEL_DIR / "confusion_matrix.png"
OUTPUT_REPORT_TXT = MODEL_DIR / "classification_report.txt"
OUTPUT_ROC_PR = MODEL_DIR / "roc_pr_curves.png"
OUTPUT_SHAP = MODEL_DIR / "feature_importance.png"
OUTPUT_REPORT = MODEL_DIR / "evaluation_report.json"


def plot_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, output_path: Path) -> dict:
    """Plot confusion matrix heatmap and return TP/FP/TN/FN."""
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()

    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(["Negative", "Positive"])
    ax.set_yticklabels(["Negative", "Positive"])
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Confusion Matrix (5-Fold CV)")

    for i in range(2):
        for j in range(2):
            color = "white" if cm[i, j] > cm.max() / 2 else "black"
            ax.text(j, i, str(cm[i, j]), ha="center", va="center", color=color, fontsize=18)

    fig.colorbar(im)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    return {"TP": int(tp), "FP": int(fp), "TN": int(tn), "FN": int(fn)}


def plot_roc_pr_curves(y_true: np.ndarray, y_prob: np.ndarray, output_path: Path) -> dict:
    """Plot ROC and PR curves side by side."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # ROC curve
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    roc_auc = roc_auc_score(y_true, y_prob)
    ax1.plot(fpr, tpr, color="blue", lw=2, label=f"ROC-AUC = {roc_auc:.3f}")
    ax1.plot([0, 1], [0, 1], color="gray", linestyle="--", lw=1)
    ax1.set_xlabel("False Positive Rate")
    ax1.set_ylabel("True Positive Rate")
    ax1.set_title("ROC Curve")
    ax1.legend(loc="lower right")
    ax1.grid(alpha=0.3)

    # PR curve
    precision_vals, recall_vals, _ = precision_recall_curve(y_true, y_prob)
    pr_auc = average_precision_score(y_true, y_prob)
    ax2.plot(recall_vals, precision_vals, color="green", lw=2, label=f"PR-AUC = {pr_auc:.3f}")
    baseline = y_true.sum() / len(y_true)
    ax2.axhline(y=baseline, color="gray", linestyle="--", lw=1, label=f"Baseline = {baseline:.3f}")
    ax2.set_xlabel("Recall")
    ax2.set_ylabel("Precision")
    ax2.set_title("Precision-Recall Curve")
    ax2.legend(loc="upper right")
    ax2.grid(alpha=0.3)

    fig.suptitle("Model Discrimination", fontsize=14)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    return {"roc_auc": float(roc_auc), "pr_auc": float(pr_auc)}


def plot_shap_importance(
    model_path: Path, X: np.ndarray, feature_names: list[str],
    experiment_type: str, output_path: Path,
) -> list[dict]:
    """Compute SHAP values and plot feature importance."""
    if experiment_type == "classifier":
        model = XGBClassifier()
    else:
        model = XGBRegressor()
    model.load_model(str(model_path))

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    sorted_idx = np.argsort(mean_abs_shap)[::-1]

    fig, ax = plt.subplots(figsize=(10, 6))
    y_pos = range(len(feature_names))
    ax.barh(
        y_pos,
        mean_abs_shap[sorted_idx[::-1]],
        color="steelblue",
    )
    ax.set_yticks(y_pos)
    ax.set_yticklabels([feature_names[i] for i in sorted_idx[::-1]])
    ax.set_xlabel("Mean |SHAP Value|")
    ax.set_title("Feature Importance (SHAP)")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    importance = []
    for idx in sorted_idx:
        importance.append({
            "feature": feature_names[idx],
            "mean_abs_shap": float(mean_abs_shap[idx]),
        })
    return importance


def compute_baseline_comparison(
    y_true: np.ndarray, y_pred: np.ndarray, X: np.ndarray
) -> dict:
    """Compare XGBoost vs convergence baseline vs naive baseline."""
    xgb_accuracy = accuracy_score(y_true, y_pred)
    xgb_f1 = f1_score(y_true, y_pred, zero_division=0)

    # Naive baseline: always predict negative (majority class)
    naive_pred = np.zeros_like(y_true)
    naive_accuracy = accuracy_score(y_true, naive_pred)

    # Convergence baseline: feature 12 (convergence_normalized) with threshold sweep
    convergence_scores = X[:, 12]
    best_conv_acc = 0.0
    best_conv_threshold = 0.0
    best_conv_f1 = 0.0
    for threshold in np.arange(0.1, 1.0, 0.05):
        conv_pred = (convergence_scores >= threshold).astype(int)
        acc = accuracy_score(y_true, conv_pred)
        f1 = f1_score(y_true, conv_pred, zero_division=0)
        if acc > best_conv_acc:
            best_conv_acc = acc
            best_conv_threshold = float(threshold)
            best_conv_f1 = f1

    return {
        "xgboost_accuracy": float(xgb_accuracy),
        "xgboost_f1": float(xgb_f1),
        "naive_accuracy": float(naive_accuracy),
        "convergence_best_accuracy": float(best_conv_acc),
        "convergence_best_threshold": best_conv_threshold,
        "convergence_best_f1": float(best_conv_f1),
        "xgboost_beats_naive": xgb_accuracy > naive_accuracy,
        "xgboost_beats_convergence": xgb_accuracy > best_conv_acc,
    }


def main() -> int:
    # Check inputs
    for f in [INPUT_CV, INPUT_MODEL, INPUT_TRAINING, INPUT_FEATURES]:
        if not f.exists():
            print(f"ERROR: Required file not found: {f}")
            print("Run 06_train_model.py first.")
            return 1

    # Load data
    cv_data = np.load(INPUT_CV, allow_pickle=True)
    y_true = cv_data["y_true"]
    y_pred = cv_data["y_pred"]
    y_prob = cv_data["y_prob"]
    optimal_threshold = float(cv_data["optimal_threshold"][0])
    experiment_type = str(cv_data["experiment_type"][0])

    training_data = np.load(INPUT_TRAINING)
    X = training_data["X"][:, :18]  # Drop features 18-21

    with open(INPUT_FEATURES) as f:
        feature_names = json.load(f)

    print(f"Loaded CV predictions: {len(y_true)} samples")
    print(f"Loaded training features: X={X.shape}")
    print(f"Experiment type: {experiment_type}")
    print(f"Optimal threshold: {optimal_threshold:.2f}")

    # A. Confusion Matrix
    print("\n--- Confusion Matrix ---")
    cm_metrics = plot_confusion_matrix(y_true, y_pred, OUTPUT_CONFUSION)
    print(f"  TP={cm_metrics['TP']} FP={cm_metrics['FP']} TN={cm_metrics['TN']} FN={cm_metrics['FN']}")
    print(f"  Saved: {OUTPUT_CONFUSION}")

    # B. Classification Report
    print("\n--- Classification Report ---")
    report_text = classification_report(
        y_true, y_pred, target_names=["negative", "positive"], zero_division=0
    )
    print(report_text)
    with open(OUTPUT_REPORT_TXT, "w") as f:
        f.write(report_text)
    print(f"  Saved: {OUTPUT_REPORT_TXT}")

    # C. ROC + PR Curves
    print("--- ROC & PR Curves ---")
    curve_metrics = plot_roc_pr_curves(y_true, y_prob, OUTPUT_ROC_PR)
    print(f"  ROC-AUC: {curve_metrics['roc_auc']:.3f}")
    print(f"  PR-AUC:  {curve_metrics['pr_auc']:.3f}")
    print(f"  Saved: {OUTPUT_ROC_PR}")

    # D. SHAP Feature Importance
    print("\n--- SHAP Feature Importance ---")
    shap_importance = plot_shap_importance(INPUT_MODEL, X, feature_names, experiment_type, OUTPUT_SHAP)
    print("  Top 5 features:")
    for i, entry in enumerate(shap_importance[:5], 1):
        print(f"    {i}. {entry['feature']}: {entry['mean_abs_shap']:.4f}")
    print(f"  Saved: {OUTPUT_SHAP}")

    # E. Baseline Comparison
    print("\n--- Baseline Comparison ---")
    baseline = compute_baseline_comparison(y_true, y_pred, X)
    print(f"  XGBoost accuracy:      {baseline['xgboost_accuracy']:.3f} (F1={baseline['xgboost_f1']:.3f})")
    print(f"  Convergence baseline:  {baseline['convergence_best_accuracy']:.3f} (threshold={baseline['convergence_best_threshold']:.2f}, F1={baseline['convergence_best_f1']:.3f})")
    print(f"  Naive baseline:        {baseline['naive_accuracy']:.3f} (always predict negative)")
    print(f"  XGBoost beats naive:       {'YES' if baseline['xgboost_beats_naive'] else 'NO'}")
    print(f"  XGBoost beats convergence: {'YES' if baseline['xgboost_beats_convergence'] else 'NO'}")

    # Save evaluation report
    report = {
        "experiment_type": experiment_type,
        "optimal_threshold": optimal_threshold,
        "confusion_matrix": cm_metrics,
        "curves": curve_metrics,
        "baseline_comparison": baseline,
        "shap_top_features": shap_importance[:10],
    }
    with open(OUTPUT_REPORT, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nEvaluation report saved to {OUTPUT_REPORT}")

    # Log to MLflow
    mlflow.set_experiment("jyotish-training")
    with mlflow.start_run(run_name="07_evaluate_model"):
        mlflow.log_metrics({
            "eval_tp": cm_metrics["TP"],
            "eval_fp": cm_metrics["FP"],
            "eval_tn": cm_metrics["TN"],
            "eval_fn": cm_metrics["FN"],
            "eval_roc_auc": curve_metrics["roc_auc"],
            "eval_pr_auc": curve_metrics["pr_auc"],
            "eval_xgboost_accuracy": baseline["xgboost_accuracy"],
            "eval_xgboost_f1": baseline["xgboost_f1"],
            "eval_naive_accuracy": baseline["naive_accuracy"],
            "eval_convergence_accuracy": baseline["convergence_best_accuracy"],
        })
        mlflow.log_params({
            "experiment_type": experiment_type,
            "optimal_threshold": optimal_threshold,
        })
        for artifact in [OUTPUT_CONFUSION, OUTPUT_ROC_PR, OUTPUT_SHAP, OUTPUT_REPORT_TXT, OUTPUT_REPORT]:
            if artifact.exists():
                mlflow.log_artifact(str(artifact))

    # Final summary
    print(f"\n{'='*60}")
    print("EVALUATION COMPLETE")
    print(f"{'='*60}")
    print(f"  Experiment:  {experiment_type}")
    print(f"  Threshold:   {optimal_threshold:.2f}")
    print(f"  Outputs in:  {MODEL_DIR}")
    print(f"    confusion_matrix.png")
    print(f"    roc_pr_curves.png")
    print(f"    feature_importance.png")
    print(f"    classification_report.txt")
    print(f"    evaluation_report.json")
    print(f"{'='*60}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
