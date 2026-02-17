"""
Structured logging configuration using JSON format.

Benefits:
- Machine-parseable logs (easy to grep, search, analyze)
- Consistent format across all log messages
- Includes context: timestamp, level, module, function
- Pretty-printed in development, compact in production
"""

import logging
import sys
from pythonjsonlogger import jsonlogger

from app.core.config import settings


def setup_logging():
    """
    Configure application-wide logging.
    
    Creates a JSON formatter that outputs structured logs like:
    {
        "timestamp": "2026-02-14T10:30:00.123Z",
        "level": "INFO",
        "module": "health",
        "function": "check_health",
        "message": "Health check passed",
        "duration_ms": 5
    }
    """
    
    # Create root logger
    logger = logging.getLogger()
    logger.setLevel(settings.log_level)
    
    # Remove existing handlers (prevents duplicate logs)
    logger.handlers.clear()
    
    # Create console handler (outputs to terminal)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(settings.log_level)
    
    # JSON formatter with custom fields
    formatter = jsonlogger.JsonFormatter(
        fmt="%(timestamp)s %(level)s %(name)s %(funcName)s %(message)s",
        rename_fields={
            "levelname": "level",
            "name": "module",
            "funcName": "function",
            "asctime": "timestamp"
        },
        datefmt="%Y-%m-%dT%H:%M:%S"
    )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Log startup message
    logger.info(
        "Logging configured",
        extra={
            "log_level": settings.log_level,
            "environment": settings.environment
        }
    )
    
    return logger


# Create logger instance
# Import this in other modules: from app.core.logging_config import logger
logger = setup_logging()