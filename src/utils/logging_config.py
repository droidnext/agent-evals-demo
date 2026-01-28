"""Enhanced logging configuration with structured logging support."""

import logging
import sys
from pathlib import Path
from typing import Optional
import structlog
from pythonjsonlogger import jsonlogger
import os


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    log_file: Optional[str] = None,
    enable_console: bool = True,
) -> None:
    """
    Setup enhanced logging with structlog and JSON formatting.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format type ('json' or 'text')
        log_file: Optional path to log file
        enable_console: Whether to enable console logging
    """
    # Get log level
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logs directory if log_file is specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer() if log_format == "json" 
            else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )
    
    # Configure standard logging
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[]
    )
    
    # Setup handlers
    handlers = []
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        if log_format == "json":
            json_formatter = jsonlogger.JsonFormatter(
                "%(timestamp)s %(level)s %(name)s %(message)s",
                rename_fields={"levelname": "level", "asctime": "timestamp"}
            )
            console_handler.setFormatter(json_formatter)
        else:
            console_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
        
        handlers.append(console_handler)
    
    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        
        json_formatter = jsonlogger.JsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s %(pathname)s %(lineno)d",
            rename_fields={"levelname": "level", "asctime": "timestamp"}
        )
        file_handler.setFormatter(json_formatter)
        
        handlers.append(file_handler)
    
    # Apply handlers to root logger
    root_logger = logging.getLogger()
    root_logger.handlers = handlers
    root_logger.setLevel(level)


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a configured structlog logger.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


def configure_from_env() -> None:
    """Configure logging from environment variables."""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_format = os.getenv("LOG_FORMAT", "json")
    log_file = os.getenv("LOG_FILE", "logs/agent-evals.log")
    
    setup_logging(
        log_level=log_level,
        log_format=log_format,
        log_file=log_file,
        enable_console=True
    )


# Initialize logging on import
configure_from_env()
