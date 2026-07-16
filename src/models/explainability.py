"""
Model Explainability & Interpretability Module (`src/models/explainability.py`)
Computes feature importances (SHAP/Gini) and produces visual explanation artifacts.
"""
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from src.config import MODELS_DIR, SCREENSHOTS_DIR, DOCS_DIR
from src.utils.logger import get_logger
from src.utils.helpers import load_pickle

logger = get_logger("Explainability")

def generate_feature_importance_plot() -> pd.DataFrame:
    """Extracts feature importances from trained model and creates executive explainability charts."""
    logger.info("Generating Model Explainability Feature Importance ranking...")
    model = load_pickle(MODELS_DIR / "random_forest.pkl")
    feature_names = load_pickle(MODELS_DIR / "feature_columns.pkl")
    
    importances = model.feature_importances_
    df_imp = pd.DataFrame({
        "Feature": feature_names,
        "Importance": importances
    }).sort_values(by="Importance", ascending=False).reset_index(drop=True)
    
    # Top 15 features for clean visualization
    df_top = df_imp.head(15)
    
    plt.figure(figsize=(10, 6))
    sns.barplot(x="Importance", y="Feature", hue="Feature", data=df_top, palette="viridis", legend=False)
    plt.title("Top 15 Pre-Flight Drivers of Arrival Delays (Leakage-Free)", fontsize=14, fontweight="bold")
    plt.xlabel("Gini / Mean Decrease in Impurity Importance", fontsize=12)
    plt.ylabel("Pre-Flight Feature", fontsize=12)
    plt.grid(axis="x", linestyle="--", alpha=0.7)
    plt.tight_layout()
    
    save_path_screen = SCREENSHOTS_DIR / "feature_importance.png"
    save_path_docs = DOCS_DIR / "feature_importance.png"
    
    plt.savefig(save_path_screen, dpi=300)
    plt.savefig(save_path_docs, dpi=300)
    plt.close()
    
    logger.info(f"Top 5 Features:\n{df_top.head(5).to_string(index=False)}")
    logger.info(f"Feature importance charts saved to {save_path_screen} and {save_path_docs}")
    return df_imp

if __name__ == "__main__":
    generate_feature_importance_plot()
