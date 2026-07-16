"""
Model Evaluation Module (`src/models/evaluate.py`)
Generates formal evaluation metrics and classification/regression diagnostic plots.
"""
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, roc_curve, auc, classification_report
from src.config import PROCESSED_DATA_DIR, MODELS_DIR, REPORTS_DIR, SCREENSHOTS_DIR, PRE_FLIGHT_FEATURES, CATEGORICAL_FEATURES, TARGET_BINARY
from src.utils.logger import get_logger
from src.utils.helpers import load_dataframe, load_pickle

logger = get_logger("ModelEvaluation")

def run_evaluation() -> None:
    logger.info("Running thorough model evaluation...")
    df = load_dataframe(PROCESSED_DATA_DIR / "flights_features.parquet")
    df_active = df[df["cancelled_flag"] == 0].reset_index(drop=True)
    
    # Use last 20% of dataset as holdout evaluation
    split_idx = int(len(df_active) * 0.8)
    df_eval = df_active.iloc[split_idx:].copy()
    
    scaler = load_pickle(MODELS_DIR / "scaler.pkl")
    model = load_pickle(MODELS_DIR / "random_forest.pkl")
    
    X_eval = scaler.transform(df_eval[PRE_FLIGHT_FEATURES + CATEGORICAL_FEATURES])
    y_true = df_eval[TARGET_BINARY].values
    
    y_pred = model.predict(X_eval)
    y_prob = model.predict_proba(X_eval)[:, 1]
    
    # Generate Confusion Matrix Plot
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False,
                xticklabels=["On-Time / Minor", "Delayed (>=15m)"],
                yticklabels=["On-Time / Minor", "Delayed (>=15m)"])
    plt.title("Confusion Matrix - Flight Delay Classifier", fontsize=13, fontweight="bold")
    plt.xlabel("Predicted Status", fontsize=11)
    plt.ylabel("Actual Status", fontsize=11)
    plt.tight_layout()
    cm_path = SCREENSHOTS_DIR / "confusion_matrix.png"
    plt.savefig(cm_path, dpi=300)
    plt.close()
    
    # Generate ROC Curve
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    roc_auc = auc(fpr, tpr)
    plt.figure(figsize=(6, 5))
    plt.plot(fpr, tpr, color="darkorange", lw=2, label=f"ROC curve (area = {roc_auc:.3f})")
    plt.plot([0, 1], [0, 1], color="navy", lw=2, linestyle="--")
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel("False Positive Rate", fontsize=11)
    plt.ylabel("True Positive Rate", fontsize=11)
    plt.title("Receiver Operating Characteristic (ROC) Curve", fontsize=13, fontweight="bold")
    plt.legend(loc="lower right")
    plt.tight_layout()
    roc_path = SCREENSHOTS_DIR / "roc_curve.png"
    plt.savefig(roc_path, dpi=300)
    plt.close()
    
    # Save text report
    rep_text = classification_report(y_true, y_pred)
    with open(REPORTS_DIR / "evaluation_summary.txt", "w") as f:
        f.write("Aviation Analytics - Model Evaluation Summary\n")
        f.write("="*50 + "\n\n")
        f.write(f"ROC-AUC Score: {roc_auc:.4f}\n\n")
        f.write(rep_text)
        
    logger.info(f"Evaluation plots saved to {SCREENSHOTS_DIR} and report saved to {REPORTS_DIR}")

if __name__ == "__main__":
    run_evaluation()
