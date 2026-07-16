"""
Hub Capacity & Disruption Surge Forecaster Page (`app/pages/03_Hub_Capacity_Forecaster.py`)
Run via main app or: `streamlit run app/pages/03_Hub_Capacity_Forecaster.py`
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.config import PROCESSED_DATA_DIR, TOP_AIRPORTS
from src.utils.helpers import load_dataframe

st.set_page_config(page_title="Hub Capacity Forecaster", page_icon="📈", layout="wide")

st.title("📈 14-Day Hub Capacity & Disruption Surge Forecaster")
st.markdown("Temporal Gradient Boosting projections anticipating daily flight volumes, delay rates, and high-surge risk windows up to two weeks in advance.")
st.markdown("---")

fc_path = PROCESSED_DATA_DIR / "hub_capacity_forecast_14d.parquet"
if fc_path.exists() or fc_path.with_suffix(".csv").exists():
    df_fc = load_dataframe(fc_path)
else:
    st.info("Run `python src/models/forecaster.py` to generate 14-day operational capacity projections.")
    df_fc = pd.DataFrame()

if not df_fc.empty:
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        sel_hub = st.selectbox("Select Hub Airport for Deep-Dive", options=TOP_AIRPORTS, index=0)
    with col_filter2:
        alert_filter = st.multiselect("Filter by Surge Alert Risk", options=["NORMAL", "MODERATE", "HIGH SURGE ALERT"], default=["NORMAL", "MODERATE", "HIGH SURGE ALERT"])
        
    df_sub = df_fc[(df_fc["airport_code"] == sel_hub) & (df_fc["disruption_surge_alert"].isin(alert_filter))].copy()
    
    # Summary Metrics for selected hub
    avg_vol = df_sub["projected_flight_volume"].mean() if not df_sub.empty else 0
    max_del_rate = df_sub["projected_delay_rate_pct"].max() if not df_sub.empty else 0
    surge_days = (df_sub["disruption_surge_alert"] == "HIGH SURGE ALERT").sum()
    
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric("14-Day Average Daily Departures", f"{int(avg_vol):,}")
    with col_m2:
        st.metric("Peak Projected Delay Rate (%)", f"{max_del_rate:.1f}%")
    with col_m3:
        st.metric("Projected Severe Surge Days", f"{surge_days} days", delta=f"{'⚠️ Risk Window' if surge_days > 0 else '🟢 Stable'}", delta_color="inverse")
        
    st.subheader(f"📅 Daily Operational Projection Table — {sel_hub}")
    st.dataframe(df_sub, use_container_width=True)
