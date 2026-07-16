"""
Helper Utilities (`src/utils/helpers.py`)
Common file I/O and formatting helpers.
"""
import os
import joblib
from pathlib import Path
from typing import Any
import pandas as pd
from src.utils.logger import get_logger

logger = get_logger("Helpers")

def save_pickle(obj: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(obj, path)
    logger.info(f"Saved artifact to {path}")

def load_pickle(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Artifact not found: {path}")
    return joblib.load(path)

def save_dataframe(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".parquet":
        try:
            df.to_parquet(path, index=False)
        except Exception:
            # Fallback to csv if parquet backend not installed
            df.to_csv(path.with_suffix(".csv"), index=False)
            logger.warning(f"Parquet engine failed, saved as CSV: {path.with_suffix('.csv')}")
    else:
        df.to_csv(path, index=False)
    logger.info(f"Saved DataFrame ({len(df):,} rows) to {path}")

def load_dataframe(path: Path) -> pd.DataFrame:
    if not path.exists():
        # Check if fallback csv exists
        if path.suffix == ".parquet" and path.with_suffix(".csv").exists():
            path = path.with_suffix(".csv")
        else:
            raise FileNotFoundError(f"File not found: {path}")
            
    if path.suffix == ".parquet":
        try:
            return pd.read_parquet(path)
        except Exception:
            if path.with_suffix(".csv").exists():
                path = path.with_suffix(".csv")
            else:
                raise
                
    df = pd.read_csv(path)
    # Parse standard datetime columns if present
    for col in ["flight_date", "crs_dep_time", "crs_arr_time", "actual_dep_time", "actual_arr_time"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df
