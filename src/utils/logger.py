"""
Logging Module (`src/utils/logger.py`)
Provides standardized console and file logging.
"""
import logging
import sys
from pathlib import Path
from src.config import PROJECT_ROOT

def get_logger(name: str = "AviationAnalytics", log_file: str = "pipeline.log") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # File handler
        log_dir = PROJECT_ROOT / "reports"
        log_dir.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_dir / log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
    return logger
