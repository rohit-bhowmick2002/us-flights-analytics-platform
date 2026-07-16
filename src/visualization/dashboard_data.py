"""
Dashboard Data Exporter (`src/visualization/dashboard_data.py`)
Exports aggregated summary CSVs/Parquet tables for BI tools (Power BI, Tableau, Excel).
"""
import pandas as pd
from pathlib import Path
from src.config import PROCESSED_DATA_DIR, DASHBOARDS_DIR, AIRLINES_REF
from src.utils.logger import get_logger
from src.utils.helpers import load_dataframe, save_dataframe

logger = get_logger("DashboardExporter")

def export_dashboard_tables() -> None:
    logger.info("Exporting aggregated BI data tables to `dashboards/powerbi/`...")
    df = load_dataframe(PROCESSED_DATA_DIR / "flights_features.parquet")
    
    pb_dir = DASHBOARDS_DIR / "powerbi"
    pb_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Executive Summary Table
    exec_summary = pd.DataFrame([{
        "Total_Flights": len(df),
        "On_Time_Flights": len(df[(df["arr_delay_mins"] < 15) & (df["cancelled_flag"] == 0)]),
        "Delayed_Flights": len(df[df["arr_delay_mins"] >= 15]),
        "Cancelled_Flights": df["cancelled_flag"].sum(),
        "On_Time_Pct": round(len(df[(df["arr_delay_mins"] < 15) & (df["cancelled_flag"] == 0)]) / len(df) * 100, 2),
        "Cancellation_Rate_Pct": round(df["cancelled_flag"].mean() * 100, 2),
        "Average_Arrival_Delay_Mins": round(df["arr_delay_mins"].mean(), 2),
        "Average_Flight_Duration_Mins": round(df["air_time_mins"].mean(), 2)
    }])
    save_dataframe(exec_summary, pb_dir / "exec_summary_kpi.csv")
    
    # 2. Airline Scorecard Table
    airline_kpi = df.groupby("airline_code").agg(
        Total_Flights=("flight_id", "count"),
        On_Time_Pct=("arr_delay_mins", lambda x: round((x < 15).mean() * 100, 2)),
        Avg_Delay_Mins=("arr_delay_mins", lambda x: round(x.mean(), 2)),
        Cancellation_Rate_Pct=("cancelled_flag", lambda x: round(x.mean() * 100, 2)),
        Total_Carrier_Delay_Mins=("carrier_delay_mins", "sum")
    ).reset_index()
    airline_kpi["Airline_Name"] = airline_kpi["airline_code"].map(AIRLINES_REF).fillna(airline_kpi["airline_code"])
    save_dataframe(airline_kpi, pb_dir / "airline_scorecard.csv")
    
    # 3. Airport Metrics Table
    apt_kpi = df.groupby("origin_airport").agg(
        Total_Departures=("flight_id", "count"),
        Avg_Departure_Delay=("dep_delay_mins", lambda x: round(x.mean(), 2)),
        Avg_Taxi_Out_Mins=("taxi_out_mins", lambda x: round(x.mean(), 2)),
        Weather_Delay_Incidents=("weather_delay_mins", lambda x: (x > 0).sum())
    ).reset_index()
    save_dataframe(apt_kpi, pb_dir / "airport_metrics.csv")
    
    # 4. Route Popularity Table
    df["route_pair"] = df["origin_airport"] + "-" + df["destination_airport"]
    route_kpi = df.groupby("route_pair").agg(
        Scheduled_Flights=("flight_id", "count"),
        Avg_Route_Delay=("arr_delay_mins", lambda x: round(x.mean(), 2)),
        Distance_Miles=("distance_miles", "first")
    ).reset_index().sort_values("Scheduled_Flights", ascending=False)
    save_dataframe(route_kpi, pb_dir / "route_popularity.csv")
    
    logger.info("Successfully exported 4 core BI data models to `dashboards/powerbi/`.")

if __name__ == "__main__":
    export_dashboard_tables()
