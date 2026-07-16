# Enterprise Aviation Analytics — Developer API & Reference Documentation (`api_documentation.md`)

This document provides complete technical specifications for the Python data engineering, graph operations research, machine learning inference engines, dbt transformation layers, and relational SQL views of the **Enterprise U.S. Flights Analytics Platform**.

---

## 1. Python Modular API (`src/`)

### 1.1 Graph Topology & Network Analytics (`src.analytics.network_graph.AviationNetworkGraph`)
#### `class AviationNetworkGraph()`
* **Description:** Models the U.S. National Airspace System (NAS) as a Directed Weighted Graph using `NetworkX`.
* **Methods:**
  * `build_graph(df_flights: pd.DataFrame = None) -> nx.DiGraph`
    * Constructs directed graph `G` where nodes are `airport_code` and edges are weighted by route frequency (`flight_count`), `avg_delay`, and `distance`.
  * `compute_centrality_metrics() -> pd.DataFrame`
    * Computes PageRank (`pagerank`), Betweenness Centrality (`betweenness_centrality`), and Node Degree (`total_node_degree`). Saves to `data/processed/airport_graph_metrics.parquet`.
  * `enrich_flight_features(df: pd.DataFrame) -> pd.DataFrame`
    * Merges origin and destination PageRank and Betweenness Centrality into the pre-flight ML feature matrix without leakage.
  * `simulate_delay_cascade(closed_airport: str = "ORD", closure_hours: int = 4) -> Dict[str, Any]`
    * Simulates how shutting down a major hub cascades delays across aircraft tail numbers (`tail_number`), reporting exact direct vs. cascading delay minutes and cascade multipliers (`~1.8x - 2.6x`).

---

### 1.2 Advanced SHAP Explainability & Interaction Engine (`src.models.shap_explainer`)
#### `run_shap_analysis() -> pd.DataFrame`
* **Description:** Computes exact Shapley Additive exPlanations (`shap.TreeExplainer`) over the trained `XGBoost` model (`xgboost.pkl`).
* **Artifacts Produced:**
  * **Beeswarm Chart:** `dashboards/screenshots/shap_beeswarm.png`
  * **Dependence Interaction Chart:** `dashboards/screenshots/shap_dependence_turnaround.png`
  * **Feature Ranking Table:** `reports/shap_feature_importance.csv`

---

### 1.3 Time-Series & Hub Capacity Forecaster (`src.models.forecaster.HubCapacityForecaster`)
#### `class HubCapacityForecaster()`
* **Description:** Multi-Horizon Time-Series Forecaster projecting daily departure volume, delayed operations, and severe delay surge alerts 14 days into the future.
* **Methods:**
  * `train_and_forecast(horizon_days: int = 14) -> pd.DataFrame`
    * Trains temporal lag models using `HistGradientBoostingRegressor` (`lag_1_flights`, `lag_2_flights`, `lag_7_flights`, `day_of_week`, `month`) across top hubs and recursively projects 14 days forward.
    * Output saved to `data/processed/hub_capacity_forecast_14d.parquet`.
  * `plot_forecast() -> None`
    * Generates `dashboards/screenshots/hub_capacity_forecast.png`.

---

### 1.4 Data Ingestion Module (`src.data.ingestion`)
#### `run_ingestion(n_flights: int = 25000) -> Dict[str, pd.DataFrame]`
* **Description:** Orchestrates the generation and storage of multi-table relational aviation datasets matching U.S. DOT BTS (`flights`, `airlines`, `airports`, `aircraft`) and NOAA ASOS (`weather_hourly`) schemas.

---

### 1.5 Data Preprocessing & Feature Engineering (`src.data.preprocessing` & `src.data.feature_engineering`)
#### `clean_flights(df_flights: pd.DataFrame) -> pd.DataFrame`
* **Description:** Parses schedule timestamps, standardizes delay null values for cancelled vs. non-cancelled flights, and removes invalid operational anomalies.

#### `run_feature_engineering() -> pd.DataFrame`
* **Description:** Computes pre-flight features without target leakage, incorporating graph centrality (`origin_betweenness_centrality`, `dest_pagerank`) and non-linear interactions (`turnaround_wind_interaction`, `congestion_weather_index`, `carrier_route_historical_risk`).

---

### 1.6 Machine Learning Inference Engine (`src.models.predict.FlightPredictor`)
#### `class FlightPredictor(model_name: str = "random_forest.pkl")`
* **Description:** Enterprise inference engine wrapping pre-trained scikit-learn preprocessing pipelines (`scaler.pkl`), classification models (`random_forest.pkl`, `xgboost.pkl`), and precision-recall optimized thresholds (`best_threshold.pkl`).

---

## 2. Apache Airflow & dbt Transformation API

### 2.1 Apache Airflow Master DAG (`dags/flights_etl_dag.py`)
* **DAG ID:** `enterprise_aviation_analytics_master_pipeline`
* **Schedule:** `0 2 * * *` (Daily at 02:00 UTC)
* **Task Sequence:** `ingest_raw_data -> clean_and_preprocess -> compute_graph_centrality -> leakage_free_feature_engineering -> train_xgboost_and_rf_models -> [compute_shap_explainability, run_14d_hub_capacity_forecaster] -> export_bi_dashboard_tables`

### 2.2 dbt Data Warehouse Models (`dbt/`)
* **Staging Layer:** `stg_flights.sql` (standardizes schedules & nulls), `stg_weather.sql` (hourly ASOS METAR truncation).
* **Marts Layer:** `fact_flights.sql` (dimensional join across staging schedules, origin weather observations, and graph centrality indices).
