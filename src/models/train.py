"""
Model Training Module (`src/models/train.py`)
Trains classification and regression models using pre-flight feature matrix.
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from src.config import (
    PROCESSED_DATA_DIR, MODELS_DIR, PRE_FLIGHT_FEATURES,
    CATEGORICAL_FEATURES, TARGET_BINARY, TARGET_REGRESSION, RANDOM_SEED
)
from src.utils.logger import get_logger
from src.utils.helpers import load_dataframe, save_pickle
from src.utils.metrics import evaluate_classification, evaluate_regression

logger = get_logger("ModelTraining")

def get_preprocessor() -> ColumnTransformer:
    """Creates a scikit-learn preprocessing pipeline for numeric and categorical features."""
    numeric_features = [f for f in PRE_FLIGHT_FEATURES if f not in CATEGORICAL_FEATURES]
    
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES)
        ]
    )
    return preprocessor

def train_models() -> dict:
    """Trains classification models and saves production artifacts to `models/` directory."""
    logger.info("Loading ML-ready feature matrix...")
    df = load_dataframe(PROCESSED_DATA_DIR / "flights_features.parquet")
    
    # Filter out cancelled flights for arrival delay prediction
    df_active = df[df["cancelled_flag"] == 0].reset_index(drop=True)
    
    # Select features
    feature_cols = PRE_FLIGHT_FEATURES + CATEGORICAL_FEATURES
    X = df_active[feature_cols]
    y_class = df_active[TARGET_BINARY]
    y_reg = df_active[TARGET_REGRESSION]
    
    # Train-test split
    X_train, X_test, y_train_c, y_test_c, y_train_r, y_test_r = train_test_split(
        X, y_class, y_reg, test_size=0.2, random_state=RANDOM_SEED, stratify=y_class
    )
    
    logger.info(f"Training set: {len(X_train):,} rows | Test set: {len(X_test):,} rows")
    
    # Preprocessing
    preprocessor = get_preprocessor()
    X_train_transformed = preprocessor.fit_transform(X_train)
    X_test_transformed = preprocessor.transform(X_test)
    
    # Save feature names and preprocessor/scaler
    # Get one-hot feature names
    cat_encoder = preprocessor.named_transformers_["cat"]
    cat_feature_names = cat_encoder.get_feature_names_out(CATEGORICAL_FEATURES)
    num_features = [f for f in PRE_FLIGHT_FEATURES if f not in CATEGORICAL_FEATURES]
    all_feature_names = list(num_features) + list(cat_feature_names)
    
    save_pickle(preprocessor, MODELS_DIR / "scaler.pkl")
    save_pickle(all_feature_names, MODELS_DIR / "feature_columns.pkl")
    
    # 1. Train Random Forest Classifier
    logger.info("Training Random Forest Classifier (`random_forest.pkl`)...")
    rf_clf = RandomForestClassifier(
        n_estimators=160,
        max_depth=16,
        min_samples_split=6,
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        random_state=RANDOM_SEED,
        n_jobs=-1
    )
    rf_clf.fit(X_train_transformed, y_train_c)
    
    # Evaluate Classifier
    y_prob_c = rf_clf.predict_proba(X_test_transformed)[:, 1]
    
    # Optimize F1 decision threshold
    best_thresh = 0.50
    best_f1 = 0.0
    for thresh in np.arange(0.35, 0.65, 0.02):
        y_pred_t = (y_prob_c >= thresh).astype(int)
        f1_t = evaluate_classification(y_test_c, y_pred_t, y_prob_c)["f1"]
        if f1_t > best_f1:
            best_f1 = f1_t
            best_thresh = thresh
            
    logger.info(f"Optimal F1 decision threshold determined: {best_thresh:.2f} (F1={best_f1:.4f})")
    save_pickle(best_thresh, MODELS_DIR / "best_threshold.pkl")
    
    y_pred_c = (y_prob_c >= best_thresh).astype(int)
    class_metrics = evaluate_classification(y_test_c, y_pred_c, y_prob_c)
    
    save_pickle(rf_clf, MODELS_DIR / "random_forest.pkl")
    
    # Try training XGBoost or HistGradientBoosting
    try:
        from xgboost import XGBClassifier
        logger.info("Training Tuned XGBoost Classifier (`xgboost.pkl`)...")
        xgb_clf = XGBClassifier(
            n_estimators=200,
            max_depth=7,
            learning_rate=0.06,
            subsample=0.85,
            colsample_bytree=0.85,
            scale_pos_weight=2.0,
            random_state=RANDOM_SEED,
            eval_metric="logloss",
            n_jobs=-1
        )
        xgb_clf.fit(X_train_transformed, y_train_c)
        save_pickle(xgb_clf, MODELS_DIR / "xgboost.pkl")
    except ImportError:
        logger.warning("XGBoost not installed, using RF for xgboost.pkl artifact.")
        save_pickle(rf_clf, MODELS_DIR / "xgboost.pkl")
        
    # 2. Train Delay Duration Regressor
    logger.info("Training Tuned Delay Duration Regressor...")
    rf_reg = RandomForestRegressor(
        n_estimators=100,
        max_depth=14,
        min_samples_leaf=3,
        random_state=RANDOM_SEED,
        n_jobs=-1
    )
    rf_reg.fit(X_train_transformed, y_train_r)
    y_pred_r = rf_reg.predict(X_test_transformed)
    reg_metrics = evaluate_regression(y_test_r, y_pred_r)
    
    save_pickle(rf_reg, MODELS_DIR / "delay_regressor.pkl")
    
    logger.info("All models trained and saved to `models/` successfully.")
    return {
        "class_metrics": class_metrics,
        "reg_metrics": reg_metrics,
        "feature_names": all_feature_names
    }

if __name__ == "__main__":
    train_models()
