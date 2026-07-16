"""
Data Validation & Quality Assurance Module (`src/data/validation.py`)
Executes automated data health checks across primary keys, null rates, and domain bounds.
"""
import pandas as pd
from typing import List, Dict, Any
from src.utils.logger import get_logger

logger = get_logger("DataValidation")

class DataValidator:
    """Performs rigorous data quality checks before pipeline progression."""
    
    @staticmethod
    def check_null_rates(df: pd.DataFrame, max_allowed_null_ratio: float = 0.05) -> Dict[str, float]:
        null_ratios = df.isnull().mean().to_dict()
        failed = {col: ratio for col, ratio in null_ratios.items() if ratio > max_allowed_null_ratio}
        if failed:
            logger.warning(f"Columns exceeding max null ratio ({max_allowed_null_ratio}): {failed}")
        else:
            logger.info("All columns passed null rate validation.")
        return null_ratios

    @staticmethod
    def check_domain_bounds(df: pd.DataFrame) -> bool:
        """Verifies physical limits (e.g., non-negative distances, valid months)."""
        checks = [
            ("Distance Non-Negative", (df["distance_miles"] >= 0).all()),
            ("Month Bounds (1-12)", df["month"].between(1, 12).all()),
            ("Day of Week Bounds (0-6)", df["day_of_week"].between(0, 6).all()),
            ("Scheduled Hour Bounds (0-23)", df["scheduled_dep_hour"].between(0, 23).all()),
        ]
        all_passed = True
        for name, passed in checks:
            if not passed:
                logger.error(f"Validation Check Failed: {name}")
                all_passed = False
            else:
                logger.info(f"Validation Check Passed: {name}")
        return all_passed

    @staticmethod
    def check_primary_key(df: pd.DataFrame, pk_col: str = "flight_id") -> bool:
        if pk_col not in df.columns:
            logger.error(f"Primary key column '{pk_col}' missing.")
            return False
        duplicates = df[pk_col].duplicated().sum()
        if duplicates > 0:
            logger.error(f"Primary key '{pk_col}' contains {duplicates:,} duplicate values.")
            return False
        logger.info(f"Primary key '{pk_col}' unique check passed.")
        return True

def run_validation(df: pd.DataFrame) -> bool:
    logger.info("Running Data Quality Validation Suite...")
    validator = DataValidator()
    pk_ok = validator.check_primary_key(df)
    bounds_ok = validator.check_domain_bounds(df)
    validator.check_null_rates(df)
    
    if pk_ok and bounds_ok:
        logger.info("Dataset passed all essential validation checks.")
        return True
    else:
        logger.error("Dataset failed one or more critical validation checks.")
        return False
