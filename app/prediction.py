"""
Streamlit Prediction Helper (`app/prediction.py`)
Provides interface bridging web UI form inputs to the backend ML inference engine.
"""
from typing import Dict, Any
from src.models.predict import FlightPredictor
from src.utils.logger import get_logger

logger = get_logger("AppPrediction")

class StreamlitPredictor:
    def __init__(self):
        try:
            self.engine = FlightPredictor()
            self.loaded = True
        except Exception as e:
            logger.error(f"Failed to load backend predictor: {e}")
            self.loaded = False

    def predict_delay(self, form_inputs: Dict[str, Any]) -> Dict[str, Any]:
        if not self.loaded:
            return {
                "is_delayed_prediction": 0,
                "delay_probability_pct": 0.0,
                "expected_delay_minutes": 0.0,
                "risk_level": "UNKNOWN (Model not built)"
            }
        return self.engine.predict(form_inputs)
