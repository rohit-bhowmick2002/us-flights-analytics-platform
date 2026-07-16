"""
Data Ingestion & Synthetic Generation Module (`src/data/ingestion.py`)
Generates production-grade multi-table relational datasets matching U.S. DOT BTS and NOAA ASOS schemas.
"""
import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Tuple
from src.config import (
    RAW_DATA_DIR, TOP_AIRPORTS, AIRLINES_REF, RANDOM_SEED
)
from src.utils.logger import get_logger
from src.utils.helpers import save_dataframe

logger = get_logger("DataIngestion")

def generate_reference_tables() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Generates Airlines, Airports, and Aircraft reference dimension tables."""
    np.random.seed(RANDOM_SEED)
    
    # 1. Airlines
    airlines_data = [
        {"airline_code": code, "airline_name": name, "alliance": np.random.choice(["Oneworld", "SkyTeam", "Star Alliance", "None"]), "fleet_size": np.random.randint(150, 950)}
        for code, name in AIRLINES_REF.items()
    ]
    df_airlines = pd.DataFrame(airlines_data)
    
    # 2. Airports
    airports_info = [
        {"airport_code": "JFK", "airport_name": "John F. Kennedy International Airport", "city": "New York", "state": "NY", "latitude": 40.6413, "longitude": -73.7781, "hub_status": "Major Hub"},
        {"airport_code": "LAX", "airport_name": "Los Angeles International Airport", "city": "Los Angeles", "state": "CA", "latitude": 33.9416, "longitude": -118.4085, "hub_status": "Major Hub"},
        {"airport_code": "ATL", "airport_name": "Hartsfield-Jackson Atlanta International Airport", "city": "Atlanta", "state": "GA", "latitude": 33.6407, "longitude": -84.4277, "hub_status": "Super Hub"},
        {"airport_code": "ORD", "airport_name": "O'Hare International Airport", "city": "Chicago", "state": "IL", "latitude": 41.9742, "longitude": -87.9073, "hub_status": "Major Hub"},
        {"airport_code": "DFW", "airport_name": "Dallas/Fort Worth International Airport", "city": "Dallas-Fort Worth", "state": "TX", "latitude": 32.8998, "longitude": -97.0403, "hub_status": "Major Hub"},
        {"airport_code": "SEA", "airport_name": "Seattle-Tacoma International Airport", "city": "Seattle", "state": "WA", "latitude": 47.4502, "longitude": -122.3088, "hub_status": "Hub"},
        {"airport_code": "SFO", "airport_name": "San Francisco International Airport", "city": "San Francisco", "state": "CA", "latitude": 37.6190, "longitude": -122.3750, "hub_status": "Hub"},
        {"airport_code": "MIA", "airport_name": "Miami International Airport", "city": "Miami", "state": "FL", "latitude": 25.7959, "longitude": -80.2870, "hub_status": "Hub"},
        {"airport_code": "BOS", "airport_name": "Logan International Airport", "city": "Boston", "state": "MA", "latitude": 42.3656, "longitude": -71.0096, "hub_status": "Hub"},
        {"airport_code": "DEN", "airport_name": "Denver International Airport", "city": "Denver", "state": "CO", "latitude": 39.8561, "longitude": -104.6737, "hub_status": "Major Hub"}
    ]
    df_airports = pd.DataFrame(airports_info)
    
    # 3. Aircraft
    manufacturers = ["Boeing", "Airbus"]
    models_boeing = ["737-800", "737 MAX 8", "787-9", "777-200"]
    models_airbus = ["A320-200", "A321neo", "A319", "A350-900"]
    
    aircraft_list = []
    for i in range(1, 501):
        mfg = np.random.choice(manufacturers)
        model = np.random.choice(models_boeing if mfg == "Boeing" else models_airbus)
        year_built = np.random.randint(2002, 2024)
        capacity = 180 if "737" in model or "A320" in model else (250 if "787" in model or "A350" in model else 140)
        aircraft_list.append({
            "tail_number": f"N{100+i}US",
            "manufacturer": mfg,
            "model": model,
            "capacity": capacity,
            "year_built": year_built,
            "engine_type": "Turbofan"
        })
    df_aircraft = pd.DataFrame(aircraft_list)
    
    return df_airlines, df_airports, df_aircraft

def generate_weather_data(airports: pd.DataFrame, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Generates hourly ASOS weather observations for each airport."""
    logger.info("Generating hourly weather station observations...")
    np.random.seed(RANDOM_SEED)
    
    weather_records = []
    current_date = start_date
    delta = timedelta(hours=1)
    
    # To keep demo dataset fast yet comprehensive, sample key days across 2023-2025 or continuous subsets
    while current_date <= end_date:
        for _, row in airports.iterrows():
            apt = row["airport_code"]
            # Seasonal temp baseline
            month = current_date.month
            temp_base = 75 if month in [6,7,8] else (35 if month in [12,1,2] else 55)
            temp = np.random.normal(temp_base, 10)
            
            # Weather events
            is_storm = np.random.random() < 0.08  # 8% chance of bad weather
            if is_storm:
                wind_speed = np.random.uniform(20, 45)
                visibility = np.random.uniform(0.5, 3.0)
                precip = np.random.uniform(0.1, 1.5)
                snow = np.random.uniform(0.5, 4.0) if temp < 34 else 0.0
                cond = np.random.choice(["Thunderstorm", "Heavy Rain", "Snowstorm", "Fog"])
            else:
                wind_speed = np.random.uniform(3, 15)
                visibility = 10.0
                precip = 0.0
                snow = 0.0
                cond = np.random.choice(["Clear", "Partly Cloudy", "Overcast"])
                
            weather_records.append({
                "airport_code": apt,
                "utc_timestamp": current_date.strftime("%Y-%m-%d %H:00:00"),
                "temperature": round(temp, 1),
                "wind_speed": round(wind_speed, 1),
                "visibility": round(visibility, 1),
                "precipitation": round(precip, 2),
                "snowfall": round(snow, 2),
                "weather_condition": cond
            })
        current_date += timedelta(hours=3) # Sample every 3 hours for balance
        
    return pd.DataFrame(weather_records)

def generate_flights_data(n_flights: int, airports: pd.DataFrame, aircraft: pd.DataFrame) -> pd.DataFrame:
    """Generates realistic flight transactions with cascading delay topology."""
    logger.info(f"Generating {n_flights:,} synthetic flight operations...")
    np.random.seed(RANDOM_SEED)
    
    airports_list = airports["airport_code"].tolist()
    tails_list = aircraft["tail_number"].tolist()
    airlines_list = list(AIRLINES_REF.keys())
    
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    date_range = (end_date - start_date).days
    
    flights = []
    
    # State tracking for tail numbers to compute realistic turnaround times & cascading late aircraft delays
    tail_last_arrival = {tail: start_date for tail in tails_list}
    
    for i in range(1, n_flights + 1):
        flight_id = f"FL_{200000 + i}"
        flight_date = start_date + timedelta(days=int(np.random.randint(0, date_range)))
        
        origin = np.random.choice(airports_list)
        dest = np.random.choice([a for a in airports_list if a != origin])
        airline = np.random.choice(airlines_list)
        tail = np.random.choice(tails_list)
        flight_num = np.random.randint(100, 5999)
        
        # Scheduled Departure Hour between 6 AM and 10 PM
        dep_hour = np.random.randint(6, 22)
        crs_dep_time = flight_date + timedelta(hours=dep_hour, minutes=int(np.random.choice([0, 15, 30, 45])))
        
        # Calculate turnaround buffer time
        last_arr = tail_last_arrival.get(tail, crs_dep_time - timedelta(hours=5))
        turnaround_buffer_mins = max(15, int((crs_dep_time - last_arr).total_seconds() / 60))
        if turnaround_buffer_mins > 600:
            turnaround_buffer_mins = 600 # Cap overnight rests
            
        # Distance & duration
        distance = int(np.random.uniform(300, 2600))
        crs_duration_mins = int(distance / 7.5 + np.random.normal(25, 5))
        crs_arr_time = crs_dep_time + timedelta(minutes=crs_duration_mins)
        
        # Delay simulation
        # Base probability of delay influenced by turnaround buffer & evening traffic
        prob_delay = 0.15 + (0.35 if turnaround_buffer_mins < 45 else 0.0) + (0.15 if dep_hour >= 16 else 0.0)
        is_delayed = np.random.random() < prob_delay
        
        if is_delayed:
            arr_delay_mins = int(np.random.exponential(45) + 15)
            dep_delay_mins = max(0, arr_delay_mins - int(np.random.normal(5, 10)))
            
            # Breakdown of delay
            if turnaround_buffer_mins < 45 and np.random.random() < 0.6:
                late_aircraft_delay = int(arr_delay_mins * 0.6)
                carrier_delay = int(arr_delay_mins * 0.2)
                weather_delay = 0
                nas_delay = arr_delay_mins - late_aircraft_delay - carrier_delay
                delay_reason = "Late Aircraft"
            elif np.random.random() < 0.3:
                weather_delay = int(arr_delay_mins * 0.7)
                nas_delay = arr_delay_mins - weather_delay
                carrier_delay = 0
                late_aircraft_delay = 0
                delay_reason = "Weather"
            else:
                carrier_delay = int(arr_delay_mins * 0.5)
                nas_delay = arr_delay_mins - carrier_delay
                weather_delay = 0
                late_aircraft_delay = 0
                delay_reason = "Carrier"
        else:
            arr_delay_mins = int(np.random.normal(-5, 8))
            dep_delay_mins = int(np.random.normal(-2, 5))
            carrier_delay = weather_delay = nas_delay = late_aircraft_delay = 0
            delay_reason = "None"
            
        # Cancellations & Diversions (< 2%)
        is_cancelled = 1 if np.random.random() < 0.018 else 0
        is_diverted = 1 if (is_cancelled == 0 and np.random.random() < 0.005) else 0
        
        if is_cancelled:
            arr_delay_mins = dep_delay_mins = 0
            actual_dep_time = actual_arr_time = None
            cancel_reason = np.random.choice(["Weather", "Carrier", "NAS", "Security"])
            taxi_out = taxi_in = wheels_off = wheels_on = air_time = 0
        else:
            cancel_reason = "None"
            actual_dep_time = crs_dep_time + timedelta(minutes=dep_delay_mins)
            actual_arr_time = crs_arr_time + timedelta(minutes=arr_delay_mins)
            taxi_out = int(np.random.uniform(12, 35))
            taxi_in = int(np.random.uniform(5, 18))
            wheels_off = actual_dep_time + timedelta(minutes=taxi_out) if actual_dep_time else None
            wheels_on = actual_arr_time - timedelta(minutes=taxi_in) if actual_arr_time else None
            air_time = max(20, crs_duration_mins + (arr_delay_mins - dep_delay_mins) - taxi_out - taxi_in)
            
            # Update last arrival for tail
            tail_last_arrival[tail] = actual_arr_time if actual_arr_time else crs_arr_time

        flights.append({
            "flight_id": flight_id,
            "flight_date": flight_date.strftime("%Y-%m-%d"),
            "crs_dep_time": crs_dep_time.strftime("%Y-%m-%d %H:%M:%S"),
            "crs_arr_time": crs_arr_time.strftime("%Y-%m-%d %H:%M:%S"),
            "actual_dep_time": actual_dep_time.strftime("%Y-%m-%d %H:%M:%S") if actual_dep_time else None,
            "actual_arr_time": actual_arr_time.strftime("%Y-%m-%d %H:%M:%S") if actual_arr_time else None,
            "airline_code": airline,
            "flight_number": flight_num,
            "tail_number": tail,
            "origin_airport": origin,
            "destination_airport": dest,
            "distance_miles": distance,
            "crs_duration_mins": crs_duration_mins,
            "air_time_mins": air_time,
            "dep_delay_mins": dep_delay_mins,
            "arr_delay_mins": arr_delay_mins,
            "taxi_out_mins": taxi_out,
            "taxi_in_mins": taxi_in,
            "cancelled_flag": is_cancelled,
            "cancellation_reason": cancel_reason,
            "diversion_flag": is_diverted,
            "delay_reason": delay_reason,
            "carrier_delay_mins": carrier_delay,
            "weather_delay_mins": weather_delay,
            "nas_delay_mins": nas_delay,
            "late_aircraft_delay_mins": late_aircraft_delay,
            "turnaround_buffer_mins": turnaround_buffer_mins
        })
        
    return pd.DataFrame(flights)

def run_ingestion(n_flights: int = 25000) -> Dict[str, pd.DataFrame]:
    """Orchestrates end-to-end data ingestion and storage."""
    logger.info("Starting Data Ingestion workflow...")
    df_airlines, df_airports, df_aircraft = generate_reference_tables()
    df_weather = generate_weather_data(df_airports, datetime(2024, 1, 1), datetime(2024, 12, 31))
    df_flights = generate_flights_data(n_flights, df_airports, df_aircraft)
    
    # Save raw tables
    save_dataframe(df_airlines, RAW_DATA_DIR / "airlines" / "airlines.csv")
    save_dataframe(df_airports, RAW_DATA_DIR / "airports" / "airports.csv")
    save_dataframe(df_aircraft, RAW_DATA_DIR / "flights" / "aircraft.csv")
    save_dataframe(df_weather, RAW_DATA_DIR / "weather" / "weather_hourly.csv")
    save_dataframe(df_flights, RAW_DATA_DIR / "flights" / "flights_raw.csv")
    
    logger.info("Ingestion complete. All raw tables stored.")
    return {
        "airlines": df_airlines,
        "airports": df_airports,
        "aircraft": df_aircraft,
        "weather": df_weather,
        "flights": df_flights
    }

if __name__ == "__main__":
    run_ingestion()
