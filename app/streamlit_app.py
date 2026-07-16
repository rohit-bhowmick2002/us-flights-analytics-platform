"""
Enterprise Aviation Analytics — Interactive Web Application (`app/streamlit_app.py`)
Run using: `streamlit run app/streamlit_app.py`
"""
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Ensure project root in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.config import PROCESSED_DATA_DIR, SCREENSHOTS_DIR, AIRLINES_REF, TOP_AIRPORTS
from app.prediction import StreamlitPredictor

st.set_page_config(page_title="Enterprise Aviation Analytics", page_icon="✈️", layout="wide")

# Header
st.title("✈️ Enterprise U.S. Aviation Analytics & Delay Prediction AI")
st.markdown("---")

# Navigation Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Executive Operations BI", "🔮 Pre-Flight Delay Predictor AI", "🧠 SHAP Explainability & Graph AI", "📁 Dataset Explorer"])

with tab1:
    st.header("Executive Business Intelligence & Operational Reliability")
    col1, col2 = st.columns(2)
    with col1:
        exec_img = SCREENSHOTS_DIR / "executive_dashboard.png"
        if exec_img.exists():
            st.image(str(exec_img), caption="Executive KPI Summary", use_container_width=True)
        else:
            st.info("Run `python src/pipeline.py --mode visualize` to generate dashboard screenshots.")
            
    with col2:
        air_img = SCREENSHOTS_DIR / "airline_dashboard.png"
        if air_img.exists():
            st.image(str(air_img), caption="Airline Reliability Scorecard", use_container_width=True)
            
    st.markdown("---")
    col3, col4 = st.columns(2)
    with col3:
        apt_img = SCREENSHOTS_DIR / "airport_dashboard.png"
        if apt_img.exists():
            st.image(str(apt_img), caption="Hub Airport Bottleneck Heatmap", use_container_width=True)
    with col4:
        wx_img = SCREENSHOTS_DIR / "weather_dashboard.png"
        if wx_img.exists():
            st.image(str(wx_img), caption="Weather Impact Analysis", use_container_width=True)

with tab2:
    st.header("🔮 Pre-Flight ML Delay Predictor (Strict Leakage-Free Architecture)")
    st.markdown("Predict the exact probability and duration of a flight delay **24 hours before departure** without target leakage.")
    
    predictor = st.session_state.get("predictor")
    if predictor is None:
        predictor = StreamlitPredictor()
        st.session_state["predictor"] = predictor
        
    form_col1, form_col2, form_col3 = st.columns(3)
    with form_col1:
        airline = st.selectbox("Airline Carrier", options=list(AIRLINES_REF.keys()), format_func=lambda x: f"{x} - {AIRLINES_REF[x]}")
        origin = st.selectbox("Origin Airport", options=TOP_AIRPORTS, index=0)
        dest = st.selectbox("Destination Airport", options=TOP_AIRPORTS, index=1)
        distance = st.number_input("Route Distance (Miles)", min_value=100, max_value=5000, value=1250)
        
    with form_col2:
        month = st.slider("Month of Travel", 1, 12, 7)
        day_of_week = st.slider("Day of Week (0=Mon, 6=Sun)", 0, 6, 4)
        dep_hour = st.slider("Scheduled Departure Hour", 5, 23, 16)
        is_holiday = st.checkbox("Peak Holiday Week Travel", value=False)
        
    with form_col3:
        turnaround_buffer = st.number_input("Turnaround Buffer from Inbound Flight (Mins)", min_value=15, max_value=300, value=35)
        wind_speed = st.number_input("Forecast Wind Speed (Knots)", min_value=0.0, max_value=60.0, value=15.0)
        visibility = st.number_input("Forecast Visibility (Miles)", min_value=0.1, max_value=10.0, value=10.0)
        precip = st.number_input("Forecast Precipitation (Inches)", min_value=0.0, max_value=4.0, value=0.0)
        
    if st.button("🚀 Predict Operational Performance", type="primary"):
        inputs = {
            "month": month,
            "day_of_week": day_of_week,
            "scheduled_dep_hour": dep_hour,
            "is_holiday": int(is_holiday),
            "is_weekend": int(day_of_week in [5, 6]),
            "distance_miles": distance,
            "aircraft_age": 10,
            "turnaround_buffer_mins": turnaround_buffer,
            "origin_hourly_traffic": 60,
            "carrier_30day_delay_rate": 0.22,
            "forecast_temp": 65.0,
            "forecast_wind_speed": wind_speed,
            "forecast_visibility": visibility,
            "forecast_precip": precip,
            "is_bad_weather": int(wind_speed > 22 or visibility < 3 or precip > 0.1),
            "airline_code": airline,
            "origin_airport": origin,
            "destination_airport": dest
        }
        res = predictor.predict_delay(inputs)
        
        st.subheader("Prediction Inference Results")
        r_col1, r_col2, r_col3 = st.columns(3)
        with r_col1:
            st.metric("Delay Probability (%)", f"{res['delay_probability_pct']}%")
        with r_col2:
            st.metric("Expected Arrival Delay", f"{res['expected_delay_minutes']} mins")
        with r_col3:
            risk_color = "🔴" if res["risk_level"] == "HIGH" else ("🟡" if res["risk_level"] == "MEDIUM" else "🟢")
            st.metric("Operational Risk Level", f"{risk_color} {res['risk_level']}")

with tab3:
    st.header("🧠 Advanced SHAP Explainability & Network Graph AI")
    st.markdown("Unlike black-box models, this platform utilizes **exact Shapley Additive exPlanations (SHAP)** and **NetworkX Directed Graph Centrality** to explain what drives every operational delay.")
    
    col_shap1, col_shap2 = st.columns(2)
    with col_shap1:
        beeswarm_img = SCREENSHOTS_DIR / "shap_beeswarm.png"
        if beeswarm_img.exists():
            st.image(str(beeswarm_img), caption="SHAP Beeswarm Feature Impact Ranking", use_container_width=True)
        else:
            st.info("Run `python src/models/shap_explainer.py` to generate SHAP Beeswarm plot.")
            
    with col_shap2:
        dep_img = SCREENSHOTS_DIR / "shap_dependence_turnaround.png"
        if dep_img.exists():
            st.image(str(dep_img), caption="SHAP Dependence: Turnaround Buffer x Wind Speed", use_container_width=True)
            
    st.markdown("---")
    st.subheader("🌐 Network Graph Topology Centrality Metrics (`src/analytics/network_graph.py`)")
    graph_path = PROCESSED_DATA_DIR / "airport_graph_metrics.parquet"
    if graph_path.exists() or graph_path.with_suffix(".csv").exists():
        df_g = load_dataframe(graph_path)
        st.dataframe(df_g, use_container_width=True)

with tab4:
    st.header("📁 Processed Data Lake Explorer")
    data_path = PROCESSED_DATA_DIR / "flights_features.parquet"
    if data_path.with_suffix(".csv").exists() or data_path.exists():
        if data_path.exists():
            df_show = pd.read_parquet(data_path)
        else:
            df_show = pd.read_csv(data_path.with_suffix(".csv"))
        st.dataframe(df_show.head(100), use_container_width=True)
    else:
        st.warning("Data lake empty. Run `python src/pipeline.py --mode all` to generate dataset.")
