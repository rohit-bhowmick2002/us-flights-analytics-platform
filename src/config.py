"""
Project Configuration Module (`src/config.py`)
Centralizes all directories, schema columns, ML feature definitions, and thresholds.
"""
import os
from pathlib import Path

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"
DASHBOARDS_DIR = PROJECT_ROOT / "dashboards"
SCREENSHOTS_DIR = DASHBOARDS_DIR / "screenshots"
DOCS_DIR = PROJECT_ROOT / "docs"

# Ensure directories exist
for path in [RAW_DATA_DIR / "flights", RAW_DATA_DIR / "weather", RAW_DATA_DIR / "airports",
             RAW_DATA_DIR / "airlines", PROCESSED_DATA_DIR, EXTERNAL_DATA_DIR,
             MODELS_DIR, REPORTS_DIR, SCREENSHOTS_DIR, DOCS_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# Random Seed for Reproducibility
RANDOM_SEED = 42

# Thresholds
DELAY_THRESHOLD_MINUTES = 15  # A flight is considered delayed if arrival delay >= 15 minutes

# Top Hub Airports for Analysis
TOP_AIRPORTS = ["JFK", "LAX", "ATL", "ORD", "DFW", "SEA", "SFO", "MIA", "BOS", "DEN"]

# Airlines Reference
AIRLINES_REF = {
    "AA": "American Airlines",
    "DL": "Delta Air Lines",
    "UA": "United Airlines",
    "WN": "Southwest Airlines",
    "B6": "JetBlue Airways",
    "AS": "Alaska Airlines",
    "NK": "Spirit Airlines",
    "F9": "Frontier Airlines"
}

# Pre-Flight Feature Columns (Strict Separation to prevent Target Leakage)
PRE_FLIGHT_FEATURES = [
    "month",
    "day_of_week",
    "scheduled_dep_hour",
    "is_holiday",
    "is_weekend",
    "distance_miles",
    "aircraft_age",
    "turnaround_buffer_mins",
    "origin_hourly_traffic",
    "carrier_30day_delay_rate",
    "forecast_temp",
    "forecast_wind_speed",
    "forecast_visibility",
    "forecast_precip",
    "is_bad_weather",
    "origin_betweenness_centrality",
    "origin_pagerank",
    "dest_pagerank",
    "route_network_centrality_index",
    "turnaround_wind_interaction",
    "congestion_weather_index",
    "carrier_route_historical_risk",
    "is_peak_afternoon_bank"
]

CATEGORICAL_FEATURES = ["airline_code", "origin_airport", "destination_airport"]

TARGET_BINARY = "is_delayed_15m"
TARGET_REGRESSION = "arr_delay_mins"
