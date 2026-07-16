"""
Data Preprocessing & Cleaning Module (`src/data/preprocessing.py`)
Cleans, harmonizes, and validates raw relational tables before feature engineering.
"""
import pandas as pd
import numpy as np
from typing import Dict
from src.config import RAW_DATA_DIR, PROCESSED_DATA_DIR
from src.utils.logger import get_logger
from src.utils.helpers import load_dataframe, save_dataframe

logger = get_logger("Preprocessing")

def clean_flights(df_flights: pd.DataFrame) -> pd.DataFrame:
    """Cleans flight schedule timestamps and handles delay nulls."""
    logger.info("Cleaning raw flights records...")
    df = df_flights.copy()
    
    # Parse timestamps
    for col in ["crs_dep_time", "crs_arr_time"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in ["actual_dep_time", "actual_arr_time"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
        
    # Standardize delay nulls
    # If cancelled, delay columns should be 0 for numerical calculations
    delay_cols = ["dep_delay_mins", "arr_delay_mins", "carrier_delay_mins", 
                  "weather_delay_mins", "nas_delay_mins", "late_aircraft_delay_mins"]
    for col in delay_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(int)
        else:
            df[col] = 0
        
    # Extract date parts
    df["flight_date"] = pd.to_datetime(df["flight_date"])
    df["month"] = df["flight_date"].dt.month
    df["day_of_week"] = df["flight_date"].dt.dayofweek
    df["scheduled_dep_hour"] = df["crs_dep_time"].dt.hour
    
    # Filter out invalid records (negative air time unless cancelled)
    valid_mask = (df["cancelled_flag"] == 1) | (df["air_time_mins"] >= 0)
    df = df[valid_mask].reset_index(drop=True)
    
    logger.info(f"Cleaned flights records: {len(df):,} rows retained.")
    return df

def join_reference_tables(df_flights: pd.DataFrame, df_airports: pd.DataFrame, 
                          df_aircraft: pd.DataFrame, df_weather: pd.DataFrame) -> pd.DataFrame:
    """Performs star-schema joins to enrich flight facts with aircraft age and origin weather."""
    logger.info("Joining flights with aircraft and weather dimensions...")
    df = df_flights.copy()
    
    # 1. Join Aircraft age
    df_aircraft_sub = df_aircraft[["tail_number", "year_built", "capacity"]].drop_duplicates("tail_number")
    df = df.merge(df_aircraft_sub, on="tail_number", how="left")
    df["aircraft_age"] = df["flight_date"].dt.year - df["year_built"].fillna(2015)
    df["aircraft_age"] = df["aircraft_age"].apply(lambda x: max(0, int(x)))
    
    # 2. Join Weather on origin_airport + rounded scheduled departure hour
    df["weather_join_time"] = df["crs_dep_time"].dt.floor("h").dt.strftime("%Y-%m-%d %H:00:00")
    df_weather["weather_join_time"] = df_weather["utc_timestamp"]
    
    df = df.merge(
        df_weather[["airport_code", "weather_join_time", "temperature", "wind_speed", "visibility", "precipitation", "weather_condition"]],
        left_on=["origin_airport", "weather_join_time"],
        right_on=["airport_code", "weather_join_time"],
        how="left"
    )
    
    # Fill missing weather with seasonal averages
    df["temperature"] = df["temperature"].fillna(60.0)
    df["wind_speed"] = df["wind_speed"].fillna(8.0)
    df["visibility"] = df["visibility"].fillna(10.0)
    df["precipitation"] = df["precipitation"].fillna(0.0)
    df["weather_condition"] = df["weather_condition"].fillna("Clear")
    
    # Clean up temp columns
    df = df.drop(columns=["weather_join_time", "airport_code"], errors="ignore")
    return df

def run_preprocessing() -> pd.DataFrame:
    """Orchestrates loading raw tables, cleaning, joining, and saving to processed data lake."""
    logger.info("Running Preprocessing pipeline...")
    df_flights = load_dataframe(RAW_DATA_DIR / "flights" / "flights_raw.csv")
    df_airports = load_dataframe(RAW_DATA_DIR / "airports" / "airports.csv")
    df_aircraft = load_dataframe(RAW_DATA_DIR / "flights" / "aircraft.csv")
    df_weather = load_dataframe(RAW_DATA_DIR / "weather" / "weather_hourly.csv")
    
    df_clean = clean_flights(df_flights)
    df_merged = join_reference_tables(df_clean, df_airports, df_aircraft, df_weather)
    
    save_path = PROCESSED_DATA_DIR / "flights_cleaned.parquet"
    save_dataframe(df_merged, save_path)
    logger.info("Preprocessing completed successfully.")
    return df_merged

if __name__ == "__main__":
    run_preprocessing()
