"""
Master Pipeline Orchestrator (`src/pipeline.py`)
Coordinates end-to-end execution of Ingestion, Preprocessing, Feature Engineering,
Model Training, Evaluation, Explainability, and BI Dashboard exports.
"""
import argparse
import sys
from pathlib import Path
from src.utils.logger import get_logger
from src.data.ingestion import run_ingestion
from src.data.preprocessing import run_preprocessing
from src.data.validation import run_validation
from src.analytics.network_graph import run_network_analytics
from src.data.feature_engineering import run_feature_engineering
from src.models.train import train_models
from src.models.evaluate import run_evaluation
from src.models.explainability import generate_feature_importance_plot
from src.models.shap_explainer import run_shap_analysis
from src.models.forecaster import run_capacity_forecasting
from src.visualization.plots import run_all_visualizations
from src.visualization.dashboard_data import export_dashboard_tables

logger = get_logger("MasterPipeline")

def run_pipeline(mode: str = "all", n_flights: int = 25000) -> bool:
    logger.info(f"=== Starting Enterprise Aviation Analytics Pipeline [Mode: {mode.upper()}] ===")
    
    if mode in ["all", "dry_run", "ingest_only"]:
        logger.info("Phase 1: Data Ingestion & Synthetic Generation")
        run_ingestion(n_flights=n_flights)
        if mode == "ingest_only":
            logger.info("Ingest-only mode specified. Exiting.")
            return True
            
    if mode in ["all", "dry_run", "preprocess"]:
        logger.info("Phase 2: Data Preprocessing & Clean Up")
        df_clean = run_preprocessing()
        
        logger.info("Phase 3: Automated Quality & Schema Validation")
        passed = run_validation(df_clean)
        if not passed:
            logger.error("Pipeline aborted due to data validation failures.")
            return False
            
    if mode in ["all", "dry_run", "feature_engineering"]:
        logger.info("Phase 3.5: Graph Network Topology & Centrality Calculation")
        run_network_analytics()
        
        logger.info("Phase 4: Leakage-Free Feature Engineering & Interaction Enrichment")
        run_feature_engineering()
        if mode == "dry_run":
            logger.info("Dry-run verification complete. Exiting before heavy ML training.")
            return True
            
    if mode in ["all", "train"]:
        logger.info("Phase 5: Machine Learning Model Training & Threshold Optimization")
        train_models()
        
        logger.info("Phase 6: Model Evaluation, SHAP Explainability & 14-Day Hub Forecasting")
        run_evaluation()
        generate_feature_importance_plot()
        run_shap_analysis()
        run_capacity_forecasting()
        
    if mode in ["all", "visualize"]:
        logger.info("Phase 7: BI Dashboard Visualization & Table Export")
        run_all_visualizations()
        export_dashboard_tables()
        
    logger.info("=== Master Pipeline Execution Completed Successfully ===")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aviation Analytics Platform Orchestrator")
    parser.add_argument("--mode", type=str, default="all", choices=["all", "dry_run", "ingest_only", "preprocess", "train", "visualize"],
                        help="Execution phase selection")
    parser.add_argument("--flights", type=int, default=25000, help="Number of synthetic flight records to generate")
    args = parser.parse_args()
    
    success = run_pipeline(mode=args.mode, n_flights=args.flights)
    sys.exit(0 if success else 1)
