"""
Time-Series & Hub Capacity Forecasting (`src/models/forecaster.py`)
Forecasts daily scheduled operations, passenger volume, and severe delay surge risk 14 days in advance.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from sklearn.ensemble import HistGradientBoostingRegressor
from src.config import PROCESSED_DATA_DIR, SCREENSHOTS_DIR, TOP_AIRPORTS
from src.utils.logger import get_logger
from src.utils.helpers import load_dataframe, save_dataframe

logger = get_logger("TimeForecaster")

class HubCapacityForecaster:
    """Multi-Horizon Time-Series Forecaster for Hub Operations & Disruption Surge Days."""
    
    def __init__(self):
        self.models = {}
        self.forecast_df = pd.DataFrame()

    def create_daily_series(self, df_flights: pd.DataFrame) -> pd.DataFrame:
        """Aggregates flight records into daily time-series by hub airport."""
        logger.info("Aggregating daily time-series metrics per hub airport...")
        df_flights["flight_date"] = pd.to_datetime(df_flights["flight_date"])
        
        daily = df_flights.groupby(["origin_airport", "flight_date"]).agg(
            total_flights=("flight_id", "count"),
            delayed_flights=("arr_delay_mins", lambda x: (x >= 15).sum()),
            severe_delayed_flights=("arr_delay_mins", lambda x: (x >= 45).sum()),
            avg_delay_mins=("arr_delay_mins", "mean")
        ).reset_index()
        
        # Sort and create lag features
        daily = daily.sort_values(["origin_airport", "flight_date"]).reset_index(drop=True)
        
        # Add temporal predictors
        daily["day_of_week"] = daily["flight_date"].dt.dayofweek
        daily["month"] = daily["flight_date"].dt.month
        daily["is_weekend"] = daily["day_of_week"].isin([5, 6]).astype(int)
        
        # Create rolling lag features per airport
        for lag in [1, 2, 7]:
            daily[f"lag_{lag}_flights"] = daily.groupby("origin_airport")["total_flights"].shift(lag)
            daily[f"lag_{lag}_delay_rate"] = daily.groupby("origin_airport")["delayed_flights"].shift(lag) / daily.groupby("origin_airport")["total_flights"].shift(lag)
            
        daily = daily.dropna().reset_index(drop=True)
        return daily

    def train_and_forecast(self, horizon_days: int = 14) -> pd.DataFrame:
        """Trains temporal lag models and projects operations 14 days forward."""
        logger.info(f"Training temporal forecasters and projecting {horizon_days} days forward...")
        df_flights = load_dataframe(PROCESSED_DATA_DIR / "flights_cleaned.parquet")
        daily = self.create_daily_series(df_flights)
        
        forecast_records = []
        last_date = daily["flight_date"].max()
        
        for apt in TOP_AIRPORTS:
            df_apt = daily[daily["origin_airport"] == apt].copy()
            if len(df_apt) < 10:
                continue
                
            features = ["day_of_week", "month", "is_weekend", "lag_1_flights", "lag_2_flights", "lag_7_flights"]
            X = df_apt[features]
            y_vol = df_apt["total_flights"]
            y_delay = df_apt["delayed_flights"]
            
            # Train models
            model_vol = HistGradientBoostingRegressor(random_state=42).fit(X, y_vol)
            model_del = HistGradientBoostingRegressor(random_state=42).fit(X, y_delay)
            
            # Recursive multi-step projection
            last_row = df_apt.iloc[-1]
            lag_1_f = last_row["total_flights"]
            lag_2_f = df_apt.iloc[-2]["total_flights"] if len(df_apt) >= 2 else lag_1_f
            lag_7_f = df_apt.iloc[-7]["total_flights"] if len(df_apt) >= 7 else lag_1_f
            
            for d in range(1, horizon_days + 1):
                proj_date = last_date + timedelta(days=d)
                dow = proj_date.dayofweek
                month = proj_date.month
                is_wk = int(dow in [5, 6])
                
                x_pred = pd.DataFrame([{
                    "day_of_week": dow,
                    "month": month,
                    "is_weekend": is_wk,
                    "lag_1_flights": lag_1_f,
                    "lag_2_flights": lag_2_f,
                    "lag_7_flights": lag_7_f
                }])
                
                pred_vol = max(10, int(round(model_vol.predict(x_pred)[0])))
                pred_del = max(0, min(pred_vol, int(round(model_del.predict(x_pred)[0]))))
                delay_rate_pct = round(pred_del / max(1, pred_vol) * 100, 1)
                
                # Surge risk flag (>25% predicted delayed)
                surge_risk = "HIGH SURGE ALERT" if delay_rate_pct >= 28.0 else ("MODERATE" if delay_rate_pct >= 18.0 else "NORMAL")
                
                forecast_records.append({
                    "airport_code": apt,
                    "forecast_date": proj_date.strftime("%Y-%m-%d"),
                    "projected_flight_volume": pred_vol,
                    "projected_delayed_flights": pred_del,
                    "projected_delay_rate_pct": delay_rate_pct,
                    "disruption_surge_alert": surge_risk
                })
                
                # Shift lags for next step
                lag_7_f = lag_2_f
                lag_2_f = lag_1_f
                lag_1_f = pred_vol
                
        self.forecast_df = pd.DataFrame(forecast_records)
        save_path = PROCESSED_DATA_DIR / "hub_capacity_forecast_14d.parquet"
        save_dataframe(self.forecast_df, save_path)
        logger.info(f"Saved 14-day capacity forecast across {len(TOP_AIRPORTS)} hubs successfully.")
        self.plot_forecast()
        return self.forecast_df

    def plot_forecast(self) -> None:
        """Generates Hub Capacity & Surge Forecast visualization."""
        if self.forecast_df.empty:
            return
            
        logger.info("Plotting Hub Capacity & Disruption Surge chart (`hub_capacity_forecast.png`)...")
        plt.figure(figsize=(12, 6))
        
        # Plot projected volume and delay rates for top 4 hubs
        top_4 = TOP_AIRPORTS[:4]
        df_sub = self.forecast_df[self.forecast_df["airport_code"].isin(top_4)].copy()
        df_sub["forecast_date"] = pd.to_datetime(df_sub["forecast_date"])
        
        sns.lineplot(x="forecast_date", y="projected_flight_volume", hue="airport_code", data=df_sub, marker="o", linewidth=2.5)
        plt.title("14-Day Hub Departure Capacity & Operations Forecast", fontsize=14, fontweight="bold", pad=15)
        plt.xlabel("Forecast Date", fontsize=11)
        plt.ylabel("Projected Daily Departures", fontsize=11)
        plt.grid(axis="y", linestyle="--", alpha=0.7)
        plt.tight_layout()
        plt.savefig(SCREENSHOTS_DIR / "hub_capacity_forecast.png", dpi=300)
        plt.close()

def run_capacity_forecasting() -> pd.DataFrame:
    forecaster = HubCapacityForecaster()
    df_fc = forecaster.train_and_forecast(horizon_days=14)
    logger.info(f"Sample Forecast Output:\n{df_fc.head(6).to_string(index=False)}")
    return df_fc

if __name__ == "__main__":
    run_capacity_forecasting()
