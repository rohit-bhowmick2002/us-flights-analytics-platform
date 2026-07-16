"""
Evaluation Metrics Module (`src/utils/metrics.py`)
Calculates and logs classification and regression metrics.
"""
from typing import Dict, Any
import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, mean_absolute_error, mean_squared_error, r2_score
)
from src.utils.logger import get_logger

logger = get_logger("Metrics")

def evaluate_classification(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray = None) -> Dict[str, float]:
    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0))
    }
    if y_prob is not None:
        try:
            metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob))
        except Exception as e:
            logger.warning(f"Could not compute ROC-AUC: {e}")
            metrics["roc_auc"] = 0.5
            
    logger.info(f"Classification Metrics: Acc={metrics['accuracy']:.4f}, F1={metrics['f1']:.4f}, AUC={metrics.get('roc_auc', 0.5):.4f}")
    return metrics

def evaluate_regression(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    metrics = {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "r2": float(r2_score(y_true, y_pred))
    }
    logger.info(f"Regression Metrics: MAE={metrics['mae']:.2f}, RMSE={metrics['rmse']:.2f}, R2={metrics['r2']:.4f}")
    return metrics
