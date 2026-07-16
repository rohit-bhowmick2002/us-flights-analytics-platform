"""
Prediction Inference Module (`src/models/predict.py`)
Provides production inference interface for predicting delays on unseen flight schedules.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Union
from src.config import (
    MODELS_DIR, PRE_FLIGHT_FEATURES, CATEGORICAL_FEATURES
)
from src.utils.logger import get_logger
from src.utils.helpers import load_pickle

logger = get_logger("InferenceEngine")

class FlightPredictor:
    """Enterprise inference engine loading pre-trained models and feature transformers."""
    
    def __init__(self, model_name: str = "random_forest.pkl"):
        self.scaler = load_pickle(MODELS_DIR / "scaler.pkl")
        self.model = load_pickle(MODELS_DIR / model_name)
        try:
            self.regressor = load_pickle(MODELS_DIR / "delay_regressor.pkl")
        except Exception:
            self.regressor = None
        self.feature_columns = load_pickle(MODELS_DIR / "feature_columns.pkl")
        logger.info(f"Loaded inference pipeline with model: {model_name}")

    def predict(self, input_data: Union[Dict[str, Any], pd.DataFrame]) -> Dict[str, Any]:
        """Predicts delay probability and estimated delay duration for input schedules."""
        if isinstance(input_data, dict):
            df_in = pd.DataFrame([input_data])
        else:
            df_in = input_data.copy()
            
        # Ensure required columns exist with sensible defaults if missing
        for col in PRE_FLIGHT_FEATURES + CATEGORICAL_FEATURES:
            if col not in df_in.columns:
                if col in ["month", "day_of_week", "scheduled_dep_hour", "is_holiday", "is_weekend", "is_bad_weather", "is_peak_afternoon_bank"]:
                    df_in[col] = 0
                elif col in ["distance_miles", "aircraft_age", "turnaround_buffer_mins", "origin_hourly_traffic"]:
                    df_in[col] = 100
                elif col in ["carrier_30day_delay_rate", "carrier_route_historical_risk"]:
                    df_in[col] = 0.18
                elif col in ["origin_betweenness_centrality", "origin_pagerank", "dest_pagerank"]:
                    df_in[col] = 0.08
                elif col in ["route_network_centrality_index", "turnaround_wind_interaction", "congestion_weather_index"]:
                    df_in[col] = 5.0
                elif col in ["forecast_temp"]:
                    df_in[col] = 65.0
                elif col in ["forecast_wind_speed"]:
                    df_in[col] = 15.0
                elif col in ["forecast_visibility"]:
                    df_in[col] = 10.0
                elif col in ["forecast_precip"]:
                    df_in[col] = 0.0
                else:
                    df_in[col] = "JFK" if col == "origin_airport" else ("LAX" if col == "destination_airport" else "DL")
                    
        # Transform features
        X_trans = self.scaler.transform(df_in[PRE_FLIGHT_FEATURES + CATEGORICAL_FEATURES])
        
        # Predict class & probability
        prob_delay = float(self.model.predict_proba(X_trans)[:, 1][0])
        try:
            best_thresh = float(load_pickle(MODELS_DIR / "best_threshold.pkl"))
        except Exception:
            best_thresh = 0.50
            
        pred_class = int(prob_delay >= best_thresh)
        
        # Predict duration
        if self.regressor and pred_class == 1:
            pred_duration = max(15.0, float(self.regressor.predict(X_trans)[0]))
        else:
            pred_duration = 0.0 if pred_class == 0 else 25.0
            
        result = {
            "is_delayed_prediction": pred_class,
            "delay_probability_pct": round(prob_delay * 100, 1),
            "expected_delay_minutes": round(pred_duration, 1),
            "risk_level": "HIGH" if prob_delay >= 0.65 else ("MEDIUM" if prob_delay >= 0.40 else "LOW")
        }
        return result

def run_sample_prediction() -> Dict[str, Any]:
    predictor = FlightPredictor()
    sample_flight = {
        "month": 12,
        "day_of_week": 4,
        "scheduled_dep_hour": 17,
        "is_holiday": 1,
        "is_weekend": 0,
        "distance_miles": 2475,
        "aircraft_age": 14,
        "turnaround_buffer_mins": 30,
        "origin_hourly_traffic": 65,
        "carrier_30day_delay_rate": 0.28,
        "forecast_temp": 32.0,
        "forecast_wind_speed": 28.5,
        "forecast_visibility": 1.5,
        "forecast_precip": 0.45,
        "is_bad_weather": 1,
        "airline_code": "AA",
        "origin_airport": "ORD",
        "destination_airport": "LAX"
    }
    pred = predictor.predict(sample_flight)
    logger.info(f"Sample Prediction Output: {pred}")
    return pred

if __name__ == "__main__":
    run_sample_prediction()
