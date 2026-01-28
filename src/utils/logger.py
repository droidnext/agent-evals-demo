"""Logging setup for the agent system."""

import logging
import sys
from typing import Optional


def setup_logger(name: str = "cruise_booking_agent", level: int = logging.INFO) -> logging.Logger:
    """Set up a logger for the agent system."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    return logger


def get_logger(name: str = "cruise_booking_agent") -> logging.Logger:
    """Get an existing logger or create a new one."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger
