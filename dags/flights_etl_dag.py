"""
Apache Airflow Orchestration DAG (`dags/flights_etl_dag.py`)
Automates daily data ingestion, validation, graph topology enrichment, feature engineering,
model training, and BI dashboard updates.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "aviation_data_team",
    "depends_on_past": False,
    "email": ["alerts@enterprise-aviation.ai"],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="enterprise_aviation_analytics_master_pipeline",
    default_args=default_args,
    description="Daily automated ETL, Graph Topology, ML Retraining, and BI Export DAG",
    schedule_interval="0 2 * * *",  # Runs daily at 02:00 UTC
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["aviation", "etl", "machine_learning", "graph_topology", "bi_exports"],
) as dag:

    # Task 1: Ingest Raw Schedules & Hourly ASOS Weather
    ingest_task = BashOperator(
        task_id="ingest_raw_data",
        bash_command="PYTHONPATH=/home/user/us-flights-analytics-platform python3 /home/user/us-flights-analytics-platform/src/pipeline.py --mode ingest_only --flights 25000"
    )

    # Task 2: Data Cleaning & Preprocessing
    preprocess_task = BashOperator(
        task_id="clean_and_preprocess",
        bash_command="PYTHONPATH=/home/user/us-flights-analytics-platform python3 /home/user/us-flights-analytics-platform/src/pipeline.py --mode preprocess"
    )

    # Task 3: Graph Topology & Centrality Calculation
    graph_topology_task = BashOperator(
        task_id="compute_graph_centrality",
        bash_command="PYTHONPATH=/home/user/us-flights-analytics-platform python3 /home/user/us-flights-analytics-platform/src/analytics/network_graph.py"
    )

    # Task 4: Feature Engineering
    feature_eng_task = BashOperator(
        task_id="leakage_free_feature_engineering",
        bash_command="PYTHONPATH=/home/user/us-flights-analytics-platform python3 -c 'from src.data.feature_engineering import run_feature_engineering; run_feature_engineering()'"
    )

    # Task 5: Model Retraining & Threshold Optimization
    ml_train_task = BashOperator(
        task_id="train_xgboost_and_rf_models",
        bash_command="PYTHONPATH=/home/user/us-flights-analytics-platform python3 -c 'from src.models.train import train_models; train_models()'"
    )

    # Task 6: SHAP Explainability & Interaction Computation
    shap_task = BashOperator(
        task_id="compute_shap_explainability",
        bash_command="PYTHONPATH=/home/user/us-flights-analytics-platform python3 /home/user/us-flights-analytics-platform/src/models/shap_explainer.py"
    )

    # Task 7: 14-Day Hub Capacity & Disruption Forecaster
    forecast_task = BashOperator(
        task_id="run_14d_hub_capacity_forecaster",
        bash_command="PYTHONPATH=/home/user/us-flights-analytics-platform python3 /home/user/us-flights-analytics-platform/src/models/forecaster.py"
    )

    # Task 8: BI Export & Visualizations
    bi_export_task = BashOperator(
        task_id="export_bi_dashboard_tables",
        bash_command="PYTHONPATH=/home/user/us-flights-analytics-platform python3 /home/user/us-flights-analytics-platform/src/pipeline.py --mode visualize"
    )

    # Define DAG Task Flow
    ingest_task >> preprocess_task >> graph_topology_task >> feature_eng_task >> ml_train_task >> [shap_task, forecast_task] >> bi_export_task
