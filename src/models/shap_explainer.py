"""
Advanced SHAP Explainability & Interaction Modeling (`src/models/shap_explainer.py`)
Computes exact Shapley Additive exPlanations (SHAP) using TreeExplainer.
Produces Beeswarm plots, Dependence interaction charts, and quantitative importance tables.
"""
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import shap
from pathlib import Path
from src.config import PROCESSED_DATA_DIR, MODELS_DIR, SCREENSHOTS_DIR, DOCS_DIR, REPORTS_DIR, PRE_FLIGHT_FEATURES, CATEGORICAL_FEATURES
from src.utils.logger import get_logger
from src.utils.helpers import load_dataframe, load_pickle, save_dataframe

logger = get_logger("SHAPExplainer")

def run_shap_analysis() -> pd.DataFrame:
    logger.info("Starting Advanced SHAP Explainability & Interaction Analysis...")
    df = load_dataframe(PROCESSED_DATA_DIR / "flights_features.parquet")
    df_active = df[df["cancelled_flag"] == 0].reset_index(drop=True)
    
    # Sample up to 2,000 rows for fast, high-fidelity SHAP computation
    if len(df_active) > 2000:
        df_sample = df_active.sample(2000, random_state=42).reset_index(drop=True)
    else:
        df_sample = df_active.copy()
        
    scaler = load_pickle(MODELS_DIR / "scaler.pkl")
    model = load_pickle(MODELS_DIR / "xgboost.pkl")
    feature_names = load_pickle(MODELS_DIR / "feature_columns.pkl")
    
    # Transform sample
    X_trans = scaler.transform(df_sample[PRE_FLIGHT_FEATURES + CATEGORICAL_FEATURES])
    df_X = pd.DataFrame(X_trans, columns=feature_names)
    
    logger.info("Computing exact Shapley values using TreeExplainer...")
    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer(df_X)
    except Exception as e:
        logger.warning(f"TreeExplainer failed ({e}), falling back to KernelExplainer/Permutation...")
        explainer = shap.Explainer(model.predict_proba, df_X.iloc[:200], feature_names=feature_names)
        shap_values = explainer(df_X.iloc[:500])
        df_X = df_X.iloc[:500]

    # Handle multi-class / binary probability shape differences
    if isinstance(shap_values.values, list) or (len(shap_values.values.shape) == 3):
        values_to_plot = shap_values.values[:, :, 1] if shap_values.values.shape[-1] > 1 else shap_values.values[:, :, 0]
    else:
        values_to_plot = shap_values.values

    # 1. Generate SHAP Beeswarm Plot
    logger.info("Generating SHAP Beeswarm Plot (`shap_beeswarm.png`)...")
    plt.figure(figsize=(11, 7))
    shap.summary_plot(values_to_plot, df_X, feature_names=feature_names, max_display=15, show=False)
    plt.title("SHAP Beeswarm Plot — Pre-Flight Delay Predictor (Log-Odds Impact)", fontsize=13, fontweight="bold", pad=15)
    plt.tight_layout()
    plt.savefig(SCREENSHOTS_DIR / "shap_beeswarm.png", dpi=300)
    plt.savefig(DOCS_DIR / "shap_beeswarm.png", dpi=300)
    plt.close()

    # 2. Generate SHAP Dependence Plot (Turnaround vs Wind / Traffic)
    logger.info("Generating SHAP Dependence Interaction Plot (`shap_dependence_turnaround.png`)...")
    plt.figure(figsize=(9, 6))
    
    # Find feature indices
    turn_idx = [i for i, name in enumerate(feature_names) if "turnaround_buffer_mins" in name]
    wind_idx = [i for i, name in enumerate(feature_names) if "forecast_wind_speed" in name]
    
    if turn_idx and wind_idx:
        t_col = turn_idx[0]
        w_col = wind_idx[0]
        shap.dependence_plot(t_col, values_to_plot, df_X, feature_names=feature_names, interaction_index=w_col, show=False)
        plt.title("SHAP Dependence Plot — Turnaround Buffer x Wind Speed Interaction", fontsize=13, fontweight="bold")
        plt.tight_layout()
        plt.savefig(SCREENSHOTS_DIR / "shap_dependence_turnaround.png", dpi=300)
        plt.savefig(DOCS_DIR / "shap_dependence_turnaround.png", dpi=300)
        plt.close()
    else:
        logger.warning("Target dependence indices not found, skipping specific dependence chart.")

    # 3. Quantitative SHAP Importance Ranking Table
    mean_abs_shap = np.abs(values_to_plot).mean(axis=0)
    df_shap_summary = pd.DataFrame({
        "Feature": feature_names,
        "Mean_Absolute_SHAP": np.round(mean_abs_shap, 5)
    }).sort_values("Mean_Absolute_SHAP", ascending=False).reset_index(drop=True)
    
    save_dataframe(df_shap_summary, REPORTS_DIR / "shap_feature_importance.csv")
    logger.info(f"SHAP Analysis complete. Top 5 Features by Mean Absolute SHAP:\n{df_shap_summary.head(5).to_string(index=False)}")
    return df_shap_summary

if __name__ == "__main__":
    run_shap_analysis()
