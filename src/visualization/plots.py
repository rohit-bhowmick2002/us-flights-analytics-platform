"""
Visualization Module (`src/visualization/plots.py`)
Generates production charts corresponding to Executive, Airline, Airport, Route, and Weather BI dashboards.
"""
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from src.config import PROCESSED_DATA_DIR, SCREENSHOTS_DIR, AIRLINES_REF
from src.utils.logger import get_logger
from src.utils.helpers import load_dataframe

logger = get_logger("Visualization")

def set_style():
    sns.set_theme(style="whitegrid", palette="tab10")
    plt.rcParams["font.family"] = "sans-serif"

def generate_executive_dashboard(df: pd.DataFrame) -> None:
    """Creates a multi-panel Executive KPI overview chart."""
    set_style()
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("U.S. Commercial Aviation Operations — Executive BI Dashboard", fontsize=16, fontweight="bold", y=0.98)
    
    # Panel 1: On-Time vs Delayed vs Cancelled breakdown
    total_flights = len(df)
    cancelled = df["cancelled_flag"].sum()
    delayed = (df["arr_delay_mins"] >= 15).sum()
    ontime = total_flights - cancelled - delayed
    
    labels = ["On-Time (<15m)", "Delayed (>=15m)", "Cancelled"]
    sizes = [ontime, delayed, cancelled]
    colors = ["#2ca02c", "#ff7f0e", "#d62728"]
    
    axes[0, 0].pie(sizes, labels=labels, autopct="%1.1f%%", startangle=140, colors=colors, wedgeprops={"edgecolor":"w", 'linewidth': 1.5})
    axes[0, 0].set_title("Overall Flight Status Distribution", fontsize=13, fontweight="bold")
    
    # Panel 2: Hourly Departure Traffic & Delay Rate
    hourly = df.groupby("scheduled_dep_hour").agg(
        flights=("flight_id", "count"),
        delay_rate=("arr_delay_mins", lambda x: (x >= 15).mean() * 100)
    ).reset_index()
    
    ax2 = axes[0, 1]
    ax2.bar(hourly["scheduled_dep_hour"], hourly["flights"], color="#1f77b4", alpha=0.7, label="Flight Volume")
    ax2.set_xlabel("Scheduled Departure Hour (Local/UTC)", fontsize=11)
    ax2.set_ylabel("Total Scheduled Flights", fontsize=11, color="#1f77b4")
    
    ax2_twin = ax2.twinx()
    ax2_twin.plot(hourly["scheduled_dep_hour"], hourly["delay_rate"], color="#d62728", marker="o", linewidth=2, label="Delay Rate (%)")
    ax2_twin.set_ylabel("Delay Percentage (%)", fontsize=11, color="#d62728")
    ax2.set_title("Hourly Traffic Volume vs. Delay Rate (%)", fontsize=13, fontweight="bold")
    ax2.grid(False)
    
    # Panel 3: Monthly Operations Trend
    monthly = df.groupby("month").agg(
        total=("flight_id", "count"),
        delayed=("arr_delay_mins", lambda x: (x >= 15).sum())
    ).reset_index()
    
    axes[1, 0].plot(monthly["month"], monthly["total"], marker="o", linewidth=2.5, color="#1f77b4", label="Total Flights")
    axes[1, 0].plot(monthly["month"], monthly["delayed"], marker="s", linewidth=2.5, color="#ff7f0e", label="Delayed Flights")
    axes[1, 0].set_title("Monthly Flight & Delay Volume Trends", fontsize=13, fontweight="bold")
    axes[1, 0].set_xlabel("Month of Year", fontsize=11)
    axes[1, 0].set_ylabel("Number of Flights", fontsize=11)
    axes[1, 0].legend()
    
    # Panel 4: Delay Reason Breakdown (Total Minutes)
    reasons = {
        "Late Aircraft": df["late_aircraft_delay_mins"].sum(),
        "Carrier / Airline": df["carrier_delay_mins"].sum(),
        "Weather System": df["weather_delay_mins"].sum(),
        "NAS / Air Traffic": df["nas_delay_mins"].sum()
    }
    df_reasons = pd.DataFrame(list(reasons.items()), columns=["Reason", "Minutes"]).sort_values("Minutes", ascending=True)
    axes[1, 1].barh(df_reasons["Reason"], df_reasons["Minutes"] / 1e6, color="#9467bd")
    axes[1, 1].set_title("Root Cause of Delays (Million Cumulative Minutes)", fontsize=13, fontweight="bold")
    axes[1, 1].set_xlabel("Million Minutes", fontsize=11)
    
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(SCREENSHOTS_DIR / "executive_dashboard.png", dpi=300)
    plt.close()
    logger.info("Generated `executive_dashboard.png`.")

def generate_airline_dashboard(df: pd.DataFrame) -> None:
    """Creates Airline Performance Scorecard panel chart."""
    set_style()
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Airline Performance & Operational Reliability Scorecard", fontsize=15, fontweight="bold")
    
    # Panel 1: On-Time Performance % by Airline
    airline_perf = df.groupby("airline_code").agg(
        total=("flight_id", "count"),
        ontime_pct=("arr_delay_mins", lambda x: (x < 15).mean() * 100),
        cancel_pct=("cancelled_flag", lambda x: x.mean() * 100)
    ).reset_index()
    airline_perf["airline_name"] = airline_perf["airline_code"].map(AIRLINES_REF).fillna(airline_perf["airline_code"])
    airline_perf = airline_perf.sort_values("ontime_pct", ascending=False)
    
    sns.barplot(x="ontime_pct", y="airline_name", hue="airline_name", data=airline_perf, ax=axes[0], palette="Greens_r", legend=False)
    axes[0].set_title("On-Time Performance Rate (%) by Airline", fontsize=13, fontweight="bold")
    axes[0].set_xlabel("On-Time Percentage (%)", fontsize=11)
    axes[0].set_ylabel("Airline", fontsize=11)
    axes[0].set_xlim([0, 100])
    
    # Panel 2: Average Delay Minutes when Delayed
    delayed_flights = df[df["arr_delay_mins"] >= 15]
    avg_delay = delayed_flights.groupby("airline_code")["arr_delay_mins"].mean().reset_index()
    avg_delay["airline_name"] = avg_delay["airline_code"].map(AIRLINES_REF).fillna(avg_delay["airline_code"])
    avg_delay = avg_delay.sort_values("arr_delay_mins", ascending=True)
    
    sns.barplot(x="arr_delay_mins", y="airline_name", hue="airline_name", data=avg_delay, ax=axes[1], palette="Reds", legend=False)
    axes[1].set_title("Average Arrival Delay (Minutes) for Delayed Flights", fontsize=13, fontweight="bold")
    axes[1].set_xlabel("Average Minutes Delayed", fontsize=11)
    axes[1].set_ylabel("")
    
    plt.tight_layout()
    plt.savefig(SCREENSHOTS_DIR / "airline_dashboard.png", dpi=300)
    plt.close()
    logger.info("Generated `airline_dashboard.png`.")

def generate_airport_dashboard(df: pd.DataFrame) -> None:
    """Creates Airport Congestion and Delay Bottleneck Dashboard."""
    set_style()
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Hub Airport Operations & Bottleneck Heatmap", fontsize=15, fontweight="bold")
    
    # Panel 1: Top 10 Busiest Origin Airports by Flight Volume
    apt_vol = df["origin_airport"].value_counts().head(10).reset_index()
    apt_vol.columns = ["airport", "flights"]
    sns.barplot(x="flights", y="airport", hue="airport", data=apt_vol, ax=axes[0], palette="Blues_r", legend=False)
    axes[0].set_title("Busiest Origin Airports by Flight Volume", fontsize=13, fontweight="bold")
    axes[0].set_xlabel("Total Scheduled Departures", fontsize=11)
    axes[0].set_ylabel("IATA Airport Code", fontsize=11)
    
    # Panel 2: Origin Airport vs Average Taxi-Out Duration
    taxi_out = df.groupby("origin_airport")["taxi_out_mins"].mean().reset_index()
    taxi_out = taxi_out[taxi_out["origin_airport"].isin(apt_vol["airport"])].sort_values("taxi_out_mins", ascending=False)
    
    sns.barplot(x="taxi_out_mins", y="origin_airport", hue="origin_airport", data=taxi_out, ax=axes[1], palette="Purples_r", legend=False)
    axes[1].set_title("Average Taxi-Out Time (Minutes) by Hub", fontsize=13, fontweight="bold")
    axes[1].set_xlabel("Minutes on Tarmac before Takeoff", fontsize=11)
    axes[1].set_ylabel("")
    
    plt.tight_layout()
    plt.savefig(SCREENSHOTS_DIR / "airport_dashboard.png", dpi=300)
    plt.close()
    logger.info("Generated `airport_dashboard.png`.")

def generate_route_dashboard(df: pd.DataFrame) -> None:
    """Creates Top Routes and Corridor Performance Dashboard."""
    set_style()
    df["route"] = df["origin_airport"] + " -> " + df["destination_airport"]
    route_stats = df.groupby("route").agg(
        flights=("flight_id", "count"),
        avg_delay=("arr_delay_mins", "mean"),
        distance=("distance_miles", "first")
    ).reset_index()
    
    # Top 10 routes by volume
    top_routes = route_stats.sort_values("flights", ascending=False).head(10)
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Route Network Analysis & Corridor Performance", fontsize=15, fontweight="bold")
    
    sns.barplot(x="flights", y="route", hue="route", data=top_routes, ax=axes[0], palette="YlGnBu_r", legend=False)
    axes[0].set_title("Top 10 High-Volume Domestic Routes", fontsize=13, fontweight="bold")
    axes[0].set_xlabel("Scheduled Flights", fontsize=11)
    axes[0].set_ylabel("Route Pair", fontsize=11)
    
    # Top 10 most delayed routes (min 30 flights)
    delayed_routes = route_stats[route_stats["flights"] >= 30].sort_values("avg_delay", ascending=False).head(10)
    sns.barplot(x="avg_delay", y="route", hue="route", data=delayed_routes, ax=axes[1], palette="Oranges_r", legend=False)
    axes[1].set_title("Top 10 Most Delayed Routes (Min. 30 Flights)", fontsize=13, fontweight="bold")
    axes[1].set_xlabel("Average Arrival Delay (Minutes)", fontsize=11)
    axes[1].set_ylabel("")
    
    plt.tight_layout()
    plt.savefig(SCREENSHOTS_DIR / "route_dashboard.png", dpi=300)
    plt.close()
    logger.info("Generated `route_dashboard.png`.")

def generate_weather_dashboard(df: pd.DataFrame) -> None:
    """Creates Weather Impact Analytics Dashboard."""
    set_style()
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Meteorological & Environmental Impact on Flight Delays", fontsize=15, fontweight="bold")
    
    # Panel 1: Delay Rate by Weather Condition
    cond_stats = df.groupby("weather_condition").agg(
        flights=("flight_id", "count"),
        delay_rate=("arr_delay_mins", lambda x: (x >= 15).mean() * 100),
        avg_delay=("arr_delay_mins", "mean")
    ).reset_index()
    cond_stats = cond_stats[cond_stats["flights"] >= 20].sort_values("delay_rate", ascending=False)
    
    sns.barplot(x="delay_rate", y="weather_condition", hue="weather_condition", data=cond_stats, ax=axes[0], palette="magma", legend=False)
    axes[0].set_title("Flight Delay Rate (%) by Weather Condition", fontsize=13, fontweight="bold")
    axes[0].set_xlabel("Percentage of Flights Delayed (>=15m)", fontsize=11)
    axes[0].set_ylabel("Hourly Weather Station Observation", fontsize=11)
    
    # Panel 2: Wind Speed vs Delay Scatter/Boxplot
    df["wind_bin"] = pd.cut(df["wind_speed"], bins=[0, 10, 20, 30, 50], labels=["Calm (0-10kt)", "Breezy (10-20kt)", "Windy (20-30kt)", "Gale (>30kt)"])
    sns.boxplot(x="wind_bin", y="arr_delay_mins", hue="wind_bin", data=df[df["arr_delay_mins"].between(-30, 180)], ax=axes[1], palette="coolwarm", legend=False)
    axes[1].set_title("Arrival Delay Distribution by Wind Speed Category", fontsize=13, fontweight="bold")
    axes[1].set_xlabel("Wind Speed Range", fontsize=11)
    axes[1].set_ylabel("Arrival Delay (Minutes)", fontsize=11)
    
    plt.tight_layout()
    plt.savefig(SCREENSHOTS_DIR / "weather_dashboard.png", dpi=300)
    plt.close()
    logger.info("Generated `weather_dashboard.png`.")

def run_all_visualizations() -> None:
    logger.info("Starting batch dashboard visualization generation...")
    df = load_dataframe(PROCESSED_DATA_DIR / "flights_features.parquet")
    generate_executive_dashboard(df)
    generate_airline_dashboard(df)
    generate_airport_dashboard(df)
    generate_route_dashboard(df)
    generate_weather_dashboard(df)
    logger.info("All 5 core dashboard screenshot packages saved successfully.")

if __name__ == "__main__":
    run_all_visualizations()
