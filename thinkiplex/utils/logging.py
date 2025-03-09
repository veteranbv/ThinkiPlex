"""
Logging utilities for ThinkiPlex.

This module provides functions for configuring and managing logging.
"""

import logging
import os
from typing import Optional


def setup_logging(
    log_file: Optional[str] = None, level: int = logging.INFO
) -> logging.Logger:
    """Set up logging for ThinkiPlex.

    Args:
        log_file: Path to log file (if None, logs to console only)
        level: Logging level

    Returns:
        Configured logger
    """
    # Create logger
    logger = logging.getLogger("thinkiplex")
    logger.setLevel(level)

    # Create formatter
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Create file handler if log file is specified
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger() -> logging.Logger:
    """Get the ThinkiPlex logger.

    Returns:
        ThinkiPlex logger
    """
    return logging.getLogger("thinkiplex")
